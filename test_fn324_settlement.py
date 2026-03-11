#!/usr/bin/env python3
"""
FN-324 Settlement Test: Replicate parlay order_details in failed/rejected states

Scenarios:
  1. SP_TIMEOUT: Create → SP Offer → User Confirm → SKIP SP Ack → order_details='failed'
  2. NO_CONFIRM: Create → SP Offer → SKIP User Confirm → let offer expire → order_details='rejected'
  3. EARLY_REFUND: Create → SP Offer (very low max_risk) → User Confirm large stake
     → partial match → UnmatchedStake >= minRefundAmount → refund

The fix is already on sandbox. This script validates that parlay_ml lines
with order_details in (failed, rejected) get properly settled (not stuck in 'tbd').

Usage:
    python3 test_fn324_settlement.py --event 20023353
    python3 test_fn324_settlement.py --event 20023353 --scenario sp_timeout
    python3 test_fn324_settlement.py --event 20023353 --scenario all --count 5
"""

import requests
import json
import time
import random
import argparse
import uuid
import sys
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)-8s %(message)s',
    handlers=[
        logging.FileHandler(f'fn324_test_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

BASE_URL = "https://api-ss-sandbox.betprophet.co"

# Patron credentials (usr004)
USER_CREDS = {
    "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
    "email": "lam.tran+usr004@betprophet.co",
    "password": "Kh0ngbiet1"
}

# SP credentials
SP1_CREDS = {
    "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
    "secret_key": "67344329e054349f07e7a29249dcadeb"
}


def auth_user():
    """Authenticate patron user, return token"""
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json=USER_CREDS)
    if resp.status_code == 200:
        token = resp.json().get("accessToken")
        log.info(f"User auth OK")
        return token
    log.error(f"User auth FAILED: {resp.status_code} {resp.text[:200]}")
    return None


def auth_sp(creds, name="SP1"):
    """Authenticate SP, return token"""
    resp = requests.post(f"{BASE_URL}/partner/auth/login", json=creds,
                         headers={"Content-Type": "application/json"})
    if resp.status_code == 200:
        token = resp.json()["data"]["access_token"]
        log.info(f"{name} auth OK")
        return token
    log.error(f"{name} auth FAILED: {resp.status_code}")
    return None


def fetch_market_lines(sp_token, event_id):
    """Fetch market lines for a specific event via MM get_multiple_markets endpoint"""
    url = f"{BASE_URL}/partner/mm/get_multiple_markets"
    headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
    resp = requests.get(url, params={'event_ids': str(event_id)}, headers=headers)
    if resp.status_code != 200:
        log.error(f"Fetch market lines failed: {resp.status_code} {resp.text[:200]}")
        return []

    lines = []
    seen = set()
    data = resp.json().get("data", {})
    for event_id_str, markets in data.items():
        eid = int(event_id_str)
        for market in markets:
            market_id = market.get("id")
            selections_sources = []
            if 'selections' in market:
                selections_sources = market.get('selections', [])
            elif 'market_lines' in market:
                for ml in market.get('market_lines', []):
                    selections_sources.extend(ml.get('selections', []))

            for selections_group in selections_sources:
                for selection in selections_group:
                    line_id = selection.get('line_id')
                    if line_id and line_id not in seen:
                        seen.add(line_id)
                        lines.append({
                            "lineId": line_id,
                            "marketId": market_id,
                            "outcomeId": selection.get("outcome_id"),
                            "sportEventId": eid,
                            "line": selection.get("line", 0)
                        })
    log.info(f"Fetched {len(lines)} market lines for event {event_id}")
    return lines


def pick_random_legs(all_lines, num_legs=2):
    """Pick random legs for a same-game parlay"""
    if len(all_lines) < num_legs:
        return all_lines[:num_legs]
    return random.sample(all_lines, num_legs)


def create_parlay(user_token, market_lines):
    """Step 1: User creates parlay request"""
    url = f"{BASE_URL}/parlay/api/v1/user/request"
    payload = {"marketLines": market_lines}
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}

    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 200:
        parlay_id = resp.json()["data"]["parlayId"]
        log.info(f"Created parlay: {parlay_id}")
        return parlay_id
    log.error(f"Create parlay failed: {resp.status_code} - {resp.text[:300]}")
    return None


def sp_offer(parlay_id, sp_token, market_lines, odds=300, max_risk_cents=50000):
    """Step 2: SP provides offer"""
    url = f"{BASE_URL}/parlay/sp/orders/offers"
    valid_until = int((time.time() + 60) * 1e9)

    leg_odds = []
    for _ in market_lines:
        leg_odds.append(random.randint(-300, 300) or 110)

    payload = {
        "parlay_id": parlay_id,
        "offers": [{
            "odds": odds,
            "max_risk": max_risk_cents,
            "valid_until": valid_until,
            "estimated_prices": [
                {"line_id": line["lineId"], "odds": leg_odds[idx]}
                for idx, line in enumerate(market_lines)
            ]
        }]
    }
    headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 200:
        log.info(f"SP offer OK for {parlay_id} (odds=+{odds}, max_risk=${max_risk_cents/100:.2f})")
        return True
    log.error(f"SP offer failed: {resp.status_code} - {resp.text[:200]}")
    return False


def user_confirm(parlay_id, user_token, odds=300, stake_cents=5000):
    """Step 3: User confirms bet"""
    url = f"{BASE_URL}/parlay/api/v1/user/confirm"
    payload = {"parlayId": parlay_id, "odds": odds, "stake": stake_cents}
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 200:
        log.info(f"User confirmed {parlay_id} (stake=${stake_cents/100:.2f})")
        return True
    log.error(f"User confirm failed: {resp.status_code} - {resp.text[:200]}")
    return False


def sp_acknowledge(parlay_id, sp_token, market_lines, stake_cents, odds):
    """Step 4: SP acknowledges confirmation"""
    # First find the order
    orders_url = f"{BASE_URL}/parlay/sp/orders"
    headers = {"Authorization": f"Bearer {sp_token}"}
    resp = requests.get(orders_url, headers=headers)
    if resp.status_code != 200:
        log.error(f"Get orders failed: {resp.status_code}")
        return False

    orders = resp.json()["data"]["orders"]
    order_uuid = None
    for order in orders:
        if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
            order_uuid = order["order_uuid"]
            break

    if not order_uuid:
        matching = [o for o in orders if o["p_id"] == parlay_id]
        statuses = [o['status'] for o in matching] if matching else ['not found']
        log.warning(f"No 'sent_confirmation' order for {parlay_id}, statuses: {statuses}")
        return False

    # Calculate probabilities
    num_legs = len(market_lines)
    base_prob = 0.5 ** (1 / num_legs) if num_legs > 0 else 0.5
    leg_probs = [base_prob] * num_legs

    combined_prob = 1.0
    for p in leg_probs:
        combined_prob *= p
    max_risk_dollars = (stake_cents / 100) * (1 / combined_prob - 1)
    max_risk_c = int(max_risk_dollars * 100)

    confirm_url = f"{BASE_URL}/parlay/sp/orders/confirmations"
    payload = {
        "action": "accept",
        "confirmed_stake": stake_cents / 100,
        "price_probability": [{
            "lines": [
                {"line_id": line["lineId"], "probability": leg_probs[idx]}
                for idx, line in enumerate(market_lines)
            ],
            "max_risk": max_risk_c,
            "vig": 0.1
        }],
        "signature": f"fn324_test_{int(time.time())}"
    }
    resp = requests.post(confirm_url, json=payload, headers=headers,
                         params={"order_uuid": order_uuid})
    if resp.status_code == 200:
        log.info(f"SP acknowledged {parlay_id}")
        return True
    log.error(f"SP ack failed: {resp.status_code} - {resp.text[:200]}")
    return False


# ============================================================================
# SCENARIO RUNNERS
# ============================================================================

def scenario_sp_timeout(user_token, sp_token, all_lines, idx):
    """
    Scenario: SP_TIMEOUT → order_details.status = 'failed'

    Flow: Create → SP Offer → User Confirm → SKIP SP Acknowledgment
    The SP never acknowledges, so the order times out → status becomes 'failed'.
    """
    log.info(f"\n{'='*80}")
    log.info(f"  SCENARIO {idx}: SP_TIMEOUT (skip SP ack → order_details='failed')")
    log.info(f"{'='*80}")

    legs = pick_random_legs(all_lines, num_legs=random.randint(2, 3))
    odds = random.randint(200, 500)
    stake = random.randint(1000, 5000)  # $10-$50

    parlay_id = create_parlay(user_token, legs)
    if not parlay_id:
        return None

    time.sleep(0.5)
    if not sp_offer(parlay_id, sp_token, legs, odds=odds, max_risk_cents=stake * 5):
        return None

    time.sleep(1.5)
    if not user_confirm(parlay_id, user_token, odds=odds, stake_cents=stake):
        return None

    # DELIBERATELY SKIP SP acknowledgment
    log.info(f"  >>> SKIPPING SP acknowledgment for {parlay_id}")
    log.info(f"  >>> Order will timeout → order_details.status should become 'failed'")
    log.info(f"  >>> parlay_ml.settlement_status should be settled (not stuck in 'tbd')")

    return parlay_id


def scenario_no_confirm(user_token, sp_token, all_lines, idx):
    """
    Scenario: NO_CONFIRM → order_details.status = 'rejected'

    Flow: Create → SP Offer → SKIP User Confirm
    User never confirms, offer expires → status becomes 'rejected'.
    """
    log.info(f"\n{'='*80}")
    log.info(f"  SCENARIO {idx}: NO_CONFIRM (skip user confirm → order_details='rejected')")
    log.info(f"{'='*80}")

    legs = pick_random_legs(all_lines, num_legs=random.randint(2, 3))
    odds = random.randint(200, 500)

    parlay_id = create_parlay(user_token, legs)
    if not parlay_id:
        return None

    time.sleep(0.5)
    if not sp_offer(parlay_id, sp_token, legs, odds=odds, max_risk_cents=20000):
        return None

    # DELIBERATELY SKIP user confirm
    log.info(f"  >>> SKIPPING user confirm for {parlay_id}")
    log.info(f"  >>> Offer will expire → order_details.status should become 'rejected'")
    log.info(f"  >>> parlay_ml.settlement_status should be settled (not stuck in 'tbd')")

    return parlay_id


def scenario_early_refund(user_token, sp_token, all_lines, idx):
    """
    Scenario: EARLY_REFUND → partial match, unmatched stake refunded

    Flow: Create → SP Offer with very low max_risk → User Confirm with larger stake
    UnmatchedStake = RequestedStake - MatchedStake >= minRefundAmount → refund
    """
    log.info(f"\n{'='*80}")
    log.info(f"  SCENARIO {idx}: EARLY_REFUND (low max_risk → partial match → refund)")
    log.info(f"{'='*80}")

    legs = pick_random_legs(all_lines, num_legs=random.randint(2, 3))
    odds = random.randint(200, 400)
    # SP offers very low max_risk but user confirms with much higher stake
    low_max_risk = 100  # $1 max risk from SP
    high_stake = 10000  # $100 stake from user

    parlay_id = create_parlay(user_token, legs)
    if not parlay_id:
        return None

    time.sleep(0.5)
    if not sp_offer(parlay_id, sp_token, legs, odds=odds, max_risk_cents=low_max_risk):
        return None

    time.sleep(1.5)
    if not user_confirm(parlay_id, user_token, odds=odds, stake_cents=high_stake):
        return None

    # SP acknowledges but with low max_risk → partial match
    time.sleep(2.0)
    ack_ok = sp_acknowledge(parlay_id, sp_token, legs, high_stake, odds)

    log.info(f"  >>> SP ack result: {ack_ok}")
    log.info(f"  >>> SP max_risk=${low_max_risk/100:.2f} vs User stake=${high_stake/100:.2f}")
    log.info(f"  >>> UnmatchedStake should trigger early refund")
    log.info(f"  >>> parlay_ml.settlement_status should be settled (not stuck in 'tbd')")

    return parlay_id


def run_test(event_id, scenario='all', count=3):
    """Run FN-324 settlement test scenarios"""
    log.info("=" * 80)
    log.info("  FN-324 SETTLEMENT TEST")
    log.info("=" * 80)
    log.info(f"  Event:     {event_id}")
    log.info(f"  Scenario:  {scenario}")
    log.info(f"  Count:     {count} per scenario")
    log.info("=" * 80)

    # Auth
    user_token = auth_user()
    sp_token = auth_sp(SP1_CREDS, "SP1")
    if not user_token or not sp_token:
        log.error("Auth failed, aborting")
        return

    # Fetch market lines
    all_lines = fetch_market_lines(sp_token, event_id)
    if not all_lines:
        log.error("No market lines, aborting")
        return

    results = {
        'sp_timeout': [],
        'no_confirm': [],
        'early_refund': []
    }

    scenarios = {
        'sp_timeout': scenario_sp_timeout,
        'no_confirm': scenario_no_confirm,
        'early_refund': scenario_early_refund,
    }

    if scenario == 'all':
        run_scenarios = list(scenarios.keys())
    else:
        run_scenarios = [scenario]

    for sc_name in run_scenarios:
        sc_func = scenarios[sc_name]
        for i in range(1, count + 1):
            p_id = sc_func(user_token, sp_token, all_lines, i)
            if p_id:
                results[sc_name].append(p_id)
            time.sleep(1)

    # Summary
    log.info(f"\n{'='*80}")
    log.info(f"  FN-324 TEST SUMMARY")
    log.info(f"{'='*80}")
    total = 0
    for sc_name in run_scenarios:
        ids = results[sc_name]
        total += len(ids)
        log.info(f"\n  {sc_name.upper()} ({len(ids)} parlays):")
        for pid in ids:
            log.info(f"    p_id = {pid}")

    log.info(f"\n  Total parlays created: {total}")
    log.info(f"\n  VALIDATION SQL (run on sandbox DB):")
    log.info(f"  ---")
    all_pids = [pid for sc in run_scenarios for pid in results[sc]]
    if all_pids:
        pid_list = ",".join(f"'{p}'" for p in all_pids)
        log.info(f"  -- Check order_details status:")
        log.info(f"  SELECT p_id, status, created_at FROM order_details WHERE p_id IN ({pid_list});")
        log.info(f"")
        log.info(f"  -- Check parlay_ml settlement_status (should NOT be stuck in 'tbd'):")
        log.info(f"  SELECT parlay_ml.* FROM parlay_ml_relations")
        log.info(f"  JOIN parlay_ml ON parlay_ml_relations.line_id = parlay_ml.line_id")
        log.info(f"  WHERE parlay_ml_relations.p_id IN ({pid_list});")
        log.info(f"")
        log.info(f"  -- General check for stuck settlements:")
        log.info(f"  SELECT parlay_ml.* FROM parlay_ml_relations")
        log.info(f"  JOIN parlay_ml ON parlay_ml_relations.line_id = parlay_ml.line_id")
        log.info(f"  JOIN order_details ON order_details.p_id = parlay_ml_relations.p_id")
        log.info(f"  WHERE order_details.status IN ('failed','rejected')")
        log.info(f"  AND parlay_ml.settlement_status = 'tbd'")
        log.info(f"  ORDER BY parlay_ml.created_at DESC LIMIT 20;")
    log.info(f"{'='*80}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FN-324 Settlement Test')
    parser.add_argument('--event', type=int, required=True, help='Event ID')
    parser.add_argument('--scenario', type=str, default='all',
                        choices=['all', 'sp_timeout', 'no_confirm', 'early_refund'],
                        help='Which scenario to run (default: all)')
    parser.add_argument('--count', type=int, default=3,
                        help='Number of parlays per scenario (default: 3)')
    args = parser.parse_args()

    run_test(args.event, args.scenario, args.count)

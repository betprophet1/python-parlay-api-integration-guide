#!/usr/bin/env python3
"""
Reproduce FN-324: settle parlay market line even when order status is failed/rejected/early-refund

3 cases:
  1. FAILED: User places parlay → SP confirm timeout (we skip SP acknowledge step)
  2. REJECTED: User places parlay → we never send SP offer → parlay times out as rejected
  3. EARLY REFUND: User places parlay → SP offers partial match → UnmatchedStake triggers refund

Usage:
  python3 reproduce_fn324.py --event 30024944
"""

import requests
import json
import time
import sys
import os
import argparse
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import config

BASE_URL = 'https://api-ss-sandbox.betprophet.co'

# ─── Auth helpers ────────────────────────────────────────────────────────────

def user_login() -> str:
    """Login as patron user, return access token"""
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
        "email": "lam.tran+usr004@betprophet.co",
        "password": "Kh0ngbiet1"
    })
    resp.raise_for_status()
    token = resp.json()["accessToken"]
    print(f"  User token: ...{token[-20:]}")
    return token


def sp_login() -> str:
    """Login as SP (MM), return access token"""
    resp = requests.post(f"{BASE_URL}/partner/auth/login", json={
        "access_key": config.MM_KEYS['access_key'],
        "secret_key": config.MM_KEYS['secret_key'],
    })
    resp.raise_for_status()
    token = resp.json()['data']['access_token']
    print(f"  SP token:   ...{token[-20:]}")
    return token


# ─── Market helpers ──────────────────────────────────────────────────────────

def get_lines_for_event(sp_token: str, event_id: int) -> list:
    """Fetch market lines for a specific event"""
    headers = {"Authorization": f"Bearer {sp_token}"}
    resp = requests.get(
        f"{BASE_URL}/partner/mm/get_multiple_markets",
        params={"event_ids": str(event_id)},
        headers=headers
    )
    resp.raise_for_status()
    data = resp.json().get("data", {})
    event_markets = data.get(str(event_id), [])

    lines = []
    for market in event_markets:
        market_id = market.get("id")
        if "selections" in market:
            for group in market.get("selections", []):
                for sel in group:
                    if sel.get("line_id"):
                        lines.append({
                            "line": sel.get("line", 0),
                            "lineId": sel["line_id"],
                            "marketId": market_id,
                            "outcomeId": sel.get("outcome_id"),
                            "sportEventId": event_id,
                        })
        elif "market_lines" in market:
            for ml in market.get("market_lines", []):
                for group in ml.get("selections", []):
                    for sel in group:
                        if sel.get("line_id"):
                            lines.append({
                                "line": sel.get("line", 0),
                                "lineId": sel["line_id"],
                                "marketId": market_id,
                                "outcomeId": sel.get("outcome_id"),
                                "sportEventId": event_id,
                            })
    return lines


def pick_legs(lines: list, n: int = 2) -> list:
    """Pick n legs from different markets"""
    by_market = {}
    for l in lines:
        mid = l["marketId"]
        if mid not in by_market:
            by_market[mid] = []
        by_market[mid].append(l)

    markets = list(by_market.keys())
    random.shuffle(markets)
    picked = []
    for mid in markets:
        if len(picked) >= n:
            break
        picked.append(random.choice(by_market[mid]))
    return picked


# ─── Parlay flow helpers ─────────────────────────────────────────────────────

def create_parlay(user_token: str, legs: list) -> str:
    """Step 1-3: User requests parlay, returns parlay_id"""
    resp = requests.post(
        f"{BASE_URL}/parlay/api/v1/user/request",
        json={"marketLines": legs},
        headers={"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"},
    )
    if resp.status_code != 200:
        print(f"    Create parlay failed: {resp.status_code} {resp.text[:200]}")
        return None
    p_id = resp.json()["data"]["parlayId"]
    return p_id


def sp_offer(sp_token: str, parlay_id: str, legs: list, odds: int = 200, max_risk: int = 50000) -> bool:
    """Step 4: SP sends offer"""
    leg_odds = [random.choice([-150, -200, 150, 200]) for _ in legs]
    valid_until = int((time.time() + 60) * 1e9)
    payload = {
        "parlay_id": parlay_id,
        "offers": [{
            "odds": odds,
            "max_risk": max_risk,
            "valid_until": valid_until,
            "estimated_prices": [
                {"line_id": l["lineId"], "odds": leg_odds[i]}
                for i, l in enumerate(legs)
            ],
        }],
    }
    resp = requests.post(
        f"{BASE_URL}/parlay/sp/orders/offers",
        json=payload,
        headers={"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"},
    )
    return resp.status_code == 200


def user_confirm(user_token: str, parlay_id: str, odds: int = 200, stake: int = 100) -> bool:
    """Step 5: User confirms bet"""
    resp = requests.post(
        f"{BASE_URL}/parlay/api/v1/user/confirm",
        json={"parlayId": parlay_id, "odds": odds, "stake": stake},
        headers={"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"},
    )
    return resp.status_code == 200


def get_sp_orders(sp_token: str, parlay_id: str) -> list:
    """Get SP orders for a parlay"""
    resp = requests.get(
        f"{BASE_URL}/parlay/sp/orders",
        headers={"Authorization": f"Bearer {sp_token}"},
    )
    if resp.status_code != 200:
        return []
    orders = resp.json().get("data", {}).get("orders", [])
    return [o for o in orders if o.get("p_id") == parlay_id]


# ─── Reproduction cases ─────────────────────────────────────────────────────

def case_failed_sp_timeout(user_token: str, sp_token: str, lines: list) -> str:
    """
    CASE 1 - FAILED (SP confirm timeout):
    User places parlay → SP offers → User confirms → SP NEVER acknowledges → timeout → FAILED
    """
    print("\n" + "=" * 70)
    print("CASE 1: FAILED (SP confirm timeout)")
    print("  Flow: request → SP offer → user confirm → [SP never acknowledges] → timeout")
    print("=" * 70)

    legs = pick_legs(lines, n=2)
    print(f"  Legs: {len(legs)} from event(s)")
    for i, l in enumerate(legs):
        print(f"    Leg {i+1}: market={l['marketId']} outcome={l['outcomeId']} line={l['line']} lineId=...{l['lineId'][-12:]}")

    # Step 1-3: Create parlay
    p_id = create_parlay(user_token, legs)
    if not p_id:
        print("  SKIP - could not create parlay")
        return None
    print(f"  p_id: {p_id}")

    # Step 4: SP offers
    odds = 200
    ok = sp_offer(sp_token, p_id, legs, odds=odds)
    print(f"  SP offer: {'OK' if ok else 'FAILED'}")
    if not ok:
        print("  SKIP - SP offer failed")
        return p_id

    # Step 5: User confirms
    ok = user_confirm(user_token, p_id, odds=odds, stake=100)
    print(f"  User confirm: {'OK' if ok else 'FAILED'}")

    # Step 6: SKIP SP acknowledge — this causes timeout → FAILED
    print("  SP acknowledge: SKIPPED (intentional - will timeout → FAILED)")
    print(f"\n  >>> p_id = {p_id}")
    print(f"  >>> Expected order_details.status = 'failed' (after SP confirm timeout)")

    # Check orders
    time.sleep(2)
    orders = get_sp_orders(sp_token, p_id)
    if orders:
        for o in orders:
            print(f"  Current order status: {o.get('status')} (order_uuid: {o.get('order_uuid')})")

    return p_id


def case_rejected_no_offer(user_token: str, sp_token: str, lines: list) -> str:
    """
    CASE 2 - REJECTED (no SP offer / timeout):
    User places parlay → SP NEVER offers → parlay times out → REJECTED
    """
    print("\n" + "=" * 70)
    print("CASE 2: REJECTED (SP never offers)")
    print("  Flow: request → [SP never offers] → timeout → rejected")
    print("=" * 70)

    legs = pick_legs(lines, n=2)
    print(f"  Legs: {len(legs)} from event(s)")
    for i, l in enumerate(legs):
        print(f"    Leg {i+1}: market={l['marketId']} outcome={l['outcomeId']} line={l['line']} lineId=...{l['lineId'][-12:]}")

    # Step 1-3: Create parlay
    p_id = create_parlay(user_token, legs)
    if not p_id:
        print("  SKIP - could not create parlay")
        return None
    print(f"  p_id: {p_id}")

    # SKIP everything else — no SP offer
    print("  SP offer: SKIPPED (intentional - will timeout → REJECTED)")
    print(f"\n  >>> p_id = {p_id}")
    print(f"  >>> Expected order_details.status = 'rejected' (after offer timeout)")

    return p_id


def case_early_refund(user_token: str, sp_token: str, lines: list) -> str:
    """
    CASE 3 - EARLY REFUND (partial match, unmatched stake refunded):
    User places parlay → SP offers with very low max_risk → user confirms large stake
    → partial match → UnmatchedStake >= minRefundAmount → early refund
    """
    print("\n" + "=" * 70)
    print("CASE 3: EARLY REFUND (partial match → unmatched stake refund)")
    print("  Flow: request → SP offer (low max_risk) → user confirm (high stake)")
    print("         → partial match → UnmatchedStake >= minRefundAmount → refund")
    print("=" * 70)

    legs = pick_legs(lines, n=2)
    print(f"  Legs: {len(legs)} from event(s)")
    for i, l in enumerate(legs):
        print(f"    Leg {i+1}: market={l['marketId']} outcome={l['outcomeId']} line={l['line']} lineId=...{l['lineId'][-12:]}")

    # Step 1-3: Create parlay
    p_id = create_parlay(user_token, legs)
    if not p_id:
        print("  SKIP - could not create parlay")
        return None
    print(f"  p_id: {p_id}")

    # Step 4: SP offers with very low max_risk ($1 = 100 cents)
    odds = 200
    ok = sp_offer(sp_token, p_id, legs, odds=odds, max_risk=100)
    print(f"  SP offer (max_risk=$1): {'OK' if ok else 'FAILED'}")
    if not ok:
        print("  SKIP - SP offer failed")
        return p_id

    # Step 5: User confirms with higher stake ($50 = 5000 cents)
    ok = user_confirm(user_token, p_id, odds=odds, stake=5000)
    print(f"  User confirm (stake=$50): {'OK' if ok else 'FAILED'}")

    # Step 6: SP acknowledges with minimal confirmed_stake to force partial match
    orders = get_sp_orders(sp_token, p_id)
    if orders:
        order = orders[0]
        order_uuid = order.get("order_uuid")
        status = order.get("status")
        print(f"  Order status: {status}, order_uuid: {order_uuid}")

        if status == "sent_confirmation" and order_uuid:
            # Acknowledge with minimal stake
            confirm_url = f"{BASE_URL}/parlay/sp/orders/confirmations"
            payload = {
                "action": "accept",
                "confirmed_stake": 1.0,  # Only $1 confirmed
                "price_probability": [{
                    "lines": [
                        {"line_id": l["lineId"], "probability": 0.5}
                        for l in legs
                    ],
                    "max_risk": 100,
                    "vig": 0.1,
                }],
                "signature": f"fn324_test_{int(time.time())}",
            }
            resp = requests.post(
                confirm_url,
                json=payload,
                headers={"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"},
                params={"order_uuid": order_uuid},
            )
            print(f"  SP acknowledge ($1 confirmed of $50 requested): {resp.status_code}")
            if resp.status_code != 200:
                print(f"    Response: {resp.text[:200]}")
    else:
        print("  No orders found for this parlay yet")

    print(f"\n  >>> p_id = {p_id}")
    print(f"  >>> Expected: early refund (UnmatchedStake = $49 >= minRefundAmount)")

    # Wait and check again
    time.sleep(2)
    orders = get_sp_orders(sp_token, p_id)
    if orders:
        for o in orders:
            print(f"  Final order status: {o.get('status')}")

    return p_id


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Reproduce FN-324")
    parser.add_argument("--event", type=int, required=True, help="Event ID to target")
    parser.add_argument("--case", type=str, default="all", choices=["all", "failed", "rejected", "early_refund"],
                        help="Which case to reproduce (default: all)")
    args = parser.parse_args()

    print("=" * 70)
    print("  FN-324 REPRODUCTION: settle parlay ML even when order failed/rejected")
    print(f"  Target event: {args.event}")
    print(f"  Cases: {args.case}")
    print("=" * 70)

    # Auth
    print("\n--- Authentication ---")
    user_token = user_login()
    sp_token = sp_login()

    # Get lines
    print(f"\n--- Fetching lines for event {args.event} ---")
    lines = get_lines_for_event(sp_token, args.event)
    print(f"  Found {len(lines)} lines across {len(set(l['marketId'] for l in lines))} markets")

    if len(lines) < 2:
        print("  ERROR: Need at least 2 lines from different markets")
        return

    results = {}

    if args.case in ("all", "failed"):
        results["failed"] = case_failed_sp_timeout(user_token, sp_token, lines)

    if args.case in ("all", "rejected"):
        results["rejected"] = case_rejected_no_offer(user_token, sp_token, lines)

    if args.case in ("all", "early_refund"):
        results["early_refund"] = case_early_refund(user_token, sp_token, lines)

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY - Parlay IDs to check in Nova / SQL")
    print("=" * 70)
    for case_name, p_id in results.items():
        print(f"  {case_name:15s}: p_id = {p_id or 'SKIPPED'}")

    print("\n--- SQL queries to verify ---")
    for case_name, p_id in results.items():
        if p_id:
            print(f"\n  -- {case_name}:")
            print(f"  SELECT parlay_ml.* FROM parlay_ml_relations")
            print(f"  JOIN parlay_ml ON parlay_ml_relations.line_id = parlay_ml.line_id")
            print(f"  WHERE p_id = '{p_id}';")

    print(f"\n  -- Find all failed orders with tbd settlement:")
    print(f"  SELECT parlay_ml.* FROM parlay_ml_relations")
    print(f"  JOIN parlay_ml ON parlay_ml_relations.line_id = parlay_ml.line_id")
    print(f"  JOIN order_details ON order_details.p_id = parlay_ml_relations.p_id")
    print(f"  WHERE order_details.status = 'failed' AND parlay_ml.settlement_status = 'tbd'")
    print(f"  ORDER BY created_at DESC LIMIT 10;")

    print(f"\n  -- Same for rejected:")
    print(f"  SELECT parlay_ml.* FROM parlay_ml_relations")
    print(f"  JOIN parlay_ml ON parlay_ml_relations.line_id = parlay_ml.line_id")
    print(f"  JOIN order_details ON order_details.p_id = parlay_ml_relations.p_id")
    print(f"  WHERE order_details.status = 'rejected' AND parlay_ml.settlement_status = 'tbd'")
    print(f"  ORDER BY created_at DESC LIMIT 10;")

    print("\n  Nova line IDs to check:")
    for case_name, p_id in results.items():
        if p_id:
            # Print the line IDs used
            print(f"  {case_name}: check lines in Nova for p_id={p_id}")

    print("\n" + "=" * 70)
    print("  Done. Check Nova & SQL to verify settlement_status stays 'tbd'")
    print("  for failed/rejected orders (FN-324 fix).")
    print("=" * 70)


if __name__ == "__main__":
    main()

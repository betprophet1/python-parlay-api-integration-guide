#!/usr/bin/env python3
"""
SSE-1855 QA Test: Verify matched_wager_id is persisted in void_match transactions.

Test flow:
  1. Login as SP → post liquidity on an active event
  2. Login as test user → place market order (matched against SP)
  3. Void the user's wager via Nova admin API
  4. Query the wager's transactions
  5. Check if void_match transactions have matched_wager populated

Expected:
  - If fix works: void_match tx has matched_wager: {refId: "partner_xxx", ...}
  - If fix is broken: void_match tx has matched_wager: null

Usage:
  python3 test_sse1855_void_match.py                        # place wager, then void via Nova UI
  python3 test_sse1855_void_match.py --check-only REF_ID    # check transactions after manual void
"""

import argparse
import json
import re
import sys
import time
import uuid

import requests

# ── Config ──────────────────────────────────────────────────────────────────
BASE_URL = "https://api-ss-sandbox.betprophet.co"
NOVA_URL = "http://nova-ss-sandbox.betprophet.io"

USER_EMAIL = "lam.tran+usr004@betprophet.co"
USER_PASSWORD = "Kh0ngbiet1"
DEVICE_ID = "sse1855-qa-test"

NOVA_EMAIL = "admin@betprophet.com"
NOVA_PASSWORD = "Testing@123"

SP_ACCESS_KEY = "3324857df2d66566dfe6b660faa2923f"
SP_SECRET_KEY = "8c970658226e64c7346e753ed7377c48"

DEFAULT_STAKE = 1.00  # small stake for test


# ── Helpers ─────────────────────────────────────────────────────────────────

def log(msg, level="INFO"):
    prefix = {"INFO": "   ", "PASS": " ✅", "FAIL": " ❌", "WARN": " ⚠️ ", "STEP": " ▶ "}
    print(f"{prefix.get(level, '   ')} {msg}")


def trade_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "__source": "web",
        "x-currency": "cash",
    }


def sp_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ── SP (Market Maker) ──────────────────────────────────────────────────────

def login_sp():
    """Login as SP / market maker."""
    log("Logging in as SP...", "STEP")
    resp = requests.post(f"{BASE_URL}/partner/auth/login", json={
        "access_key": SP_ACCESS_KEY,
        "secret_key": SP_SECRET_KEY,
    })
    resp.raise_for_status()
    token = resp.json()["data"]["access_token"]
    log("SP logged in")
    return token


def find_event_and_lines(sp_token):
    """Find an active event with a 2-sided market (e.g. moneyline).
    Returns both sides' line_ids so SP can post on one and user bets on the other.
    """
    log("Finding active event with 2-sided market...", "STEP")

    # Get upcoming events from public API
    resp = requests.get(f"{BASE_URL}/trade/public/api/v1/events",
                        params={"type": "upcoming", "limit": 20})
    resp.raise_for_status()
    events = resp.json().get("data", [])
    if not events:
        log("No upcoming events found!", "FAIL")
        sys.exit(1)

    log(f"Found {len(events)} upcoming events, checking for 2-sided markets...")

    for event in events:
        event_id = event["id"]
        event_name = event.get("name", str(event_id))

        # Get markets via partner API
        resp = requests.get(f"{BASE_URL}/partner/mm/get_markets",
                            params={"event_id": event_id},
                            headers=sp_headers(sp_token))
        if resp.status_code != 200:
            continue

        markets = resp.json().get("data", {}).get("markets", [])
        for market in markets:
            # Only look at moneyline (2 sides, no line value)
            if market.get("type") != "moneyline":
                continue

            # Collect all line_ids from selections
            all_lines = []
            selections = market.get("selections", [])
            for sel_group in selections:
                if not sel_group or not isinstance(sel_group, list):
                    continue
                for sel in sel_group:
                    if not sel:
                        continue
                    lid = sel.get("line_id")
                    name = sel.get("name", sel.get("outcome_name", "?"))
                    if lid:
                        all_lines.append({"line_id": lid, "name": name})

            # Need at least 2 sides
            if len(all_lines) >= 2:
                market_name = market.get("name", "?")
                log(f"Found: event={event_name}, market={market_name}")
                log(f"  Side A: {all_lines[0]['name']} (line={all_lines[0]['line_id']})")
                log(f"  Side B: {all_lines[1]['name']} (line={all_lines[1]['line_id']})")
                return (event_id, event_name, market_name,
                        all_lines[0]["line_id"], all_lines[0]["name"],
                        all_lines[1]["line_id"], all_lines[1]["name"])

    log("No 2-sided markets found!", "FAIL")
    sys.exit(1)


def post_sp_liquidity(sp_token, line_id, stake, odds=100):
    """Post SP liquidity (place SP wager) so user can match against it."""
    log(f"Posting SP liquidity: line={line_id}, odds={odds}, stake=${stake}...", "STEP")
    ext_id = f"sse1855_test_{uuid.uuid4().hex[:10]}"

    resp = requests.post(f"{BASE_URL}/partner/mm/place_wager",
                         headers=sp_headers(sp_token),
                         json={
                             "external_id": ext_id,
                             "line_id": line_id,
                             "odds": odds,
                             "stake": stake,
                         })
    if resp.status_code != 200:
        log(f"SP place_wager failed: {resp.status_code} {resp.text[:300]}", "FAIL")
        sys.exit(1)

    data = resp.json().get("data", {})
    wager = data.get("wager", {})
    sp_wager_id = wager.get("id", "?")
    log(f"SP wager placed: id={sp_wager_id}, external_id={ext_id}")
    return sp_wager_id, ext_id


# ── User ────────────────────────────────────────────────────────────────────

def login_user():
    """Login as test user."""
    log("Logging in as test user...", "STEP")
    resp = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
        "email": USER_EMAIL,
        "password": USER_PASSWORD,
        "device_id": DEVICE_ID,
    })
    resp.raise_for_status()
    token = resp.json()["accessToken"]
    log(f"Logged in as {USER_EMAIL}")
    return token


def place_market_order(user_token, line_id, stake):
    """Estimate odds and place a market order."""
    log(f"Estimating odds for line={line_id}, stake=${stake}...", "STEP")
    est_resp = requests.post(
        f"{BASE_URL}/trade/private/api/v1/market-orders/estimate-odds",
        headers=trade_headers(user_token),
        json={"lineId": line_id, "stake": stake},
    )
    if est_resp.status_code != 200:
        log(f"Estimate failed: {est_resp.status_code} {est_resp.text[:300]}", "FAIL")
        sys.exit(1)

    est_data = est_resp.json().get("data", {})
    avail = est_data.get("availableStake", 0)
    odds = est_data.get("expectedAverageOdds", 0)
    odds_list = est_data.get("oddsList", [])
    log(f"Estimated: available=${avail:.2f}, odds={odds}")

    if avail < stake:
        log(f"Not enough liquidity (available=${avail:.2f} < stake=${stake})", "FAIL")
        sys.exit(1)

    log(f"Placing market order: stake=${stake}, odds={odds}...", "STEP")
    resp = requests.post(
        f"{BASE_URL}/trade/private/api/v1/market-orders",
        headers=trade_headers(user_token),
        json={
            "lineID": line_id,
            "expectedAverageOdds": odds,
            "oddsList": odds_list,
            "stake": stake,
        },
    )
    if resp.status_code != 200:
        log(f"Place order failed: {resp.status_code} {resp.text[:300]}", "FAIL")
        sys.exit(1)

    data = resp.json().get("data", resp.json())
    mo_ref_id = data.get("refId", "")
    log(f"Market order placed: refId={mo_ref_id}")
    return mo_ref_id


def get_wager_ref_from_market_order(user_token, mo_ref_id):
    """Get individual wager ref_id from a market order."""
    log("Getting wager ref_id from market order...", "STEP")
    resp = requests.get(
        f"{BASE_URL}/trade/private/api/v1/market-orders/{mo_ref_id}",
        headers=trade_headers(user_token),
    )
    if resp.status_code == 200:
        data = resp.json().get("data", resp.json())
        wagers = data.get("wagers", [])
        if wagers:
            ref_id = wagers[0].get("refId", "")
            status = wagers[0].get("matchingStatus", "?")
            log(f"Wager ref_id={ref_id}, matchingStatus={status}")
            return ref_id

    # Fallback: check user transactions to find the wager
    log("Falling back to transaction search...", "WARN")
    resp = requests.get(
        f"{BASE_URL}/trade/private/api/v1/transactions",
        params={"limit": 10},
        headers=trade_headers(user_token),
    )
    if resp.status_code == 200:
        txns = resp.json().get("data", {}).get("transactions", [])
        for t in txns:
            if t.get("actionType") in ("open", "match"):
                wager = t.get("wager", {})
                if wager and wager.get("refId"):
                    log(f"Found wager via transactions: ref_id={wager['refId']}")
                    return wager["refId"]

    log("Could not find wager ref_id", "FAIL")
    sys.exit(1)


def wait_for_matching(user_token, ref_id, timeout=15):
    """Wait for wager to be matched."""
    log(f"Waiting for matching (up to {timeout}s)...", "STEP")
    for _ in range(timeout):
        resp = requests.get(
            f"{BASE_URL}/trade/private/api/v1/wagers/{ref_id}",
            headers=trade_headers(user_token),
        )
        if resp.status_code == 200:
            data = resp.json().get("data", resp.json())
            matched = data.get("matchedStake", 0)
            status = data.get("matchingStatus", "?")
            if matched > 0:
                log(f"Matched: matchedStake=${matched}, status={status}")
                return True
        time.sleep(1)
    log("Not matched within timeout", "WARN")
    return False


# ── Nova Admin ──────────────────────────────────────────────────────────────

def nova_login():
    """Login to Nova admin portal."""
    log("Logging into Nova admin...", "STEP")
    session = requests.Session()

    resp = session.get(f"{NOVA_URL}/login", timeout=10)
    resp.raise_for_status()
    # Try multiple CSRF patterns
    m = (re.search(r'name="_token".*?value="([^"]+)"', resp.text)
         or re.search(r'meta name="csrf-token" content="([^"]+)"', resp.text)
         or re.search(r'"csrfToken":"([^"]+)"', resp.text))
    if not m:
        log("Could not find CSRF token", "FAIL")
        sys.exit(1)

    resp = session.post(f"{NOVA_URL}/login", data={
        "_token": m.group(1),
        "email": NOVA_EMAIL,
        "password": NOVA_PASSWORD,
    }, allow_redirects=False)

    if resp.status_code not in (302, 200):
        log(f"Nova login failed: HTTP {resp.status_code}", "FAIL")
        sys.exit(1)

    session.get(NOVA_URL)
    log("Nova login OK")
    return session


def nova_get_csrf(session):
    """Get CSRF token from Nova."""
    page = session.get(NOVA_URL)
    m = re.search(r'meta name="csrf-token" content="([^"]+)"', page.text)
    if m:
        return m.group(1)
    m = re.search(r'name="_token".*?value="([^"]+)"', page.text)
    if m:
        return m.group(1)
    xsrf = session.cookies.get("XSRF-TOKEN", "")
    if xsrf:
        return requests.utils.unquote(xsrf)
    log("No CSRF token found", "FAIL")
    sys.exit(1)


def nova_find_wager_id(session, ref_id):
    """Find wager numeric ID in Nova by ref_id."""
    log(f"Searching Nova for wager {ref_id}...", "STEP")
    resp = session.get(
        f"{NOVA_URL}/nova-api/wagers",
        params={"search": ref_id, "perPage": 5},
        headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
    )
    resp.raise_for_status()
    resources = resp.json().get("resources", [])
    if not resources:
        log(f"Wager not found in Nova", "FAIL")
        return None

    wager_id = resources[0].get("id", {})
    if isinstance(wager_id, dict):
        wager_id = wager_id.get("value", wager_id)
    log(f"Found in Nova: wager_id={wager_id}")
    return wager_id


def nova_void_wager(session, ref_id):
    """Void a wager via Nova admin action."""
    log(f"Voiding wager {ref_id} via Nova...", "STEP")

    csrf = nova_get_csrf(session)
    wager_id = nova_find_wager_id(session, ref_id)
    if wager_id is None:
        return False

    resp = session.post(
        f"{NOVA_URL}/nova-api/wagers/action",
        params={"action": "void-wagers"},
        headers={
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRF-TOKEN": csrf,
            "Content-Type": "application/json",
        },
        json={"resources": [wager_id]},
    )

    if resp.status_code == 200:
        result = resp.json()
        msg = result.get("message", json.dumps(result))
        log(f"Void response: {msg}")
        return True
    else:
        log(f"Void failed: HTTP {resp.status_code} — {resp.text[:300]}", "FAIL")
        return False


# ── Transaction Check ───────────────────────────────────────────────────────

def check_transactions(user_token, ref_id):
    """Query wager transactions and verify void_match has matched_wager."""
    log(f"Checking transactions for wager {ref_id}...", "STEP")
    resp = requests.get(
        f"{BASE_URL}/trade/private/api/v1/wagers/{ref_id}/transactions",
        headers=trade_headers(user_token),
    )
    if resp.status_code != 200:
        log(f"Failed to get transactions: HTTP {resp.status_code}", "FAIL")
        return None

    txns = resp.json().get("data", {}).get("transactions", [])
    log(f"Found {len(txns)} transactions:")
    sp_wager_refs = []
    for t in txns:
        action = t.get("actionType", "?")
        value = t.get("value", 0)
        mw = t.get("matched_wager")
        mw_ref = mw.get("refId", "?") if mw else "null"
        log(f"  {action:15s}  value={value:>8.2f}  matched_wager={mw_ref}")
        if action == "match" and mw:
            sp_wager_refs.append(mw.get("refId", ""))

    void_matches = [t for t in txns if t.get("actionType") == "void_match"]
    voids = [t for t in txns if t.get("actionType") == "void"]

    return {
        "transactions": txns,
        "void_matches": void_matches,
        "voids": voids,
        "sp_wager_refs": sp_wager_refs,
    }


def print_verdict(result):
    """Print final pass/fail verdict."""
    print()
    print("=" * 70)
    print("  SSE-1855 VERIFICATION RESULT")
    print("=" * 70)

    if result is None:
        log("Could not retrieve transactions", "FAIL")
        print("=" * 70)
        return

    void_matches = result["void_matches"]
    voids = result["voids"]
    sp_refs = result["sp_wager_refs"]

    if not void_matches and not voids:
        log("No void or void_match transactions found.", "WARN")
        log("The wager hasn't been voided yet.", "INFO")
        if sp_refs:
            print()
            log("Matched SP wager ref_ids (for reference):", "INFO")
            for r in sp_refs:
                log(f"  → {r}", "INFO")
        print("=" * 70)
        return

    if voids and not void_matches:
        log("Found void transactions but NO void_match.", "WARN")
        log("void_match is created on the OPPOSITE (SP) side.", "INFO")
        log("This user's wager was voided → void_match is on SP's wagers.", "INFO")
        if sp_refs:
            print()
            log("Check these SP wagers for void_match transactions:", "INFO")
            for r in sp_refs:
                log(f"  → {r}", "INFO")
            log("(SP wagers require SP login to check via trade API,", "INFO")
            log(" or check via database / Nova admin)", "INFO")
        print("=" * 70)
        return

    # We have void_match transactions — check matched_wager
    all_pass = True
    for t in void_matches:
        tx_id = t.get("id", "?")
        mw = t.get("matched_wager")
        if mw and mw.get("refId"):
            log(f"void_match tx {tx_id}: matched_wager.refId = {mw['refId']}", "PASS")
        else:
            log(f"void_match tx {tx_id}: matched_wager is NULL — "
                "matched_wager_id NOT persisted!", "FAIL")
            all_pass = False

    print()
    if all_pass:
        log("SSE-1855 VERIFIED: matched_wager_id is persisted", "PASS")
    else:
        log("SSE-1855 BROKEN: matched_wager_id NOT persisted", "FAIL")
        log("Root cause: batchInsertTransactionsQuery SQL template", "FAIL")
        log("is missing matched_wager_id column", "FAIL")

    print("=" * 70)


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SSE-1855: Test matched_wager_id in void_match")
    parser.add_argument("--check-only", metavar="REF_ID",
                        help="Just check transactions (no placement or void)")
    parser.add_argument("--stake", type=float, default=DEFAULT_STAKE,
                        help=f"Stake amount (default: ${DEFAULT_STAKE})")
    args = parser.parse_args()

    stake = args.stake

    print()
    print("=" * 70)
    print("  SSE-1855: Verify matched_wager_id in void_match transactions")
    print("=" * 70)
    print()

    # ── Check-only mode ─────────────────────────────────────────────────
    if args.check_only:
        user_token = login_user()
        print()
        result = check_transactions(user_token, args.check_only)
        print_verdict(result)
        return

    # ── Place + manual void flow ────────────────────────────────────────

    # Step 1: SP posts liquidity on Side A
    sp_token = login_sp()
    print()
    (event_id, event_name, market_name,
     line_a, name_a, line_b, name_b) = find_event_and_lines(sp_token)
    print()
    # SP bets on Side A → User bets on Side B to match
    sp_wager_id, sp_ext_id = post_sp_liquidity(sp_token, line_a, stake * 5, odds=100)
    log(f"SP bet on: {name_a}")
    print()

    # Step 2: User places market order on Side B (opposite → matches against SP)
    user_token = login_user()
    print()
    log(f"User betting on opposite side: {name_b}")
    mo_ref_id = place_market_order(user_token, line_b, stake)
    print()

    # Get wager ref_id
    wager_ref_id = get_wager_ref_from_market_order(user_token, mo_ref_id)
    print()

    # Wait for matching
    wait_for_matching(user_token, wager_ref_id)
    print()

    # Show transactions before void
    log("=== TRANSACTIONS BEFORE VOID ===", "STEP")
    result_before = check_transactions(user_token, wager_ref_id)
    print()

    # Step 3: Manual void instructions
    print()
    print("=" * 70)
    log("STEP 3: Void the wager manually via Nova", "STEP")
    print("=" * 70)
    log(f"Wager ref_id: {wager_ref_id}", "INFO")
    log(f"SP wager:     {sp_wager_id} (ext: {sp_ext_id})", "INFO")
    log("", "INFO")
    log(f"1. Open Nova: {NOVA_URL}/resources/wagers", "INFO")
    log(f"2. Search for: {wager_ref_id}", "INFO")
    log("3. Select the wager → Actions → 'Void Wagers'", "INFO")
    log("", "INFO")
    log("After voiding, run:", "INFO")
    log(f"  python3 {sys.argv[0]} --check-only {wager_ref_id}", "INFO")
    print("=" * 70)


if __name__ == "__main__":
    main()

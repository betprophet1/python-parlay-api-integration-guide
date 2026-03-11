#!/usr/bin/env python3
import requests, logging, json

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

BASE = "https://api-ss-sandbox.betprophet.co"
SP_CREDS = {
  "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
  "secret_key": "67344329e054349f07e7a29249dcadeb"
}

def main():
  # 1) SP auth
  r = requests.post(f"{BASE}/partner/auth/login", json=SP_CREDS)
  r.raise_for_status()
  sp_token = r.json()["data"]["access_token"]
  headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}

  # 2) Get latest SP order (any), no need to match a specific parlay
  r = requests.get(f"{BASE}/parlay/sp/orders", headers=headers)
  r.raise_for_status()
  orders = r.json().get("data", {}).get("orders", [])
  if not orders:
    log.info("No SP orders available to test against.")
    return
  # pick most recent by updated_at or created_at
  orders_sorted = sorted(orders, key=lambda o: o.get("updated_at", o.get("created_at", 0)), reverse=True)
  order = orders_sorted[0]
  order_uuid = order.get("order_uuid")
  log.info(f"Using order_uuid={order_uuid} (status={order.get('status')})")

  # 3) Send acknowledgment WITHOUT price_probability
  payload = {
    "action": "accept",
    "confirmed_stake": 100,
    # INTENTIONALLY no price_probability
    "signature": "test_signature_no_pp"
  }
  r = requests.post(
    f"{BASE}/parlay/sp/orders/confirmations",
    headers=headers,
    params={"order_uuid": order_uuid},
    json=payload,
  )

  log.info(f"Status: {r.status_code}")
  try:
    log.info(json.dumps(r.json(), indent=2))
  except Exception:
    log.info(r.text)

if __name__ == "__main__":
  main()

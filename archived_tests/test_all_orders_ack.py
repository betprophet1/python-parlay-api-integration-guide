#!/usr/bin/env python3
import requests, logging, json

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

BASE = "https://api-ss-sandbox.betprophet.co"
SP_CREDS = {
  "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
  "secret_key": "67344329e054349f07e7a29249dcadeb"
}

def test_order_ack(headers, order):
  order_uuid = order.get("order_uuid")
  status = order.get("status")
  parlay_id = order.get("p_id")
  
  log.info(f"\n🧪 Testing order {order_uuid}")
  log.info(f"   Status: {status}, Parlay: {parlay_id}")
  
  # Send acknowledgment WITHOUT price_probability
  payload = {
    "action": "accept",
    "confirmed_stake": 50,
    # INTENTIONALLY no price_probability field
    "signature": "test_signature_no_pp"
  }
  
  r = requests.post(
    f"{BASE}/parlay/sp/orders/confirmations",
    headers=headers,
    params={"order_uuid": order_uuid},
    json=payload,
  )
  
  log.info(f"📥 Status: {r.status_code}")
  try:
    response_data = r.json()
    log.info(f"📋 Response: {json.dumps(response_data, indent=2)}")
    
    # Check for the specific warning we're looking for
    expected_warning = "the confirmation is rejected automatically because the parlay is non-SGP, but no price probability provided"
    if (response_data.get("success") == True and 
        expected_warning in response_data.get("warning", "")):
      log.info("🎉 FOUND THE EXPECTED RESPONSE!")
      return True
      
  except Exception:
    log.info(f"📋 Raw: {r.text}")
  
  return False

def main():
  # 1) SP auth
  r = requests.post(f"{BASE}/partner/auth/login", json=SP_CREDS)
  r.raise_for_status()
  sp_token = r.json()["data"]["access_token"]
  headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}

  # 2) Get all SP orders and try each one
  r = requests.get(f"{BASE}/parlay/sp/orders", headers=headers)
  r.raise_for_status()
  orders = r.json().get("data", {}).get("orders", [])
  
  log.info(f"📊 Found {len(orders)} total orders to test")
  
  if not orders:
    log.info("❌ No SP orders available to test")
    return
  
  # Show status distribution
  statuses = {}
  for order in orders:
    status = order.get("status", "unknown")
    statuses[status] = statuses.get(status, 0) + 1
  log.info(f"📋 Order statuses: {statuses}")
  
  # Test each order
  success_found = False
  for i, order in enumerate(orders[:5]):  # Test first 5 orders
    if test_order_ack(headers, order):
      success_found = True
      break
  
  if not success_found:
    log.info(f"\n⚠️  Did not find the expected price_probability rejection response")
    log.info(f"   This could mean:")
    log.info(f"   1. All orders are in final states (can't be re-acknowledged)")
    log.info(f"   2. The requirement validation happens at a different stage")
    log.info(f"   3. Need fresh orders in 'sent_confirmation' status")

if __name__ == "__main__":
  main()
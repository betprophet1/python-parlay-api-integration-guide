#!/usr/bin/env python3
import requests, logging, json

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

BASE = "https://api-ss-sandbox.betprophet.co"

SP_CREDS = {
  "SP1": {"access_key": "e85df05bd1bd885fbc0fc4b24fdd2500", "secret_key": "67344329e054349f07e7a29249dcadeb"},
  "SP2": {"access_key": "ec45827afa933f97ec19e674c0fa39c6", "secret_key": "442df8e9fe96e4f7e744b2d3cac5cd51"}
}

def test_acknowledgment_validation(sp_name, sp_creds):
  log.info(f"\n🧪 Testing {sp_name} acknowledgment validation")
  
  # Auth
  r = requests.post(f"{BASE}/partner/auth/login", json=sp_creds)
  r.raise_for_status()
  sp_token = r.json()["data"]["access_token"]
  headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
  
  # Get orders
  r = requests.get(f"{BASE}/parlay/sp/orders", headers=headers)
  r.raise_for_status()
  orders = r.json().get("data", {}).get("orders", [])
  
  log.info(f"📊 {sp_name} has {len(orders)} orders")
  if orders:
    statuses = {}
    for order in orders:
      status = order.get("status", "unknown")
      statuses[status] = statuses.get(status, 0) + 1
    log.info(f"📋 Order statuses: {statuses}")
  
  # Test with each available order
  for i, order in enumerate(orders[:2]):  # Test first 2 orders
    order_uuid = order.get("order_uuid")
    status = order.get("status")
    parlay_id = order.get("p_id")
    
    log.info(f"\n  📋 Testing order {i+1}: {order_uuid[:20]}... (status: {status})")
    
    # Acknowledgment WITHOUT price_probability
    payload = {
      "action": "accept",
      "confirmed_stake": 25,
      # INTENTIONALLY omitting price_probability
      "signature": f"test_{sp_name.lower()}_no_pp"
    }
    
    r = requests.post(f"{BASE}/parlay/sp/orders/confirmations",
                     json=payload, headers=headers, 
                     params={"order_uuid": order_uuid})
    
    log.info(f"  📥 Status: {r.status_code}")
    try:
      response_data = r.json()
      log.info(f"  📋 Response: {json.dumps(response_data, indent=4)}")
      
      # Check for the expected warning
      expected = "the confirmation is rejected automatically because the parlay is non-SGP, but no price probability provided"
      if expected in response_data.get("warning", ""):
        log.info(f"  🎉 FOUND EXPECTED RESPONSE in {sp_name}!")
        return True
        
    except:
      log.info(f"  📋 Raw: {r.text}")
  
  # Test with a fake order UUID to see validation behavior
  log.info(f"\n  🧪 Testing {sp_name} with fake UUID for validation behavior")
  fake_uuid = "019a0000-fake-fake-fake-fakeorderfake"
  
  payload = {
    "action": "accept",
    "confirmed_stake": 10,
    # INTENTIONALLY omitting price_probability
    "signature": f"test_{sp_name.lower()}_fake"
  }
  
  r = requests.post(f"{BASE}/parlay/sp/orders/confirmations",
                   json=payload, headers=headers,
                   params={"order_uuid": fake_uuid})
  
  log.info(f"  📥 Fake UUID Status: {r.status_code}")
  try:
    response_data = r.json()
    log.info(f"  📋 Fake UUID Response: {json.dumps(response_data, indent=4)}")
  except:
    log.info(f"  📋 Fake UUID Raw: {r.text}")
  
  return False

def main():
  log.info("🔍 TESTING ACKNOWLEDGMENT VALIDATION WITHOUT price_probability")
  log.info("=" * 80)
  
  success_found = False
  
  for sp_name, sp_creds in SP_CREDS.items():
    try:
      if test_acknowledgment_validation(sp_name, sp_creds):
        success_found = True
    except Exception as e:
      log.info(f"❌ Error testing {sp_name}: {e}")
  
  log.info(f"\n{'='*80}")
  if success_found:
    log.info("🎉 FOUND THE EXPECTED price_probability REJECTION RESPONSE!")
  else:
    log.info("⚠️  Did not find expected response. Possible reasons:")
    log.info("   1. All orders are finalized (can't be re-acknowledged)")
    log.info("   2. Validation happens before reaching acknowledgment endpoint")
    log.info("   3. Different response format than expected")

if __name__ == "__main__":
  main()
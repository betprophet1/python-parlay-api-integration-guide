#!/usr/bin/env python3
import requests, logging, json, time

logging.basicConfig(level=logging.INFO, format='%(message)s')
log = logging.getLogger(__name__)

BASE = "https://api-ss-sandbox.betprophet.co"
SP_CREDS = {
  "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
  "secret_key": "67344329e054349f07e7a29249dcadeb"
}

def get_user_token():
  r = requests.post(f"{BASE}/api/v1/auth/login", json={
    "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
    "email": "lam.tran+usr004@betprophet.co",
    "password": "Kh0ngbiet1"
  })
  r.raise_for_status()
  return r.json()["accessToken"]

def main():
  # Auth
  user_token = get_user_token()
  r = requests.post(f"{BASE}/partner/auth/login", json=SP_CREDS)
  r.raise_for_status()
  sp_token = r.json()["data"]["access_token"]
  
  sp_headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
  user_headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
  
  # Fresh market lines
  market_lines = [
    {"line": -4.5, "lineId": "04f2da44cbba365fd807c2bf6c5f09ab", "marketId": 223, "outcomeId": 1714, "sportEventId": 19191},
    {"line": -1.5, "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852", "marketId": 223, "outcomeId": 1714, "sportEventId": 19192}
  ]
  
  log.info("🚀 Creating fresh parlay flow...")
  
  # 1) Create parlay
  r = requests.post(f"{BASE}/parlay/api/v1/user/request", 
                   json={"marketLines": market_lines}, headers=user_headers)
  r.raise_for_status()
  parlay_id = r.json()["data"]["parlayId"]
  log.info(f"✅ Parlay created: {parlay_id}")
  
  # 2) SP provides offer
  offer_payload = {
    "parlay_id": parlay_id,
    "offers": [{
      "odds": 800, "max_risk": 100,
      "valid_until": int((time.time() + 60) * 1_000_000_000),
      "estimated_prices": [{"line_id": line["lineId"], "odds": 800} for line in market_lines]
    }]
  }
  r = requests.post(f"{BASE}/parlay/sp/orders/offers", json=offer_payload, headers=sp_headers)
  r.raise_for_status()
  log.info("✅ SP offer sent")
  
  # 3) User confirms
  r = requests.post(f"{BASE}/parlay/api/v1/user/confirm", 
                   json={"parlayId": parlay_id, "odds": 800, "stake": 10000}, headers=user_headers)
  r.raise_for_status()
  log.info("✅ User confirmed bet")
  
  # 4) Immediately try to find and acknowledge the order
  log.info("🔍 Looking for SP order...")
  
  for attempt in range(10):  # Try 10 times with short delays
    r = requests.get(f"{BASE}/parlay/sp/orders", headers=sp_headers)
    r.raise_for_status()
    orders = r.json().get("data", {}).get("orders", [])
    
    matching_orders = [o for o in orders if o.get("p_id") == parlay_id]
    if matching_orders:
      order = matching_orders[0]
      order_uuid = order.get("order_uuid")
      status = order.get("status")
      
      log.info(f"📋 Found order: {order_uuid} (status: {status})")
      
      # Test acknowledgment WITHOUT price_probability
      ack_payload = {
        "action": "accept",
        "confirmed_stake": 100,
        # NO price_probability field
        "signature": "test_no_pp"
      }
      
      log.info("🧪 Testing acknowledgment WITHOUT price_probability...")
      r = requests.post(f"{BASE}/parlay/sp/orders/confirmations", 
                       json=ack_payload, headers=sp_headers, 
                       params={"order_uuid": order_uuid})
      
      log.info(f"📥 Status: {r.status_code}")
      try:
        response_data = r.json()
        log.info(f"📋 Response:")
        log.info(json.dumps(response_data, indent=2))
        
        # Check for expected warning
        expected = "the confirmation is rejected automatically because the parlay is non-SGP, but no price probability provided"
        if expected in response_data.get("warning", ""):
          log.info("🎉 SUCCESS: Found expected price_probability rejection!")
        
      except:
        log.info(f"📋 Raw response: {r.text}")
      
      return
    
    time.sleep(0.5)  # Wait 0.5s between attempts
  
  log.info("❌ Could not find SP order for acknowledgment test")

if __name__ == "__main__":
  main()
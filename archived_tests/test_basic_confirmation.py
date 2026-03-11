#!/usr/bin/env python3
"""
Basic SP Confirmation Test - Debug Version
"""
import requests
import json
from datetime import datetime
import time

class BasicConfirmationTest:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.mm1_token = None
        self.user_token = None
        
    def authenticate_mm1(self):
        """Authenticate MM1 (SP1)"""
        url = f"{self.base_url}/partner/auth/login"
        payload = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            self.mm1_token = data["data"]["access_token"]
            print(f"✅ MM1 Authentication SUCCESS")
            return True
        print(f"❌ MM1 Authentication FAILED: {response.status_code}")
        return False
        
    def authenticate_user(self):
        """Use Pre-authenticated User Token"""
        # Use the provided pre-authenticated token
        self.user_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6InNpbTIifQ.eyJhY2NvdW50VHlwZSI6MCwiZXhwIjoxNzU5ODMwNTg4LCJleHRyYU9ubGluZVRpbWUiOjAsImlzT3RwRXhwaXJlZCI6ZmFsc2UsImlzU3VzcGVuZGVkIjpmYWxzZSwiaXNzIjoiaHR0cDovL21vdGhlcnNoaXAubW90aGVyc2hpcC1zYW5kYm94IiwianRpIjoiZTg5M2I5MmYtNjdjZi00OWQyLTk2NGQtMzhjNjI2YzVlMzg3Iiwia2JhQW5zd2Vyc0luZm8iOiJOL0EiLCJreWNJbmZvIjoiU3VjY2VzcyIsInBlbmRpbmdCeUFkbWluIjpmYWxzZSwicHVzaGVySW5mbyI6eyJhdXRoQ2hhbm5lbCI6InVzZXIuYXV0aGVudGljYXRpb24uZTg5M2I5MmYtNjdjZi00OWQyLTk2NGQtMzhjNjI2YzVlMzg3IiwiYmFsYW5jZVVwZGF0ZWRFdmVudCI6IndhbGxldC5iYWxhbmNlLnVwZGF0ZWQiLCJjbHVzdGVyIjoibXQxIiwiaWQiOiJjMjBmYTM2ZmJjM2MzYzMwOGZmYSIsImluZm9DaGFubmVsIjoidXNlci5pbmZvcm1hdGlvbi5lZjVjM2JlMy1hZDRkLTRlMGYtYWNlNy05NzA1NjkwYzgyNmUiLCJpbmZvcm1hdGlvblVwZGF0ZWRFdmVudCI6InVzZXIuaW5mb3JtYXRpb24udXBkYXRlZCIsImtiYUNoYWxsZW5nZVF1ZXN0aW9uc0V2ZW50IjoidXNlci5rYmEuY2hhbGxlbmdlIiwic2Vzc2lvblRlcm1pbmF0ZWRFdmVudCI6InNlc3Npb24udGVybWluYXRlZCJ9LCJyZWdpb24iOiJOWSIsInN1YiI6ImxhbS50cmFuK3VzcjAwNEBiZXRwcm9waGV0LmNvIiwidXNlcklkIjoiZWY1YzNiZTMtYWQ0ZC00ZTBmLWFjZTctOTcwNTY5MGM4MjZlIn0.esyueJeCe4Xqdj9tbzZQYD0I8W8eGs31-XQal6hj5lY"
        print(f"✅ User Pre-authenticated Token SUCCESS")
        print(f"   User: lam.tran+usr004@betprophet.co")
        return True
        
    def create_parlay(self):
        """Create a simple parlay"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        # Simple 2-leg parlay
        payload = {
            "marketLines": [
                {
                    "line": 0,
                    "lineId": "99fe18eea332562ac5cd04d4b3c772d0",
                    "marketId": 406,
                    "outcomeId": 4,
                    "sportEventId": 30023983
                },
                {
                    "line": -1.5,
                    "lineId": "b3ac37f3974eb98f726a5f852f07f9f6",
                    "marketId": 410,
                    "outcomeId": 1714,
                    "sportEventId": 30023984
                }
            ]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            parlay_id = data["data"]["parlayId"]
            print(f"✅ Parlay Created: {parlay_id}")
            return parlay_id
        print(f"❌ Parlay Creation FAILED: {response.status_code}")
        return None
        
    def provide_offer(self, parlay_id, odds=850):
        """SP provides an offer"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        headers = {
            "Authorization": f"Bearer {self.mm1_token}",
            "Content-Type": "application/json"
        }
        
        valid_until = int((time.time() + 300) * 1000 * 1_000_000)  # 5 minutes from now
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [{
                "odds": odds,
                "max_risk": 200,
                "valid_until": valid_until,
                "estimated_prices": [
                    {"line_id": "99fe18eea332562ac5cd04d4b3c772d0", "odds": odds},
                    {"line_id": "b3ac37f3974eb98f726a5f852f07f9f6", "odds": odds}
                ]
            }]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"✅ Offer Provided: odds={odds}")
            return True
        print(f"❌ Offer FAILED: {response.status_code} - {response.text}")
        return False
        
    def user_confirm_bet(self, parlay_id, odds=850, stake=100.0):
        """User confirms the bet"""
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "parlayId": parlay_id,
            "odds": odds,
            "stake": stake
        }
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"✅ User Bet Confirmed: stake=${stake}, odds={odds}")
            return True
        print(f"❌ User Bet FAILED: {response.status_code} - {response.text}")
        return False
        
    def get_orders(self):
        """Get SP orders"""
        url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {self.mm1_token}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'orders' in data['data']:
                orders = data['data']['orders']
                print(f"✅ Found {len(orders)} orders")
                for i, order in enumerate(orders[:3]):  # Show first 3
                    print(f"   Order {i+1}: UUID={order.get('order_uuid', 'N/A')[:20]}...")
                    print(f"             Status={order.get('status', 'N/A')}")
                    print(f"             Parlay={order.get('p_id', 'N/A')[:20]}...")
                return orders
            else:
                print("❌ No orders found")
                return []
        print(f"❌ Get Orders FAILED: {response.status_code}")
        return []
        
    def confirm_order(self, order_uuid, action="accept", confirmed_odds=850, confirmed_stake=100.0):
        """Confirm an order"""
        url = f"{self.base_url}/parlay/sp/orders/confirmations"
        headers = {
            "Authorization": f"Bearer {self.mm1_token}",
            "Content-Type": "application/json"
        }
        params = {"order_uuid": order_uuid}
        
        # CRITICAL: confirmed_odds must be OPPOSITE sign of requested odds
        if confirmed_odds > 0:
            final_confirmed_odds = -confirmed_odds
        else:
            final_confirmed_odds = -confirmed_odds  # This makes negative become positive
        
        payload = {
            "action": action,
            "confirmed_odds": final_confirmed_odds,
            "confirmed_stake": confirmed_stake,
            "price_probability": [{
                "lines": [
                    {"line_id": "99fe18eea332562ac5cd04d4b3c772d0", "probability": 0.5},
                    {"line_id": "b3ac37f3974eb98f726a5f852f07f9f6", "probability": 0.5}
                ],
                "max_risk": 200,
                "vig": 0.1
            }],
            "signature": "test_signature"
        }
            
        print(f"🔄 Confirming order: {order_uuid[:20]}...")
        print(f"   Action: {action}")
        print(f"   Original Odds: {confirmed_odds}")
        print(f"   Confirmed Odds (opposite): {final_confirmed_odds}")
        print(f"   Confirmed Stake: ${confirmed_stake}")
        
        response = requests.post(url, json=payload, headers=headers, params=params)
        print(f"📤 Request URL: {url}")
        print(f"📤 Query Params: {params}")
        print(f"📤 Payload: {json.dumps(payload, indent=2)}")
        print(f"📥 Response Status: {response.status_code}")
        print(f"📥 Response Body: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Order Confirmation SUCCESS")
            return True
        print(f"❌ Order Confirmation FAILED")
        return False
        
    def run_basic_test(self):
        """Run the basic confirmation test"""
        print("🚀 BASIC SP CONFIRMATION TEST")
        print("="*40)
        
        # Step 1: Authentication
        if not self.authenticate_mm1():
            return False
        if not self.authenticate_user():
            return False
            
        # Step 2: Create parlay
        parlay_id = self.create_parlay()
        if not parlay_id:
            return False
            
        # Step 3: Provide offer (try negative American odds)
        if not self.provide_offer(parlay_id, -110):
            return False
            
        # Step 4: User confirms
        if not self.user_confirm_bet(parlay_id, -110, 100.0):
            return False
            
        # Step 5: Wait a moment for processing
        print("⏱️  Waiting 2 seconds for order processing...")
        time.sleep(2)
        
        # Step 6: Get orders
        orders = self.get_orders()
        if not orders:
            return False
            
        # Step 7: Try to confirm the most recent order (only if status allows it)
        for order in orders:
            if order.get('p_id') == parlay_id:
                order_uuid = order.get('order_uuid')
                order_status = order.get('status', 'unknown')
                if order_uuid:
                    print(f"🎯 Found matching order for parlay {parlay_id[:20]}...")
                    print(f"   Order Status: {order_status}")
                    
                    if order_status in ['rejected', 'failed', 'expired']:
                        print(f"   ✅ Status '{order_status}' allows confirmation - proceeding")
                        return self.confirm_order(order_uuid, "accept", -110, 100.0)
                    elif order_status == 'sent_confirmation':
                        print(f"   ⚠️ Status '{order_status}' - order already sent for confirmation, waiting...")
                        time.sleep(5)  # Wait and check again
                        updated_orders = self.get_orders()
                        for updated_order in updated_orders:
                            if updated_order.get('order_uuid') == order_uuid:
                                new_status = updated_order.get('status', 'unknown')
                                print(f"   Updated Status: {new_status}")
                                if new_status in ['rejected', 'failed', 'expired']:
                                    return self.confirm_order(order_uuid, "accept", -110, 100.0)
                                break
                        return False
                    else:
                        print(f"   ❌ Status '{order_status}' doesn't allow confirmation yet")
                        return False
                    
        print("❌ No matching order found for confirmation")
        return False

if __name__ == "__main__":
    test = BasicConfirmationTest()
    success = test.run_basic_test()
    print(f"\n🏁 Test Result: {'SUCCESS' if success else 'FAILED'}")
#!/usr/bin/env python3
"""
Simple Happy Flow Test

This test replicates the successful Postman flow:
1. Authenticate SPs and User
2. Create parlay request
3. SPs provide offers
4. User confirms bet
5. Check final status

No complex confirmations or edge cases - just the core happy path.
"""

import json
import requests
import time
from datetime import datetime

class SimpleHappyFlowTest:
    """Simple test that mirrors successful Postman workflow"""
    
    def __init__(self):
        with open("test_config.json", 'r') as f:
            self.config = json.load(f)["test_configuration"]
        
        self.base_url = self.config["base_url"]
        self.market_lines = self.config["test_data"]["market_lines"]
        
        self.sp1_token = None
        self.sp2_token = None
        self.user_token = None

    def authenticate_all(self):
        """Authenticate all parties"""
        print("🔐 AUTHENTICATING ALL PARTIES")
        print("="*40)
        
        # SP1
        print("📍 Authenticating SP1...")
        sp1_creds = self.config["service_providers"]["sp1"]
        response = requests.post(
            f"{self.base_url}/partner/auth/login",
            json={
                "access_key": sp1_creds["access_key"],
                "secret_key": sp1_creds["secret_key"]
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            self.sp1_token = response.json()["data"]["access_token"]
            print("✅ SP1 authenticated")
        else:
            raise Exception(f"SP1 auth failed: {response.status_code}")
        
        # SP2
        print("📍 Authenticating SP2...")
        sp2_creds = self.config["service_providers"]["sp2"]
        response = requests.post(
            f"{self.base_url}/partner/auth/login",
            json={
                "access_key": sp2_creds["access_key"],
                "secret_key": sp2_creds["secret_key"]
            },
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            self.sp2_token = response.json()["data"]["access_token"]
            print("✅ SP2 authenticated")
        else:
            raise Exception(f"SP2 auth failed: {response.status_code}")
        
        # User - using pre-authenticated token
        print("📍 Using pre-authenticated user token...")
        self.user_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6InNpbTIifQ.eyJhY2NvdW50VHlwZSI6MCwiZXhwIjoxNzU5ODMwNTg4LCJleHRyYU9ubGluZVRpbWUiOjAsImlzT3RwRXhwaXJlZCI6ZmFsc2UsImlzU3VzcGVuZGVkIjpmYWxzZSwiaXNzIjoiaHR0cDovL21vdGhlcnNoaXAubW90aGVyc2hpcC1zYW5kYm94IiwianRpIjoiZTg5M2I5MmYtNjdjZi00OWQyLTk2NGQtMzhjNjI2YzVlMzg3Iiwia2JhQW5zd2Vyc0luZm8iOiJOL0EiLCJreWNJbmZvIjoiU3VjY2VzcyIsInBlbmRpbmdCeUFkbWluIjpmYWxzZSwicHVzaGVySW5mbyI6eyJhdXRoQ2hhbm5lbCI6InVzZXIuYXV0aGVudGljYXRpb24uZTg5M2I5MmYtNjdjZi00OWQyLTk2NGQtMzhjNjI2YzVlMzg3IiwiYmFsYW5jZVVwZGF0ZWRFdmVudCI6IndhbGxldC5iYWxhbmNlLnVwZGF0ZWQiLCJjbHVzdGVyIjoibXQxIiwiaWQiOiJjMjBmYTM2ZmJjM2MzYzMwOGZmYSIsImluZm9DaGFubmVsIjoidXNlci5pbmZvcm1hdGlvbi5lZjVjM2JlMy1hZDRkLTRlMGYtYWNlNy05NzA1NjkwYzgyNmUiLCJpbmZvcm1hdGlvblVwZGF0ZWRFdmVudCI6InVzZXIuaW5mb3JtYXRpb24udXBkYXRlZCIsImtiYUNoYWxsZW5nZVF1ZXN0aW9uc0V2ZW50IjoidXNlci5rYmEuY2hhbGxlbmdlIiwic2Vzc2lvblRlcm1pbmF0ZWRFdmVudCI6InNlc3Npb24udGVybWluYXRlZCJ9LCJyZWdpb24iOiJOWSIsInN1YiI6ImxhbS50cmFuK3VzcjAwNEBiZXRwcm9waGV0LmNvIiwidXNlcklkIjoiZWY1YzNiZTMtYWQ0ZC00ZTBmLWFjZTctOTcwNTY5MGM4MjZlIn0.esyueJeCe4Xqdj9tbzZQYD0I8W8eGs31-XQal6hj5lY"
        print("✅ User token ready")
        
        print("\n🎉 All authentication completed successfully!")

    def create_parlay(self):
        """Create parlay request using the exact same payload as your curl"""
        print("\n📋 CREATING PARLAY REQUEST")
        print("="*30)
        
        # Use fresh market data
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
                },
                {
                    "line": 8,
                    "lineId": "fe8faadbb8748059f28e08cf85558fbc",
                    "marketId": 258,
                    "outcomeId": 12,
                    "sportEventId": 10076791
                }
            ]
        }
        
        print(f"📊 Creating parlay with {len(payload['marketLines'])} lines:")
        for i, line in enumerate(payload['marketLines'], 1):
            print(f"   Line {i}: {line['line']} (Market: {line['marketId']})")
        
        response = requests.post(
            f"{self.base_url}/parlay/api/v1/user/request",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            parlay_id = data["data"]["parlayId"]
            print(f"✅ Parlay created successfully!")
            print(f"   Parlay ID: {parlay_id}")
            return parlay_id
        else:
            print(f"❌ Parlay creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            raise Exception(f"Parlay creation failed: {response.status_code}")

    def sp_provide_offers(self, parlay_id):
        """Both SPs provide offers"""
        print("\n💰 SPs PROVIDING OFFERS")
        print("="*25)
        
        offers = {}
        
        # SP1 Offer
        print("📍 SP1 providing offer...")
        sp1_payload = {
            "parlay_id": parlay_id,
            "offers": [{
                "odds": 850,
                "max_risk": 200,
                "valid_until": int((time.time() + 60) * 1000 * 1_000_000),  # 60 seconds
                "estimated_prices": [
                    {"line_id": "99fe18eea332562ac5cd04d4b3c772d0", "odds": 850},
                    {"line_id": "b3ac37f3974eb98f726a5f852f07f9f6", "odds": 850},
                    {"line_id": "fe8faadbb8748059f28e08cf85558fbc", "odds": 850}
                ]
            }]
        }
        
        response = requests.post(
            f"{self.base_url}/parlay/sp/orders/offers",
            json=sp1_payload,
            headers={
                "Authorization": f"Bearer {self.sp1_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print("✅ SP1 offer provided (odds: 850, max_risk: $200)")
            offers['sp1'] = {'odds': 850, 'max_risk': 200}
        else:
            print(f"❌ SP1 offer failed: {response.status_code} - {response.text}")
            return None
        
        # SP2 Offer
        print("📍 SP2 providing offer...")
        sp2_payload = {
            "parlay_id": parlay_id,
            "offers": [{
                "odds": 800,
                "max_risk": 300,
                "valid_until": int((time.time() + 60) * 1000 * 1_000_000),  # 60 seconds
                "estimated_prices": [
                    {"line_id": "99fe18eea332562ac5cd04d4b3c772d0", "odds": 800},
                    {"line_id": "b3ac37f3974eb98f726a5f852f07f9f6", "odds": 800},
                    {"line_id": "fe8faadbb8748059f28e08cf85558fbc", "odds": 800}
                ]
            }]
        }
        
        response = requests.post(
            f"{self.base_url}/parlay/sp/orders/offers",
            json=sp2_payload,
            headers={
                "Authorization": f"Bearer {self.sp2_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print("✅ SP2 offer provided (odds: 800, max_risk: $300)")
            offers['sp2'] = {'odds': 800, 'max_risk': 300}
        else:
            print(f"❌ SP2 offer failed: {response.status_code} - {response.text}")
            return None
        
        return offers

    def user_confirm_bet(self, parlay_id, offers):
        """User confirms bet with best available odds"""
        print("\n✅ USER CONFIRMING BET")
        print("="*20)
        
        # Choose best odds (SP1: 850 vs SP2: 800)
        best_odds = max(offers['sp1']['odds'], offers['sp2']['odds'])
        stake = 100.0
        
        print(f"📊 User selecting best odds: {best_odds}")
        print(f"💰 Stake: ${stake}")
        
        payload = {
            "parlayId": parlay_id,
            "odds": best_odds,
            "stake": stake
        }
        
        response = requests.post(
            f"{self.base_url}/parlay/api/v1/user/confirm",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User bet confirmed successfully!")
            print(f"   Confirmed at: {datetime.now().strftime('%H:%M:%S')}")
            return True
        else:
            print(f"❌ User bet confirmation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    def check_simple_status(self):
        """Simple status check without verbose output"""
        print("\n🔍 CHECKING STATUS")
        print("="*20)
        
        # Just check if we can get orders without errors
        for sp_name, token in [("SP1", self.sp1_token), ("SP2", self.sp2_token)]:
            try:
                response = requests.get(
                    f"{self.base_url}/parlay/sp/orders",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 200:
                    data = response.json()
                    order_count = len(data.get('data', {}).get('orders', []))
                    print(f"✅ {sp_name}: {order_count} orders found")
                else:
                    print(f"⚠️ {sp_name}: Status check returned {response.status_code}")
            except Exception as e:
                print(f"❌ {sp_name}: Error checking status - {str(e)}")

    def run_happy_flow(self):
        """Run the complete happy flow"""
        print("🚀 SIMPLE HAPPY FLOW TEST")
        print("="*50)
        print("📝 This test replicates successful Postman workflow")
        print("="*50)
        
        try:
            # Step 1: Authenticate
            self.authenticate_all()
            
            # Step 2: Create parlay
            parlay_id = self.create_parlay()
            
            # Step 3: Get offers
            offers = self.sp_provide_offers(parlay_id)
            if not offers:
                raise Exception("Failed to get offers from SPs")
            
            # Step 4: User confirms bet
            success = self.user_confirm_bet(parlay_id, offers)
            if not success:
                raise Exception("User bet confirmation failed")
            
            # Step 5: Quick status check
            self.check_simple_status()
            
            print("\n🎉 HAPPY FLOW COMPLETED SUCCESSFULLY!")
            print("="*50)
            print("✅ All steps passed - parlay flow working correctly")
            return True
            
        except Exception as e:
            print(f"\n❌ HAPPY FLOW FAILED: {str(e)}")
            print("="*50)
            return False


def main():
    test = SimpleHappyFlowTest()
    success = test.run_happy_flow()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
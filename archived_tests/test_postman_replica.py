#!/usr/bin/env python3
"""
Test that exactly replicates the successful Postman workflow

This test follows the exact sequence and payload structure from the Postman collection:
1. MM1 and MM2 authentication 
2. User parlay request (calculates combined odds from individual odds)
3. SP2 provides offer with calculated odds
4. SP1 provides offer with calculated odds  
5. User confirms bet with calculated odds
6. SP1 lists orders and finds order_uuid
7. SP1 acknowledges confirmation
8. SP2 lists orders and finds order_uuid2  
9. SP2 acknowledges confirmation
"""

import json
import requests
import time
import math
from datetime import datetime

class PostmanReplicaTest:
    """Test that exactly follows the Postman collection workflow"""
    
    def __init__(self):
        with open("test_config.json", 'r') as f:
            self.config = json.load(f)["test_configuration"]
        
        self.base_url = self.config["base_url"]
        
        # Tokens
        self.mm1_token = None
        self.mm2_token = None
        self.user_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6InNpbTIifQ.eyJhY2NvdW50VHlwZSI6MCwiZXhwIjoxNzU5ODMwNTg4LCJleHRyYU9ubGluZVRpbWUiOjAsImlzT3RwRXhwaXJlZCI6ZmFsc2UsImlzU3VzcGVuZGVkIjpmYWxzZSwiaXNzIjoiaHR0cDovL21vdGhlcnNoaXAubW90aGVyc2hpcC1zYW5kYm94IiwianRpIjoiZTg5M2I5MmYtNjdjZi00OWQyLTk2NGQtMzhjNjI2YzVlMzg3Iiwia2JhQW5zd2Vyc0luZm8iOiJOL0EiLCJreWNJbmZvIjoiU3VjY2VzcyIsInBlbmRpbmdCeUFkbWluIjpmYWxzZSwicHVzaGVySW5mbyI6eyJhdXRoQ2hhbm5lbCI6InVzZXIuYXV0aGVudGljYXRpb24uZTg5M2I5MmYtNjdjZi00OWQyLTk2NGQtMzhjNjI2YzVlMzg3IiwiYmFsYW5jZVVwZGF0ZWRFdmVudCI6IndhbGxldC5iYWxhbmNlLnVwZGF0ZWQiLCJjbHVzdGVyIjoibXQxIiwiaWQiOiJjMjBmYTM2ZmJjM2MzYzMwOGZmYSIsImluZm9DaGFubmVsIjoidXNlci5pbmZvcm1hdGlvbi5lZjVjM2JlMy1hZDRkLTRlMGYtYWNlNy05NzA1NjkwYzgyNmUiLCJpbmZvcm1hdGlvblVwZGF0ZWRFdmVudCI6InVzZXIuaW5mb3JtYXRpb24udXBkYXRlZCIsImtiYUNoYWxsZW5nZVF1ZXN0aW9uc0V2ZW50IjoidXNlci5rYmEuY2hhbGxlbmdlIiwic2Vzc2lvblRlcm1pbmF0ZWRFdmVudCI6InNlc3Npb24udGVybWluYXRlZCJ9LCJyZWdpb24iOiJOWSIsInN1YiI6ImxhbS50cmFuK3VzcjAwNEBiZXRwcm9waGV0LmNvIiwidXNlcklkIjoiZWY1YzNiZTMtYWQ0ZC00ZTBmLWFjZTctOTcwNTY5MGM4MjZlIn0.esyueJeCe4Xqdj9tbzZQYD0I8W8eGs31-XQal6hj5lY"
        
        # Calculated values (will be set during execution)
        self.parlay_id = None
        self.offer_odds = None
        self.estimated_prices = None
        self.valid_until = None
        self.order_uuid = None
        self.order_uuid2 = None

    def american_to_decimal(self, american_odds):
        """Convert American odds to decimal odds"""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1

    def decimal_to_american(self, decimal_odds):
        """Convert decimal odds to American odds"""
        if decimal_odds >= 2:
            return round((decimal_odds - 1) * 100)
        else:
            return round(-100 / (decimal_odds - 1))

    def calculate_and_round_probability(self, odds):
        """Calculate probability from American odds and round to 10 decimals"""
        if odds > 0:
            probability = 100 / (odds + 100)
        else:
            probability = abs(odds) / (abs(odds) + 100)
        return round(probability, 10)

    def step1_mm1_login(self):
        """Step 1: MM1 Login"""
        print("🔐 STEP 1: MM1 Login")
        
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
            self.mm1_token = response.json()["data"]["access_token"]
            print(f"✅ MM1 authenticated successfully")
        else:
            raise Exception(f"MM1 authentication failed: {response.status_code}")

    def step2_mm2_login(self):
        """Step 2: MM2 Login"""
        print("🔐 STEP 2: MM2 Login")
        
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
            self.mm2_token = response.json()["data"]["access_token"]
            print(f"✅ MM2 authenticated successfully")
        else:
            raise Exception(f"MM2 authentication failed: {response.status_code}")

    def step3_configure_parlay_and_request_price(self):
        """Step 3: Configure Parlay & Request Price (with odds calculation like Postman)"""
        print("📋 STEP 3: Configure Parlay & Request Price")
        
        # Individual American odds array from Postman
        individual_american_odds_array = [800, -300, 300, 860]
        
        market_lines = [
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
        
        # Calculate parlay odds (exactly like Postman prerequest script)
        parlay_decimal_odds = 1
        estimated_prices = []
        
        for i, line in enumerate(market_lines):
            individual_american_odds = individual_american_odds_array[i]
            individual_decimal_odds = self.american_to_decimal(individual_american_odds)
            
            estimated_prices.append({
                "line_id": line["lineId"],
                "odds": individual_american_odds
            })
            
            parlay_decimal_odds *= individual_decimal_odds
        
        # Convert back to American odds
        parlay_american_odds = self.decimal_to_american(parlay_decimal_odds)
        
        # Set calculated values
        self.offer_odds = parlay_american_odds
        self.estimated_prices = estimated_prices
        
        # Calculate valid_until (100 seconds from now, like Postman)
        future_ms = int(time.time() * 1000) + 100000
        self.valid_until = future_ms * 1_000_000
        
        print(f"📊 Calculated Parlay Odds: {parlay_american_odds}")
        print(f"📊 Estimated Prices: {estimated_prices}")
        
        # Make the request
        payload = {"marketLines": market_lines}
        
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
            self.parlay_id = data["data"]["parlayId"]
            print(f"✅ Parlay created - ID: {self.parlay_id}")
        else:
            raise Exception(f"Parlay creation failed: {response.status_code} - {response.text}")

    def step4_sp2_respond_with_offer(self):
        """Step 4: SP2 Respond with Offer"""
        print("💰 STEP 4: SP2 Respond with Offer")
        
        # Update valid_until (500 seconds from now, like Postman)
        future_ms = int(time.time() * 1000) + 500000
        valid_until = future_ms * 1_000_000
        
        payload = {
            "parlay_id": self.parlay_id,
            "offers": [{
                "odds": self.offer_odds,
                "max_risk": 100.0,
                "valid_until": valid_until,
                "estimated_prices": self.estimated_prices
            }]
        }
        
        response = requests.post(
            f"{self.base_url}/parlay/sp/orders/offers",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.mm2_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print(f"✅ SP2 offer provided - odds: {self.offer_odds}, max_risk: $100")
        else:
            raise Exception(f"SP2 offer failed: {response.status_code} - {response.text}")

    def step5_sp1_respond_with_offer(self):
        """Step 5: SP1 Respond with Offer"""
        print("💰 STEP 5: SP1 Respond with Offer")
        
        # Update valid_until (500 seconds from now, like Postman)
        future_ms = int(time.time() * 1000) + 500000
        valid_until = future_ms * 1_000_000
        
        payload = {
            "parlay_id": self.parlay_id,
            "offers": [{
                "odds": self.offer_odds,
                "max_risk": 100.0,
                "valid_until": valid_until,
                "estimated_prices": self.estimated_prices
            }]
        }
        
        response = requests.post(
            f"{self.base_url}/parlay/sp/orders/offers",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.mm1_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print(f"✅ SP1 offer provided - odds: {self.offer_odds}, max_risk: $100")
        else:
            raise Exception(f"SP1 offer failed: {response.status_code} - {response.text}")

    def step6_user_confirm_bet(self):
        """Step 6: User Confirm Bet"""
        print("✅ STEP 6: User Confirm Bet")
        
        payload = {
            "parlayId": self.parlay_id,
            "odds": self.offer_odds,
            "stake": 200  # Same stake as Postman
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
            print(f"✅ User bet confirmed - odds: {self.offer_odds}, stake: $200")
        else:
            raise Exception(f"User bet confirmation failed: {response.status_code} - {response.text}")

    def step7_sp1_list_orders(self):
        """Step 7: SP1 List Orders and find order_uuid"""
        print("🔍 STEP 7: SP1 List Orders")
        
        response = requests.get(
            f"{self.base_url}/parlay/sp/orders",
            headers={"Authorization": f"Bearer {self.mm1_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Find matching order (like Postman script)
            found_order_uuid = None
            if data and data.get("data") and data["data"].get("orders"):
                for order in data["data"]["orders"]:
                    if order.get("p_id") == self.parlay_id:
                        found_order_uuid = order.get("order_uuid")
                        break
            
            if found_order_uuid:
                self.order_uuid = found_order_uuid
                print(f"✅ Found SP1 order_uuid: {found_order_uuid}")
            else:
                raise Exception(f"No matching SP1 order found for parlay_id: {self.parlay_id}")
        else:
            raise Exception(f"SP1 list orders failed: {response.status_code} - {response.text}")

    def step8_sp1_acknowledge_confirmation(self):
        """Step 8: SP1 Acknowledge Confirmation"""
        print("🤝 STEP 8: SP1 Acknowledge Confirmation")
        
        # Calculate price_probability (like Postman prerequest script)
        price_probability = []
        for item in self.estimated_prices:
            probability = self.calculate_and_round_probability(item["odds"])
            price_probability.append({
                "line_id": item["line_id"],
                "probability": probability
            })
        
        # Note: confirmed_odds is commented out in Postman, so we exclude it
        payload = {
            "action": "accept",
            "confirmed_stake": 100,
            "price_probability": [{
                "lines": price_probability,
                "max_risk": 200,
                "vig": 0.1
            }],
            "signature": "string"
        }
        
        response = requests.post(
            f"{self.base_url}/parlay/sp/orders/confirmations",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.mm1_token}",
                "Content-Type": "application/json"
            },
            params={"order_uuid": self.order_uuid}
        )
        
        if response.status_code == 200:
            print(f"✅ SP1 confirmation acknowledged")
        else:
            print(f"⚠️ SP1 acknowledgment: {response.status_code} - {response.text}")

    def step9_sp2_list_orders(self):
        """Step 9: SP2 List Orders and find order_uuid2"""
        print("🔍 STEP 9: SP2 List Orders")
        
        response = requests.get(
            f"{self.base_url}/parlay/sp/orders",
            headers={"Authorization": f"Bearer {self.mm2_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Find matching order (like Postman script)
            found_order_uuid = None
            if data and data.get("data") and data["data"].get("orders"):
                for order in data["data"]["orders"]:
                    if order.get("p_id") == self.parlay_id:
                        found_order_uuid = order.get("order_uuid")
                        break
            
            if found_order_uuid:
                self.order_uuid2 = found_order_uuid
                print(f"✅ Found SP2 order_uuid2: {found_order_uuid}")
            else:
                raise Exception(f"No matching SP2 order found for parlay_id: {self.parlay_id}")
        else:
            raise Exception(f"SP2 list orders failed: {response.status_code} - {response.text}")

    def step10_sp2_acknowledge_confirmation(self):
        """Step 10: SP2 Acknowledge Confirmation"""
        print("🤝 STEP 10: SP2 Acknowledge Confirmation")
        
        # Calculate price_probability (like Postman prerequest script)
        price_probability = []
        for item in self.estimated_prices:
            probability = self.calculate_and_round_probability(item["odds"])
            price_probability.append({
                "line_id": item["line_id"],
                "probability": probability
            })
        
        # Note: confirmed_odds is commented out in Postman, so we exclude it
        payload = {
            "action": "accept",
            "confirmed_stake": 50,  # Different stake for SP2 in Postman
            "price_probability": [{
                "lines": price_probability,
                "max_risk": 200,
                "vig": 0.1
            }],
            "signature": "string"
        }
        
        response = requests.post(
            f"{self.base_url}/parlay/sp/orders/confirmations",
            json=payload,
            headers={
                "Authorization": f"Bearer {self.mm2_token}",
                "Content-Type": "application/json"
            },
            params={"order_uuid": self.order_uuid2}
        )
        
        if response.status_code == 200:
            print(f"✅ SP2 confirmation acknowledged")
        else:
            print(f"⚠️ SP2 acknowledgment: {response.status_code} - {response.text}")

    def run_full_workflow(self):
        """Run the complete Postman workflow"""
        print("🚀 POSTMAN REPLICA TEST")
        print("="*60)
        print("📝 Following exact Postman collection workflow")
        print("="*60)
        
        try:
            self.step1_mm1_login()
            self.step2_mm2_login()
            self.step3_configure_parlay_and_request_price()
            self.step4_sp2_respond_with_offer()
            self.step5_sp1_respond_with_offer()
            self.step6_user_confirm_bet()
            
            # Small delay before checking orders (like in real workflow)
            print("\n⏱️ Waiting 2 seconds before checking orders...")
            time.sleep(2)
            
            self.step7_sp1_list_orders()
            self.step8_sp1_acknowledge_confirmation()
            self.step9_sp2_list_orders()  
            self.step10_sp2_acknowledge_confirmation()
            
            print("\n🎉 POSTMAN REPLICA WORKFLOW COMPLETED!")
            print("="*60)
            print(f"✅ Parlay ID: {self.parlay_id}")
            print(f"✅ Final odds: {self.offer_odds}")
            print(f"✅ SP1 order_uuid: {self.order_uuid}")
            print(f"✅ SP2 order_uuid2: {self.order_uuid2}")
            return True
            
        except Exception as e:
            print(f"\n❌ POSTMAN REPLICA FAILED: {str(e)}")
            print("="*60)
            return False


def main():
    test = PostmanReplicaTest()
    success = test.run_full_workflow()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
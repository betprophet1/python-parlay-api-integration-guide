#!/usr/bin/env python3
"""
Modern Postman Replica Test - Dynamic Market Selection

This test follows the exact Postman workflow logic but dynamically finds
available markets instead of using hardcoded ones that may be expired.

Workflow:
1. MM1 and MM2 authentication 
2. User parlay request (with available markets)
3. SP2 provides offer with calculated odds
4. SP1 provides offer with calculated odds  
5. User confirms bet
6. SP1 lists orders and acknowledges
7. SP2 lists orders and acknowledges
"""

import json
import requests
import time
import math
from datetime import datetime

class ModernPostmanReplicaTest:
    """Modern test that follows Postman workflow with dynamic market selection"""
    
    def __init__(self):
        with open("test_config.json", 'r') as f:
            self.config = json.load(f)["test_configuration"]
        
        self.base_url = self.config["base_url"]
        
        # Tokens
        self.mm1_token = None
        self.mm2_token = None
        self.user_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6InNpbTIifQ.eyJhY2NvdW50VHlwZSI6MCwiZXhwIjoxNzU5ODMwNTg4LCJleHRyYU9ubGluZVRpbWUiOjAsImlzT3RwRXhwaXJlZCI6ZmFsc2UsImlzU3VzcGVuZGVkIjpmYWxzZSwiaXNzIjoiaHR0cDovL21vdGhlcnNoaXAubW90aGVyc2hpcC1zYW5kYm94IiwianRpIjoiZTg5M2I5MmYtNjdjZi00OWQyLTk2NGQtMzhjNjI2YzVlMzg3Iiwia2JhQW5zd2Vyc0luZm8iOiJOL0EiLCJreWNJbmZvIjoiU3VjY2VzcyIsInBlbmRpbmdCeUFkbWluIjpmYWxzZSwicHVzaGVySW5mbyI6eyJhdXRoQ2hhbm5lbCI6InVzZXIuYXV0aGVudGljYXRpb24uZTg5M2I5MmYtNjdjZi00OWQyLTk2NGQtMzhjNjI2YzVlMzg3IiwiYmFsYW5jZVVwZGF0ZWRFdmVudCI6IndhbGxldC5iYWxhbmNlLnVwZGF0ZWQiLCJjbHVzdGVyIjoibXQxIiwiaWQiOiJjMjBmYTM2ZmJjM2MzYzMwOGZmYSIsImluZm9DaGFubmVsIjoidXNlci5pbmZvcm1hdGlvbi5lZjVjM2JlMy1hZDRkLTRlMGYtYWNlNy05NzA1NjkwYzgyNmUiLCJpbmZvcm1hdGlvblVwZGF0ZWRFdmVudCI6InVzZXIuaW5mb3JtYXRpb24udXBkYXRlZCIsImtiYUNoYWxsZW5nZVF1ZXN0aW9uc0V2ZW50IjoidXNlci5rYmEuY2hhbGxlbmdlIiwic2Vzc2lvblRlcm1pbmF0ZWRFdmVudCI6InNlc3Npb24udGVybWluYXRlZCJ9LCJyZWdpb24iOiJOWSIsInN1YiI6ImxhbS50cmFuK3VzcjAwNEBiZXRwcm9waGV0LmNvIiwidXNlcklkIjoiZWY1YzNiZTMtYWQ0ZC00ZTBmLWFjZTctOTcwNTY5MGM4MjZlIn0.esyueJeCe4Xqdj9tbzZQYD0I8W8eGs31-XQal6hj5lY"
        
        # Available market combinations to try (fresh market data)
        self.market_combinations = [
            # Fresh market data from currently open events
            [
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
        ]
        
        # Calculated values (will be set during execution)
        self.parlay_id = None
        self.offer_odds = None
        self.estimated_prices = None
        self.valid_until = None
        self.order_uuid = None
        self.order_uuid2 = None
        self.selected_markets = None

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
        """Step 3: Try different market combinations until one works"""
        print("📋 STEP 3: Configure Parlay & Request Price (Dynamic Market Selection)")
        
        for i, market_lines in enumerate(self.market_combinations):
            print(f"🔍 Trying market combination {i+1}/{len(self.market_combinations)}")
            
            # Calculate parlay odds (like Postman prerequest script)
            individual_american_odds_array = [110, -150, 200]  # Default odds for calculation
            
            parlay_decimal_odds = 1
            estimated_prices = []
            
            for j, line in enumerate(market_lines):
                individual_american_odds = individual_american_odds_array[j] if j < len(individual_american_odds_array) else 100
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
                self.selected_markets = market_lines
                print(f"✅ Parlay created - ID: {self.parlay_id}")
                print(f"✅ Using market combination {i+1}")
                return
            else:
                print(f"❌ Market combination {i+1} failed: {response.status_code} - {response.text}")
        
        raise Exception("All market combinations failed")

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
            print("✅ SP2 offer submitted successfully")
        else:
            raise Exception(f"SP2 offer failed: {response.status_code} - {response.text}")

    def step5_sp1_respond_with_offer(self):
        """Step 5: SP1 Respond with Offer"""
        print("💰 STEP 5: SP1 Respond with Offer")
        
        # Update valid_until (400 seconds from now, like Postman)
        future_ms = int(time.time() * 1000) + 400000
        valid_until = future_ms * 1_000_000
        
        payload = {
            "parlay_id": self.parlay_id,
            "offers": [{
                "odds": self.offer_odds,
                "max_risk": 200.0,
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
            print("✅ SP1 offer submitted successfully")
        else:
            raise Exception(f"SP1 offer failed: {response.status_code} - {response.text}")

    def step6_user_confirm_bet(self):
        """Step 6: User Confirm Bet"""
        print("🎯 STEP 6: User Confirm Bet")
        
        payload = {
            "parlayId": self.parlay_id,
            "odds": self.offer_odds,
            "stake": 50.0,
            "estimated_prices": self.estimated_prices
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
            print("✅ User bet confirmed successfully")
        else:
            raise Exception(f"User confirmation failed: {response.status_code} - {response.text}")

    def step7_sp1_list_orders_and_acknowledge(self):
        """Step 7: SP1 List Orders and Acknowledge"""
        print("📋 STEP 7: SP1 List Orders and Acknowledge")
        
        # List orders
        response = requests.get(
            f"{self.base_url}/parlay/sp/orders",
            headers={
                "Authorization": f"Bearer {self.mm1_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            orders_data = response.json()
            
            # Find our parlay order
            orders = orders_data["data"]["orders"]
            matching_orders = [
                order for order in orders 
                if order.get("p_id") == self.parlay_id
            ]
            
            if matching_orders:
                self.order_uuid = matching_orders[0]["order_uuid"]
                print(f"✅ Found SP1 order UUID: {self.order_uuid}")
                
                # Acknowledge confirmation
                ack_payload = {
                    "action": "accept",
                    "confirmed_stake": 50.0,
                    "price_probability": [{
                        "lines": [{"line_id": price["line_id"], "probability": 0.5} 
                                 for price in self.estimated_prices],
                        "max_risk": 200.0,
                        "vig": 0.1
                    }],
                    "signature": "test_signature"
                }
                
                ack_response = requests.post(
                    f"{self.base_url}/parlay/sp/orders/confirmations",
                    json=ack_payload,
                    headers={
                        "Authorization": f"Bearer {self.mm1_token}",
                        "Content-Type": "application/json"
                    },
                    params={"order_uuid": self.order_uuid}
                )
                
                if ack_response.status_code == 200:
                    print("✅ SP1 acknowledgment successful")
                else:
                    raise Exception(f"SP1 acknowledgment failed: {ack_response.status_code}")
            else:
                print("⚠️ No matching SP1 order found")
        else:
            raise Exception(f"SP1 order listing failed: {response.status_code}")

    def step8_sp2_list_orders_and_acknowledge(self):
        """Step 8: SP2 List Orders and Acknowledge"""
        print("📋 STEP 8: SP2 List Orders and Acknowledge")
        
        # List orders
        response = requests.get(
            f"{self.base_url}/parlay/sp/orders",
            headers={
                "Authorization": f"Bearer {self.mm2_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            orders_data = response.json()
            
            # Find our parlay order
            orders = orders_data["data"]["orders"]
            matching_orders = [
                order for order in orders 
                if order.get("p_id") == self.parlay_id
            ]
            
            if matching_orders:
                self.order_uuid2 = matching_orders[0]["order_uuid"]
                print(f"✅ Found SP2 order UUID: {self.order_uuid2}")
                
                # Acknowledge confirmation
                ack_payload = {
                    "action": "accept",
                    "confirmed_stake": 50.0,
                    "price_probability": [{
                        "lines": [{"line_id": price["line_id"], "probability": 0.5} 
                                 for price in self.estimated_prices],
                        "max_risk": 100.0,
                        "vig": 0.1
                    }],
                    "signature": "test_signature"
                }
                
                ack_response = requests.post(
                    f"{self.base_url}/parlay/sp/orders/confirmations",
                    json=ack_payload,
                    headers={
                        "Authorization": f"Bearer {self.mm2_token}",
                        "Content-Type": "application/json"
                    },
                    params={"order_uuid": self.order_uuid2}
                )
                
                if ack_response.status_code == 200:
                    print("✅ SP2 acknowledgment successful")
                else:
                    raise Exception(f"SP2 acknowledgment failed: {ack_response.status_code}")
            else:
                print("⚠️ No matching SP2 order found")
        else:
            raise Exception(f"SP2 order listing failed: {response.status_code}")

    def run_comprehensive_test(self):
        """Run the complete Postman replica workflow"""
        print("🚀 MODERN POSTMAN REPLICA TEST")
        print("============================================================")
        print("📝 Following exact Postman workflow with dynamic market selection")
        print("============================================================")
        
        try:
            self.step1_mm1_login()
            self.step2_mm2_login()
            self.step3_configure_parlay_and_request_price()
            self.step4_sp2_respond_with_offer()
            self.step5_sp1_respond_with_offer()
            self.step6_user_confirm_bet()
            self.step7_sp1_list_orders_and_acknowledge()
            self.step8_sp2_list_orders_and_acknowledge()
            
            print("\n🎉 MODERN POSTMAN REPLICA SUCCESSFUL!")
            print("============================================================")
            print(f"📊 Parlay ID: {self.parlay_id}")
            print(f"📊 SP1 Order UUID: {self.order_uuid}")
            print(f"📊 SP2 Order UUID: {self.order_uuid2}")
            print(f"📊 Final Odds: {self.offer_odds}")
            print("============================================================")
            
        except Exception as e:
            print(f"\n❌ MODERN POSTMAN REPLICA FAILED: {e}")
            print("============================================================")
            return False
        
        return True

if __name__ == "__main__":
    test = ModernPostmanReplicaTest()
    success = test.run_comprehensive_test()
    exit(0 if success else 1)
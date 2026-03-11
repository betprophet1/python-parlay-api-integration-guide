#!/usr/bin/env python3
"""
🧪 IMPROVED PRICE PROBABILITY REQUIREMENT VERIFICATION

Enhanced test to verify the new price_probability requirement with better order status handling.
"""

import requests
import json
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImprovedPriceProbabilityTester:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.user_token = self.get_user_token()
        
        # SP Credentials
        self.sp1_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        
        # Simple test scenarios
        self.test_scenarios = {
            "non_sgp_parlay": {
                "name": "Non-SGP Parlay (Different Events)",
                "market_lines": [
                    {
                        "line": -4.5,
                        "lineId": "04f2da44cbba365fd807c2bf6c5f09ab",
                        "marketId": 223,
                        "outcomeId": 1714,
                        "sportEventId": 19191
                    },
                    {
                        "line": -1.5,
                        "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852",
                        "marketId": 223,
                        "outcomeId": 1714,
                        "sportEventId": 19192
                    }
                ],
                "is_sgp": False
            },
            "sgp_parlay": {
                "name": "SGP Parlay (Same Event + Different Event)", 
                "market_lines": [
                    {
                        "line": -4.5,
                        "lineId": "04f2da44cbba365fd807c2bf6c5f09ab",
                        "marketId": 223,
                        "outcomeId": 1714,
                        "sportEventId": 19191  # Same event
                    },
                    {
                        "line": 46.5,
                        "lineId": "59d4d1618c30fb8bbbcaf5d22b7f293a",
                        "marketId": 225,
                        "outcomeId": 12,
                        "sportEventId": 19191  # Same event
                    }
                ],
                "is_sgp": True
            }
        }

    def get_user_token(self):
        """Get fresh user token"""
        url = f"{self.base_url}/api/v1/auth/login"
        payload = {
            "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
            "email": "lam.tran+usr004@betprophet.co",
            "password": "Kh0ngbiet1"
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("accessToken")
        return None

    def authenticate_sp(self, credentials, sp_name):
        """Authenticate Service Provider"""
        url = f"{self.base_url}/partner/auth/login"
        
        try:
            response = requests.post(url, json=credentials)
            if response.status_code == 200:
                token = response.json()["data"]["access_token"]
                logger.info(f"✅ {sp_name} Authentication SUCCESS")
                return token
            else:
                logger.error(f"❌ {sp_name} Authentication FAILED: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ {sp_name} Authentication ERROR: {str(e)}")
            return None

    def create_parlay_request(self, market_lines):
        """Create parlay request"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        payload = {"marketLines": market_lines}
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                parlay_id = response.json()["data"]["parlayId"]
                logger.info(f"✅ Parlay created: {parlay_id}")
                return parlay_id
            else:
                logger.error(f"❌ Parlay creation FAILED: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Parlay creation ERROR: {str(e)}")
            return None

    def provide_sp_offer(self, parlay_id, sp_token, market_lines):
        """SP provides offer"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": 800,
                    "max_risk": 100,
                    "valid_until": int((time.time() + 50) * 1_000_000_000),
                    "estimated_prices": [
                        {
                            "line_id": line["lineId"],
                            "odds": 800
                        }
                        for line in market_lines
                    ]
                }
            ]
        }
        
        headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                logger.info("✅ SP offer sent")
                return True
            else:
                logger.error(f"❌ SP offer FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ SP offer ERROR: {str(e)}")
            return False

    def user_confirm_bet(self, parlay_id):
        """User confirms bet"""
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        payload = {
            "parlayId": parlay_id,
            "odds": 800,
            "stake": 10000  # $100 in cents
        }
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                logger.info("✅ User confirmed bet")
                return True
            else:
                logger.error(f"❌ User confirmation FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ User confirmation ERROR: {str(e)}")
            return False

    def debug_sp_orders(self, parlay_id, sp_token):
        """Debug: Check all SP orders and their statuses"""
        url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                orders = response.json()["data"]["orders"]
                logger.info(f"🔍 DEBUG: Found {len(orders)} total SP orders")
                
                matching_orders = [order for order in orders if order["p_id"] == parlay_id]
                logger.info(f"🔍 DEBUG: Found {len(matching_orders)} orders for parlay {parlay_id}")
                
                for i, order in enumerate(matching_orders):
                    logger.info(f"   Order {i+1}: Status={order.get('status')}, UUID={order.get('order_uuid')}")
                    logger.info(f"            Created={order.get('created_at')}, Updated={order.get('updated_at')}")
                
                return matching_orders
            else:
                logger.error(f"❌ DEBUG: Failed to get orders: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting orders: {str(e)}")
            return []

    def test_confirmation_without_price_probability(self, parlay_id, sp_token, market_lines, scenario_name):
        """Test SP confirmation without price_probability field"""
        logger.info(f"\n🔍 TESTING CONFIRMATION WITHOUT price_probability for {scenario_name}")
        
        # Wait a bit for order status to update
        time.sleep(3)
        
        # Debug: Check current orders
        matching_orders = self.debug_sp_orders(parlay_id, sp_token)
        
        if not matching_orders:
            logger.error("❌ No matching orders found")
            return None
        
        # Find the most recent order
        latest_order = max(matching_orders, key=lambda x: x.get('created_at', 0))
        order_uuid = latest_order.get('order_uuid')
        current_status = latest_order.get('status')
        
        logger.info(f"📋 Latest order: UUID={order_uuid}, Status={current_status}")
        
        if not order_uuid:
            logger.error("❌ No order UUID found")
            return None
        
        # Attempt confirmation without price_probability
        url = f"{self.base_url}/parlay/sp/orders/confirmations"
        payload = {
            "action": "accept",
            "confirmed_stake": 100,
            # INTENTIONALLY OMIT price_probability field
            "signature": "test_signature_sp1"
        }
        
        headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
        
        logger.info(f"📤 Sending confirmation WITHOUT price_probability:")
        logger.info(f"   Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, params={"order_uuid": order_uuid})
            
            logger.info(f"📥 Confirmation response:")
            logger.info(f"   Status: {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"   Response: {json.dumps(response_data, indent=2)}")
                return response_data
            except:
                logger.info(f"   Raw response: {response.text}")
                return {"raw_response": response.text, "status_code": response.status_code}
                
        except Exception as e:
            logger.error(f"❌ Confirmation ERROR: {str(e)}")
            return None

    def test_scenario(self, scenario_key, scenario):
        """Test a single scenario"""
        logger.info(f"\n🧪 TESTING {scenario_key.upper()}: {scenario['name']}")
        logger.info("=" * 80)
        logger.info(f"📊 Is SGP: {scenario['is_sgp']}")
        logger.info(f"📊 Market Lines: {len(scenario['market_lines'])} lines")
        
        # Events analysis
        event_ids = [line["sportEventId"] for line in scenario["market_lines"]]
        unique_events = set(event_ids)
        logger.info(f"📊 Events: {len(unique_events)} unique events from {event_ids}")
        
        # Step 1: Authenticate SP
        sp_token = self.authenticate_sp(self.sp1_credentials, "SP1")
        if not sp_token:
            return False
        
        # Step 2: Create parlay
        parlay_id = self.create_parlay_request(scenario['market_lines'])
        if not parlay_id:
            return False
        
        # Step 3: SP provides offer
        if not self.provide_sp_offer(parlay_id, sp_token, scenario['market_lines']):
            return False
        
        # Step 4: User confirms bet
        if not self.user_confirm_bet(parlay_id):
            return False
        
        # Step 5: Test confirmation without price_probability
        response = self.test_confirmation_without_price_probability(
            parlay_id, sp_token, scenario['market_lines'], scenario['name']
        )
        
        if not response:
            logger.error("❌ No response from confirmation test")
            return False
        
        # Step 6: Analyze results
        logger.info(f"\n📊 ANALYZING RESULTS for {scenario_key.upper()}:")
        
        expected_warning = "the confirmation is rejected automatically because the parlay is non-SGP, but no price probability provided"
        
        if scenario['is_sgp']:
            # SGP: Should succeed without price_probability
            if response.get("success") == True and "warning" not in response:
                logger.info("✅ CORRECT: SGP confirmation succeeded without price_probability")
                return True
            else:
                logger.error("❌ INCORRECT: SGP should succeed without price_probability")
                logger.error(f"   Got: {response}")
                return False
        else:
            # Non-SGP: Should be rejected without price_probability
            if (response.get("success") == True and 
                expected_warning in response.get("warning", "")):
                logger.info("✅ CORRECT: Non-SGP confirmation rejected with expected warning")
                return True
            else:
                logger.error("❌ INCORRECT: Non-SGP should be rejected with specific warning")
                logger.error(f"   Expected warning containing: '{expected_warning}'")
                logger.error(f"   Got: {response}")
                return False

    def run_all_tests(self):
        """Run all test scenarios"""
        logger.info("🚀 STARTING IMPROVED PRICE_PROBABILITY REQUIREMENT VERIFICATION")
        logger.info("=" * 100)
        logger.info("📅 Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("🎯 Testing requirement:")
        logger.info("   - Non-SGP parlays (different events): price_probability REQUIRED")
        logger.info("   - SGP parlays (same events): price_probability OPTIONAL")
        logger.info("=" * 100)
        
        results = {"total": 0, "passed": 0, "failed": 0, "scenarios": {}}
        
        for scenario_key, scenario in self.test_scenarios.items():
            results["total"] += 1
            
            try:
                if self.test_scenario(scenario_key, scenario):
                    results["passed"] += 1
                    results["scenarios"][scenario_key] = "PASSED"
                    logger.info(f"\n✅ {scenario_key.upper()}: PASSED")
                else:
                    results["failed"] += 1
                    results["scenarios"][scenario_key] = "FAILED"
                    logger.error(f"\n❌ {scenario_key.upper()}: FAILED")
                    
            except Exception as e:
                results["failed"] += 1
                results["scenarios"][scenario_key] = f"ERROR: {str(e)}"
                logger.error(f"\n❌ {scenario_key.upper()}: ERROR - {str(e)}")
        
        # Final summary
        logger.info("\n" + "=" * 100)
        logger.info("🏁 IMPROVED PRICE_PROBABILITY REQUIREMENT TEST RESULTS")
        logger.info("=" * 100)
        logger.info(f"📊 Total tests: {results['total']}")
        logger.info(f"📊 Passed: {results['passed']}")
        logger.info(f"📊 Failed: {results['failed']}")
        
        for scenario_key, result in results["scenarios"].items():
            status_emoji = "✅" if result == "PASSED" else "❌"
            logger.info(f"   {status_emoji} {scenario_key}: {result}")
        
        if results["passed"] == results["total"]:
            logger.info("\n🎉 ALL TESTS PASSED! price_probability requirement is working correctly.")
        else:
            logger.info(f"\n⚠️  {results['failed']} test(s) failed. Check implementation or test logic.")
        
        return results

if __name__ == "__main__":
    tester = ImprovedPriceProbabilityTester()
    results = tester.run_all_tests()
#!/usr/bin/env python3
"""
🧪 PRICE PROBABILITY REQUIREMENT VERIFICATION

Test the new requirement:
- price_probability field is REQUIRED for confirmation if parlay satisfies:
  1. All legs are from different games (non-SGP)
  2. Has 2+ legs (which is all parlays since 1-leg not allowed)

If field not provided, should reject confirmation and treat as SP rejection.
Expected response: {"success": true, "warning": "the confirmation is rejected automatically because the parlay is non-SGP, but no price probability provided"}
Expected order status: "rejected"
"""

import requests
import json
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PriceProbabilityRequirementTester:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.user_token = self.get_user_token()
        
        # SP Credentials
        self.sp1_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        
        self.sp2_credentials = {
            "access_key": "ec45827afa933f97ec19e674c0fa39c6",
            "secret_key": "442df8e9fe96e4f7e744b2d3cac5cd51"
        }
        
        # Fresh active market data from updated_test_scenarios.py
        self.test_scenarios = {
            "non_sgp_regular_parlay": {
                "name": "Non-SGP Regular Parlay - Different Events Only",
                "description": "2 lines from completely different events (should require price_probability)",
                "market_lines": [
                    {
                        "line": -4.5,
                        "lineId": "04f2da44cbba365fd807c2bf6c5f09ab",  # TB -4.5
                        "marketId": 223,
                        "outcomeId": 1714,
                        "sportEventId": 19191
                    },
                    {
                        "line": -1.5,
                        "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852",  # SEA -1.5
                        "marketId": 223,
                        "outcomeId": 1714,
                        "sportEventId": 19192
                    }
                ],
                "is_sgp": False,
                "expected_rejection": True
            },
            "non_sgp_mixed_markets": {
                "name": "Non-SGP Mixed Markets - 3 Different Events",
                "description": "3 lines from different events, mixed markets (should require price_probability)",
                "market_lines": [
                    {
                        "line": 46.5,
                        "lineId": "59d4d1618c30fb8bbbcaf5d22b7f293a",  # TB/NE Over 46.5
                        "marketId": 225,
                        "outcomeId": 12,
                        "sportEventId": 19191
                    },
                    {
                        "line": 0,
                        "lineId": "b13ea0fce285c5b5dbb800c47fe88019",  # SEA Moneyline
                        "marketId": 219,
                        "outcomeId": 4,
                        "sportEventId": 19192
                    },
                    {
                        "line": 50,
                        "lineId": "be5b47eaaa33b9c7d7671c40d44a7734",  # WAS/DET Over 50
                        "marketId": 225,
                        "outcomeId": 12,
                        "sportEventId": 19194
                    }
                ],
                "is_sgp": False,
                "expected_rejection": True
            },
            "sgp_control_test": {
                "name": "SGP Control Test - Same Event + Different Event",
                "description": "2 lines from same event + 1 from different (SGP, should NOT require price_probability)",
                "market_lines": [
                    {
                        "line": -4.5,
                        "lineId": "04f2da44cbba365fd807c2bf6c5f09ab",  # TB -4.5
                        "marketId": 223,
                        "outcomeId": 1714,
                        "sportEventId": 19191  # Same event
                    },
                    {
                        "line": 46.5,
                        "lineId": "59d4d1618c30fb8bbbcaf5d22b7f293a",  # TB/NE Over 46.5
                        "marketId": 225,
                        "outcomeId": 12,
                        "sportEventId": 19191  # Same event as above
                    },
                    {
                        "line": -1.5,
                        "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852",  # SEA -1.5
                        "marketId": 223,
                        "outcomeId": 1714,
                        "sportEventId": 19192  # Different event
                    }
                ],
                "is_sgp": True,
                "expected_rejection": False
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
        """Create parlay request and return parlay ID"""
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
                logger.info(f"✅ Parlay created successfully - ID: {parlay_id}")
                return parlay_id
            else:
                logger.error(f"❌ Parlay creation FAILED: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Parlay creation ERROR: {str(e)}")
            return None

    def provide_sp_offer(self, parlay_id, sp_token, odds, max_risk, sp_name, market_lines):
        """Service Provider provides offer"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": odds,
                    "max_risk": max_risk,
                    "valid_until": int((time.time() + 50) * 1_000_000_000),
                    "estimated_prices": [
                        {
                            "line_id": line["lineId"],
                            "odds": odds
                        }
                        for line in market_lines
                    ]
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {sp_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                logger.info(f"✅ {sp_name} offer sent successfully")
                return True
            else:
                logger.error(f"❌ {sp_name} offer FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ {sp_name} offer ERROR: {str(e)}")
            return False

    def user_confirm_bet(self, parlay_id, odds, stake):
        """User confirms the bet"""
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        payload = {
            "parlayId": parlay_id,
            "odds": odds,
            "stake": int(stake * 100)  # Convert to cents
        }
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                logger.info("✅ User bet confirmed successfully")
                return True
            else:
                logger.error(f"❌ User bet confirmation FAILED: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ User bet confirmation ERROR: {str(e)}")
            return False

    def sp_confirm_without_price_probability(self, parlay_id, sp_token, sp_name, market_lines):
        """SP attempts confirmation WITHOUT price_probability field (should be rejected for non-SGP)"""
        # Get order UUID first
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(orders_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ {sp_name} get orders FAILED: {response.status_code}")
                return None
            
            orders = response.json()["data"]["orders"]
            order_uuid = None
            
            for order in orders:
                if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
                    order_uuid = order["order_uuid"]
                    break
            
            if not order_uuid:
                logger.error(f"❌ {sp_name} order UUID not found for parlay {parlay_id}")
                return None
            
            logger.info(f"📋 Found {sp_name} order UUID: {order_uuid}")
            
            # Attempt confirmation WITHOUT price_probability field
            confirm_url = f"{self.base_url}/parlay/sp/orders/confirmations"
            payload = {
                "action": "accept",
                "confirmed_stake": 100,  # $100 stake
                # INTENTIONALLY OMITTING price_probability field to test requirement
                "signature": f"test_signature_{sp_name.lower()}"
            }
            
            logger.info(f"📤 {sp_name} sending confirmation WITHOUT price_probability:")
            logger.info(f"   Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(confirm_url, json=payload, headers=headers, params={"order_uuid": order_uuid})
            
            logger.info(f"📥 {sp_name} confirmation response:")
            logger.info(f"   Status: {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"   Response: {json.dumps(response_data, indent=2)}")
                return response_data
            except:
                logger.info(f"   Raw response: {response.text}")
                return {"raw_response": response.text}
                
        except Exception as e:
            logger.error(f"❌ {sp_name} confirmation ERROR: {str(e)}")
            return None

    def sp_confirm_with_price_probability(self, parlay_id, sp_token, sp_name, market_lines):
        """SP attempts confirmation WITH price_probability field (should succeed)"""
        # Get order UUID first
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(orders_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ {sp_name} get orders FAILED: {response.status_code}")
                return None
            
            orders = response.json()["data"]["orders"]
            order_uuid = None
            
            for order in orders:
                if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
                    order_uuid = order["order_uuid"]
                    break
            
            if not order_uuid:
                logger.error(f"❌ {sp_name} order UUID not found for parlay {parlay_id}")
                return None
            
            # Confirmation WITH price_probability field
            confirm_url = f"{self.base_url}/parlay/sp/orders/confirmations"
            payload = {
                "action": "accept",
                "confirmed_stake": 100,
                "price_probability": [
                    {
                        "lines": [
                            {
                                "line_id": line["lineId"],
                                "probability": 0.5  # Example probability
                            }
                            for line in market_lines
                        ],
                        "max_risk": 10000,  # $100 in cents
                        "vig": 0.1
                    }
                ],
                "signature": f"test_signature_{sp_name.lower()}"
            }
            
            logger.info(f"📤 {sp_name} sending confirmation WITH price_probability:")
            logger.info(f"   Payload: {json.dumps(payload, indent=2)}")
            
            response = requests.post(confirm_url, json=payload, headers=headers, params={"order_uuid": order_uuid})
            
            logger.info(f"📥 {sp_name} confirmation response:")
            logger.info(f"   Status: {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"   Response: {json.dumps(response_data, indent=2)}")
                return response_data
            except:
                logger.info(f"   Raw response: {response.text}")
                return {"raw_response": response.text}
                
        except Exception as e:
            logger.error(f"❌ {sp_name} confirmation ERROR: {str(e)}")
            return None

    def check_order_status(self, parlay_id, sp_token, sp_name):
        """Check the order status after confirmation attempt"""
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(orders_url, headers=headers)
            if response.status_code == 200:
                orders = response.json()["data"]["orders"]
                for order in orders:
                    if order["p_id"] == parlay_id:
                        status = order.get("status", "unknown")
                        logger.info(f"📊 {sp_name} order status for {parlay_id}: {status}")
                        return status
            return "not_found"
        except Exception as e:
            logger.error(f"❌ {sp_name} status check ERROR: {str(e)}")
            return "error"

    def test_scenario(self, scenario_key, scenario):
        """Test a single scenario"""
        logger.info(f"\n🧪 TESTING {scenario_key.upper()}: {scenario['name']}")
        logger.info("=" * 100)
        logger.info(f"📋 {scenario['description']}")
        logger.info(f"📊 Is SGP: {scenario['is_sgp']}")
        logger.info(f"📊 Expected rejection without price_probability: {scenario['expected_rejection']}")
        
        # Step 1: Authenticate SP
        sp_token = self.authenticate_sp(self.sp1_credentials, "SP1")
        if not sp_token:
            return False
        
        # Step 2: Create parlay
        parlay_id = self.create_parlay_request(scenario['market_lines'])
        if not parlay_id:
            return False
        
        # Step 3: SP provides offer
        if not self.provide_sp_offer(parlay_id, sp_token, 800, 100, "SP1", scenario['market_lines']):
            return False
        
        # Step 4: User confirms bet
        if not self.user_confirm_bet(parlay_id, 800, 100):
            return False
        
        time.sleep(2)  # Wait for confirmation to propagate
        
        # Step 5: Test confirmation WITHOUT price_probability
        logger.info(f"\n🔍 TESTING CONFIRMATION WITHOUT price_probability:")
        logger.info(f"   Expected result: {'REJECTION' if scenario['expected_rejection'] else 'SUCCESS'}")
        
        response_without_pp = self.sp_confirm_without_price_probability(parlay_id, sp_token, "SP1", scenario['market_lines'])
        
        time.sleep(1)
        order_status = self.check_order_status(parlay_id, sp_token, "SP1")
        
        # Validate results
        success = True
        if scenario['expected_rejection']:
            # Should be rejected for non-SGP parlays
            expected_warning = "the confirmation is rejected automatically because the parlay is non-SGP, but no price probability provided"
            
            if response_without_pp:
                if (response_without_pp.get("success") == True and 
                    expected_warning in response_without_pp.get("warning", "")):
                    logger.info("✅ CORRECT: Confirmation rejected with expected warning for non-SGP")
                    if order_status == "rejected":
                        logger.info("✅ CORRECT: Order status is 'rejected'")
                    else:
                        logger.error(f"❌ INCORRECT: Order status is '{order_status}', expected 'rejected'")
                        success = False
                else:
                    logger.error(f"❌ INCORRECT: Expected rejection warning not found")
                    logger.error(f"   Got: {response_without_pp}")
                    success = False
            else:
                logger.error("❌ INCORRECT: No response received")
                success = False
        else:
            # Should succeed for SGP parlays
            if response_without_pp and response_without_pp.get("success") == True:
                logger.info("✅ CORRECT: SGP confirmation succeeded without price_probability")
            else:
                logger.error(f"❌ INCORRECT: SGP confirmation should succeed")
                success = False
        
        return success

    def run_all_tests(self):
        """Run all test scenarios"""
        logger.info("🚀 STARTING PRICE_PROBABILITY REQUIREMENT VERIFICATION")
        logger.info("=" * 120)
        logger.info("📅 Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("🎯 Testing new requirement:")
        logger.info("   - price_probability field REQUIRED for non-SGP parlays (all legs from different games)")
        logger.info("   - price_probability field OPTIONAL for SGP parlays (at least 2 legs from same game)")
        logger.info("=" * 120)
        
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
        logger.info("\n" + "=" * 120)
        logger.info("🏁 PRICE_PROBABILITY REQUIREMENT TEST RESULTS")
        logger.info("=" * 120)
        logger.info(f"📊 Total tests: {results['total']}")
        logger.info(f"📊 Passed: {results['passed']}")
        logger.info(f"📊 Failed: {results['failed']}")
        
        for scenario_key, result in results["scenarios"].items():
            status_emoji = "✅" if result == "PASSED" else "❌"
            logger.info(f"   {status_emoji} {scenario_key}: {result}")
        
        if results["passed"] == results["total"]:
            logger.info("\n🎉 ALL TESTS PASSED! price_probability requirement is working correctly.")
        else:
            logger.info(f"\n⚠️  {results['failed']} test(s) failed. Review implementation.")
        
        return results

if __name__ == "__main__":
    tester = PriceProbabilityRequirementTester()
    results = tester.run_all_tests()
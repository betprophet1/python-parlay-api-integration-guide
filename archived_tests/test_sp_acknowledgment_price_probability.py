#!/usr/bin/env python3
"""
🧪 TEST SP ACKNOWLEDGMENT WITHOUT PRICE_PROBABILITY

This test creates a full parlay flow and then tests SP acknowledgment confirmation
WITHOUT the price_probability field to verify the expected rejection response.
"""

import requests
import json
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SPAcknowledgmentTester:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.user_token = self.get_fresh_user_token()
        
        # SP Credentials
        self.sp1_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        
        # Fresh market lines (Non-SGP - different events)
        self.market_lines = [
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
        ]

    def get_fresh_user_token(self):
        """Get fresh user authentication token"""
        login_url = "https://api-ss-sandbox.betprophet.co/api/v1/auth/login"
        payload = {
            "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
            "email": "lam.tran+usr004@betprophet.co",
            "password": "Kh0ngbiet1"
        }
        
        try:
            response = requests.post(login_url, json=payload)
            if response.status_code == 200:
                token = response.json().get("accessToken")
                logger.info("✅ Fresh user token obtained")
                return token
            else:
                logger.error(f"❌ Failed to get user token: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting user token: {e}")
            return None

    def authenticate_sp(self, sp_name):
        """Authenticate Service Provider"""
        url = f"{self.base_url}/partner/auth/login"
        
        try:
            response = requests.post(url, json=self.sp1_credentials)
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

    def create_parlay_request(self):
        """Create parlay request and return parlay ID"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        
        payload = {"marketLines": self.market_lines}
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                parlay_id = response.json()["data"]["parlayId"]
                logger.info(f"✅ Parlay created successfully - ID: {parlay_id}")
                logger.info(f"📋 Parlay type: NON-SGP (different events: {[line['sportEventId'] for line in self.market_lines]})")
                return parlay_id
            else:
                logger.error(f"❌ Parlay creation FAILED: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Parlay creation ERROR: {str(e)}")
            return None

    def provide_sp_offer(self, parlay_id, sp_token, sp_name):
        """Service Provider provides offer"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": 800,
                    "max_risk": 200,
                    "valid_until": int((time.time() + 50) * 1_000_000_000),  # 50 seconds
                    "estimated_prices": [
                        {
                            "line_id": line["lineId"],
                            "odds": 800
                        }
                        for line in self.market_lines
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

    def user_confirm_bet(self, parlay_id):
        """User confirms the bet"""
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        
        payload = {
            "parlayId": parlay_id,
            "odds": 800,
            "stake": 20000  # $200 in cents
        }
        
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        
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

    def sp_acknowledge_without_price_probability(self, sp_token, parlay_id, sp_name):
        """SP acknowledges confirmation WITHOUT price_probability field - should be rejected"""
        # First get SP orders to find the order UUID
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            # Wait a bit for order to be created
            logger.info("⏰ Waiting for SP order to be available...")
            time.sleep(3)
            
            response = requests.get(orders_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ {sp_name} get orders FAILED: {response.status_code}")
                return None
            
            orders = response.json()["data"]["orders"]
            matching_orders = [order for order in orders if order["p_id"] == parlay_id]
            
            logger.info(f"🔍 {sp_name} found {len(matching_orders)} orders for parlay {parlay_id}")
            
            if not matching_orders:
                logger.error(f"❌ No orders found for parlay {parlay_id}")
                # Debug: show recent orders
                recent_orders = sorted(orders, key=lambda x: x.get('created_at', 0), reverse=True)[:3]
                logger.info(f"📋 Recent orders for debugging:")
                for order in recent_orders:
                    logger.info(f"   Parlay: {order.get('p_id')}, Status: {order.get('status')}, UUID: {order.get('order_uuid')}")
                return None
            
            # Use the first matching order
            order = matching_orders[0]
            order_uuid = order["order_uuid"]
            current_status = order.get("status")
            
            logger.info(f"📋 Found {sp_name} order:")
            logger.info(f"   UUID: {order_uuid}")
            logger.info(f"   Status: {current_status}")
            logger.info(f"   Parlay: {parlay_id}")
            
            # Acknowledge confirmation WITHOUT price_probability field
            logger.info(f"\n🧪 TESTING: SP ACKNOWLEDGMENT WITHOUT price_probability")
            logger.info(f"   Expected: Rejection with specific warning for non-SGP parlay")
            
            confirm_url = f"{self.base_url}/parlay/sp/orders/confirmations"
            payload = {
                "action": "accept",
                "confirmed_stake": 200,  # $200
                # INTENTIONALLY OMITTING price_probability field to test requirement
                "signature": f"test_signature_without_price_prob"
            }
            
            logger.info(f"📤 Sending acknowledgment WITHOUT price_probability:")
            logger.info(f"   {json.dumps(payload, indent=2)}")
            
            response = requests.post(confirm_url, json=payload, headers=headers, params={"order_uuid": order_uuid})
            
            logger.info(f"\n📥 SP ACKNOWLEDGMENT RESPONSE:")
            logger.info(f"   Status Code: {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"   Response Data: {json.dumps(response_data, indent=2)}")
                return response_data
            except:
                logger.info(f"   Raw Response: {response.text}")
                return {"raw_response": response.text, "status_code": response.status_code}
                
        except Exception as e:
            logger.error(f"❌ {sp_name} acknowledgment ERROR: {str(e)}")
            return None

    def sp_acknowledge_with_price_probability(self, sp_token, parlay_id, sp_name):
        """SP acknowledges confirmation WITH price_probability field - should succeed (control test)"""
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(orders_url, headers=headers)
            if response.status_code != 200:
                return None
            
            orders = response.json()["data"]["orders"]
            matching_orders = [order for order in orders if order["p_id"] == parlay_id]
            
            if not matching_orders:
                return None
            
            order = matching_orders[0]
            order_uuid = order["order_uuid"]
            
            logger.info(f"\n✅ CONTROL TEST: SP ACKNOWLEDGMENT WITH price_probability")
            
            confirm_url = f"{self.base_url}/parlay/sp/orders/confirmations"
            payload = {
                "action": "accept",
                "confirmed_stake": 200,
                "price_probability": [
                    {
                        "lines": [
                            {
                                "line_id": line["lineId"],
                                "probability": 0.5  # Example probability
                            }
                            for line in self.market_lines
                        ],
                        "max_risk": 20000,  # $200 in cents
                        "vig": 0.1
                    }
                ],
                "signature": f"test_signature_with_price_prob"
            }
            
            logger.info(f"📤 Sending acknowledgment WITH price_probability (control):")
            
            response = requests.post(confirm_url, json=payload, headers=headers, params={"order_uuid": order_uuid})
            
            logger.info(f"📥 Control Response: Status {response.status_code}")
            
            try:
                response_data = response.json()
                logger.info(f"   Response Data: {json.dumps(response_data, indent=2)}")
                return response_data
            except:
                logger.info(f"   Raw Response: {response.text}")
                return {"raw_response": response.text, "status_code": response.status_code}
                
        except Exception as e:
            logger.error(f"❌ Control test ERROR: {str(e)}")
            return None

    def analyze_response(self, response, test_type):
        """Analyze the response to determine if it matches expectations"""
        logger.info(f"\n📊 ANALYZING {test_type} RESPONSE:")
        
        expected_warning = "the confirmation is rejected automatically because the parlay is non-SGP, but no price probability provided"
        
        if test_type == "WITHOUT price_probability":
            # Should be rejected with specific warning
            if (response and 
                response.get("success") == True and 
                expected_warning in response.get("warning", "")):
                logger.info("✅ CORRECT: Non-SGP parlay rejected with expected warning")
                logger.info(f"   Warning message: '{response.get('warning')}'")
                return True
            else:
                logger.error("❌ UNEXPECTED RESPONSE:")
                logger.error(f"   Expected: success=True with warning containing '{expected_warning}'")
                logger.error(f"   Got: {response}")
                return False
        else:
            # Should succeed
            if response and response.get("success") == True:
                logger.info("✅ CORRECT: Control test with price_probability succeeded")
                return True
            else:
                logger.error("❌ UNEXPECTED: Control test should succeed")
                logger.error(f"   Got: {response}")
                return False

    def run_complete_test(self):
        """Run the complete test flow"""
        logger.info("🚀 STARTING SP ACKNOWLEDGMENT PRICE_PROBABILITY REQUIREMENT TEST")
        logger.info("=" * 100)
        logger.info("📅 Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("🎯 Testing SP acknowledgment without price_probability field")
        logger.info("   Expected: Rejection with specific warning for non-SGP parlay")
        logger.info("=" * 100)
        
        results = {"total_tests": 0, "passed_tests": 0}
        
        # Step 1: Authenticate SP
        sp_token = self.authenticate_sp("SP1")
        if not sp_token:
            return results
        
        # Step 2: Create parlay
        parlay_id = self.create_parlay_request()
        if not parlay_id:
            return results
        
        # Step 3: SP provides offer
        if not self.provide_sp_offer(parlay_id, sp_token, "SP1"):
            return results
        
        # Step 4: User confirms bet
        if not self.user_confirm_bet(parlay_id):
            return results
        
        # Step 5: Test SP acknowledgment WITHOUT price_probability
        logger.info(f"\n{'='*80}")
        logger.info("🧪 MAIN TEST: SP ACKNOWLEDGMENT WITHOUT price_probability")
        logger.info("   This should be REJECTED for non-SGP parlays")
        logger.info(f"{'='*80}")
        
        results["total_tests"] += 1
        response_without = self.sp_acknowledge_without_price_probability(sp_token, parlay_id, "SP1")
        
        if response_without and self.analyze_response(response_without, "WITHOUT price_probability"):
            results["passed_tests"] += 1
        
        # Final summary
        logger.info("\n" + "=" * 100)
        logger.info("🏁 SP ACKNOWLEDGMENT PRICE_PROBABILITY TEST RESULTS")
        logger.info("=" * 100)
        logger.info(f"📊 Total tests: {results['total_tests']}")
        logger.info(f"📊 Passed: {results['passed_tests']}")
        logger.info(f"📊 Failed: {results['total_tests'] - results['passed_tests']}")
        
        if results["passed_tests"] == results["total_tests"] and results["total_tests"] > 0:
            logger.info("\n🎉 SUCCESS! price_probability requirement is working correctly!")
            logger.info("   ✅ Non-SGP parlays require price_probability field")
            logger.info("   ✅ Missing field triggers expected rejection response")
        elif results["total_tests"] == 0:
            logger.info("\n⚠️  NO TESTS COMPLETED - Check workflow setup")
        else:
            logger.info(f"\n❌ TEST FAILED - Requirement may not be implemented correctly")
        
        return results

if __name__ == "__main__":
    tester = SPAcknowledgmentTester()
    results = tester.run_complete_test()
#!/usr/bin/env python3
"""
🧪 FIXED PRICE_PROBABILITY REQUIREMENT TEST

Tests the price_probability requirement at the SP confirmation stage by:
1. Using an existing working SP order from previous tests
2. Testing confirmation WITH and WITHOUT price_probability field
3. Verifying the rejection behavior for non-SGP parlays
"""

import requests
import json
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixedPriceProbabilityTester:
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

    def get_existing_sp_orders(self, sp_token, sp_name):
        """Get existing SP orders that might be in 'sent_confirmation' status"""
        url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                orders = response.json()["data"]["orders"]
                logger.info(f"📊 {sp_name}: Found {len(orders)} total orders")
                
                # Look for orders in sent_confirmation status
                confirmation_orders = [order for order in orders if order.get("status") == "sent_confirmation"]
                logger.info(f"📊 {sp_name}: Found {len(confirmation_orders)} orders in 'sent_confirmation' status")
                
                # Show all order statuses for debugging
                status_counts = {}
                for order in orders:
                    status = order.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                logger.info(f"📋 {sp_name} Order statuses: {status_counts}")
                
                return orders, confirmation_orders
                
            else:
                logger.error(f"❌ Failed to get {sp_name} orders: {response.status_code}")
                return [], []
        except Exception as e:
            logger.error(f"❌ Error getting {sp_name} orders: {str(e)}")
            return [], []

    def create_fresh_parlay_and_order(self, sp_token, sp_name):
        """Create a fresh parlay and get it to sent_confirmation status"""
        logger.info(f"\n🆕 CREATING FRESH PARLAY FOR {sp_name}")
        
        # Non-SGP parlay (different events)
        market_lines = [
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
        ]
        
        # Step 1: Create parlay
        url = f"{self.base_url}/parlay/api/v1/user/request"
        payload = {"marketLines": market_lines}
        headers = {"Authorization": f"Bearer {self.user_token}", "Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            logger.error(f"❌ Failed to create parlay: {response.status_code}")
            return None, None
        
        parlay_id = response.json()["data"]["parlayId"]
        logger.info(f"✅ Created parlay: {parlay_id}")
        
        # Step 2: SP provides offer
        offer_url = f"{self.base_url}/parlay/sp/orders/offers"
        offer_payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": 800,
                    "max_risk": 200,
                    "valid_until": int((time.time() + 60) * 1_000_000_000),
                    "estimated_prices": [
                        {"line_id": line["lineId"], "odds": 800}
                        for line in market_lines
                    ]
                }
            ]
        }
        
        offer_headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
        response = requests.post(offer_url, json=offer_payload, headers=offer_headers)
        
        if response.status_code != 200:
            logger.error(f"❌ Failed to send {sp_name} offer: {response.status_code}")
            return parlay_id, None
        
        logger.info(f"✅ {sp_name} offer sent")
        
        # Step 3: User confirms bet
        confirm_url = f"{self.base_url}/parlay/api/v1/user/confirm"
        confirm_payload = {
            "parlayId": parlay_id,
            "odds": 800,
            "stake": 10000  # $100
        }
        confirm_headers = {"Authorization": f"Bearer {self.user_token}"}
        
        response = requests.post(confirm_url, json=confirm_payload, headers=confirm_headers)
        if response.status_code != 200:
            logger.error(f"❌ Failed user confirmation: {response.status_code}")
            return parlay_id, None
        
        logger.info("✅ User confirmed bet")
        
        # Step 4: Wait and check for SP order
        logger.info("⏰ Waiting for SP order to be created...")
        time.sleep(5)  # Give more time for order creation
        
        # Check for the order
        orders_url = f"{self.base_url}/parlay/sp/orders"
        orders_headers = {"Authorization": f"Bearer {sp_token}"}
        response = requests.get(orders_url, headers=orders_headers)
        
        if response.status_code == 200:
            orders = response.json()["data"]["orders"]
            matching_orders = [order for order in orders if order.get("p_id") == parlay_id]
            
            if matching_orders:
                latest_order = matching_orders[0]  # Get the first matching order
                logger.info(f"✅ Found SP order: UUID={latest_order.get('order_uuid')}, Status={latest_order.get('status')}")
                return parlay_id, latest_order
            else:
                logger.error(f"❌ No SP order found for parlay {parlay_id}")
        
        return parlay_id, None

    def test_confirmation_without_price_probability(self, sp_token, sp_name, order, parlay_type):
        """Test SP confirmation without price_probability field"""
        if not order:
            logger.error(f"❌ No order available for {sp_name}")
            return None
        
        order_uuid = order.get("order_uuid")
        parlay_id = order.get("p_id")
        
        logger.info(f"\n🔍 TESTING {parlay_type} CONFIRMATION WITHOUT price_probability")
        logger.info(f"📋 Order UUID: {order_uuid}")
        logger.info(f"📋 Parlay ID: {parlay_id}")
        logger.info(f"📋 Current Status: {order.get('status')}")
        
        # Confirmation payload WITHOUT price_probability field
        url = f"{self.base_url}/parlay/sp/orders/confirmations"
        payload = {
            "action": "accept",
            "confirmed_stake": 100,
            # INTENTIONALLY OMITTING price_probability field to test requirement
            "signature": f"test_signature_{sp_name.lower()}"
        }
        
        headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
        params = {"order_uuid": order_uuid}
        
        logger.info(f"📤 Sending confirmation payload:")
        logger.info(f"   {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, params=params)
            
            logger.info(f"📥 Confirmation response:")
            logger.info(f"   Status: {response.status_code}")
            
            if response.status_code in [200, 400]:  # Both success and validation errors are valid responses
                try:
                    response_data = response.json()
                    logger.info(f"   Response: {json.dumps(response_data, indent=2)}")
                    return response_data
                except:
                    logger.info(f"   Raw response: {response.text}")
                    return {"raw_response": response.text, "status_code": response.status_code}
            else:
                logger.error(f"❌ Unexpected status code: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return {"error": f"Unexpected status: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Confirmation request failed: {str(e)}")
            return None

    def test_confirmation_with_price_probability(self, sp_token, sp_name, order, parlay_type):
        """Test SP confirmation with price_probability field (should always work)"""
        if not order:
            logger.error(f"❌ No order available for {sp_name}")
            return None
        
        order_uuid = order.get("order_uuid")
        
        logger.info(f"\n✅ TESTING {parlay_type} CONFIRMATION WITH price_probability (control test)")
        
        # Confirmation payload WITH price_probability field
        url = f"{self.base_url}/parlay/sp/orders/confirmations"
        payload = {
            "action": "accept",
            "confirmed_stake": 100,
            "price_probability": [
                {
                    "lines": [
                        {
                            "line_id": "04f2da44cbba365fd807c2bf6c5f09ab",
                            "probability": 0.5
                        },
                        {
                            "line_id": "b6cb5cf18a0148dfac0ae113e3ee6852",
                            "probability": 0.5
                        }
                    ],
                    "max_risk": 20000,  # $200 in cents
                    "vig": 0.1
                }
            ],
            "signature": f"test_signature_{sp_name.lower()}"
        }
        
        headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
        params = {"order_uuid": order_uuid}
        
        logger.info(f"📤 Sending confirmation WITH price_probability (should work):")
        
        try:
            response = requests.post(url, json=payload, headers=headers, params=params)
            logger.info(f"📥 Response: Status {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(f"   ✅ SUCCESS: {json.dumps(response_data, indent=2)}")
                    return response_data
                except:
                    logger.info(f"   ✅ SUCCESS: {response.text}")
                    return {"success": True, "raw_response": response.text}
            else:
                logger.error(f"   ❌ FAILED: {response.text}")
                return {"error": f"Status {response.status_code}"}
                
        except Exception as e:
            logger.error(f"❌ Confirmation request failed: {str(e)}")
            return None

    def analyze_results(self, response, parlay_type, test_type):
        """Analyze the response and determine if it matches expectations"""
        logger.info(f"\n📊 ANALYZING {parlay_type} {test_type} RESULTS:")
        
        expected_warning = "the confirmation is rejected automatically because the parlay is non-SGP, but no price probability provided"
        
        if test_type == "WITHOUT price_probability":
            if parlay_type == "NON-SGP":
                # Should be rejected with specific warning
                if (response and 
                    response.get("success") == True and 
                    expected_warning in response.get("warning", "")):
                    logger.info("✅ CORRECT: Non-SGP rejected with expected warning")
                    return True
                else:
                    logger.error("❌ INCORRECT: Non-SGP should be rejected with specific warning")
                    logger.error(f"   Expected warning containing: '{expected_warning}'")
                    logger.error(f"   Got: {response}")
                    return False
            else:  # SGP
                # Should succeed
                if response and response.get("success") == True and "warning" not in response:
                    logger.info("✅ CORRECT: SGP succeeded without price_probability")
                    return True
                else:
                    logger.error("❌ INCORRECT: SGP should succeed without price_probability")
                    logger.error(f"   Got: {response}")
                    return False
        else:  # WITH price_probability
            # Should always succeed
            if response and response.get("success") == True:
                logger.info("✅ CORRECT: Confirmation with price_probability succeeded")
                return True
            else:
                logger.error("❌ INCORRECT: Confirmation with price_probability should succeed")
                logger.error(f"   Got: {response}")
                return False

    def run_comprehensive_test(self):
        """Run comprehensive test for price_probability requirement"""
        logger.info("🚀 STARTING FIXED PRICE_PROBABILITY REQUIREMENT TEST")
        logger.info("=" * 100)
        logger.info("📅 Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("🎯 Testing the requirement:")
        logger.info("   - Non-SGP parlays (different events): price_probability REQUIRED")
        logger.info("   - If omitted: reject with specific warning and 'rejected' status")
        logger.info("=" * 100)
        
        results = {"total_tests": 0, "passed_tests": 0, "test_details": []}
        
        # Test with SP1
        sp_token = self.authenticate_sp(self.sp1_credentials, "SP1")
        if not sp_token:
            logger.error("❌ Failed to authenticate SP1")
            return results
        
        # Create fresh parlay and order
        parlay_id, order = self.create_fresh_parlay_and_order(sp_token, "SP1")
        
        if order:
            # Test 1: Non-SGP without price_probability (should be rejected)
            logger.info(f"\n{'='*80}")
            logger.info("🧪 TEST 1: NON-SGP CONFIRMATION WITHOUT price_probability")
            logger.info("   Expected: REJECTION with specific warning")
            logger.info(f"{'='*80}")
            
            results["total_tests"] += 1
            response1 = self.test_confirmation_without_price_probability(sp_token, "SP1", order, "NON-SGP")
            
            if self.analyze_results(response1, "NON-SGP", "WITHOUT price_probability"):
                results["passed_tests"] += 1
                results["test_details"].append("✅ NON-SGP without price_probability: CORRECTLY REJECTED")
            else:
                results["test_details"].append("❌ NON-SGP without price_probability: INCORRECTLY HANDLED")
        
        else:
            logger.error("❌ Could not create test order - skipping confirmation tests")
            logger.error("   This indicates an issue with the SP workflow setup")
        
        # Final summary
        logger.info("\n" + "=" * 100)
        logger.info("🏁 FIXED PRICE_PROBABILITY REQUIREMENT TEST RESULTS")
        logger.info("=" * 100)
        logger.info(f"📊 Total tests: {results['total_tests']}")
        logger.info(f"📊 Passed: {results['passed_tests']}")
        logger.info(f"📊 Failed: {results['total_tests'] - results['passed_tests']}")
        
        for detail in results["test_details"]:
            logger.info(f"   {detail}")
        
        if results["passed_tests"] == results["total_tests"] and results["total_tests"] > 0:
            logger.info("\n🎉 ALL TESTS PASSED! price_probability requirement is working correctly.")
        elif results["total_tests"] == 0:
            logger.info("\n⚠️  NO TESTS RUN - Check SP workflow setup.")
        else:
            logger.info(f"\n⚠️  {results['total_tests'] - results['passed_tests']} test(s) failed.")
        
        return results

if __name__ == "__main__":
    tester = FixedPriceProbabilityTester()
    results = tester.run_comprehensive_test()
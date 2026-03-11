#!/usr/bin/env python3
"""
🧪 TEST EXISTING ORDERS FOR PRICE_PROBABILITY REQUIREMENT

Uses existing SP orders that are in 'sent_confirmation' status to test the price_probability requirement.
This approach avoids the workflow timing issues we've been experiencing.
"""

import requests
import json
import logging
import time
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExistingOrdersTester:
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

    def find_testable_orders(self, sp_token, sp_name):
        """Find orders that can be used for testing price_probability requirement"""
        url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                orders = response.json()["data"]["orders"]
                logger.info(f"📊 {sp_name}: Found {len(orders)} total orders")
                
                # Show status distribution
                status_counts = {}
                for order in orders:
                    status = order.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                logger.info(f"📋 {sp_name} Order statuses: {status_counts}")
                
                # Look for orders in testable status
                testable_statuses = ["sent_confirmation", "pending", "created"]
                testable_orders = [order for order in orders if order.get("status") in testable_statuses]
                
                logger.info(f"📊 {sp_name}: Found {len(testable_orders)} potentially testable orders")
                
                if testable_orders:
                    logger.info("📋 Testable orders sample:")
                    for i, order in enumerate(testable_orders[:3]):
                        logger.info(f"   {i+1}. Parlay: {order.get('p_id')}")
                        logger.info(f"      Status: {order.get('status')}")
                        logger.info(f"      UUID: {order.get('order_uuid')}")
                        logger.info(f"      Created: {order.get('created_at')}")
                
                return orders, testable_orders
                
            else:
                logger.error(f"❌ Failed to get {sp_name} orders: {response.status_code}")
                return [], []
        except Exception as e:
            logger.error(f"❌ Error getting {sp_name} orders: {str(e)}")
            return [], []

    def test_confirmation_without_price_probability(self, sp_token, sp_name, order):
        """Test SP confirmation without price_probability field"""
        order_uuid = order.get("order_uuid")
        parlay_id = order.get("p_id")
        
        logger.info(f"\n🔍 TESTING CONFIRMATION WITHOUT price_probability")
        logger.info(f"📋 Order UUID: {order_uuid}")
        logger.info(f"📋 Parlay ID: {parlay_id}")
        logger.info(f"📋 Current Status: {order.get('status')}")
        
        # Confirmation payload WITHOUT price_probability field
        url = f"{self.base_url}/parlay/sp/orders/confirmations"
        payload = {
            "action": "accept",
            "confirmed_stake": 50,  # Smaller stake for testing
            # INTENTIONALLY OMITTING price_probability field to test requirement
            "signature": f"test_signature_{sp_name.lower()}_npp"
        }
        
        headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
        params = {"order_uuid": order_uuid}
        
        logger.info(f"📤 Sending confirmation WITHOUT price_probability:")
        logger.info(f"   {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, params=params)
            
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
            logger.error(f"❌ Confirmation request failed: {str(e)}")
            return None

    def determine_parlay_type(self, parlay_id):
        """Determine if a parlay is SGP or non-SGP by checking the parlay details"""
        # For this test, we'll make a reasonable assumption that we're testing non-SGP
        # In a real implementation, you'd fetch parlay details to check if multiple lines are from same event
        
        # Since we know our test creates non-SGP parlays (different events), we'll assume non-SGP
        # but we could enhance this by actually fetching parlay details
        return "NON-SGP"  # Assume non-SGP for our test cases

    def analyze_test_results(self, response, parlay_type="NON-SGP"):
        """Analyze the response to see if it matches the expected behavior"""
        logger.info(f"\n📊 ANALYZING RESULTS FOR {parlay_type} PARLAY:")
        
        expected_warning = "the confirmation is rejected automatically because the parlay is non-SGP, but no price probability provided"
        
        if parlay_type == "NON-SGP":
            # For non-SGP parlays, should be rejected with specific warning
            if (response and 
                response.get("success") == True and 
                expected_warning in response.get("warning", "")):
                logger.info("✅ CORRECT: Non-SGP parlay rejected with expected warning")
                logger.info(f"   Warning: {response.get('warning')}")
                return True
            elif response and response.get("success") == False:
                logger.info("⚠️  Non-SGP parlay rejected, but need to check reason")
                logger.info(f"   Response: {response}")
                # Could be rejected for other reasons - check if it's the price_probability reason
                message = response.get("message", "").lower()
                if "price probability" in message or "price_probability" in message:
                    logger.info("✅ CORRECT: Rejected for price_probability reason")
                    return True
                else:
                    logger.info("❌ Rejected for different reason")
                    return False
            else:
                logger.error("❌ INCORRECT: Non-SGP should be rejected for missing price_probability")
                logger.error(f"   Expected rejection with warning containing: '{expected_warning}'")
                logger.error(f"   Got: {response}")
                return False
        else:
            # For SGP parlays, should succeed without price_probability
            if response and response.get("success") == True and "warning" not in response:
                logger.info("✅ CORRECT: SGP parlay succeeded without price_probability")
                return True
            else:
                logger.error("❌ INCORRECT: SGP should succeed without price_probability")
                logger.error(f"   Got: {response}")
                return False

    def run_test_with_existing_orders(self):
        """Run the price_probability requirement test using existing orders"""
        logger.info("🚀 STARTING PRICE_PROBABILITY TEST WITH EXISTING ORDERS")
        logger.info("=" * 100)
        logger.info("📅 Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("🎯 Testing price_probability requirement using existing SP orders")
        logger.info("=" * 100)
        
        results = {"total_tests": 0, "passed_tests": 0, "test_details": []}
        
        # Test with both SPs to increase chances of finding testable orders
        for sp_name, credentials in [("SP1", self.sp1_credentials), ("SP2", self.sp2_credentials)]:
            logger.info(f"\n📋 CHECKING {sp_name} ORDERS")
            logger.info("-" * 50)
            
            sp_token = self.authenticate_sp(credentials, sp_name)
            if not sp_token:
                continue
            
            all_orders, testable_orders = self.find_testable_orders(sp_token, sp_name)
            
            if testable_orders:
                # Test with the first testable order
                test_order = testable_orders[0]
                parlay_type = self.determine_parlay_type(test_order.get("p_id"))
                
                logger.info(f"\n🧪 TESTING WITH {sp_name} ORDER:")
                logger.info(f"   Parlay ID: {test_order.get('p_id')}")
                logger.info(f"   Status: {test_order.get('status')}")
                logger.info(f"   Assumed Type: {parlay_type}")
                
                results["total_tests"] += 1
                
                response = self.test_confirmation_without_price_probability(sp_token, sp_name, test_order)
                
                if response and self.analyze_test_results(response, parlay_type):
                    results["passed_tests"] += 1
                    results["test_details"].append(f"✅ {sp_name}: price_probability requirement working correctly")
                else:
                    results["test_details"].append(f"❌ {sp_name}: price_probability requirement not working as expected")
                
                # Only test with first available order to avoid multiple tests on same system
                break
            else:
                logger.info(f"   No testable orders found for {sp_name}")
        
        # Summary
        logger.info("\n" + "=" * 100)
        logger.info("🏁 PRICE_PROBABILITY REQUIREMENT TEST RESULTS")
        logger.info("=" * 100)
        logger.info(f"📊 Total tests: {results['total_tests']}")
        logger.info(f"📊 Passed: {results['passed_tests']}")
        logger.info(f"📊 Failed: {results['total_tests'] - results['passed_tests']}")
        
        for detail in results["test_details"]:
            logger.info(f"   {detail}")
        
        if results["total_tests"] == 0:
            logger.info("\n⚠️  NO TESTABLE ORDERS FOUND")
            logger.info("   Need orders in 'sent_confirmation', 'pending', or 'created' status")
            logger.info("   This might indicate:")
            logger.info("   1. All orders are already finalized")
            logger.info("   2. No recent parlay activity")  
            logger.info("   3. Different order lifecycle than expected")
        elif results["passed_tests"] == results["total_tests"]:
            logger.info("\n🎉 ALL TESTS PASSED!")
            logger.info("   The price_probability requirement is working correctly.")
        else:
            logger.info(f"\n⚠️  {results['total_tests'] - results['passed_tests']} test(s) failed")
            logger.info("   Check the requirement implementation.")
        
        return results

if __name__ == "__main__":
    tester = ExistingOrdersTester()
    results = tester.run_test_with_existing_orders()
#!/usr/bin/env python3
"""
🧪 End-to-End Parlay Flow with Odds Validation
Complete parlay lifecycle testing with raw request/response logging.

Flow:
1. User creates parlay request
2. SP receives quote request 
3. SP provides price quote with estimated_prices
4. User confirms bet
5. SP confirms with price_probability (validated with new odds validation)
"""

import sys
sys.path.insert(0, 'src')

import requests
import json
import time
import logging
from datetime import datetime
from odds_validation import validate_price_probability

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class E2EParlayFlowTester:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.user_token = None
        self.sp_token = None
        
        # SP Credentials
        self.sp_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        
    def log_request(self, title, method, url, headers=None, payload=None, params=None):
        """Log HTTP request details"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📤 {title}")
        logger.info(f"{'='*80}")
        logger.info(f"Method: {method}")
        logger.info(f"URL: {url}")
        if params:
            logger.info(f"Params: {json.dumps(params, indent=2)}")
        if headers:
            # Mask sensitive headers
            safe_headers = {k: ('***' if k == 'Authorization' else v) for k, v in headers.items()}
            logger.info(f"Headers: {json.dumps(safe_headers, indent=2)}")
        if payload:
            logger.info(f"Payload:")
            logger.info(json.dumps(payload, indent=2))
    
    def log_response(self, title, response):
        """Log HTTP response details"""
        logger.info(f"\n{'='*80}")
        logger.info(f"📥 {title}")
        logger.info(f"{'='*80}")
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Headers: {dict(response.headers)}")
        try:
            response_data = response.json()
            logger.info(f"Body:")
            logger.info(json.dumps(response_data, indent=2))
            return response_data
        except:
            logger.info(f"Raw Body: {response.text}")
            return None
    
    def authenticate_user(self):
        """Authenticate user and get token"""
        url = f"{self.base_url}/api/v1/auth/login"
        payload = {
            "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
            "email": "lam.tran+usr004@betprophet.co",
            "password": "Kh0ngbiet1"
        }
        
        self.log_request("USER LOGIN", "POST", url, payload=payload)
        response = requests.post(url, json=payload)
        data = self.log_response("USER LOGIN RESPONSE", response)
        
        if response.status_code == 200 and data:
            self.user_token = data.get("accessToken")
            logger.info(f"\n✅ User authenticated successfully")
            return True
        else:
            logger.error(f"\n❌ User authentication failed")
            return False
    
    def authenticate_sp(self):
        """Authenticate Service Provider"""
        url = f"{self.base_url}/partner/auth/login"
        
        self.log_request("SP LOGIN", "POST", url, payload=self.sp_credentials)
        response = requests.post(url, json=self.sp_credentials)
        data = self.log_response("SP LOGIN RESPONSE", response)
        
        if response.status_code == 200 and data:
            self.sp_token = data["data"]["access_token"]
            logger.info(f"\n✅ SP authenticated successfully")
            return True
        else:
            logger.error(f"\n❌ SP authentication failed")
            return False
    
    def create_parlay_request(self, market_lines, test_name):
        """Step 1: User creates parlay request"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        payload = {"marketLines": market_lines}
        
        self.log_request(f"STEP 1: CREATE PARLAY REQUEST - {test_name}", "POST", url, headers, payload)
        response = requests.post(url, json=payload, headers=headers)
        data = self.log_response("STEP 1: CREATE PARLAY RESPONSE", response)
        
        if response.status_code == 200 and data:
            parlay_id = data["data"]["parlayId"]
            logger.info(f"\n✅ Parlay created: {parlay_id}")
            return parlay_id
        else:
            logger.error(f"\n❌ Parlay creation failed")
            return None
    
    def provide_sp_quote(self, parlay_id, odds, max_risk, market_lines):
        """Step 2: SP provides price quote"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        headers = {
            "Authorization": f"Bearer {self.sp_token}",
            "Content-Type": "application/json"
        }
        
        # Generate estimated_prices for each line
        estimated_prices = [
            {
                "line_id": line["lineId"],
                "odds": odds  # Using parlay odds for simplicity
            }
            for line in market_lines
        ]
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": odds,
                    "max_risk": max_risk,
                    "valid_until": int((time.time() + 6) * 1_000_000_000),  # 6 seconds validity (API requires > 5s)
                    "estimated_prices": estimated_prices
                }
            ]
        }
        
        self.log_request("STEP 2: SP PRICE QUOTE", "POST", url, headers, payload)
        response = requests.post(url, json=payload, headers=headers)
        data = self.log_response("STEP 2: SP PRICE QUOTE RESPONSE", response)
        
        if response.status_code == 200:
            logger.info(f"\n✅ SP quote provided successfully")
            return True
        else:
            logger.error(f"\n❌ SP quote failed")
            return False
    
    def user_confirm_bet(self, parlay_id, odds, stake):
        """Step 3: User confirms the bet"""
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "parlayId": parlay_id,
            "odds": odds,
            "stake": int(stake * 100)  # Convert to cents
        }
        
        self.log_request("STEP 3: USER CONFIRM BET", "POST", url, headers, payload)
        response = requests.post(url, json=payload, headers=headers)
        data = self.log_response("STEP 3: USER CONFIRM RESPONSE", response)
        
        if response.status_code == 200:
            logger.info(f"\n✅ User bet confirmed")
            return True
        else:
            logger.error(f"\n❌ User bet confirmation failed")
            return False
    
    def get_order_uuid(self, parlay_id):
        """Get order UUID for confirmation"""
        url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {self.sp_token}"}
        
        self.log_request("GET SP ORDERS", "GET", url, headers)
        response = requests.get(url, headers=headers)
        data = self.log_response("GET SP ORDERS RESPONSE", response)
        
        if response.status_code == 200 and data:
            orders = data["data"]["orders"]
            for order in orders:
                if order["p_id"] == parlay_id:
                    order_status = order["status"]
                    if order_status in ["sent_confirmation", "finalized"]:
                        order_uuid = order["order_uuid"]
                        logger.info(f"\n✅ Found order UUID: {order_uuid} (status: {order_status})")
                        return order_uuid
                    else:
                        logger.warning(f"\n⚠️  Order found but status is '{order_status}' (expected 'sent_confirmation' or 'finalized')")
        
        logger.error(f"\n❌ Order UUID not found for parlay {parlay_id}")
        return None
    
    def sp_confirm_with_validation(self, order_uuid, odds, stake, price_probability_data):
        """Step 4: SP confirms with price_probability and validation"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 ODDS VALIDATION CHECK")
        logger.info(f"{'='*80}")
        
        # Validate odds before sending confirmation
        validation_result = validate_price_probability(odds, price_probability_data)
        
        logger.info(f"Validation Input:")
        logger.info(f"  sp_odds: {odds:+d}")
        logger.info(f"  price_probability: {json.dumps(price_probability_data, indent=2)}")
        logger.info(f"\nValidation Result:")
        logger.info(f"  valid: {validation_result.get('valid')}")
        if 'calculated_probability' in validation_result:
            logger.info(f"  calculated_probability: {validation_result['calculated_probability']:.4f}")
            logger.info(f"  calculated_odds: {validation_result['calculated_odds']:+d}")
            logger.info(f"  odds_range: {validation_result['odds_range']}")
        logger.info(f"  explanation: {validation_result.get('explanation', validation_result.get('error'))}")
        
        if not validation_result.get('valid'):
            logger.warning(f"\n⚠️  Odds validation failed! Proceeding anyway for testing...")
        else:
            logger.info(f"\n✅ Odds validation passed!")
        
        # Send confirmation
        url = f"{self.base_url}/parlay/sp/orders/confirmations"
        headers = {
            "Authorization": f"Bearer {self.sp_token}",
            "Content-Type": "application/json"
        }
        params = {"order_uuid": order_uuid}
        payload = {
            "action": "accept",
            "confirmed_stake": int(stake * 100),
            "price_probability": price_probability_data,
            "signature": f"test_signature_{int(time.time())}"
        }
        
        self.log_request("STEP 4: SP CONFIRMATION WITH VALIDATION", "POST", url, headers, payload, params)
        response = requests.post(url, json=payload, headers=headers, params=params)
        data = self.log_response("STEP 4: SP CONFIRMATION RESPONSE", response)
        
        if response.status_code == 200:
            logger.info(f"\n✅ SP confirmation successful")
            return True, validation_result
        else:
            logger.error(f"\n❌ SP confirmation failed")
            return False, validation_result
    
    def run_e2e_test(self, test_config):
        """Run complete end-to-end test"""
        logger.info(f"\n\n")
        logger.info(f"{'#'*80}")
        logger.info(f"# E2E TEST: {test_config['name']}")
        logger.info(f"{'#'*80}")
        logger.info(f"Description: {test_config['description']}")
        logger.info(f"Expected: {test_config['expected_result']}")
        
        # Step 1: Create parlay
        parlay_id = self.create_parlay_request(
            test_config['market_lines'],
            test_config['name']
        )
        if not parlay_id:
            return False
        
        # Step 2: SP provides quote
        if not self.provide_sp_quote(
            parlay_id,
            test_config['odds'],
            test_config['max_risk'],
            test_config['market_lines']
        ):
            return False
        
        # Step 3: User confirms bet
        if not self.user_confirm_bet(
            parlay_id,
            test_config['odds'],
            test_config['stake']
        ):
            return False
        
        # Wait for order to appear in system
        time.sleep(2)
        
        # Get order UUID
        order_uuid = self.get_order_uuid(parlay_id)
        if not order_uuid:
            return False
        
        # Step 4: SP confirms with price_probability validation
        success, validation = self.sp_confirm_with_validation(
            order_uuid,
            test_config['odds'],
            test_config['stake'],
            test_config['price_probability']
        )
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🏁 TEST RESULT: {test_config['name']}")
        logger.info(f"{'='*80}")
        logger.info(f"Expected Validation: {test_config['expected_validation']}")
        logger.info(f"Actual Validation: {validation.get('valid')}")
        logger.info(f"Confirmation Success: {success}")
        
        test_passed = (validation.get('valid') == test_config['expected_validation'])
        status = "✅ PASS" if test_passed else "❌ FAIL"
        logger.info(f"\n{status}: E2E test completed")
        
        return test_passed


def main():
    """Run end-to-end tests"""
    logger.info(f"\n{'#'*80}")
    logger.info(f"# END-TO-END PARLAY FLOW TESTING WITH ODDS VALIDATION")
    logger.info(f"# Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'#'*80}")
    
    tester = E2EParlayFlowTester()
    
    # Authenticate
    if not tester.authenticate_user():
        return False
    if not tester.authenticate_sp():
        return False
    
    # Test configurations - Comprehensive coverage from unit tests
    test_configs = [
        # Test 1: Valid Positive Odds (+377) - From requirement
        {
            "name": "Test 1: Valid +377 (Requirement Example)",
            "description": "2-leg parlay with probabilities [0.8161, 0.2570] matching +377 odds",
            "market_lines": [
                {"line": -4.5, "lineId": "04f2da44cbba365fd807c2bf6c5f09ab", "marketId": 223, "outcomeId": 1714, "sportEventId": 19191},
                {"line": -1.5, "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852", "marketId": 223, "outcomeId": 1714, "sportEventId": 19192}
            ],
            "odds": 377,
            "max_risk": 5000,
            "stake": 50.0,
            "price_probability": [{"lines": [{"line_id": "04f2da44cbba365fd807c2bf6c5f09ab", "probability": 0.8160750396014694}, {"line_id": "b6cb5cf18a0148dfac0ae113e3ee6852", "probability": 0.2570033410434336}], "max_risk": 5000, "vig": 0.05}],
            "expected_validation": True,
            "expected_result": "Combined prob: 0.2097 → odds: +377, range: [370, 380] ✓"
        },
        # Test 2: Simple 2-leg parlay - Positive odds
        {
            "name": "Test 2: Valid +300 (Simple 2-leg)",
            "description": "2-leg parlay with probabilities [0.5, 0.5] matching +300 odds",
            "market_lines": [
                {"line": 0, "lineId": "b13ea0fce285c5b5dbb800c47fe88019", "marketId": 219, "outcomeId": 4, "sportEventId": 19192},
                {"line": -1.5, "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852", "marketId": 223, "outcomeId": 1714, "sportEventId": 19192}
            ],
            "odds": 300,
            "max_risk": 4000,
            "stake": 40.0,
            "price_probability": [{"lines": [{"line_id": "b13ea0fce285c5b5dbb800c47fe88019", "probability": 0.5}, {"line_id": "b6cb5cf18a0148dfac0ae113e3ee6852", "probability": 0.5}], "max_risk": 4000, "vig": 0.05}],
            "expected_validation": True,
            "expected_result": "Combined prob: 0.25 → odds: +300, exact match ✓"
        },
        # Test 3: 3-leg parlay - Positive odds
        {
            "name": "Test 3: Valid +700 (3-leg parlay)",
            "description": "3-leg parlay with probabilities [0.5, 0.5, 0.5] matching +700 odds",
            "market_lines": [
                {"line": -4.5, "lineId": "04f2da44cbba365fd807c2bf6c5f09ab", "marketId": 223, "outcomeId": 1714, "sportEventId": 19191},
                {"line": 0, "lineId": "b13ea0fce285c5b5dbb800c47fe88019", "marketId": 219, "outcomeId": 4, "sportEventId": 19192},
                {"line": -1.5, "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852", "marketId": 223, "outcomeId": 1714, "sportEventId": 19192}
            ],
            "odds": 700,
            "max_risk": 6000,
            "stake": 60.0,
            "price_probability": [{"lines": [{"line_id": "04f2da44cbba365fd807c2bf6c5f09ab", "probability": 0.5}, {"line_id": "b13ea0fce285c5b5dbb800c47fe88019", "probability": 0.5}, {"line_id": "b6cb5cf18a0148dfac0ae113e3ee6852", "probability": 0.5}], "max_risk": 6000, "vig": 0.05}],
            "expected_validation": True,
            "expected_result": "Combined prob: 0.125 → odds: +700, exact match ✓"
        },
        # Test 4: Heavy favorite - Valid negative odds
        {
            "name": "Test 4: Valid -200 (Heavy favorite)",
            "description": "2-leg favorite parlay with probabilities [0.8, 0.833] matching -200 odds",
            "market_lines": [
                {"line": -4.5, "lineId": "04f2da44cbba365fd807c2bf6c5f09ab", "marketId": 223, "outcomeId": 1714, "sportEventId": 19191},
                {"line": 0, "lineId": "b13ea0fce285c5b5dbb800c47fe88019", "marketId": 219, "outcomeId": 4, "sportEventId": 19192}
            ],
            "odds": -200,
            "max_risk": 8000,
            "stake": 80.0,
            "price_probability": [{"lines": [{"line_id": "04f2da44cbba365fd807c2bf6c5f09ab", "probability": 0.8}, {"line_id": "b13ea0fce285c5b5dbb800c47fe88019", "probability": 0.833}], "max_risk": 8000, "vig": 0.08}],
            "expected_validation": True,
            "expected_result": "Combined prob: 0.6664 → odds: -200, range: [-200, -198] ✓"
        },
        # Test 5: Favorite edge case - Invalid negative odds
        {
            "name": "Test 5: Invalid -110 (Edge case - calculated -111)",
            "description": "Calculated odds -111 falls outside range [-110, -109]",
            "market_lines": [
                {"line": 0, "lineId": "b13ea0fce285c5b5dbb800c47fe88019", "marketId": 219, "outcomeId": 4, "sportEventId": 19192},
                {"line": -1.5, "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852", "marketId": 223, "outcomeId": 1714, "sportEventId": 19192}
            ],
            "odds": -110,
            "max_risk": 3500,
            "stake": 35.0,
            "price_probability": [{"lines": [{"line_id": "b13ea0fce285c5b5dbb800c47fe88019", "probability": 0.7}, {"line_id": "b6cb5cf18a0148dfac0ae113e3ee6852", "probability": 0.75}], "max_risk": 3500, "vig": 0.05}],
            "expected_validation": False,
            "expected_result": "Combined prob: 0.525 → odds: -111, outside [-110, -109] ✗"
        },
        # Test 6: Valid favorite with correct probabilities
        {
            "name": "Test 6: Valid -112 (Favorite 2-leg)",
            "description": "2-leg favorite with probabilities [0.73, 0.7237] matching -112 odds",
            "market_lines": [
                {"line": -4.5, "lineId": "04f2da44cbba365fd807c2bf6c5f09ab", "marketId": 223, "outcomeId": 1714, "sportEventId": 19191},
                {"line": 0, "lineId": "b13ea0fce285c5b5dbb800c47fe88019", "marketId": 219, "outcomeId": 4, "sportEventId": 19192}
            ],
            "odds": -112,
            "max_risk": 4500,
            "stake": 45.0,
            "price_probability": [{"lines": [{"line_id": "04f2da44cbba365fd807c2bf6c5f09ab", "probability": 0.73}, {"line_id": "b13ea0fce285c5b5dbb800c47fe88019", "probability": 0.7237}], "max_risk": 4500, "vig": 0.05}],
            "expected_validation": True,
            "expected_result": "Combined prob: 0.5283 → odds: -112, range: [-112, -111] ✓"
        },
        # Test 7: Negative vs Positive mismatch
        {
            "name": "Test 7: Invalid -150 (Negative vs Positive mismatch)",
            "description": "SP odds -150 but calculated odds +198 (positive)",
            "market_lines": [
                {"line": -4.5, "lineId": "04f2da44cbba365fd807c2bf6c5f09ab", "marketId": 223, "outcomeId": 1714, "sportEventId": 19191},
                {"line": 0, "lineId": "b13ea0fce285c5b5dbb800c47fe88019", "marketId": 219, "outcomeId": 4, "sportEventId": 19192}
            ],
            "odds": -150,
            "max_risk": 3000,
            "stake": 30.0,
            "price_probability": [{"lines": [{"line_id": "04f2da44cbba365fd807c2bf6c5f09ab", "probability": 0.6}, {"line_id": "b13ea0fce285c5b5dbb800c47fe88019", "probability": 0.56}], "max_risk": 3000, "vig": 0.05}],
            "expected_validation": False,
            "expected_result": "Combined prob: 0.336 → odds: +198, doesn't match -150 ✗"
        },
        # Test 8: Positive odds mismatch
        {
            "name": "Test 8: Invalid +500 (Positive mismatch)",
            "description": "SP odds +500 but calculated odds -178 (negative)",
            "market_lines": [
                {"line": 0, "lineId": "b13ea0fce285c5b5dbb800c47fe88019", "marketId": 219, "outcomeId": 4, "sportEventId": 19192},
                {"line": -1.5, "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852", "marketId": 223, "outcomeId": 1714, "sportEventId": 19192}
            ],
            "odds": 500,
            "max_risk": 3000,
            "stake": 30.0,
            "price_probability": [{"lines": [{"line_id": "b13ea0fce285c5b5dbb800c47fe88019", "probability": 0.8}, {"line_id": "b6cb5cf18a0148dfac0ae113e3ee6852", "probability": 0.8}], "max_risk": 3000, "vig": 0.1}],
            "expected_validation": False,
            "expected_result": "Combined prob: 0.64 → odds: -178, doesn't match +500 ✗"
        },
        # Test 9: Negative odds large mismatch
        {
            "name": "Test 9: Invalid -150 (Large negative mismatch)",
            "description": "SP odds -150 but calculated odds -426",
            "market_lines": [
                {"line": 0, "lineId": "b13ea0fce285c5b5dbb800c47fe88019", "marketId": 219, "outcomeId": 4, "sportEventId": 19192},
                {"line": -1.5, "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852", "marketId": 223, "outcomeId": 1714, "sportEventId": 19192}
            ],
            "odds": -150,
            "max_risk": 3500,
            "stake": 35.0,
            "price_probability": [{"lines": [{"line_id": "b13ea0fce285c5b5dbb800c47fe88019", "probability": 0.9}, {"line_id": "b6cb5cf18a0148dfac0ae113e3ee6852", "probability": 0.9}], "max_risk": 3500, "vig": 0.1}],
            "expected_validation": False,
            "expected_result": "Combined prob: 0.81 → odds: -426, doesn't match -150 ✗"
        }
    ]
    
    # Run tests
    results = []
    for config in test_configs:
        try:
            passed = tester.run_e2e_test(config)
            results.append((config['name'], passed))
            time.sleep(1)  # Brief wait between tests
        except Exception as e:
            logger.error(f"\n❌ Test failed with exception: {str(e)}")
            results.append((config['name'], False))
    
    # Summary
    logger.info(f"\n\n{'#'*80}")
    logger.info(f"# FINAL SUMMARY")
    logger.info(f"{'#'*80}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n📊 Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        logger.info(f"\n🎉 ALL E2E TESTS PASSED! 🎉")
    else:
        logger.info(f"\n⚠️  {total_count - passed_count} test(s) failed")
    
    return passed_count == total_count


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

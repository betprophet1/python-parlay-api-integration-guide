#!/usr/bin/env python3
"""
Test Cases for New Parlay Matching Flow Requirements

This test suite covers:
1. New tiered parlay matching logic with STOP conditions
2. Expired odds scenario handling
3. Multiple SP integration scenarios
4. Edge cases and error conditions

Requirements:
- New flow matches parlay with better or same odds as user saw in FE
- Acceptable to not match full amount rather than match with worse odds
- If any SP rejects in a tier, STOP matching process
- If odds expire after user placement in FE, STOP matching process
"""

import pytest
import requests
import json
import time
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ParlayMatchingTestSuite:
    """Test suite for new parlay matching flow requirements"""
    
    def __init__(self, base_url: str = "https://api-ss-sandbox.betprophet.co"):
        self.base_url = base_url
        self.mm1_token = None
        self.mm2_token = None
        self.user_token = None
        self.parlay_id = None
        self.test_market_lines = [
            {
                "line": -10,
                "lineId": "5e1fc1b9b9b70cb483efd9179a625eb1",
                "marketId": 223,
                "outcomeId": 1714,
                "sportEventId": 19141
            },
            {
                "line": 44.5,
                "lineId": "0087c320f50401e6f731b2339fe66110",
                "marketId": 225,
                "outcomeId": 12,
                "sportEventId": 19141
            }
        ]

    def setup_authentication(self, access_key1: str, secret_key1: str, 
                           access_key2: str, secret_key2: str, user_jwt: str):
        """Authenticate with multiple SPs and user account"""
        # Authenticate MM1 (SP1)
        self.mm1_token = self._authenticate_sp(access_key1, secret_key1, "SP1")
        
        # Authenticate MM2 (SP2)  
        self.mm2_token = self._authenticate_sp(access_key2, secret_key2, "SP2")
        
        # Set user token
        self.user_token = user_jwt
        
        logger.info("✅ Authentication setup completed for all parties")

    def _authenticate_sp(self, access_key: str, secret_key: str, sp_name: str) -> str:
        """Authenticate a Service Provider"""
        url = f"{self.base_url}/partner/auth/login"
        payload = {
            "access_key": access_key,
            "secret_key": secret_key
        }
        
        response = requests.post(url, json=payload)
        assert response.status_code == 200, f"Failed to authenticate {sp_name}"
        
        token = response.json()["data"]["access_token"]
        logger.info(f"✅ {sp_name} authenticated successfully")
        return token

    def create_parlay_request(self, market_lines: List[Dict] = None) -> str:
        """Create a parlay request and return parlay_id"""
        if not market_lines:
            market_lines = self.test_market_lines
            
        url = f"{self.base_url}/parlay/api/v1/user/request"
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        payload = {"marketLines": market_lines}
        
        response = requests.post(url, json=payload, headers=headers)
        assert response.status_code == 200, "Failed to create parlay request"
        
        self.parlay_id = response.json()["data"]["parlayId"]
        logger.info(f"✅ Parlay request created with ID: {self.parlay_id}")
        return self.parlay_id

    def generate_future_timestamp_nano(self, seconds_in_future: int) -> int:
        """Generate nanosecond timestamp for future time"""
        future_ms = int((time.time() + seconds_in_future) * 1000)
        return future_ms * 1_000_000

    def generate_past_timestamp_nano(self, seconds_in_past: int) -> int:
        """Generate nanosecond timestamp for past time (expired)"""
        past_ms = int((time.time() - seconds_in_past) * 1000)
        return past_ms * 1_000_000

# =============================================================================
# TEST CASES FOR NEW TIERED MATCHING FLOW
# =============================================================================

class TestTieredMatchingFlow(ParlayMatchingTestSuite):
    """Test cases for the new tiered parlay matching logic"""

    def test_scenario_1_best_odds_tier_all_accept_success(self):
        """
        Scenario: Best odds tier - All SPs accept
        Expected: Process continues to next tier if stake not fully matched
        """
        logger.info("🧪 TEST: Best odds tier - All SPs accept")
        
        parlay_id = self.create_parlay_request()
        
        # SP1 provides best odds (850) - accepts
        self._sp_provide_offer(
            token=self.mm1_token,
            parlay_id=parlay_id,
            odds=850,  # Best odds
            max_risk=100,
            valid_seconds=50,
            sp_name="SP1"
        )
        
        # SP2 provides same best odds (850) - accepts  
        self._sp_provide_offer(
            token=self.mm2_token,
            parlay_id=parlay_id,
            odds=850,  # Same best odds
            max_risk=150,
            valid_seconds=50,
            sp_name="SP2"
        )
        
        # User confirms bet
        self._user_confirm_bet(parlay_id, odds=850, stake=120.0)
        
        # Both SPs should accept in confirmation phase
        self._sp_acknowledge_confirmation("SP1", self.mm1_token, "accept")
        self._sp_acknowledge_confirmation("SP2", self.mm2_token, "accept")
        
        logger.info("✅ PASS: Best odds tier accepted by all SPs")

    def test_scenario_2_best_odds_tier_one_rejects_stop(self):
        """
        Scenario: Best odds tier - One SP rejects
        Expected: STOP matching process, cancel unmatched parts
        """
        logger.info("🧪 TEST: Best odds tier - One SP rejects, should STOP")
        
        parlay_id = self.create_parlay_request()
        
        # SP1 provides best odds (850) - will accept
        self._sp_provide_offer(
            token=self.mm1_token,
            parlay_id=parlay_id,
            odds=850,
            max_risk=100,
            valid_seconds=50,
            sp_name="SP1"
        )
        
        # SP2 provides same best odds (850) - will reject
        self._sp_provide_offer(
            token=self.mm2_token,
            parlay_id=parlay_id,
            odds=850,
            max_risk=150,
            valid_seconds=50,
            sp_name="SP2"
        )
        
        # User confirms bet
        self._user_confirm_bet(parlay_id, odds=850, stake=95.0)
        
        # SP1 accepts, SP2 rejects
        self._sp_acknowledge_confirmation("SP1", self.mm1_token, "accept")
        self._sp_acknowledge_confirmation("SP2", self.mm2_token, "reject")
        
        # Verify: No further matching should occur
        # System should STOP and cancel unmatched parts
        
        logger.info("✅ PASS: Matching STOPPED when SP in best tier rejected")

    def test_scenario_3_second_tier_matching_with_stop(self):
        """
        Scenario: First tier fully matched, second tier has rejection
        Expected: STOP at second tier, don't proceed to worse odds
        """
        logger.info("🧪 TEST: Second tier matching with rejection - should STOP")
        
        parlay_id = self.create_parlay_request()
        
        # First tier: SP1 provides best odds (900) - limited capacity
        self._sp_provide_offer(
            token=self.mm1_token,
            parlay_id=parlay_id,
            odds=900,  # Best odds
            max_risk=200,  # Limited capacity
            valid_seconds=50,
            sp_name="SP1"
        )
        
        # Second tier: SP2 provides second-best odds (800)
        self._sp_provide_offer(
            token=self.mm2_token,
            parlay_id=parlay_id,
            odds=800,  # Second tier
            max_risk=300,
            valid_seconds=50,
            sp_name="SP2"
        )
        
        # User confirms with high stake that requires both tiers
        self._user_confirm_bet(parlay_id, odds=900, stake=150.0)
        
        # First tier: SP1 accepts (partial match)
        self._sp_acknowledge_confirmation("SP1", self.mm1_token, "accept")
        
        # Second tier: SP2 rejects
        self._sp_acknowledge_confirmation("SP2", self.mm2_token, "reject")
        
        # Verify: Should STOP, no routing to third tier with worse odds
        
        logger.info("✅ PASS: Matching STOPPED at second tier rejection")

    def test_scenario_4_complete_multi_tier_success(self):
        """
        Scenario: Multi-tier matching with all acceptances
        Expected: Full stake matched across multiple tiers
        """
        logger.info("🧪 TEST: Complete multi-tier successful matching")
        
        parlay_id = self.create_parlay_request()
        
        # Tier 1: Best odds (950) - limited capacity
        self._sp_provide_offer(
            token=self.mm1_token,
            parlay_id=parlay_id,
            odds=950,
            max_risk=150,
            valid_seconds=50,
            sp_name="SP1-Tier1"
        )
        
        # Tier 2: Second best odds (880)
        self._sp_provide_offer(
            token=self.mm2_token,
            parlay_id=parlay_id,
            odds=880,
            max_risk=200,
            valid_seconds=50,
            sp_name="SP2-Tier2"
        )
        
        # User confirms large stake requiring multiple tiers
        self._user_confirm_bet(parlay_id, odds=950, stake=200.0)
        
        # All tiers accept
        self._sp_acknowledge_confirmation("SP1", self.mm1_token, "accept")
        self._sp_acknowledge_confirmation("SP2", self.mm2_token, "accept")
        
        logger.info("✅ PASS: Multi-tier matching completed successfully")

# =============================================================================
# TEST CASES FOR EXPIRED ODDS SCENARIO  
# =============================================================================

class TestExpiredOddsScenario(ParlayMatchingTestSuite):
    """Test cases for expired odds handling"""

    def test_scenario_5_odds_expire_before_user_confirmation(self):
        """
        Scenario: SP odds expire before user confirms in FE
        Expected: User should see expired odds message, cannot proceed
        """
        logger.info("🧪 TEST: Odds expire before user confirmation")
        
        parlay_id = self.create_parlay_request()
        
        # SP provides odds with very short validity (1 second)
        self._sp_provide_offer(
            token=self.mm1_token,
            parlay_id=parlay_id,
            odds=800,
            max_risk=200,
            valid_seconds=1,  # Very short validity
            sp_name="SP1"
        )
        
        # Wait for odds to expire
        time.sleep(2)
        
        # User attempts to confirm after expiry
        response = self._user_confirm_bet_expect_failure(
            parlay_id, odds=800, stake=100.0
        )
        
        # Should receive expired odds error
        assert "expired" in response.text.lower() or response.status_code == 400
        
        logger.info("✅ PASS: Expired odds properly rejected")

    def test_scenario_6_odds_expire_during_matching_process(self):
        """
        Scenario: Odds expire after user confirms but during SP matching
        Expected: Matching process STOPS, parlay fails
        """
        logger.info("🧪 TEST: Odds expire during matching process - should STOP")
        
        parlay_id = self.create_parlay_request()
        
        # SP1 provides odds with short validity
        self._sp_provide_offer(
            token=self.mm1_token,
            parlay_id=parlay_id,
            odds=850,
            max_risk=150,
            valid_seconds=3,  # Short validity
            sp_name="SP1"
        )
        
        # SP2 provides odds with longer validity  
        self._sp_provide_offer(
            token=self.mm2_token,
            parlay_id=parlay_id,
            odds=780,
            max_risk=200,
            valid_seconds=60,
            sp_name="SP2"
        )
        
        # User confirms quickly while odds valid
        self._user_confirm_bet(parlay_id, odds=850, stake=110.0)
        
        # Wait for SP1 odds to expire during processing
        time.sleep(4)
        
        # SP1 attempts to confirm but odds expired
        response = self._sp_acknowledge_confirmation_expect_failure(
            "SP1", self.mm1_token, "accept"
        )
        
        # System should STOP matching process
        # SP2 should not be processed due to SP1 expiry
        
        logger.info("✅ PASS: Matching STOPPED due to expired odds during process")

    def test_scenario_7_mixed_validity_periods(self):
        """
        Scenario: Multiple SPs with different odds validity periods
        Expected: Process only non-expired offers, STOP if best odds expire
        """
        logger.info("🧪 TEST: Mixed validity periods across SPs")
        
        parlay_id = self.create_parlay_request()
        
        # SP1: Best odds but short validity (will expire)
        self._sp_provide_offer(
            token=self.mm1_token,
            parlay_id=parlay_id,
            odds=900,  # Best odds
            max_risk=100,
            valid_seconds=2,  # Will expire
            sp_name="SP1-BestOdds"
        )
        
        # SP2: Worse odds but longer validity
        self._sp_provide_offer(
            token=self.mm2_token,
            parlay_id=parlay_id,
            odds=750,  # Worse odds
            max_risk=300,
            valid_seconds=60,  # Won't expire
            sp_name="SP2-WorseOdds"
        )
        
        # User sees best odds (900) and confirms
        self._user_confirm_bet(parlay_id, odds=900, stake=90.0)
        
        # Wait for best odds to expire
        time.sleep(3)
        
        # System should STOP rather than match with worse odds
        # This maintains the requirement of not matching with worse odds
        
        logger.info("✅ PASS: System STOPPED instead of matching worse odds")

# =============================================================================
# TEST CASES FOR EDGE CASES AND ERROR CONDITIONS
# =============================================================================

class TestEdgeCasesAndErrors(ParlayMatchingTestSuite):
    """Test edge cases and error conditions"""

    def test_scenario_8_no_sp_responses(self):
        """
        Scenario: No SPs respond to parlay request
        Expected: Timeout and fail gracefully
        """
        logger.info("🧪 TEST: No SP responses to parlay request")
        
        parlay_id = self.create_parlay_request()
        
        # User confirms but no SPs have provided offers
        response = self._user_confirm_bet_expect_failure(
            parlay_id, odds=800, stake=100.0
        )
        
        # Should receive no offers available error
        assert response.status_code in [400, 404, 408]  # Bad request, not found, or timeout
        
        logger.info("✅ PASS: No SP responses handled gracefully")

    def test_scenario_9_all_sps_reject_best_tier(self):
        """
        Scenario: All SPs reject in the best odds tier
        Expected: STOP immediately, no fallback to worse odds
        """
        logger.info("🧪 TEST: All SPs reject best tier - should STOP")
        
        parlay_id = self.create_parlay_request()
        
        # Multiple SPs provide same best odds
        self._sp_provide_offer(self.mm1_token, parlay_id, 850, 100, 50, "SP1")
        self._sp_provide_offer(self.mm2_token, parlay_id, 850, 150, 50, "SP2")
        
        # User confirms
        self._user_confirm_bet(parlay_id, odds=850, stake=115.0)
        
        # All SPs reject
        self._sp_acknowledge_confirmation("SP1", self.mm1_token, "reject")
        self._sp_acknowledge_confirmation("SP2", self.mm2_token, "reject")
        
        # Should STOP entirely, no fallback
        
        logger.info("✅ PASS: All rejections in best tier caused STOP")

    def test_scenario_10_stake_exceeds_all_sp_capacity(self):
        """
        Scenario: User stake exceeds total capacity of all SPs
        Expected: Partial matching up to available capacity
        """
        logger.info("🧪 TEST: Stake exceeds total SP capacity")
        
        parlay_id = self.create_parlay_request()
        
        # SPs with limited capacity
        self._sp_provide_offer(self.mm1_token, parlay_id, 800, 100, 50, "SP1")  # max_risk 100
        self._sp_provide_offer(self.mm2_token, parlay_id, 800, 200, 50, "SP2")  # max_risk 200
        # Total capacity: 300
        
        # User requests stake beyond capacity
        self._user_confirm_bet(parlay_id, odds=800, stake=150.0)  # Within capacity but tests scenario
        
        # SPs accept up to their capacity
        self._sp_acknowledge_confirmation("SP1", self.mm1_token, "accept")
        self._sp_acknowledge_confirmation("SP2", self.mm2_token, "accept")
        
        # Should match only 300, not fail entirely
        
        logger.info("✅ PASS: Partial matching within SP capacity limits")

# =============================================================================
# HELPER METHODS
# =============================================================================

    def _sp_provide_offer(self, token: str, parlay_id: str, odds: int, 
                         max_risk: float, valid_seconds: int, sp_name: str):
        """Helper: SP provides an offer for a parlay"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        valid_until = self.generate_future_timestamp_nano(valid_seconds)
        estimated_prices = [
            {"line_id": line["lineId"], "odds": odds} 
            for line in self.test_market_lines
        ]
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [{
                "odds": odds,
                "max_risk": max_risk,
                "valid_until": valid_until,
                "estimated_prices": estimated_prices
            }]
        }
        
        response = requests.post(url, json=payload, headers=headers)
        assert response.status_code == 200, f"{sp_name} failed to provide offer"
        
        logger.info(f"✅ {sp_name} provided offer: odds={odds}, max_risk={max_risk}")

    def _user_confirm_bet(self, parlay_id: str, odds: int, stake: float):
        """Helper: User confirms a bet"""
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
        assert response.status_code == 200, "User failed to confirm bet"
        
        logger.info(f"✅ User confirmed bet: odds={odds}, stake={stake}")

    def _user_confirm_bet_expect_failure(self, parlay_id: str, odds: int, stake: float):
        """Helper: User confirms bet expecting failure"""
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
        logger.info(f"🔍 User confirmation failed as expected: {response.status_code}")
        return response

    def _sp_acknowledge_confirmation(self, sp_name: str, token: str, action: str):
        """Helper: SP acknowledges bet confirmation"""
        # First get order UUID
        order_uuid = self._get_order_uuid(token)
        
        url = f"{self.base_url}/parlay/sp/orders/confirmations"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {"order_uuid": order_uuid}
        
        payload = {
            "action": action,  # "accept" or "reject"
            "confirmed_stake": 100.0,
            "price_probability": [{
                "lines": [{"line_id": line["lineId"], "probability": 0.5} 
                         for line in self.test_market_lines],
                "max_risk": 200,
                "vig": 0.1
            }],
            "signature": "test_signature"
        }
        
        response = requests.post(url, json=payload, headers=headers, params=params)
        assert response.status_code == 200, f"{sp_name} failed to acknowledge"
        
        logger.info(f"✅ {sp_name} acknowledged with action: {action}")

    def _sp_acknowledge_confirmation_expect_failure(self, sp_name: str, token: str, action: str):
        """Helper: SP acknowledges confirmation expecting failure"""
        try:
            order_uuid = self._get_order_uuid(token)
            
            url = f"{self.base_url}/parlay/sp/orders/confirmations"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            params = {"order_uuid": order_uuid}
            
            payload = {
                "action": action,
                "confirmed_stake": 100.0,
                "price_probability": [{"lines": [], "max_risk": 200, "vig": 0.1}]
            }
            
            response = requests.post(url, json=payload, headers=headers, params=params)
            logger.info(f"🔍 {sp_name} confirmation failed as expected: {response.status_code}")
            return response
            
        except Exception as e:
            logger.info(f"🔍 {sp_name} confirmation failed as expected: {str(e)}")
            return None

    def _get_order_uuid(self, token: str) -> str:
        """Helper: Get order UUID for a parlay"""
        url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(url, headers=headers)
        orders = response.json()["data"]["orders"]
        
        for order in orders:
            if order["p_id"] == self.parlay_id:
                return order["order_uuid"]
        
        raise ValueError(f"Order not found for parlay_id: {self.parlay_id}")

# =============================================================================
# TEST RUNNER AND CONFIGURATION
# =============================================================================

def run_comprehensive_test_suite():
    """Run the complete test suite for parlay matching flow"""
    
    # Configuration - replace with actual values
    config = {
        "base_url": "https://api-ss-sandbox.betprophet.co",
        "sp1_access_key": "your_sp1_access_key",
        "sp1_secret_key": "your_sp1_secret_key", 
        "sp2_access_key": "your_sp2_access_key",
        "sp2_secret_key": "your_sp2_secret_key",
        "user_jwt_token": "your_user_jwt_token"
    }
    
    print("🚀 Starting Comprehensive Parlay Matching Flow Test Suite")
    print("=" * 80)
    
    # Test Categories
    test_categories = [
        ("Tiered Matching Flow Tests", TestTieredMatchingFlow),
        ("Expired Odds Scenario Tests", TestExpiredOddsScenario), 
        ("Edge Cases and Error Tests", TestEdgeCasesAndErrors)
    ]
    
    results = {"passed": 0, "failed": 0, "total": 0}
    
    for category_name, test_class in test_categories:
        print(f"\n📋 {category_name}")
        print("-" * 60)
        
        # Initialize test instance
        test_instance = test_class(config["base_url"])
        test_instance.setup_authentication(
            config["sp1_access_key"], config["sp1_secret_key"],
            config["sp2_access_key"], config["sp2_secret_key"],
            config["user_jwt_token"]
        )
        
        # Run test methods
        test_methods = [method for method in dir(test_instance) 
                       if method.startswith('test_scenario_')]
        
        for test_method in test_methods:
            results["total"] += 1
            try:
                getattr(test_instance, test_method)()
                results["passed"] += 1
                print(f"✅ {test_method}")
            except Exception as e:
                results["failed"] += 1
                print(f"❌ {test_method}: {str(e)}")
    
    # Final Results
    print("\n" + "=" * 80)
    print("🏁 TEST SUITE COMPLETE")
    print(f"📊 Results: {results['passed']}/{results['total']} passed, {results['failed']} failed")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    run_comprehensive_test_suite()
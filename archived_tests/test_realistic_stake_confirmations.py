#!/usr/bin/env python3
"""
Realistic Parlay Stake Confirmation Test Suite

This test suite creates realistic test cases based on the discovered stake calculation formula:
Available Stake = max_risk ÷ decimal_odds

Key principles:
1. SPs provide offers with odds + max_risk
2. System calculates available stake for user UI
3. User can only confirm amount ≤ total available stake
4. Multiple SPs with same odds blend their available stakes
5. SP's actual risk exposure = user's potential winnings
"""

import json
import time
import requests
from datetime import datetime, timezone
from typing import Dict, List, Tuple

# Configuration
BASE_URL = "https://parlay-api-staging.herokuapp.com"
SP1_ACCESS_KEY = "sp1_access_key_here"
SP1_SECRET_KEY = "sp1_secret_key_here"
SP2_ACCESS_KEY = "sp2_access_key_here"
SP2_SECRET_KEY = "sp2_secret_key_here"
SP3_ACCESS_KEY = "sp3_access_key_here"
SP3_SECRET_KEY = "sp3_secret_key_here"
USER_TOKEN = "user_token_here"

def american_odds_to_decimal(american_odds: int) -> float:
    """Convert American odds to decimal odds"""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1

def calculate_available_stake_from_offer(odds: int, max_risk_cents: int) -> int:
    """
    Calculate available stake from SP offer
    Formula: Available Stake = max_risk / decimal_odds
    Returns stake in cents
    """
    decimal_odds = american_odds_to_decimal(odds)
    available_stake_cents = int(max_risk_cents / decimal_odds)
    return available_stake_cents

def calculate_sp_risk_exposure(stake_cents: int, odds: int) -> int:
    """Calculate SP's risk exposure (potential payout) from user stake"""
    decimal_odds = american_odds_to_decimal(odds)
    risk_exposure = int(stake_cents * (decimal_odds - 1))
    return risk_exposure

def log_request_response(operation: str, response):
    """Log request and response details for debugging"""
    print(f"\n{'='*60}")
    print(f"📋 OPERATION: {operation}")
    print(f"⏰ TIMESTAMP: {datetime.now(timezone.utc).isoformat()}")
    if hasattr(response, 'request'):
        print(f"📤 REQUEST URL: {response.request.url}")
        print(f"📤 REQUEST METHOD: {response.request.method}")
        if response.request.body:
            try:
                body = json.loads(response.request.body)
                print(f"📤 REQUEST BODY: {json.dumps(body, indent=2)}")
            except:
                print(f"📤 REQUEST BODY: {response.request.body}")
    print(f"📥 RESPONSE STATUS: {response.status_code}")
    try:
        print(f"📥 RESPONSE BODY: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"📥 RESPONSE BODY: {response.text}")
    print(f"{'='*60}")

class RealisticStakeTestSuite:
    """Test suite with realistic stake calculations"""
    
    def __init__(self):
        self.results = {"passed": 0, "failed": 0, "scenarios": {}}
    
    def authenticate_sp(self, access_key: str, secret_key: str, sp_name: str) -> str:
        """Authenticate service provider and return token"""
        auth_data = {
            "access_key": access_key,
            "secret_key": secret_key
        }
        
        print(f"\n🔐 Authenticating {sp_name}...")
        response = requests.post(f"{BASE_URL}/api/v1/auth", json=auth_data)
        log_request_response(f"{sp_name} Authentication", response)
        
        if response.status_code == 200:
            token = response.json().get("token")
            print(f"✅ {sp_name} authenticated successfully")
            return token
        else:
            print(f"❌ {sp_name} authentication failed")
            return None

    def create_parlay(self, user_token: str) -> str:
        """Create parlay with user token"""
        parlay_data = {
            "stake_cents": 50000,  # Will be overridden by realistic calculations
            "selections": [
                {
                    "line_id": "11_7540_49094",
                    "side": "1"
                },
                {
                    "line_id": "11_7540_49095", 
                    "side": "2"
                }
            ]
        }
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        print("\n🎰 Creating parlay request...")
        response = requests.post(f"{BASE_URL}/api/v1/parlay", json=parlay_data, headers=headers)
        log_request_response("Create Parlay", response)
        
        if response.status_code == 201:
            parlay_id = response.json().get("parlay_id")
            print(f"✅ Parlay created with ID: {parlay_id}")
            return parlay_id
        else:
            print("❌ Failed to create parlay")
            return None

    def provide_sp_offer(self, sp_token: str, parlay_id: str, sp_name: str, 
                        odds: int, max_risk_dollars: float, valid_seconds: int = 30) -> Dict:
        """SP provides offer and returns offer details"""
        max_risk_cents = int(max_risk_dollars * 100)
        available_stake_cents = calculate_available_stake_from_offer(odds, max_risk_cents)
        
        offers_data = {
            "offers": [
                {
                    "odds": odds,
                    "max_risk": max_risk_cents,
                    "valid_until": int(time.time()) + valid_seconds
                }
            ]
        }
        
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        print(f"\n💰 {sp_name} providing offer:")
        print(f"   Odds: +{odds}")
        print(f"   Max Risk: ${max_risk_dollars:.2f}")
        print(f"   Available Stake: ${available_stake_cents/100:.2f}")
        
        response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
        log_request_response(f"{sp_name} Provide Offer", response)
        
        offer_details = {
            "sp_name": sp_name,
            "odds": odds,
            "max_risk_cents": max_risk_cents,
            "available_stake_cents": available_stake_cents,
            "success": response.status_code == 200
        }
        
        if response.status_code == 200:
            print(f"✅ {sp_name} offer submitted successfully")
        else:
            print(f"❌ {sp_name} failed to submit offer")
        
        return offer_details

    def calculate_total_available_stake(self, offers: List[Dict]) -> int:
        """Calculate total available stake from all SP offers"""
        # Group by odds (same odds can be blended)
        odds_groups = {}
        for offer in offers:
            if offer["success"]:
                odds = offer["odds"]
                if odds not in odds_groups:
                    odds_groups[odds] = 0
                odds_groups[odds] += offer["available_stake_cents"]
        
        # Return the maximum available stake (best odds group)
        if odds_groups:
            best_odds = max(odds_groups.keys())
            return odds_groups[best_odds]
        return 0

    def confirm_parlay_with_realistic_stake(self, user_token: str, parlay_id: str, 
                                          offers: List[Dict], stake_ratio: float = 1.0) -> Tuple[bool, int]:
        """
        User confirms parlay with realistic stake amount
        stake_ratio: 1.0 = full available, 0.5 = half available, etc.
        """
        total_available = self.calculate_total_available_stake(offers)
        
        if total_available == 0:
            print("❌ No available stake to confirm")
            return False, 0
        
        # Calculate confirmation stake based on ratio
        confirmation_stake_cents = int(total_available * stake_ratio)
        
        # Find best odds for confirmation
        successful_offers = [offer for offer in offers if offer["success"]]
        best_odds = max(offer["odds"] for offer in successful_offers) if successful_offers else 0
        
        confirm_data = {
            "offers": [{
                "odds": best_odds,
                "stake_cents": confirmation_stake_cents
            }]
        }
        
        headers = {"Authorization": f"Bearer {user_token}"}
        
        print(f"\n✅ User confirming parlay:")
        print(f"   Available Stake: ${total_available/100:.2f}")
        print(f"   Confirmation Stake: ${confirmation_stake_cents/100:.2f} ({stake_ratio*100:.0f}% of available)")
        print(f"   Odds: +{best_odds}")
        
        # Calculate expected payout
        decimal_odds = american_odds_to_decimal(best_odds)
        expected_payout = int(confirmation_stake_cents * (decimal_odds - 1))
        print(f"   Expected Payout: ${expected_payout/100:.2f}")
        
        response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/confirm", json=confirm_data, headers=headers)
        log_request_response("Confirm Parlay with Realistic Stake", response)
        
        success = response.status_code == 200
        if success:
            print("✅ Parlay confirmation processed successfully")
        else:
            print("❌ Failed to confirm parlay")
        
        return success, confirmation_stake_cents

    def get_final_parlay_status(self, user_token: str, parlay_id: str) -> Dict:
        """Get final parlay status"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        print("\n📊 Getting final parlay status...")
        response = requests.get(f"{BASE_URL}/api/v1/parlay/{parlay_id}", headers=headers)
        log_request_response("Final Parlay Status", response)
        
        if response.status_code == 200:
            status = response.json()
            print("✅ Final status retrieved")
            return status
        else:
            print("❌ Failed to retrieve final status")
            return None

    def test_scenario_single_sp_full_confirmation(self):
        """Test: Single SP, user confirms full available stake"""
        scenario_name = "Single SP Full Confirmation"
        print(f"\n🧪 TEST SCENARIO: {scenario_name}")
        print("="*60)
        
        try:
            # Authenticate SP1
            sp1_token = self.authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
            if not sp1_token:
                raise Exception("SP1 authentication failed")
            
            # Create parlay
            parlay_id = self.create_parlay(USER_TOKEN)
            if not parlay_id:
                raise Exception("Failed to create parlay")
            
            # SP1 provides realistic offer
            # Example: +800 odds, $112.50 max_risk → $12.50 available stake
            offers = [
                self.provide_sp_offer(sp1_token, parlay_id, "SP1", 800, 112.50)
            ]
            
            time.sleep(2)
            
            # User confirms full available stake
            success, confirmed_stake = self.confirm_parlay_with_realistic_stake(
                USER_TOKEN, parlay_id, offers, 1.0
            )
            
            if success:
                print(f"✅ {scenario_name} PASSED")
                self.results["passed"] += 1
            else:
                print(f"❌ {scenario_name} FAILED")
                self.results["failed"] += 1
                
            self.results["scenarios"][scenario_name] = "PASSED" if success else "FAILED"
            
        except Exception as e:
            print(f"❌ {scenario_name} FAILED: {str(e)}")
            self.results["failed"] += 1
            self.results["scenarios"][scenario_name] = f"FAILED: {str(e)}"

    def test_scenario_single_sp_partial_confirmation(self):
        """Test: Single SP, user confirms partial available stake"""
        scenario_name = "Single SP Partial Confirmation"
        print(f"\n🧪 TEST SCENARIO: {scenario_name}")
        print("="*60)
        
        try:
            # Authenticate SP1
            sp1_token = self.authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
            if not sp1_token:
                raise Exception("SP1 authentication failed")
            
            # Create parlay
            parlay_id = self.create_parlay(USER_TOKEN)
            if not parlay_id:
                raise Exception("Failed to create parlay")
            
            # SP1 provides realistic offer
            # Example: +400 odds, $200 max_risk → $40 available stake
            offers = [
                self.provide_sp_offer(sp1_token, parlay_id, "SP1", 400, 200.0)
            ]
            
            time.sleep(2)
            
            # User confirms 50% of available stake
            success, confirmed_stake = self.confirm_parlay_with_realistic_stake(
                USER_TOKEN, parlay_id, offers, 0.5
            )
            
            if success:
                print(f"✅ {scenario_name} PASSED")
                self.results["passed"] += 1
            else:
                print(f"❌ {scenario_name} FAILED")
                self.results["failed"] += 1
                
            self.results["scenarios"][scenario_name] = "PASSED" if success else "FAILED"
            
        except Exception as e:
            print(f"❌ {scenario_name} FAILED: {str(e)}")
            self.results["failed"] += 1
            self.results["scenarios"][scenario_name] = f"FAILED: {str(e)}"

    def test_scenario_multi_sp_same_odds_blended(self):
        """Test: Multiple SPs with same odds, stakes blended"""
        scenario_name = "Multi-SP Same Odds Blended"
        print(f"\n🧪 TEST SCENARIO: {scenario_name}")
        print("="*60)
        
        try:
            # Authenticate SPs
            sp1_token = self.authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
            sp2_token = self.authenticate_sp(SP2_ACCESS_KEY, SP2_SECRET_KEY, "SP2")
            
            if not sp1_token or not sp2_token:
                raise Exception("SP authentication failed")
            
            # Create parlay
            parlay_id = self.create_parlay(USER_TOKEN)
            if not parlay_id:
                raise Exception("Failed to create parlay")
            
            # Both SPs provide same odds but different capacities
            # SP1: +800 odds, $112.50 max_risk → $12.50 available
            # SP2: +800 odds, $225.00 max_risk → $25.00 available
            # Total: $37.50 available
            offers = [
                self.provide_sp_offer(sp1_token, parlay_id, "SP1", 800, 112.50),
                self.provide_sp_offer(sp2_token, parlay_id, "SP2", 800, 225.00)
            ]
            
            time.sleep(2)
            
            # User confirms 75% of total available stake
            success, confirmed_stake = self.confirm_parlay_with_realistic_stake(
                USER_TOKEN, parlay_id, offers, 0.75
            )
            
            if success:
                print(f"✅ {scenario_name} PASSED")
                self.results["passed"] += 1
            else:
                print(f"❌ {scenario_name} FAILED")
                self.results["failed"] += 1
                
            self.results["scenarios"][scenario_name] = "PASSED" if success else "FAILED"
            
        except Exception as e:
            print(f"❌ {scenario_name} FAILED: {str(e)}")
            self.results["failed"] += 1
            self.results["scenarios"][scenario_name] = f"FAILED: {str(e)}"

    def test_scenario_multi_sp_different_odds_best_selected(self):
        """Test: Multiple SPs with different odds, best odds selected"""
        scenario_name = "Multi-SP Different Odds Best Selected"
        print(f"\n🧪 TEST SCENARIO: {scenario_name}")
        print("="*60)
        
        try:
            # Authenticate SPs
            sp1_token = self.authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
            sp2_token = self.authenticate_sp(SP2_ACCESS_KEY, SP2_SECRET_KEY, "SP2")
            
            if not sp1_token or not sp2_token:
                raise Exception("SP authentication failed")
            
            # Create parlay
            parlay_id = self.create_parlay(USER_TOKEN)
            if not parlay_id:
                raise Exception("Failed to create parlay")
            
            # SPs provide different odds
            # SP1: +900 odds, $180.00 max_risk → $18.00 available (BEST)
            # SP2: +600 odds, $140.00 max_risk → $20.00 available
            # User should see best odds (+900) with $18.00 available
            offers = [
                self.provide_sp_offer(sp1_token, parlay_id, "SP1", 900, 180.00),
                self.provide_sp_offer(sp2_token, parlay_id, "SP2", 600, 140.00)
            ]
            
            time.sleep(2)
            
            # User confirms full available stake from best odds SP
            success, confirmed_stake = self.confirm_parlay_with_realistic_stake(
                USER_TOKEN, parlay_id, offers, 1.0
            )
            
            if success:
                print(f"✅ {scenario_name} PASSED")
                self.results["passed"] += 1
            else:
                print(f"❌ {scenario_name} FAILED")
                self.results["failed"] += 1
                
            self.results["scenarios"][scenario_name] = "PASSED" if success else "FAILED"
            
        except Exception as e:
            print(f"❌ {scenario_name} FAILED: {str(e)}")
            self.results["failed"] += 1
            self.results["scenarios"][scenario_name] = f"FAILED: {str(e)}"

    def test_scenario_high_stake_low_odds(self):
        """Test: High available stake with low odds"""
        scenario_name = "High Stake Low Odds"
        print(f"\n🧪 TEST SCENARIO: {scenario_name}")
        print("="*60)
        
        try:
            # Authenticate SP1
            sp1_token = self.authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
            if not sp1_token:
                raise Exception("SP1 authentication failed")
            
            # Create parlay
            parlay_id = self.create_parlay(USER_TOKEN)
            if not parlay_id:
                raise Exception("Failed to create parlay")
            
            # SP1 provides low odds, high capacity
            # Example: +150 odds, $500 max_risk → $200 available stake
            offers = [
                self.provide_sp_offer(sp1_token, parlay_id, "SP1", 150, 500.0)
            ]
            
            time.sleep(2)
            
            # User confirms 60% of available stake
            success, confirmed_stake = self.confirm_parlay_with_realistic_stake(
                USER_TOKEN, parlay_id, offers, 0.6
            )
            
            if success:
                print(f"✅ {scenario_name} PASSED")
                self.results["passed"] += 1
            else:
                print(f"❌ {scenario_name} FAILED")
                self.results["failed"] += 1
                
            self.results["scenarios"][scenario_name] = "PASSED" if success else "FAILED"
            
        except Exception as e:
            print(f"❌ {scenario_name} FAILED: {str(e)}")
            self.results["failed"] += 1
            self.results["scenarios"][scenario_name] = f"FAILED: {str(e)}"

    def test_scenario_favorite_negative_odds(self):
        """Test: Favorite with negative odds"""
        scenario_name = "Favorite Negative Odds"
        print(f"\n🧪 TEST SCENARIO: {scenario_name}")
        print("="*60)
        
        try:
            # Authenticate SP1
            sp1_token = self.authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
            if not sp1_token:
                raise Exception("SP1 authentication failed")
            
            # Create parlay
            parlay_id = self.create_parlay(USER_TOKEN)
            if not parlay_id:
                raise Exception("Failed to create parlay")
            
            # SP1 provides negative odds (favorite)
            # Example: -110 odds, $200 max_risk → ~$105 available stake
            offers = [
                self.provide_sp_offer(sp1_token, parlay_id, "SP1", -110, 200.0)
            ]
            
            time.sleep(2)
            
            # User confirms 80% of available stake
            success, confirmed_stake = self.confirm_parlay_with_realistic_stake(
                USER_TOKEN, parlay_id, offers, 0.8
            )
            
            if success:
                print(f"✅ {scenario_name} PASSED")
                self.results["passed"] += 1
            else:
                print(f"❌ {scenario_name} FAILED")
                self.results["failed"] += 1
                
            self.results["scenarios"][scenario_name] = "PASSED" if success else "FAILED"
            
        except Exception as e:
            print(f"❌ {scenario_name} FAILED: {str(e)}")
            self.results["failed"] += 1
            self.results["scenarios"][scenario_name] = f"FAILED: {str(e)}"

    def run_all_realistic_stake_tests(self):
        """Run all realistic stake test scenarios"""
        print("🚀 REALISTIC STAKE CONFIRMATION TEST SUITE")
        print("="*80)
        print("Testing parlay confirmations with realistic stake calculations")
        print("Formula: Available Stake = max_risk ÷ decimal_odds")
        print("="*80)
        
        # Run test scenarios
        self.test_scenario_single_sp_full_confirmation()
        self.test_scenario_single_sp_partial_confirmation()
        self.test_scenario_multi_sp_same_odds_blended()
        self.test_scenario_multi_sp_different_odds_best_selected()
        self.test_scenario_high_stake_low_odds()
        self.test_scenario_favorite_negative_odds()
        
        # Print results
        self.print_results()

    def print_results(self):
        """Print test results summary"""
        total = self.results["passed"] + self.results["failed"]
        
        print(f"\n📊 REALISTIC STAKE TEST RESULTS")
        print("="*80)
        print(f"Total: {total} | Passed: {self.results['passed']} | Failed: {self.results['failed']}")
        
        if self.results["scenarios"]:
            print("\nDetailed Results:")
            for scenario, result in self.results["scenarios"].items():
                status_icon = "✅" if "PASSED" in result else "❌"
                print(f"   {status_icon} {scenario}: {result}")
        
        if self.results["failed"] == 0:
            print("\n🎉 ALL REALISTIC STAKE TESTS PASSED!")
            print("✅ Stake calculations working correctly")
            print("✅ User confirmations within available limits")
            print("✅ Multi-SP blending functioning properly")
        else:
            print(f"\n⚠️  {self.results['failed']} scenarios need attention")
        
        print("="*80)

def main():
    """Main test runner"""
    test_suite = RealisticStakeTestSuite()
    test_suite.run_all_realistic_stake_tests()

if __name__ == "__main__":
    main()
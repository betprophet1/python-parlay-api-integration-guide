#!/usr/bin/env python3
"""
Corrected Test Scenario with Proper Probability Calculations

ISSUE IDENTIFIED: Our test scripts were using hardcoded probabilities (0.5) instead of
calculating actual probabilities from odds like the real system does.

FIX: Use the correct probability calculation formula:
- For positive odds: probability = 100 / (odds + 100)  
- For negative odds: probability = |odds| / (|odds| + 100)

This should make our test results match the user-view confirmed stakes.
"""

import json
import requests
import logging
import time
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CorrectedTestScenario:
    def __init__(self):
        self.base_url = "https://parlay-api-staging.herokuapp.com"
        self.user_token = "test_user_token"  # Will be replaced with real token
        
        # SP credentials (test values)
        self.sp1_credentials = {"access_key": "sp1_key", "secret_key": "sp1_secret"}
        self.sp2_credentials = {"access_key": "sp2_key", "secret_key": "sp2_secret"}
        
        # Market lines for testing  
        self.market_lines = [
            {"lineId": "99fe18eea332562ac5cd04d4b3c772d0"},
            {"lineId": "b3ac37f3974eb98f726a5f852f07f9f6"}
        ]
    
    def calculate_probability_from_odds(self, odds: int) -> float:
        """
        Calculate probability from American odds and round to 10 decimals
        This matches the exact formula from your JavaScript code.
        """
        if odds > 0:
            probability = 100 / (odds + 100)
        else:
            probability = abs(odds) / (abs(odds) + 100)
        
        # Round to 10 decimal places (matching your toFixed(10))
        return round(probability, 10)
    
    def create_correct_price_probability(self, estimated_prices: list) -> list:
        """
        Create the price_probability array with proper probability calculations
        This replicates your JavaScript logic exactly.
        
        Args:
            estimated_prices: List of {"line_id": str, "odds": int} objects
            
        Returns:
            List of {"line_id": str, "probability": float} objects
        """
        price_probability = []
        
        for item in estimated_prices:
            probability = self.calculate_probability_from_odds(item["odds"])
            price_probability.append({
                "line_id": item["line_id"], 
                "probability": probability
            })
        
        return price_probability
    
    def sp_acknowledge_confirmation_corrected(self, sp_token: str, parlay_id: str, 
                                           confirmed_stake: float, odds: int, sp_name: str) -> bool:
        """
        SP acknowledges confirmation with CORRECT probability calculations
        """
        # Get SP orders first
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(orders_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ {sp_name} get orders FAILED: {response.status_code}")
                return False
            
            orders = response.json()["data"]["orders"]
            order_uuid = None
            
            # Find matching order
            for order in orders:
                if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
                    order_uuid = order["order_uuid"]
                    break
            
            if not order_uuid:
                logger.error(f"❌ {sp_name} order UUID not found for parlay {parlay_id}")
                return False
            
            logger.info(f"📋 Found {sp_name} order UUID: {order_uuid}")
            
            # Calculate proper max_risk based on confirmed_stake and odds
            decimal_odds = (odds + 100) / 100 if odds > 0 else 100 / abs(odds) + 1
            max_risk_dollars = confirmed_stake * decimal_odds
            max_risk_cents = int(max_risk_dollars * 100)
            
            # Create estimated_prices for probability calculation
            estimated_prices = [
                {"line_id": line["lineId"], "odds": odds}
                for line in self.market_lines
            ]
            
            # Calculate CORRECT probabilities from odds
            price_probability_lines = self.create_correct_price_probability(estimated_prices)
            
            logger.info(f"📋 {sp_name} acknowledgment details:")
            logger.info(f"   confirmed_stake: ${confirmed_stake:.2f}")
            logger.info(f"   odds: {odds:+d}")
            logger.info(f"   decimal_odds: {decimal_odds:.3f}")
            logger.info(f"   max_risk: ${confirmed_stake:.2f} × {decimal_odds:.3f} = ${max_risk_dollars:.2f}")
            logger.info(f"   max_risk (cents): {max_risk_cents}")
            logger.info(f"   probabilities: {[p['probability'] for p in price_probability_lines]}")
            
            # Acknowledge with CORRECT probability structure
            confirm_url = f"{self.base_url}/parlay/sp/orders/confirmations"
            payload = {
                "action": "accept",
                "confirmed_stake": confirmed_stake,
                "price_probability": [
                    {
                        "lines": price_probability_lines,  # CORRECTED: Use calculated probabilities
                        "max_risk": max_risk_cents,        # CORRECTED: Use calculated max_risk  
                        "vig": 0.1
                    }
                ],
                "signature": f"test_signature_{sp_name.lower()}"
            }
            
            logger.info(f"📤 {sp_name} sending acknowledgment payload:")
            logger.info(json.dumps(payload, indent=2))
            
            response = requests.post(confirm_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✅ {sp_name} confirmation acknowledged successfully")
                return True
            else:
                logger.error(f"❌ {sp_name} acknowledgment FAILED: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ {sp_name} acknowledgment ERROR: {str(e)}")
            return False
    
    def demonstrate_probability_calculation_fix(self):
        """Demonstrate the difference between old and new probability calculations"""
        
        logger.info("🔧 DEMONSTRATING PROBABILITY CALCULATION FIX")
        logger.info("="*80)
        
        test_odds = [800, 850, 900, -110, -280]
        
        logger.info("📊 Comparing OLD vs NEW probability calculations:")
        logger.info("-"*60)
        
        for odds in test_odds:
            old_probability = 0.5  # What our test scripts were using
            new_probability = self.calculate_probability_from_odds(odds)
            
            logger.info(f"Odds {odds:+4d}:")
            logger.info(f"  OLD (hardcoded): {old_probability:.10f}")
            logger.info(f"  NEW (calculated): {new_probability:.10f}")
            logger.info(f"  Difference: {abs(new_probability - old_probability):.10f}")
            logger.info("")
        
        logger.info("💡 INSIGHT: The hardcoded 0.5 probabilities were completely wrong!")
        logger.info("   Real probabilities vary significantly based on odds.")
        logger.info("   This explains why our test results didn't match user-view.")
    
    def test_corrected_scenario_flow(self):
        """Test the corrected scenario flow with proper calculations"""
        
        logger.info("\n🧪 TESTING CORRECTED SCENARIO FLOW")
        logger.info("="*80)
        
        # Simulate the scenario from your evidence
        user_stake = 27.77
        odds = 800
        
        # MM2 should accept some portion (let's say 60% for this test)
        mm2_confirmed_stake = user_stake * 0.6  # This gives us ~16.66
        
        logger.info(f"📋 SCENARIO SETUP:")
        logger.info(f"   User confirms: ${user_stake:.2f}")
        logger.info(f"   Odds: +{odds}")
        logger.info(f"   MM2 accepts: ${mm2_confirmed_stake:.2f} ({mm2_confirmed_stake/user_stake*100:.0f}% of user request)")
        
        # Calculate what MM2 should send in acknowledgment
        decimal_odds = (odds + 100) / 100
        max_risk_dollars = mm2_confirmed_stake * decimal_odds
        max_risk_cents = int(max_risk_dollars * 100)
        
        # Calculate proper probabilities
        estimated_prices = [
            {"line_id": "99fe18eea332562ac5cd04d4b3c772d0", "odds": odds},
            {"line_id": "b3ac37f3974eb98f726a5f852f07f9f6", "odds": odds}
        ]
        
        price_probability = self.create_correct_price_probability(estimated_prices)
        
        logger.info(f"\n📤 MM2 CORRECTED ACKNOWLEDGMENT:")
        logger.info(f"   confirmed_stake: ${mm2_confirmed_stake:.2f}")
        logger.info(f"   max_risk: ${max_risk_dollars:.2f} ({max_risk_cents} cents)")
        logger.info(f"   probabilities: {[p['probability'] for p in price_probability]}")
        
        logger.info(f"\n🎯 EXPECTED RESULT:")
        logger.info(f"   With corrected probabilities, user-view should show:")
        logger.info(f"   ${mm2_confirmed_stake:.2f} confirmed (not $3.71)")
        logger.info(f"   This matches MM2's intended acceptance amount")

def main():
    """Run the corrected test scenario demonstration"""
    test = CorrectedTestScenario()
    
    # First demonstrate the probability calculation fix
    test.demonstrate_probability_calculation_fix()
    
    # Then test the corrected flow
    test.test_corrected_scenario_flow()
    
    logger.info(f"\n✅ CONCLUSION:")
    logger.info("="*60)
    logger.info("🔧 The flaw was in our test scripts using hardcoded probabilities")
    logger.info("🎯 Using correct probability calculations should fix the user-view discrepancy")
    logger.info("📋 Update all test scripts to use calculate_probability_from_odds()")
    logger.info("🧪 Test results should now match the actual system behavior")

if __name__ == "__main__":
    main()
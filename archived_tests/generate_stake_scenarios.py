#!/usr/bin/env python3
"""
Comprehensive Stake Scenario Generator

This script generates realistic test scenarios for parlay confirmation testing
based on different betting situations and stake requirements.

Usage: python generate_stake_scenarios.py
"""

import json
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class SPOffer:
    """SP offer data structure"""
    sp_name: str
    odds: int
    max_risk_dollars: float
    description: str

@dataclass  
class TestScenario:
    """Test scenario data structure"""
    scenario_name: str
    description: str
    sp_offers: List[SPOffer]
    user_confirmation_ratio: float
    expected_behavior: str

def american_odds_to_decimal(american_odds: int) -> float:
    """Convert American odds to decimal odds"""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1

def calculate_available_stake(odds: int, max_risk_dollars: float) -> float:
    """Calculate available stake from SP offer"""
    decimal_odds = american_odds_to_decimal(odds)
    available_stake_dollars = max_risk_dollars / decimal_odds
    return available_stake_dollars

def generate_realistic_stake_scenarios() -> List[TestScenario]:
    """Generate comprehensive list of realistic stake test scenarios"""
    
    scenarios = []
    
    # Scenario 1: Single SP - Full Confirmation (Your Original Example)
    scenarios.append(TestScenario(
        scenario_name="User's Original Example Replicated",
        description="Replicate user's observation: +800 odds, $12.50 stake, $100 payout",
        sp_offers=[
            SPOffer("SP1", 800, 112.50, "Best odds with exact capacity for $12.50 stake"),
            SPOffer("SP2", 800, 112.50, "Matching SP for blended liquidity")
        ],
        user_confirmation_ratio=0.5,  # User confirms $12.50 out of $25.00 available
        expected_behavior="Should match exactly: $12.50 stake → $100 payout"
    ))
    
    # Scenario 2: Low Odds, High Stakes  
    scenarios.append(TestScenario(
        scenario_name="Low Odds High Stakes",
        description="Favorite lines with high available stakes",
        sp_offers=[
            SPOffer("SP1", 150, 600.0, "Confident in favorite, high capacity"),
            SPOffer("SP2", 150, 375.0, "Secondary capacity on favorite")
        ],
        user_confirmation_ratio=0.6,
        expected_behavior="High stake confirmation: ~$234 stake → ~$140 payout"
    ))
    
    # Scenario 3: High Odds, Low Stakes
    scenarios.append(TestScenario(
        scenario_name="High Odds Low Stakes", 
        description="Long shot parlay with limited available stakes",
        sp_offers=[
            SPOffer("SP1", 1200, 195.0, "Long shot with moderate risk tolerance"),
            SPOffer("SP2", 1200, 260.0, "Slightly higher risk tolerance")
        ],
        user_confirmation_ratio=1.0,
        expected_behavior="Low stake confirmation: ~$35 stake → ~$420 payout"
    ))
    
    # Scenario 4: Mixed Odds - Best Selection
    scenarios.append(TestScenario(
        scenario_name="Mixed Odds Best Selection",
        description="Multiple SPs with different odds, user should see best",
        sp_offers=[
            SPOffer("SP1", 900, 270.0, "Best odds with good capacity"),
            SPOffer("SP2", 750, 300.0, "Worse odds, better capacity"),
            SPOffer("SP3", 600, 420.0, "Worst odds, highest capacity")
        ],
        user_confirmation_ratio=0.8,
        expected_behavior="User sees +900 odds with $27 available, confirms ~$22"
    ))
    
    # Scenario 5: Negative Odds (Favorites)
    scenarios.append(TestScenario(
        scenario_name="Favorite Lines Negative Odds",
        description="Standard favorite lines with negative odds", 
        sp_offers=[
            SPOffer("SP1", -110, 190.9, "Standard -110 favorite"),
            SPOffer("SP2", -105, 200.0, "Slightly better favorite odds")
        ],
        user_confirmation_ratio=0.7,
        expected_behavior="User sees -105 odds with ~$105 available, confirms ~$74"
    ))
    
    # Scenario 6: Even Money
    scenarios.append(TestScenario(
        scenario_name="Even Money Bets",
        description="50/50 proposition bets",
        sp_offers=[
            SPOffer("SP1", 100, 300.0, "Even money proposition"),
            SPOffer("SP2", 105, 315.0, "Slightly better even money")
        ],
        user_confirmation_ratio=0.9,
        expected_behavior="User sees +105 odds with ~$154 available, confirms ~$138"
    ))
    
    # Scenario 7: Very High Odds (Extreme Long Shot)
    scenarios.append(TestScenario(
        scenario_name="Extreme Long Shot",
        description="Very high odds parlay with tiny stakes",
        sp_offers=[
            SPOffer("SP1", 2500, 260.0, "Extreme long shot, limited risk"),
            SPOffer("SP2", 2500, 520.0, "Higher risk tolerance on long shot")
        ],
        user_confirmation_ratio=1.0,
        expected_behavior="Very low stakes: ~$30 stake → ~$750 payout"
    ))
    
    # Scenario 8: Heavy Favorite
    scenarios.append(TestScenario(
        scenario_name="Heavy Favorite",
        description="Heavy favorite with very negative odds",
        sp_offers=[
            SPOffer("SP1", -300, 150.0, "Heavy favorite, moderate risk"),
            SPOffer("SP2", -280, 175.0, "Slightly better odds on heavy favorite")
        ],
        user_confirmation_ratio=0.8,
        expected_behavior="High stake on heavy favorite: ~$157 stake → ~$47 payout"
    ))
    
    # Scenario 9: Multiple Same Odds (Liquidity Blending)
    scenarios.append(TestScenario(
        scenario_name="High Liquidity Blending",
        description="Many SPs with same odds providing high liquidity",
        sp_offers=[
            SPOffer("SP1", 500, 150.0, "First SP with good odds"),
            SPOffer("SP2", 500, 180.0, "Second SP, higher capacity"),  
            SPOffer("SP3", 500, 120.0, "Third SP, moderate capacity"),
            SPOffer("SP4", 500, 225.0, "Fourth SP, highest capacity")
        ],
        user_confirmation_ratio=0.6,
        expected_behavior="High liquidity: ~$112 available, user confirms ~$67"
    ))
    
    # Scenario 10: Tier-Based Matching Requirements
    scenarios.append(TestScenario(
        scenario_name="Tier Based Matching Required",
        description="Large user stake requiring multiple SP tiers",
        sp_offers=[
            SPOffer("SP1", 400, 200.0, "Best tier, limited capacity"),
            SPOffer("SP2", 400, 150.0, "Best tier, additional capacity"),
            SPOffer("SP3", 380, 190.0, "Second tier fallback"),
            SPOffer("SP4", 350, 280.0, "Third tier, high capacity")
        ],
        user_confirmation_ratio=1.0,
        expected_behavior="Multi-tier matching: User wants $70, system blends tiers"
    ))
    
    return scenarios

def print_scenario_details(scenario: TestScenario):
    """Print detailed information about a test scenario"""
    print(f"\n{'='*80}")
    print(f"📋 SCENARIO: {scenario.scenario_name}")
    print(f"📝 Description: {scenario.description}")
    print("="*80)
    
    total_available = 0.0
    best_odds = 0
    
    print("💰 SP Offers:")
    for i, offer in enumerate(scenario.sp_offers, 1):
        available_stake = calculate_available_stake(offer.odds, offer.max_risk_dollars)
        decimal_odds = american_odds_to_decimal(offer.odds)
        potential_payout = available_stake * (decimal_odds - 1)
        
        print(f"   {offer.sp_name}:")
        print(f"      Odds: {offer.odds:+d}")
        print(f"      Max Risk: ${offer.max_risk_dollars:.2f}")
        print(f"      Available Stake: ${available_stake:.2f}")
        print(f"      Potential Payout: ${potential_payout:.2f}")
        print(f"      Description: {offer.description}")
        
        # Calculate totals (same odds are blended)
        # For negative odds, we want the least negative (closest to 0)
        # For positive odds, we want the highest
        is_better_odds = False
        if best_odds == 0:  # First offer
            is_better_odds = True
        elif best_odds > 0 and offer.odds > best_odds:  # Both positive, higher is better
            is_better_odds = True
        elif best_odds < 0 and offer.odds < 0 and offer.odds > best_odds:  # Both negative, less negative is better
            is_better_odds = True
        elif best_odds < 0 and offer.odds > 0:  # Current negative, new positive
            is_better_odds = True
            
        if is_better_odds:
            best_odds = offer.odds
            total_available = available_stake
        elif offer.odds == best_odds:
            total_available += available_stake
    
    print(f"\n📊 User Experience:")
    print(f"   Best Odds Available: {best_odds:+d}")
    print(f"   Total Available Stake: ${total_available:.2f}")
    
    user_stake = total_available * scenario.user_confirmation_ratio
    decimal_odds = american_odds_to_decimal(best_odds)
    user_payout = user_stake * (decimal_odds - 1)
    
    print(f"   User Confirmation: ${user_stake:.2f} ({scenario.user_confirmation_ratio*100:.0f}% of available)")
    print(f"   Expected Payout: ${user_payout:.2f}")
    
    print(f"\n🎯 Expected Behavior:")
    print(f"   {scenario.expected_behavior}")
    
    print(f"\n🔧 Test Configuration:")
    print(f"   confirmation_stake_cents: {int(user_stake * 100)}")
    print(f"   expected_payout_cents: {int(user_payout * 100)}")

def generate_test_data_json(scenarios: List[TestScenario]) -> str:
    """Generate JSON test data for automated testing"""
    test_data = {
        "realistic_stake_scenarios": []
    }
    
    for scenario in scenarios:
        scenario_data = {
            "scenario_name": scenario.scenario_name,
            "description": scenario.description,
            "sp_offers": [],
            "user_confirmation_ratio": scenario.user_confirmation_ratio,
            "expected_behavior": scenario.expected_behavior
        }
        
        total_available = 0.0
        best_odds = 0
        
        for offer in scenario.sp_offers:
            available_stake = calculate_available_stake(offer.odds, offer.max_risk_dollars)
            
            scenario_data["sp_offers"].append({
                "sp_name": offer.sp_name,
                "odds": offer.odds,
                "max_risk_dollars": offer.max_risk_dollars,
                "max_risk_cents": int(offer.max_risk_dollars * 100),
                "available_stake_dollars": round(available_stake, 2),
                "available_stake_cents": int(available_stake * 100),
                "description": offer.description
            })
            
            # Calculate best available (handle negative odds properly)
            is_better_odds = False
            if best_odds == 0:  # First offer
                is_better_odds = True
            elif best_odds > 0 and offer.odds > best_odds:  # Both positive, higher is better
                is_better_odds = True
            elif best_odds < 0 and offer.odds < 0 and offer.odds > best_odds:  # Both negative, less negative is better
                is_better_odds = True
            elif best_odds < 0 and offer.odds > 0:  # Current negative, new positive
                is_better_odds = True
                
            if is_better_odds:
                best_odds = offer.odds
                total_available = available_stake
            elif offer.odds == best_odds:
                total_available += available_stake
        
        # Add calculated values
        user_stake = total_available * scenario.user_confirmation_ratio
        decimal_odds = american_odds_to_decimal(best_odds)
        user_payout = user_stake * (decimal_odds - 1)
        
        scenario_data["calculations"] = {
            "best_odds": best_odds,
            "total_available_stake_dollars": round(total_available, 2),
            "total_available_stake_cents": int(total_available * 100),
            "user_confirmation_stake_dollars": round(user_stake, 2),
            "user_confirmation_stake_cents": int(user_stake * 100),
            "expected_payout_dollars": round(user_payout, 2),
            "expected_payout_cents": int(user_payout * 100),
            "decimal_odds": round(decimal_odds, 3)
        }
        
        test_data["realistic_stake_scenarios"].append(scenario_data)
    
    return json.dumps(test_data, indent=2)

def main():
    """Generate and display all realistic stake scenarios"""
    print("🎯 COMPREHENSIVE REALISTIC STAKE SCENARIO GENERATOR")
    print("="*80)
    print("Generating test scenarios based on realistic SP offers and user confirmations")
    print("Formula: Available Stake = max_risk ÷ decimal_odds")
    print("="*80)
    
    scenarios = generate_realistic_stake_scenarios()
    
    # Print all scenarios
    for scenario in scenarios:
        print_scenario_details(scenario)
    
    # Generate JSON test data
    json_data = generate_test_data_json(scenarios)
    
    # Save to file
    with open("/Users/tranlam/Documents/GitHub/python-parlay-api-integration-guide/realistic_stake_scenarios.json", "w") as f:
        f.write(json_data)
    
    print(f"\n💾 SAVED TEST DATA")
    print("="*60)
    print("📁 File: realistic_stake_scenarios.json")
    print("📊 Contains: Detailed test data for all scenarios")
    print("🔧 Usage: Import into test scripts for automated testing")
    
    print(f"\n📈 SUMMARY")
    print("="*60)
    print(f"Generated {len(scenarios)} realistic stake scenarios")
    print("Covers: Single/Multi SP, Various odds ranges, Different confirmation ratios")
    print("Includes: Long shots, favorites, even money, extreme cases")
    print("Ready for: Automated parlay confirmation testing")

if __name__ == "__main__":
    main()
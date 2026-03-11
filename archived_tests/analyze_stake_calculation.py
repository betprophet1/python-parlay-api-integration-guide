#!/usr/bin/env python3
"""
Stake Calculation Analysis

This script analyzes how SP offers (odds + max_risk) translate to user available stakes.
Based on user observation: Odds +800, Matched stake $12.50, To Win $100.00

The relationship appears to be:
Available Stake = max_risk / (odds/100 + 1)

Where:
- max_risk = SP's maximum risk exposure in cents
- odds = American odds (e.g., +800)
- Available Stake = maximum stake user can place with this SP
"""

def american_odds_to_decimal(american_odds):
    """Convert American odds to decimal odds"""
    if american_odds > 0:
        return (american_odds / 100) + 1
    else:
        return (100 / abs(american_odds)) + 1

def calculate_available_stake_from_offer(odds, max_risk_cents):
    """
    Calculate available stake from SP offer
    
    Formula: Available Stake = max_risk / decimal_odds
    
    This ensures SP's risk exposure doesn't exceed their max_risk limit.
    """
    decimal_odds = american_odds_to_decimal(odds)
    available_stake_cents = max_risk_cents / decimal_odds
    return available_stake_cents

def validate_calculation(odds, available_stake_cents, to_win_cents):
    """Validate the calculation matches expected payout"""
    decimal_odds = american_odds_to_decimal(odds)
    calculated_to_win = available_stake_cents * (decimal_odds - 1)
    return abs(calculated_to_win - to_win_cents) < 0.01

def analyze_user_example():
    """Analyze the user's specific example"""
    print("🔍 ANALYZING USER EXAMPLE")
    print("="*60)
    
    # User's observed data
    odds = 800  # +800
    matched_stake_dollars = 12.50
    to_win_dollars = 100.00
    
    matched_stake_cents = matched_stake_dollars * 100
    to_win_cents = to_win_dollars * 100
    
    print(f"📊 User Observation:")
    print(f"   Odds: +{odds}")
    print(f"   Matched Stake: ${matched_stake_dollars}")
    print(f"   To Win: ${to_win_dollars}")
    
    # Calculate decimal odds
    decimal_odds = american_odds_to_decimal(odds)
    print(f"\n🔢 Decimal Odds: {decimal_odds}")
    
    # Reverse calculate the max_risk that would produce this stake
    # If Available Stake = max_risk / decimal_odds
    # Then max_risk = Available Stake * decimal_odds
    implied_max_risk = matched_stake_cents * decimal_odds
    
    print(f"\n💰 Implied SP max_risk:")
    print(f"   ${implied_max_risk/100:.2f} ({implied_max_risk:.0f} cents)")
    
    # Validate the payout calculation
    calculated_to_win = matched_stake_cents * (decimal_odds - 1)
    print(f"\n✅ Payout Validation:")
    print(f"   Expected To Win: ${to_win_dollars}")
    print(f"   Calculated To Win: ${calculated_to_win/100:.2f}")
    print(f"   Match: {'✅' if abs(calculated_to_win - to_win_cents) < 0.01 else '❌'}")
    
    return implied_max_risk

def test_stake_calculation_scenarios():
    """Test various stake calculation scenarios"""
    print("\n🧪 TESTING STAKE CALCULATION SCENARIOS")
    print("="*60)
    
    test_cases = [
        # (odds, max_risk_cents, expected_description)
        (800, 11250, "User's example scenario"),
        (400, 10000, "Lower odds, same risk"),
        (200, 5000, "Even lower odds"),
        (-110, 10000, "Negative odds (favorite)"),
        (1000, 50000, "High odds, high risk"),
    ]
    
    for odds, max_risk_cents, description in test_cases:
        print(f"\n📋 {description}")
        print(f"   SP Offer: +{odds} odds, ${max_risk_cents/100:.2f} max_risk")
        
        available_stake_cents = calculate_available_stake_from_offer(odds, max_risk_cents)
        decimal_odds = american_odds_to_decimal(odds)
        to_win_cents = available_stake_cents * (decimal_odds - 1)
        
        print(f"   Available Stake: ${available_stake_cents/100:.2f}")
        print(f"   To Win: ${to_win_cents/100:.2f}")
        print(f"   Decimal Odds: {decimal_odds:.3f}")
        
        # Verify SP's actual risk
        sp_actual_risk = to_win_cents
        print(f"   SP Risk Exposure: ${sp_actual_risk/100:.2f}")
        print(f"   Within max_risk: {'✅' if sp_actual_risk <= max_risk_cents else '❌'}")

def demonstrate_multi_sp_blending():
    """Demonstrate how multiple SP offers are blended for user"""
    print("\n🔄 MULTI-SP OFFER BLENDING")
    print("="*60)
    
    # Example: User's scenario with 2 SPs
    print("📋 Scenario: 2 SPs provide same odds but different capacities")
    
    sp_offers = [
        {"sp": "SP1", "odds": 800, "max_risk_cents": 11250},
        {"sp": "SP2", "odds": 800, "max_risk_cents": 11250},
    ]
    
    total_available_stake = 0
    
    for offer in sp_offers:
        available_stake = calculate_available_stake_from_offer(
            offer["odds"], offer["max_risk_cents"]
        )
        total_available_stake += available_stake
        
        print(f"\n{offer['sp']}:")
        print(f"   Offer: +{offer['odds']} odds, ${offer['max_risk_cents']/100:.2f} max_risk")
        print(f"   Available Stake: ${available_stake/100:.2f}")
    
    print(f"\n📊 Combined Availability:")
    print(f"   Total Available Stake: ${total_available_stake/100:.2f}")
    print(f"   User Matched: $12.50 (using both SPs)")
    
    # Show how stake is distributed
    stake_per_sp = 1250 / 2  # $12.50 split between 2 SPs
    decimal_odds = american_odds_to_decimal(800)
    to_win_per_sp = stake_per_sp * (decimal_odds - 1)
    
    print(f"\n💰 Stake Distribution:")
    print(f"   SP1: ${stake_per_sp/100:.2f} stake → ${to_win_per_sp/100:.2f} to_win")
    print(f"   SP2: ${stake_per_sp/100:.2f} stake → ${to_win_per_sp/100:.2f} to_win")
    print(f"   Total To Win: ${(to_win_per_sp * 2)/100:.2f}")

def create_sp_offer_examples():
    """Create realistic SP offer examples for testing"""
    print("\n🎯 SP OFFER EXAMPLES FOR TESTING")
    print("="*60)
    
    examples = [
        {
            "scenario": "High odds, moderate risk",
            "odds": 800,
            "max_risk_dollars": 100,
            "description": "SP comfortable with $100 risk on long shot"
        },
        {
            "scenario": "Medium odds, high capacity", 
            "odds": 400,
            "max_risk_dollars": 500,
            "description": "SP willing to take larger risk on medium odds"
        },
        {
            "scenario": "Low odds, very high capacity",
            "odds": 150,
            "max_risk_dollars": 1000,
            "description": "SP confident in favorite, high capacity"
        },
        {
            "scenario": "Negative odds (favorite)",
            "odds": -110,
            "max_risk_dollars": 200,
            "description": "Standard -110 favorite line"
        }
    ]
    
    for example in examples:
        print(f"\n📋 {example['scenario']}")
        print(f"   {example['description']}")
        
        max_risk_cents = example['max_risk_dollars'] * 100
        available_stake_cents = calculate_available_stake_from_offer(
            example['odds'], max_risk_cents
        )
        
        decimal_odds = american_odds_to_decimal(example['odds'])
        to_win_cents = available_stake_cents * (decimal_odds - 1)
        
        print(f"   SP Offer: {example['odds']:+d} odds, ${example['max_risk_dollars']:.2f} max_risk")
        print(f"   User Available: ${available_stake_cents/100:.2f} stake")
        print(f"   Potential Payout: ${to_win_cents/100:.2f}")
        print(f"   SP Risk Check: ${to_win_cents/100:.2f} ≤ ${example['max_risk_dollars']:.2f} = {'✅' if to_win_cents <= max_risk_cents else '❌'}")

def main():
    """Main analysis function"""
    print("🔍 PARLAY STAKE CALCULATION ANALYSIS")
    print("="*80)
    print("Based on user observation: Odds +800, Matched stake $12.50, To Win $100.00")
    print("="*80)
    
    # Analyze user's specific example
    implied_max_risk = analyze_user_example()
    
    # Test various scenarios
    test_stake_calculation_scenarios()
    
    # Show multi-SP blending
    demonstrate_multi_sp_blending()
    
    # Create examples for testing
    create_sp_offer_examples()
    
    print(f"\n🎯 KEY FINDINGS:")
    print(f"="*60)
    print(f"1. Formula: Available Stake = max_risk ÷ decimal_odds")
    print(f"2. User's example implies SP max_risk ≈ ${implied_max_risk/100:.2f}")
    print(f"3. Multiple SPs with same odds blend their available stakes")
    print(f"4. SP's actual risk exposure = user's potential winnings")
    print(f"5. This ensures SP never exceeds their max_risk limit")
    
    print(f"\n🔧 TESTING RECOMMENDATIONS:")
    print(f"="*60)
    print(f"1. Use max_risk values that produce realistic available stakes")
    print(f"2. For +800 odds: max_risk $112.50 → available stake $12.50")
    print(f"3. Test with multiple SPs to verify stake blending")
    print(f"4. Validate SP risk exposure never exceeds max_risk")

if __name__ == "__main__":
    main()
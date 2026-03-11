#!/usr/bin/env python3
"""
Fix for MM Acknowledgment Logic

PROBLEM IDENTIFIED:
- User confirms: $27.77
- MM2 acknowledges: confirmed_stake = $16.66
- MM2 sends: max_risk = 200 cents ($2.00) ← WRONG!
- System executes: Only $2.00 worth of action because max_risk constrains it
- User sees: $3.71 confirmed (based on $2.00 constraint)

SOLUTION:
- max_risk must equal confirmed_stake × decimal_odds
- For confirmed_stake=$16.66 at odds=800: max_risk = $16.66 × 9.0 = $149.94

This fix updates the MM acknowledgment logic to properly calculate max_risk.
"""

import json

def calculate_proper_max_risk(confirmed_stake_dollars: float, odds: int) -> float:
    """
    Calculate proper max_risk for MM acknowledgment
    
    Args:
        confirmed_stake_dollars: The stake amount SP wants to accept ($)
        odds: American odds (e.g., 800, 850, 900)
        
    Returns:
        max_risk in dollars that SP needs to cover this stake
    """
    # Convert American odds to decimal odds
    if odds > 0:
        decimal_odds = (odds + 100) / 100
    else:
        decimal_odds = 100 / abs(odds) + 1
    
    # Max risk = stake × decimal_odds (potential payout to user)
    max_risk_dollars = confirmed_stake_dollars * decimal_odds
    
    return max_risk_dollars

def generate_corrected_acknowledgment_payload(parlay_id: str, confirmed_stake: float, odds: int, market_lines: list) -> dict:
    """
    Generate corrected MM acknowledgment payload with proper max_risk calculation
    
    Args:
        parlay_id: The parlay ID
        confirmed_stake: Stake amount MM wants to accept (dollars)
        odds: American odds
        market_lines: List of market lines with line_id
        
    Returns:
        Corrected payload dict
    """
    # Calculate proper max_risk
    max_risk_dollars = calculate_proper_max_risk(confirmed_stake, odds)
    max_risk_cents = int(max_risk_dollars * 100)  # Convert to cents for API
    
    # Generate corrected payload
    payload = {
        "action": "accept",
        "confirmed_stake": confirmed_stake,
        "price_probability": [
            {
                "lines": [
                    {
                        "line_id": line["lineId"],
                        "probability": 0.5
                    }
                    for line in market_lines
                ],
                "max_risk": max_risk_cents,  # CORRECTED VALUE
                "vig": 0.1
            }
        ],
        "signature": "test_signature_sp"
    }
    
    return payload

def demonstrate_correction():
    """Demonstrate the correction using the failing scenario"""
    
    print("🔧 MM ACKNOWLEDGMENT FIX DEMONSTRATION")
    print("="*80)
    
    # Example from failing scenario
    user_stake = 27.77
    sp_confirmed_stake = 16.66  # SP wants to accept 60% of user request
    odds = 800
    
    print(f"📋 SCENARIO:")
    print(f"  User Confirmed Stake: ${user_stake:.2f}")
    print(f"  SP Wants to Accept: ${sp_confirmed_stake:.2f}")
    print(f"  Odds: +{odds}")
    
    # Current broken logic
    broken_max_risk_cents = 200  # Hardcoded $2.00
    broken_max_risk_dollars = broken_max_risk_cents / 100
    
    print(f"\n❌ CURRENT BROKEN LOGIC:")
    print(f"  max_risk (hardcoded): {broken_max_risk_cents} cents = ${broken_max_risk_dollars:.2f}")
    print(f"  System constraint: min(${sp_confirmed_stake:.2f}, ${broken_max_risk_dollars:.2f})")
    print(f"  Actual executed: ${broken_max_risk_dollars:.2f} (constrained by max_risk)")
    
    # Fixed logic
    correct_max_risk_dollars = calculate_proper_max_risk(sp_confirmed_stake, odds)
    correct_max_risk_cents = int(correct_max_risk_dollars * 100)
    
    print(f"\n✅ CORRECTED LOGIC:")
    print(f"  confirmed_stake: ${sp_confirmed_stake:.2f}")
    print(f"  decimal_odds: {(odds + 100) / 100}")
    print(f"  max_risk: ${sp_confirmed_stake:.2f} × {(odds + 100) / 100} = ${correct_max_risk_dollars:.2f}")
    print(f"  max_risk (cents): {correct_max_risk_cents}")
    print(f"  System executes: ${sp_confirmed_stake:.2f} (not constrained)")
    
    # Show the payload difference
    market_lines = [
        {"lineId": "99fe18eea332562ac5cd04d4b3c772d0"},
        {"lineId": "b3ac37f3974eb98f726a5f852f07f9f6"}
    ]
    
    corrected_payload = generate_corrected_acknowledgment_payload(
        "example-parlay-id", 
        sp_confirmed_stake, 
        odds, 
        market_lines
    )
    
    print(f"\n📤 CORRECTED PAYLOAD:")
    print(json.dumps(corrected_payload, indent=2))
    
    print(f"\n🎯 EXPECTED RESULT:")
    print(f"  User confirms: ${user_stake:.2f}")
    print(f"  SP2 accepts: ${sp_confirmed_stake:.2f}")
    print(f"  System executes: ${sp_confirmed_stake:.2f}")
    print(f"  User-view shows: ${sp_confirmed_stake:.2f} confirmed (not ${broken_max_risk_dollars:.2f})")

def test_multiple_scenarios():
    """Test the fix across multiple scenarios"""
    
    print(f"\n🧪 TESTING MULTIPLE SCENARIOS")
    print("="*60)
    
    test_cases = [
        {"user_stake": 27.77, "sp_accepts": 16.66, "odds": 800},
        {"user_stake": 119.04, "sp_accepts": 71.42, "odds": 900},
        {"user_stake": 65.00, "sp_accepts": 32.50, "odds": 900},
        {"user_stake": 100.00, "sp_accepts": 100.00, "odds": 800},
    ]
    
    for i, case in enumerate(test_cases, 1):
        user_stake = case["user_stake"]
        sp_accepts = case["sp_accepts"]
        odds = case["odds"]
        
        broken_constraint = 2.00  # Current hardcoded max_risk
        correct_max_risk = calculate_proper_max_risk(sp_accepts, odds)
        
        print(f"\nTest Case {i}:")
        print(f"  User: ${user_stake:.2f} | SP: ${sp_accepts:.2f} | Odds: +{odds}")
        print(f"  Broken (max_risk=$2.00): System executes ${min(sp_accepts, broken_constraint):.2f}")
        print(f"  Fixed (max_risk=${correct_max_risk:.2f}): System executes ${sp_accepts:.2f}")

if __name__ == "__main__":
    demonstrate_correction()
    test_multiple_scenarios()
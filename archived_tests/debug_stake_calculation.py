#!/usr/bin/env python3
"""
Debug Stake Calculation Flow

This script focuses on understanding the discrepancy between:
1. What we think the available stake should be
2. What the user actually sees in their user-view

Key Investigation Points:
1. SP offers max_risk, we calculate available_stake = max_risk / decimal_odds
2. User requests stake_cents in confirmation
3. But user-view shows much smaller confirmed stakes

This suggests either:
- Our calculation is wrong
- There are additional constraints/factors we're not accounting for
- The system applies additional risk management or liquidity constraints
"""

import json
import requests
from datetime import datetime, timezone

class StakeCalculationDebugger:
    def __init__(self):
        # Use the fresh working token
        self.user_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6InNpbTIifQ.eyJhY2NvdW50VHlwZSI6MCwiZXhwIjoxNzU5ODk2NzI0LCJleHRyYU9ubGluZVRpbWUiOjAsImlzT3RwRXhwaXJlZCI6ZmFsc2UsImlzU3VzcGVuZGVkIjpmYWxzZSwiaXNzIjoiaHR0cDovL21vdGhlcnNoaXAubW90aGVyc2hpcC1zYW5kYm94IiwianRpIjoiNmIwNDVmMGItOTVhOC00MDNiLThjYTgtYmQyYmE3MzM0NWMyIiwia2JhQW5zd2Vyc0luZm8iOiJOL0EiLCJreWNJbmZvIjoiU3VjY2VzcyIsInBlbmRpbmdCeUFkbWluIjpmYWxzZSwicHVzaGVySW5mbyI6eyJhdXRoQ2hhbm5lbCI6InVzZXIuYXV0aGVudGljYXRpb24uNmIwNDVmMGItOTVhOC00MDNiLThjYTgtYmQyYmE3MzM0NWMyIiwiYmFsYW5jZVVwZGF0ZWRFdmVudCI6IndhbGxldC5iYWxhbmNlLnVwZGF0ZWQiLCJjbHVzdGVyIjoibXQxIiwiaWQiOiJjMjBmYTM2ZmJjM2MzYzMwOGZmYSIsImluZm9DaGFubmVsIjoidXNlci5pbmZvcm1hdGlvbi5lZjVjM2JlMy1hZDRkLTRlMGYtYWNlNy05NzA1NjkwYzgyNmUiLCJpbmZvcm1hdGlvblVwZGF0ZWRFdmVudCI6InVzZXIuaW5mb3JtYXRpb24udXBkYXRlZCIsImtiYUNoYWxsZW5nZVF1ZXN0aW9uc0V2ZW50IjoidXNlci5rYmEuY2hhbGxlbmdlIiwic2Vzc2lvblRlcm1pbmF0ZWRFdmVudCI6InNlc3Npb24udGVybWluYXRlZCJ9LCJyZWdpb24iOiJOWSIsInN1YiI6ImxhbS50cmFuK3VzcjAwNEBiZXRwcm9waGV0LmNvIiwidXNlcklkIjoiZWY1YzNiZTMtYWQ0ZC00ZTBmLWFjZTctOTcwNTY5MGM4MjZlIn0.Qdl4xsYl9nL9I9JgBphjE84PEWsAT3g-RYviuV1raxo"
        
        # Analyze actual confirmed orders from user-view
        self.user_view_data = [
            # Based on the curl response you just ran
            {"requested_stake": 180.98, "confirmed_stake": 3.71, "odds": 850},
            {"requested_stake": 119.04, "confirmed_stake": 4.89, "odds": 900},
            {"requested_stake": 65.00, "confirmed_stake": 1.67, "odds": 900},
            {"requested_stake": 27.77, "confirmed_stake": 2.08, "odds": 800},
            {"requested_stake": 100.00, "confirmed_stake": 12.50, "odds": 800},
            {"requested_stake": 150.00, "confirmed_stake": 18.75, "odds": 800},
            {"requested_stake": 400.00, "confirmed_stake": 35.29, "odds": 850},
            {"requested_stake": 50.00, "confirmed_stake": 12.50, "odds": 800},
        ]
    
    def analyze_user_view_patterns(self):
        """Analyze patterns in confirmed vs requested stakes"""
        print("🔍 ANALYZING USER-VIEW CONFIRMED STAKES")
        print("="*80)
        
        for i, data in enumerate(self.user_view_data, 1):
            requested = data["requested_stake"]
            confirmed = data["confirmed_stake"]
            odds = data["odds"]
            
            ratio = confirmed / requested if requested > 0 else 0
            reduction = ((requested - confirmed) / requested * 100) if requested > 0 else 0
            
            print(f"Order {i}:")
            print(f"  Requested: ${requested:.2f}")
            print(f"  Confirmed: ${confirmed:.2f}")
            print(f"  Odds: {odds}")
            print(f"  Ratio: {ratio:.3f} ({ratio*100:.1f}%)")
            print(f"  Reduction: {reduction:.1f}%")
            print()
        
        # Look for patterns
        ratios = [d["confirmed_stake"] / d["requested_stake"] for d in self.user_view_data]
        avg_ratio = sum(ratios) / len(ratios)
        
        print(f"📊 PATTERN ANALYSIS:")
        print(f"  Average Confirmation Ratio: {avg_ratio:.3f} ({avg_ratio*100:.1f}%)")
        print(f"  Min Ratio: {min(ratios):.3f} ({min(ratios)*100:.1f}%)")
        print(f"  Max Ratio: {max(ratios):.3f} ({max(ratios)*100:.1f}%)")
        
        # Group by odds to see if there's an odds-based pattern
        print(f"\n📈 RATIO BY ODDS:")
        odds_groups = {}
        for data in self.user_view_data:
            odds = data["odds"]
            ratio = data["confirmed_stake"] / data["requested_stake"]
            if odds not in odds_groups:
                odds_groups[odds] = []
            odds_groups[odds].append(ratio)
        
        for odds in sorted(odds_groups.keys()):
            ratios = odds_groups[odds]
            avg = sum(ratios) / len(ratios)
            print(f"  Odds {odds}: {avg:.3f} avg ratio ({len(ratios)} samples)")
    
    def check_current_user_balance(self):
        """Check current user balance and limits"""
        print(f"\n💰 CHECKING USER ACCOUNT STATUS")
        print("="*60)
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Check user profile/balance
        try:
            response = requests.get(
                "https://api-ss-sandbox.betprophet.co/parlay/api/v1/user/profile",
                headers=headers
            )
            
            if response.status_code == 200:
                profile = response.json()
                print(f"✅ User Profile Retrieved")
                print(f"   Balance: ${profile.get('balance', 'N/A')}")
                print(f"   Currency: {profile.get('currency', 'N/A')}")
                print(f"   Status: {profile.get('status', 'N/A')}")
                
                # Look for any limits or constraints
                if 'limits' in profile:
                    print(f"   Limits: {json.dumps(profile['limits'], indent=2)}")
            else:
                print(f"❌ Failed to get profile: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error checking profile: {e}")
    
    def test_simple_stake_flow(self):
        """Test a simple stake flow to understand the calculation"""
        print(f"\n🧪 TESTING SIMPLE STAKE FLOW")
        print("="*60)
        
        # We'll analyze the flow but not actually place bets
        # Just understand what should happen vs what does happen
        
        test_cases = [
            {"odds": 800, "max_risk": 10000},  # $100 max risk
            {"odds": 850, "max_risk": 15000},  # $150 max risk
            {"odds": 900, "max_risk": 20000},  # $200 max risk
        ]
        
        for case in test_cases:
            odds = case["odds"]
            max_risk_cents = case["max_risk"]
            max_risk_dollars = max_risk_cents / 100
            
            # Calculate expected available stake using our formula
            decimal_odds = (odds + 100) / 100 if odds > 0 else 100 / abs(odds) + 1
            expected_available = max_risk_dollars / decimal_odds
            
            print(f"Test Case:")
            print(f"  SP Odds: +{odds}")
            print(f"  SP Max Risk: ${max_risk_dollars:.2f}")
            print(f"  Decimal Odds: {decimal_odds:.3f}")
            print(f"  Expected Available Stake: ${expected_available:.2f}")
            
            # Compare with user-view patterns
            matching_orders = [d for d in self.user_view_data if d["odds"] == odds]
            if matching_orders:
                print(f"  User-View Examples:")
                for order in matching_orders:
                    actual_ratio = order["confirmed_stake"] / order["requested_stake"]
                    print(f"    Requested ${order['requested_stake']:.2f} → Confirmed ${order['confirmed_stake']:.2f} (ratio: {actual_ratio:.3f})")
            print()
    
    def investigate_potential_causes(self):
        """Investigate potential causes for the discrepancy"""
        print(f"\n🕵️ INVESTIGATING POTENTIAL CAUSES")
        print("="*60)
        
        print("🤔 HYPOTHESIS 1: Risk Management Constraints")
        print("   - System applies additional risk limits beyond SP max_risk")
        print("   - Account-level position limits")
        print("   - Market-wide exposure limits")
        print()
        
        print("🤔 HYPOTHESIS 2: Liquidity Fragmentation")
        print("   - Available stake split across multiple SPs")
        print("   - Each SP only fills partial amount")
        print("   - User sees aggregate of all partial fills")
        print()
        
        print("🤔 HYPOTHESIS 3: Dynamic Repricing")
        print("   - SP offers change between quote and confirmation")
        print("   - Odds move or max_risk gets reduced")
        print("   - System confirms at current availability, not original quote")
        print()
        
        print("🤔 HYPOTHESIS 4: Calculation Error in Our Logic")
        print("   - Our available_stake = max_risk / decimal_odds might be wrong")
        print("   - Could be: max_risk / (decimal_odds - 1) for profit calculation")
        print("   - Or some other formula we're not aware of")
        print()
        
        print("🤔 HYPOTHESIS 5: Multiple Offer Types")
        print("   - SP provides multiple offers with different stakes/odds")
        print("   - User confirmation picks specific offer, not necessarily the main one")
        print("   - We're logging one thing but system executes another")
    
    def run_full_analysis(self):
        """Run complete stake calculation analysis"""
        print("🔬 STAKE CALCULATION FLOW DEBUGGER")
        print("="*80)
        print("Investigating discrepancy between expected and confirmed stakes")
        print("Based on user-view data from recent test runs")
        print("="*80)
        
        self.analyze_user_view_patterns()
        self.check_current_user_balance()
        self.test_simple_stake_flow()
        self.investigate_potential_causes()
        
        print(f"\n💡 NEXT STEPS RECOMMENDATION:")
        print("="*60)
        print("1. 🔍 Analyze the exact offers structure returned by SP")
        print("2. 🔍 Check if there are multiple offers per SP")
        print("3. 🔍 Verify the exact confirmation request structure")
        print("4. 🔍 Compare requested vs actual available stakes from system")
        print("5. 🔍 Check for any account or market-level limits being applied")
        print()
        print("🎯 KEY INSIGHT: The system is consistently accepting smaller stakes")
        print("   than requested, suggesting either:")
        print("   • Our available stake calculation is incorrect")
        print("   • Additional constraints are being applied")
        print("   • The SP offers are different than we expect")

def main():
    debugger = StakeCalculationDebugger()
    debugger.run_full_analysis()

if __name__ == "__main__":
    main()
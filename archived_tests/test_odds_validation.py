#!/usr/bin/env python3
"""
🧪 Odds Validation Test Suite
Tests the new probability-based odds validation with odds ladder ranges.
"""

import sys
sys.path.insert(0, 'src')

from odds_validation import (
    american_to_probability,
    probability_to_american,
    find_odds_range,
    validate_odds_with_probability,
    validate_price_probability
)


def test_american_to_probability():
    """Test American odds to probability conversion"""
    print("\n" + "="*60)
    print("🧪 TEST: American Odds → Probability Conversion")
    print("="*60)
    
    test_cases = [
        (+100, 0.5000),      # Even odds
        (+377, 0.2096),      # Example from requirement
        (-110, 0.5238),      # Common favorite odds
        (+300, 0.2500),      # 3:1 underdog
        (-200, 0.6667),      # 1:2 favorite
    ]
    
    passed = 0
    for odds, expected_prob in test_cases:
        result = american_to_probability(odds)
        is_close = abs(result - expected_prob) < 0.001
        status = "✓" if is_close else "✗"
        print(f"{status} {odds:+5d} → {result:.4f} (expected: {expected_prob:.4f})")
        if is_close:
            passed += 1
    
    print(f"\n📊 Passed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_probability_to_american():
    """Test probability to American odds conversion"""
    print("\n" + "="*60)
    print("🧪 TEST: Probability → American Odds Conversion")
    print("="*60)
    
    test_cases = [
        (0.5000, +100),      # Even odds
        (0.2097, +377),      # Example from requirement (0.8161 * 0.2570)
        (0.2500, +300),      # 3:1 underdog
        (0.6667, -200),      # 1:2 favorite
    ]
    
    passed = 0
    for prob, expected_odds in test_cases:
        result = probability_to_american(prob)
        # Allow 1-2 point tolerance for rounding
        is_close = abs(result - expected_odds) <= 2
        status = "✓" if is_close else "✗"
        print(f"{status} {prob:.4f} → {result:+5d} (expected: {expected_odds:+5d})")
        if is_close:
            passed += 1
    
    print(f"\n📊 Passed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_find_odds_range():
    """Test finding odds range in ladder"""
    print("\n" + "="*60)
    print("🧪 TEST: Find Odds Range in Ladder")
    print("="*60)
    
    test_cases = [
        (+377, (370, 380)),   # Between 370 and 380
        (+100, (100, 101)),   # Exact match at 100
        (-115, (-115, -114)), # Exact match at -115
        (+500, (500, 520)),   # Exact match at 500
    ]
    
    passed = 0
    for odds, expected_range in test_cases:
        result = find_odds_range(odds)
        is_correct = result == expected_range
        status = "✓" if is_correct else "✗"
        print(f"{status} {odds:+5d} → range: [{result[0]:+5d}, {result[1]:+5d}] (expected: [{expected_range[0]:+5d}, {expected_range[1]:+5d}])")
        if is_correct:
            passed += 1
    
    print(f"\n📊 Passed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_validate_odds_with_probability():
    """Test the core validation logic"""
    print("\n" + "="*60)
    print("🧪 TEST: Validate Odds with Probability (Core Logic)")
    print("="*60)
    
    test_cases = [
        {
            "name": "Example from requirement - VALID (positive odds)",
            "sp_odds": +377,
            "leg_probabilities": [0.8160750396014694, 0.2570033410434336],
            "expected_valid": True,
            "note": "Combined prob: 0.2097 → odds: +375, range: [370, 380]"
        },
        {
            "name": "Simple 2-leg parlay - VALID (positive odds)",
            "sp_odds": +300,
            "leg_probabilities": [0.5, 0.5],
            "expected_valid": True,
            "note": "Combined prob: 0.25 → odds: +300, exact match"
        },
        {
            "name": "3-leg parlay - VALID (positive odds)",
            "sp_odds": +700,
            "leg_probabilities": [0.5, 0.5, 0.5],
            "expected_valid": True,
            "note": "Combined prob: 0.125 → odds: +700, exact match"
        },
        {
            "name": "Favorite 2-leg parlay - INVALID (negative odds edge case)",
            "sp_odds": -110,
            "leg_probabilities": [0.7, 0.75],
            "expected_valid": False,
            "note": "Combined prob: 0.525 → odds: -111, outside range [-110, -109]"
        },
        {
            "name": "Heavy favorite parlay - VALID (negative odds)",
            "sp_odds": -200,
            "leg_probabilities": [0.8, 0.833],
            "expected_valid": True,
            "note": "Combined prob: 0.6664 → odds: -200, range: [-200, -198]"
        },
        {
            "name": "Mixed probabilities - INVALID (negative vs positive mismatch)",
            "sp_odds": -150,
            "leg_probabilities": [0.6, 0.7, 0.8],
            "expected_valid": False,
            "note": "Combined prob: 0.336 → odds: +198, doesn't match -150 range"
        },
        {
            "name": "Favorite 2-leg parlay - VALID (negative odds)",
            "sp_odds": -112,
            "leg_probabilities": [0.73, 0.7237],
            "expected_valid": True,
            "note": "Combined prob: 0.5283 → odds: -112, range: [-112, -111]"
        },
        {
            "name": "Out of range - INVALID (positive odds mismatch)",
            "sp_odds": +500,
            "leg_probabilities": [0.8, 0.8],
            "expected_valid": False,
            "note": "Combined prob: 0.64 → odds: -178, doesn't match +500 range"
        },
        {
            "name": "Out of range - INVALID (negative odds mismatch)",
            "sp_odds": -150,
            "leg_probabilities": [0.9, 0.9],
            "expected_valid": False,
            "note": "Combined prob: 0.81 → odds: -426, doesn't match -150 range"
        },
    ]
    
    passed = 0
    for i, test in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test['name']}")
        print(f"   Note: {test['note']}")
        print(f"   📤 REQUEST:")
        print(f"      sp_odds: {test['sp_odds']:+d}")
        print(f"      leg_probabilities: {test['leg_probabilities']}")
        
        result = validate_odds_with_probability(
            test['sp_odds'],
            test['leg_probabilities']
        )
        
        print(f"   📥 RESPONSE:")
        print(f"      valid: {result['valid']}")
        print(f"      calculated_probability: {result['calculated_probability']:.4f}")
        print(f"      calculated_odds: {result['calculated_odds']:+d}")
        print(f"      sp_odds: {result['sp_odds']:+d}")
        print(f"      odds_range: [{result['odds_range'][0]:+d}, {result['odds_range'][1]:+d}]")
        print(f"      explanation: {result['explanation']}")
        
        is_correct = result['valid'] == test['expected_valid']
        status = "✓" if is_correct else "✗"
        
        print(f"   {status} RESULT: Expected={'VALID' if test['expected_valid'] else 'INVALID'}, Got={'VALID' if result['valid'] else 'INVALID'}")
        
        if is_correct:
            passed += 1
    
    print(f"\n📊 Passed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def test_validate_price_probability():
    """Test the full price_probability validation"""
    print("\n" + "="*60)
    print("🧪 TEST: Validate Price Probability (Full Flow)")
    print("="*60)
    
    test_cases = [
        {
            "name": "Valid 2-leg parlay from requirement (positive odds)",
            "sp_odds": +377,
            "price_probability": [
                {
                    "vig": None,
                    "lines": [
                        {"line_id": "de27e08e8671600fad78ba041d26ae2f", "probability": 0.8160750396014694},
                        {"line_id": "f7a2855f7d0e470ba0e92531c2dd4263", "probability": 0.2570033410434336}
                    ],
                    "max_risk": 5499
                }
            ],
            "expected_valid": True
        },
        {
            "name": "Valid 3-leg parlay (positive odds)",
            "sp_odds": +700,
            "price_probability": [
                {
                    "lines": [
                        {"line_id": "line1", "probability": 0.5},
                        {"line_id": "line2", "probability": 0.5},
                        {"line_id": "line3", "probability": 0.5}
                    ],
                    "max_risk": 10000,
                    "vig": 0.1
                }
            ],
            "expected_valid": True
        },
        {
            "name": "Invalid favorite parlay (negative odds edge case)",
            "sp_odds": -110,
            "price_probability": [
                {
                    "lines": [
                        {"line_id": "line1", "probability": 0.7},
                        {"line_id": "line2", "probability": 0.75}
                    ],
                    "max_risk": 8000,
                    "vig": 0.05
                }
            ],
            "expected_valid": False
        },
        {
            "name": "Valid favorite parlay (negative odds)",
            "sp_odds": -112,
            "price_probability": [
                {
                    "lines": [
                        {"line_id": "line1", "probability": 0.73},
                        {"line_id": "line2", "probability": 0.7237}
                    ],
                    "max_risk": 8000,
                    "vig": 0.05
                }
            ],
            "expected_valid": True
        },
        {
            "name": "Valid heavy favorite parlay (negative odds)",
            "sp_odds": -200,
            "price_probability": [
                {
                    "lines": [
                        {"line_id": "line1", "probability": 0.8},
                        {"line_id": "line2", "probability": 0.833}
                    ],
                    "max_risk": 12000,
                    "vig": 0.08
                }
            ],
            "expected_valid": True
        },
        {
            "name": "Invalid - probabilities don't match positive odds",
            "sp_odds": +500,
            "price_probability": [
                {
                    "lines": [
                        {"line_id": "line1", "probability": 0.9},
                        {"line_id": "line2", "probability": 0.9}
                    ],
                    "max_risk": 5000,
                    "vig": 0.1
                }
            ],
            "expected_valid": False
        },
        {
            "name": "Invalid - probabilities don't match negative odds",
            "sp_odds": -150,
            "price_probability": [
                {
                    "lines": [
                        {"line_id": "line1", "probability": 0.9},
                        {"line_id": "line2", "probability": 0.9}
                    ],
                    "max_risk": 6000,
                    "vig": 0.1
                }
            ],
            "expected_valid": False
        },
        {
            "name": "Missing price_probability data",
            "sp_odds": +300,
            "price_probability": [],
            "expected_valid": False
        }
    ]
    
    passed = 0
    for i, test in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test['name']}")
        print(f"   📤 REQUEST:")
        print(f"      sp_odds: {test['sp_odds']:+d}")
        print(f"      price_probability: {test['price_probability']}")
        
        result = validate_price_probability(
            test['sp_odds'],
            test['price_probability']
        )
        
        print(f"   📥 RESPONSE:")
        if 'explanation' in result:
            print(f"      valid: {result['valid']}")
            print(f"      calculated_probability: {result.get('calculated_probability', 'N/A')}")
            print(f"      calculated_odds: {result.get('calculated_odds', 'N/A'):+d}" if isinstance(result.get('calculated_odds'), int) else f"      calculated_odds: N/A")
            print(f"      sp_odds: {result.get('sp_odds', 'N/A'):+d}" if isinstance(result.get('sp_odds'), int) else f"      sp_odds: N/A")
            print(f"      odds_range: {result.get('odds_range', 'N/A')}")
            print(f"      explanation: {result['explanation']}")
        elif 'error' in result:
            print(f"      valid: {result.get('valid', False)}")
            print(f"      error: {result['error']}")
        else:
            print(f"      {result}")
        
        is_correct = result.get('valid', False) == test['expected_valid']
        status = "✓" if is_correct else "✗"
        
        print(f"   {status} RESULT: Expected={'VALID' if test['expected_valid'] else 'INVALID'}, Got={'VALID' if result.get('valid', False) else 'INVALID'}")
        
        if is_correct:
            passed += 1
    
    print(f"\n📊 Passed: {passed}/{len(test_cases)}")
    return passed == len(test_cases)


def run_all_tests():
    """Run all test suites"""
    print("\n" + "🎯 " + "="*58)
    print("🎯 STARTING ODDS VALIDATION TEST SUITE")
    print("🎯 " + "="*58)
    
    results = []
    
    # Run each test suite
    results.append(("American → Probability", test_american_to_probability()))
    results.append(("Probability → American", test_probability_to_american()))
    results.append(("Find Odds Range", test_find_odds_range()))
    results.append(("Validate with Probability", test_validate_odds_with_probability()))
    results.append(("Validate Price Probability", test_validate_price_probability()))
    
    # Summary
    print("\n" + "🏁 " + "="*58)
    print("🏁 TEST SUMMARY")
    print("🏁 " + "="*58)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n📊 Overall: {passed_count}/{total_count} test suites passed")
    
    if passed_count == total_count:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("✓ Odds validation logic is working correctly")
        print("✓ Probability-based range validation implemented successfully")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} test suite(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

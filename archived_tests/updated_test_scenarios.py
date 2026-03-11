#!/usr/bin/env python3
"""
🧪 UPDATED TEST SCENARIOS WITH FRESH ACTIVE MARKET DATA
=======================================================

Based on fresh market data from the API, creating comprehensive test scenarios for:
1. Regular Parlay (2+ lines all from different events)
2. SGP (Same Game Parlay - 2+ lines with at least 2 from same event)

Fresh data retrieved from events: 19187,19188,19191,19192,19194,19193,19195,19044,19196,19046,19201,19197,19203,19200
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Fresh active market data
ACTIVE_MARKET_DATA = {
    # Event 19191: Tampa Bay Buccaneers vs New England Patriots
    "19191": {
        "event_name": "Tampa Bay Buccaneers vs New England Patriots",
        "spread": {
            "line_id_home": "04f2da44cbba365fd807c2bf6c5f09ab",  # TB -4.5
            "line_id_away": "ae8cabf43066a53bf376ab4ed3f886ec",  # NE +4.5
            "home_line": -4.5,
            "away_line": 4.5,
            "market_id": 223,
            "home_outcome_id": 1714,
            "away_outcome_id": 1715
        },
        "total": {
            "over_line_id": "59d4d1618c30fb8bbbcaf5d22b7f293a",  # Over 46.5
            "under_line_id": "605011a40f9bd31ac2864715688551d7",  # Under 46.5
            "line": 46.5,
            "market_id": 225,
            "over_outcome_id": 12,
            "under_outcome_id": 13
        },
        "moneyline": {
            "home_line_id": "adaac2f54f39fa21bbc983b6963e8863",  # TB
            "away_line_id": "4e8d0e70b902ea2ef4a261a9e5739a91",  # NE
            "market_id": 219,
            "home_outcome_id": 4,
            "away_outcome_id": 5
        }
    },
    
    # Event 19192: Seattle Seahawks vs Arizona Cardinals
    "19192": {
        "event_name": "Seattle Seahawks vs Arizona Cardinals",
        "spread": {
            "line_id_home": "b6cb5cf18a0148dfac0ae113e3ee6852",  # SEA -1.5
            "line_id_away": "798b6a347840daa0eda7374f8974b396",  # ARI +1.5
            "home_line": -1.5,
            "away_line": 1.5,
            "market_id": 223,
            "home_outcome_id": 1714,
            "away_outcome_id": 1715
        },
        "total": {
            "over_line_id": "ee01ddaa812ec54acb6affd9d1d6a0b1",  # Over 45.5
            "under_line_id": "b9e5e0e0b10685e6628b7f0ab372f2f6",  # Under 45.5
            "line": 45.5,
            "market_id": 225,
            "over_outcome_id": 12,
            "under_outcome_id": 13
        },
        "moneyline": {
            "home_line_id": "b13ea0fce285c5b5dbb800c47fe88019",  # SEA
            "away_line_id": "9d494145fe722733e7ab3e00c97bb8f0",  # ARI
            "market_id": 219,
            "home_outcome_id": 4,
            "away_outcome_id": 5
        }
    },
    
    # Event 19194: Washington Commanders vs Detroit Lions
    "19194": {
        "event_name": "Washington Commanders vs Detroit Lions",
        "spread": {
            "line_id_home": "ac39842c26c6fd2ceea6c11701d76dbf",  # WAS -1
            "line_id_away": "0771fb6a4573787372386ff9a0c1eec3",  # DET +1
            "home_line": -1,
            "away_line": 1,
            "market_id": 223,
            "home_outcome_id": 1714,
            "away_outcome_id": 1715
        },
        "total": {
            "over_line_id": "be5b47eaaa33b9c7d7671c40d44a7734",  # Over 50
            "under_line_id": "8a027433b3f150ce38714f237e04faf8",  # Under 50
            "line": 50,
            "market_id": 225,
            "over_outcome_id": 12,
            "under_outcome_id": 13
        }
    },
    
    # Event 19046: Miami Dolphins vs Washington Commanders
    "19046": {
        "event_name": "Miami Dolphins vs Washington Commanders",
        "spread": {
            "line_id_home": "5ad6be7be3834e70ae77113ca60ace77",  # MIA +4.5
            "line_id_away": "9d265d6a26e1127af542b1bbcf7a91fc",  # WAS -4.5
            "home_line": 4.5,
            "away_line": -4.5,
            "market_id": 223,
            "home_outcome_id": 1714,
            "away_outcome_id": 1715
        },
        "total": {
            "over_line_id": "a13ac1f0098ad0d0106d482749e847ab",  # Over 49
            "under_line_id": "b9bd7200d1fe70dadb901eeed130347b",  # Under 49
            "line": 49,
            "market_id": 225,
            "over_outcome_id": 12,
            "under_outcome_id": 13
        }
    }
}

# Test scenario configurations
TEST_SCENARIOS = {
    "regular_parlay_scenarios": [
        {
            "scenario_id": "PARLAY_01",
            "name": "Regular Parlay - Different Events Only",
            "description": "2 lines from completely different events",
            "market_lines": [
                {
                    "line": -4.5,
                    "lineId": "04f2da44cbba365fd807c2bf6c5f09ab",  # TB -4.5
                    "marketId": 223,
                    "outcomeId": 1714,
                    "sportEventId": 19191
                },
                {
                    "line": -1.5,
                    "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852",  # SEA -1.5
                    "marketId": 223,
                    "outcomeId": 1714,
                    "sportEventId": 19192
                }
            ],
            "expected_result": "SUCCESS - Regular parlay with different events"
        },
        
        {
            "scenario_id": "PARLAY_02",
            "name": "Regular Parlay - Mixed Markets",
            "description": "3 lines from different events, mixed market types",
            "market_lines": [
                {
                    "line": 46.5,
                    "lineId": "59d4d1618c30fb8bbbcaf5d22b7f293a",  # TB/NE Over 46.5
                    "marketId": 225,
                    "outcomeId": 12,
                    "sportEventId": 19191
                },
                {
                    "line": 0,
                    "lineId": "b13ea0fce285c5b5dbb800c47fe88019",  # SEA Moneyline
                    "marketId": 219,
                    "outcomeId": 4,
                    "sportEventId": 19192
                },
                {
                    "line": 50,
                    "lineId": "be5b47eaaa33b9c7d7671c40d44a7734",  # WAS/DET Over 50
                    "marketId": 225,
                    "outcomeId": 12,
                    "sportEventId": 19194
                }
            ],
            "expected_result": "SUCCESS - Mixed market types from different events"
        }
    ],
    
    "sgp_scenarios": [
        {
            "scenario_id": "SGP_01", 
            "name": "SGP - Same Event + Different Event",
            "description": "2 lines from same event + 1 line from different event",
            "market_lines": [
                {
                    "line": -4.5,
                    "lineId": "04f2da44cbba365fd807c2bf6c5f09ab",  # TB -4.5
                    "marketId": 223,
                    "outcomeId": 1714,
                    "sportEventId": 19191  # Same event
                },
                {
                    "line": 46.5,
                    "lineId": "59d4d1618c30fb8bbbcaf5d22b7f293a",  # TB/NE Over 46.5
                    "marketId": 225,
                    "outcomeId": 12,
                    "sportEventId": 19191  # Same event as above
                },
                {
                    "line": -1.5,
                    "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852",  # SEA -1.5
                    "marketId": 223,
                    "outcomeId": 1714,
                    "sportEventId": 19192  # Different event
                }
            ],
            "expected_result": "SUCCESS - SGP with same event correlations"
        },
        
        {
            "scenario_id": "SGP_02",
            "name": "SGP - Multiple Same Events",
            "description": "2 lines from event A + 2 lines from event B",
            "market_lines": [
                {
                    "line": -4.5,
                    "lineId": "04f2da44cbba365fd807c2bf6c5f09ab",  # TB -4.5
                    "marketId": 223,
                    "outcomeId": 1714,
                    "sportEventId": 19191  # Event A
                },
                {
                    "line": 0,
                    "lineId": "adaac2f54f39fa21bbc983b6963e8863",  # TB Moneyline
                    "marketId": 219,
                    "outcomeId": 4,
                    "sportEventId": 19191  # Event A (same as above)
                },
                {
                    "line": -1.5,
                    "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852",  # SEA -1.5
                    "marketId": 223,
                    "outcomeId": 1714,
                    "sportEventId": 19192  # Event B
                },
                {
                    "line": 45.5,
                    "lineId": "ee01ddaa812ec54acb6affd9d1d6a0b1",  # SEA/ARI Over 45.5
                    "marketId": 225,
                    "outcomeId": 12,
                    "sportEventId": 19192  # Event B (same as above)
                }
            ],
            "expected_result": "SUCCESS - Complex SGP with multiple correlations"
        },
        
        {
            "scenario_id": "SGP_03",
            "name": "SGP - Heavy Same Event Focus",
            "description": "3 lines from same event + 1 from different event",
            "market_lines": [
                {
                    "line": -4.5,
                    "lineId": "04f2da44cbba365fd807c2bf6c5f09ab",  # TB -4.5
                    "marketId": 223,
                    "outcomeId": 1714,
                    "sportEventId": 19191  # Same event
                },
                {
                    "line": 46.5,
                    "lineId": "59d4d1618c30fb8bbbcaf5d22b7f293a",  # TB/NE Over 46.5
                    "marketId": 225,
                    "outcomeId": 12,
                    "sportEventId": 19191  # Same event
                },
                {
                    "line": 0,
                    "lineId": "adaac2f54f39fa21bbc983b6963e8863",  # TB Moneyline
                    "marketId": 219,
                    "outcomeId": 4,
                    "sportEventId": 19191  # Same event
                },
                {
                    "line": 49,
                    "lineId": "a13ac1f0098ad0d0106d482749e847ab",  # MIA/WAS Over 49
                    "marketId": 225,
                    "outcomeId": 12,
                    "sportEventId": 19046  # Different event
                }
            ],
            "expected_result": "SUCCESS - Heavy SGP correlation testing"
        }
    ]
}

def get_user_token():
    """Get fresh user token"""
    url = "https://api-ss-sandbox.betprophet.co/api/v1/auth/login"
    payload = {
        "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
        "email": "lam.tran+usr004@betprophet.co",
        "password": "Kh0ngbiet1"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get("accessToken")
    return None

def test_parlay_scenario(scenario):
    """Test a single parlay scenario"""
    logger.info(f"\n🧪 TESTING {scenario['scenario_id']}: {scenario['name']}")
    logger.info("=" * 80)
    logger.info(f"📋 {scenario['description']}")
    
    # Get fresh user token
    user_token = get_user_token()
    if not user_token:
        logger.error("❌ Failed to get user token")
        return False
    
    # Create parlay request
    url = "https://api-ss-sandbox.betprophet.co/parlay/api/v1/user/request"
    payload = {"marketLines": scenario["market_lines"]}
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    logger.info(f"📤 PARLAY REQUEST:")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        logger.info(f"\n📥 PARLAY RESPONSE:")
        logger.info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            parlay_id = response_data.get("data", {}).get("parlayId")
            logger.info(f"✅ SUCCESS: Parlay created with ID: {parlay_id}")
            logger.info(f"Expected: {scenario['expected_result']}")
            return True
        else:
            try:
                error_data = response.json()
                logger.error(f"❌ FAILED: {error_data}")
            except:
                logger.error(f"❌ FAILED: Status {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ EXCEPTION: {str(e)}")
        return False

def run_all_test_scenarios():
    """Run all test scenarios"""
    logger.info("🚀 STARTING COMPREHENSIVE PARLAY & SGP TEST SCENARIOS")
    logger.info("=" * 100)
    logger.info("📊 Using FRESH ACTIVE MARKET DATA from live API")
    logger.info("=" * 100)
    
    results = {
        "regular_parlay": {"passed": 0, "total": 0},
        "sgp": {"passed": 0, "total": 0}
    }
    
    # Test Regular Parlay scenarios
    logger.info("\n📋 REGULAR PARLAY SCENARIOS (Different Events Only)")
    logger.info("-" * 70)
    for scenario in TEST_SCENARIOS["regular_parlay_scenarios"]:
        results["regular_parlay"]["total"] += 1
        if test_parlay_scenario(scenario):
            results["regular_parlay"]["passed"] += 1
    
    # Test SGP scenarios
    logger.info("\n📋 SGP SCENARIOS (Same Event + Different Events)")
    logger.info("-" * 70)
    for scenario in TEST_SCENARIOS["sgp_scenarios"]:
        results["sgp"]["total"] += 1
        if test_parlay_scenario(scenario):
            results["sgp"]["passed"] += 1
    
    # Results summary
    logger.info("\n" + "=" * 100)
    logger.info("🏁 COMPREHENSIVE TEST RESULTS SUMMARY")
    logger.info("=" * 100)
    logger.info(f"📊 Regular Parlay Tests: {results['regular_parlay']['passed']}/{results['regular_parlay']['total']} passed")
    logger.info(f"📊 SGP Tests: {results['sgp']['passed']}/{results['sgp']['total']} passed")
    
    total_passed = results['regular_parlay']['passed'] + results['sgp']['passed']
    total_tests = results['regular_parlay']['total'] + results['sgp']['total']
    logger.info(f"📊 OVERALL: {total_passed}/{total_tests} scenarios passed")
    
    if total_passed == total_tests:
        logger.info("✅ ALL TESTS PASSED! Ready for comprehensive test suite execution.")
    else:
        logger.info("⚠️  Some tests failed. Check market data freshness and API status.")
    
    return results

if __name__ == "__main__":
    run_all_test_scenarios()
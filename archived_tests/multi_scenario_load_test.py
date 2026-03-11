#!/usr/bin/env python3
"""
🎯 MULTI-SCENARIO PARLAY LOAD TEST - ALL 4 SUCCESS CASES x 5 ITERATIONS

Comprehensive load testing that runs all successful scenarios in each iteration:
- Scenario 1: Basic Single SP Success
- Scenario 4: Complete Multi-Tier Success  
- Scenario 8: No SP Responses (graceful failure)
- Scenario 10: Stake Exceeds SP Capacity (partial fill)

5 iterations total, with each iteration running all 4 scenarios
Provides detailed performance analysis and success rate reporting
"""

import requests
import json
import time
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import threading
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'multi_scenario_load_test_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ScenarioResult:
    scenario: str
    iteration: int
    success: bool
    total_time: float
    steps: Dict[str, float]
    error: Optional[str] = None
    details: Optional[Dict] = None

class MultiScenarioLoadTest:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        
        # Working SP Credentials
        self.sp1_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        
        self.sp2_credentials = {
            "access_key": "ec45827afa933f97ec19e674c0fa39c6",
            "secret_key": "442df8e9fe96e4f7e744b2d3cac5cd51"
        }
        
        # Working market lines data
        self.market_lines = [
            {
                "line": 2,
                "lineId": "01e69752c33c3835e18578752565934a",
                "marketId": 223,
                "outcomeId": 1714,
                "sportEventId": 19167
            },
            {
                "line": 0,
                "lineId": "b823a3699ec9461c8cebec1b5724dfa0",
                "marketId": 219,
                "outcomeId": 4,
                "sportEventId": 19167
            }
        ]
        
        # Performance tracking
        self.response_times = {
            'auth': [],
            'create_parlay': [],
            'sp_offer': [],
            'user_confirm': [],
            'sp_accept': [],
            'user_view': []
        }
        self.lock = threading.Lock()
        
        # Scenario definitions
        self.scenarios = {
            "scenario_1": "Basic Single SP Success",
            "scenario_4": "Complete Multi-Tier Success", 
            "scenario_8": "No SP Responses (Graceful Failure)",
            "scenario_10": "Stake Exceeds SP Capacity (Partial Fill)"
        }

    def get_user_token(self) -> Tuple[str, float]:
        """Get user authentication token with timing"""
        url = f"{self.base_url}/api/v1/auth/login"
        payload = {
            "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
            "email": "lam.tran+usr004@betprophet.co",
            "password": "Kh0ngbiet1"
        }
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['auth'].append(response_time)
            
            if response.status_code == 200:
                token = response.json().get("accessToken")
                return token, response_time
            else:
                return "fallback_token", response_time
        except Exception as e:
            return "fallback_token", time.time() - start_time

    def authenticate_sp(self, credentials: Dict[str, str]) -> Tuple[Optional[str], float]:
        """Authenticate SP with timing"""
        url = f"{self.base_url}/partner/auth/login"
        
        start_time = time.time()
        try:
            response = requests.post(url, json=credentials, headers={
                "Content-Type": "application/json"
            })
            
            response_time = time.time() - start_time
            with self.lock:
                self.response_times['auth'].append(response_time)
            
            if response.status_code == 200:
                token = response.json()["data"]["access_token"]
                return token, response_time
            else:
                return None, response_time
                
        except Exception as e:
            return None, time.time() - start_time

    def create_parlay(self, user_token: str) -> Tuple[Optional[str], float]:
        """Create parlay with timing"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        
        payload = {"marketLines": self.market_lines}
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['create_parlay'].append(response_time)
            
            if response.status_code == 200:
                parlay_id = response.json()["data"]["parlayId"]
                return parlay_id, response_time
            else:
                return None, response_time
                
        except Exception as e:
            return None, time.time() - start_time

    def sp_offer(self, parlay_id: str, sp_token: str, odds: int, max_risk: int) -> Tuple[bool, float]:
        """SP provides offer with timing"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        
        valid_until = int((time.time() + 60) * 1e9)
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": odds,
                    "max_risk": max_risk,
                    "valid_until": valid_until,
                    "estimated_prices": [
                        {"line_id": "01e69752c33c3835e18578752565934a", "odds": odds},
                        {"line_id": "b823a3699ec9461c8cebec1b5724dfa0", "odds": odds}
                    ]
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {sp_token}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['sp_offer'].append(response_time)
            
            return response.status_code == 200, response_time
            
        except Exception as e:
            return False, time.time() - start_time

    def user_confirm(self, parlay_id: str, user_token: str, odds: int, stake: int) -> Tuple[bool, float]:
        """User confirms bet with timing"""
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        
        payload = {
            "parlayId": parlay_id,
            "odds": odds,
            "stake": stake
        }
        
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['user_confirm'].append(response_time)
            
            return response.status_code == 200, response_time
            
        except Exception as e:
            return False, time.time() - start_time

    def sp_accept(self, sp_token: str, parlay_id: str, stake: int, odds: int) -> Tuple[bool, float]:
        """SP accepts confirmation with timing"""
        # Get order UUID
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        start_time = time.time()
        try:
            orders_response = requests.get(orders_url, headers=headers)
            if orders_response.status_code != 200:
                return False, time.time() - start_time
            
            orders_data = orders_response.json()
            target_order = None
            
            for order in orders_data["data"]["orders"]:
                if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
                    target_order = order
                    break
            
            if not target_order:
                return False, time.time() - start_time
            
            order_uuid = target_order["order_uuid"]
            
            # Accept the confirmation
            url = f"{self.base_url}/parlay/sp/orders/confirmations"
            params = {"order_uuid": order_uuid}
            
            probability = 100.0 / (odds + 100.0) if odds > 0 else abs(odds) / (abs(odds) + 100.0)
            max_risk_cents = int((stake * probability) * 100)
            
            payload = {
                "action": "accept",
                "confirmed_stake": stake,
                "price_probability": [
                    {
                        "lines": [
                            {"line_id": "01e69752c33c3835e18578752565934a", "probability": probability},
                            {"line_id": "b823a3699ec9461c8cebec1b5724dfa0", "probability": probability}
                        ],
                        "max_risk": max_risk_cents,
                        "vig": 0.1
                    }
                ],
                "signature": "test_signature_multi_scenario"
            }
            
            response = requests.post(url, json=payload, headers=headers, params=params)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['sp_accept'].append(response_time)
            
            return response.status_code == 200, response_time
            
        except Exception as e:
            return False, time.time() - start_time

    def verify_user_view(self, user_token: str, parlay_id: str) -> Tuple[List[Dict], float]:
        """Verify user view and return matching parlays"""
        url = f"{self.base_url}/parlay/api/v1/user/list?limit=50"
        headers = {"Authorization": f"Bearer {user_token}"}
        
        start_time = time.time()
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    matching_parlays = [
                        order for order in user_data["data"]["orders"]
                        if order["parlayId"] == parlay_id
                    ]
                    
                    if matching_parlays or attempt == max_attempts - 1:
                        response_time = time.time() - start_time
                        with self.lock:
                            self.response_times['user_view'].append(response_time)
                        return matching_parlays, response_time
                    
                    time.sleep(2)
                        
            except Exception as e:
                if attempt == max_attempts - 1:
                    break
                time.sleep(2)
                
        response_time = time.time() - start_time
        with self.lock:
            self.response_times['user_view'].append(response_time)
        return [], response_time

    def run_scenario_1(self, iteration: int) -> ScenarioResult:
        """Scenario 1: Basic Single SP Success"""
        scenario = "scenario_1"
        logger.info(f"  🔄 S1: Basic Single SP Success")
        
        test_start = time.time()
        steps = {}
        
        try:
            # Get tokens
            user_token, step_time = self.get_user_token()
            steps['user_auth'] = step_time
            if user_token == "fallback_token":
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "User auth failed")
            
            sp1_token, step_time = self.authenticate_sp(self.sp1_credentials)
            steps['sp_auth'] = step_time
            if not sp1_token:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "SP auth failed")
            
            # Create parlay
            parlay_id, step_time = self.create_parlay(user_token)
            steps['create_parlay'] = step_time
            if not parlay_id:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "Create parlay failed")
            
            # SP offer
            offer_success, step_time = self.sp_offer(parlay_id, sp1_token, 800, 200)
            steps['sp_offer'] = step_time
            if not offer_success:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "SP offer failed")
            
            # User confirm
            confirm_success, step_time = self.user_confirm(parlay_id, user_token, 800, 100)
            steps['user_confirm'] = step_time
            if not confirm_success:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "User confirm failed")
            
            time.sleep(3)
            
            # SP accept
            accept_success, step_time = self.sp_accept(sp1_token, parlay_id, 100, 800)
            steps['sp_accept'] = step_time
            if not accept_success:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "SP accept failed")
            
            # Verify
            parlays, step_time = self.verify_user_view(user_token, parlay_id)
            steps['user_view'] = step_time
            
            finalized_parlays = [p for p in parlays if p.get("status") == "finalized"]
            success = len(finalized_parlays) >= 1
            
            details = {
                "parlay_id": parlay_id,
                "finalized_count": len(finalized_parlays),
                "total_parlays": len(parlays)
            }
            
            return ScenarioResult(scenario, iteration, success, time.time() - test_start, steps, 
                                None if success else "No finalized parlays", details)
            
        except Exception as e:
            return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, f"Exception: {str(e)}")

    def run_scenario_4(self, iteration: int) -> ScenarioResult:
        """Scenario 4: Complete Multi-Tier Success"""
        scenario = "scenario_4"
        logger.info(f"  🔄 S4: Complete Multi-Tier Success")
        
        test_start = time.time()
        steps = {}
        
        try:
            # Get tokens
            user_token, step_time = self.get_user_token()
            steps['user_auth'] = step_time
            if user_token == "fallback_token":
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "User auth failed")
            
            sp1_token, step_time1 = self.authenticate_sp(self.sp1_credentials)
            sp2_token, step_time2 = self.authenticate_sp(self.sp2_credentials)
            steps['sp_auth'] = max(step_time1, step_time2)
            if not sp1_token or not sp2_token:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "SP auth failed")
            
            # Create parlay
            parlay_id, step_time = self.create_parlay(user_token)
            steps['create_parlay'] = step_time
            if not parlay_id:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "Create parlay failed")
            
            # Both SP offers
            sp1_offer, step_time1 = self.sp_offer(parlay_id, sp1_token, 850, 100)  # Best odds, limited capacity
            sp2_offer, step_time2 = self.sp_offer(parlay_id, sp2_token, 800, 150)  # Second tier
            steps['sp_offer'] = max(step_time1, step_time2)
            if not sp1_offer or not sp2_offer:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "SP offers failed")
            
            # User confirm (high stake requiring both tiers)
            confirm_success, step_time = self.user_confirm(parlay_id, user_token, 850, 200)
            steps['user_confirm'] = step_time
            if not confirm_success:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "User confirm failed")
            
            time.sleep(3)
            
            # Both SPs accept
            sp1_accept, step_time1 = self.sp_accept(sp1_token, parlay_id, 100, 850)
            sp2_accept, step_time2 = self.sp_accept(sp2_token, parlay_id, 100, 800)
            steps['sp_accept'] = max(step_time1, step_time2)
            
            # Verify
            parlays, step_time = self.verify_user_view(user_token, parlay_id)
            steps['user_view'] = step_time
            
            finalized_parlays = [p for p in parlays if p.get("status") == "finalized"]
            success = sp1_accept and sp2_accept and len(finalized_parlays) >= 2
            
            details = {
                "parlay_id": parlay_id,
                "sp1_accept": sp1_accept,
                "sp2_accept": sp2_accept,
                "finalized_count": len(finalized_parlays),
                "total_parlays": len(parlays)
            }
            
            return ScenarioResult(scenario, iteration, success, time.time() - test_start, steps,
                                None if success else "Multi-tier matching failed", details)
            
        except Exception as e:
            return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, f"Exception: {str(e)}")

    def run_scenario_8(self, iteration: int) -> ScenarioResult:
        """Scenario 8: No SP Responses (Graceful Failure)"""
        scenario = "scenario_8"
        logger.info(f"  🔄 S8: No SP Responses (Graceful Failure)")
        
        test_start = time.time()
        steps = {}
        
        try:
            # Get user token only
            user_token, step_time = self.get_user_token()
            steps['user_auth'] = step_time
            if user_token == "fallback_token":
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "User auth failed")
            
            # Create parlay without SP offers
            parlay_id, step_time = self.create_parlay(user_token)
            steps['create_parlay'] = step_time
            if not parlay_id:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "Create parlay failed")
            
            # Wait for potential offers (none expected)
            time.sleep(5)
            steps['wait_time'] = 5.0
            
            # Attempt user confirmation without offers (should fail gracefully)
            confirm_success, step_time = self.user_confirm(parlay_id, user_token, 800, 100)
            steps['user_confirm'] = step_time
            
            # Success criteria: Confirmation should fail gracefully
            success = not confirm_success
            
            details = {
                "parlay_id": parlay_id,
                "confirm_attempted": True,
                "confirm_success": confirm_success,
                "expected_failure": True
            }
            
            return ScenarioResult(scenario, iteration, success, time.time() - test_start, steps,
                                None if success else "Expected failure did not occur", details)
            
        except Exception as e:
            return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, f"Exception: {str(e)}")

    def run_scenario_10(self, iteration: int) -> ScenarioResult:
        """Scenario 10: Stake Exceeds SP Capacity (Partial Fill)"""
        scenario = "scenario_10"
        logger.info(f"  🔄 S10: Stake Exceeds SP Capacity (Partial Fill)")
        
        test_start = time.time()
        steps = {}
        
        try:
            # Get tokens
            user_token, step_time = self.get_user_token()
            steps['user_auth'] = step_time
            if user_token == "fallback_token":
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "User auth failed")
            
            sp1_token, step_time1 = self.authenticate_sp(self.sp1_credentials)
            sp2_token, step_time2 = self.authenticate_sp(self.sp2_credentials)
            steps['sp_auth'] = max(step_time1, step_time2)
            if not sp1_token or not sp2_token:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "SP auth failed")
            
            # Create parlay
            parlay_id, step_time = self.create_parlay(user_token)
            steps['create_parlay'] = step_time
            if not parlay_id:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "Create parlay failed")
            
            # Limited capacity offers
            sp1_offer, step_time1 = self.sp_offer(parlay_id, sp1_token, 800, 150)  # $150 max
            sp2_offer, step_time2 = self.sp_offer(parlay_id, sp2_token, 800, 150)  # $150 max
            steps['sp_offer'] = max(step_time1, step_time2)
            if not sp1_offer or not sp2_offer:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "SP offers failed")
            
            # User requests stake beyond capacity (500 > 300 total)
            confirm_success, step_time = self.user_confirm(parlay_id, user_token, 800, 500)
            steps['user_confirm'] = step_time
            if not confirm_success:
                return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, "User confirm failed")
            
            time.sleep(3)
            
            # SPs accept what they can (partial fills)
            sp1_accept, step_time1 = self.sp_accept(sp1_token, parlay_id, 150, 800)
            sp2_accept, step_time2 = self.sp_accept(sp2_token, parlay_id, 150, 800)
            steps['sp_accept'] = max(step_time1, step_time2)
            
            # Verify
            parlays, step_time = self.verify_user_view(user_token, parlay_id)
            steps['user_view'] = step_time
            
            finalized_parlays = [p for p in parlays if p.get("status") == "finalized"]
            total_confirmed_stake = sum(p.get("confirmedStake", 0) for p in finalized_parlays)
            
            # Success: Partial match (≤300), doesn't fail entirely
            success = sp1_accept and sp2_accept and total_confirmed_stake <= 300 and len(finalized_parlays) >= 2
            
            details = {
                "parlay_id": parlay_id,
                "sp1_accept": sp1_accept,
                "sp2_accept": sp2_accept,
                "finalized_count": len(finalized_parlays),
                "total_confirmed_stake": total_confirmed_stake,
                "requested_stake": 500
            }
            
            return ScenarioResult(scenario, iteration, success, time.time() - test_start, steps,
                                None if success else "Partial fill failed", details)
            
        except Exception as e:
            return ScenarioResult(scenario, iteration, False, time.time() - test_start, steps, f"Exception: {str(e)}")

    def run_iteration(self, iteration: int) -> List[ScenarioResult]:
        """Run all 4 scenarios in a single iteration"""
        logger.info(f"\n🚀 ITERATION {iteration}: Running All 4 Scenarios")
        
        results = []
        
        # Run all scenarios
        results.append(self.run_scenario_1(iteration))
        time.sleep(1)  # Brief pause between scenarios
        
        results.append(self.run_scenario_4(iteration))
        time.sleep(1)
        
        results.append(self.run_scenario_8(iteration))
        time.sleep(1)
        
        results.append(self.run_scenario_10(iteration))
        
        # Log iteration summary
        successes = sum(1 for r in results if r.success)
        logger.info(f"  📊 Iteration {iteration}: {successes}/4 scenarios successful")
        
        return results

    def run_load_test(self, iterations: int = 5) -> Dict[str, Any]:
        """Run complete load test with all scenarios"""
        logger.info(f"\n{'='*120}")
        logger.info(f"🎯 MULTI-SCENARIO PARLAY LOAD TEST - ALL 4 SUCCESS CASES")
        logger.info(f"Started at: {datetime.now().isoformat()}")
        logger.info(f"Iterations: {iterations} (each running all 4 scenarios)")
        logger.info("="*120)
        
        test_start_time = time.time()
        all_results = []
        
        # Run iterations
        for i in range(iterations):
            iteration_results = self.run_iteration(i + 1)
            all_results.extend(iteration_results)
            
            if i < iterations - 1:  # Don't sleep after last iteration
                time.sleep(2)
        
        total_test_time = time.time() - test_start_time
        
        # Analyze and report
        analysis = self.analyze_results(all_results, total_test_time, iterations)
        self.generate_report(analysis)
        
        return analysis

    def analyze_results(self, results: List[ScenarioResult], total_time: float, iterations: int) -> Dict[str, Any]:
        """Comprehensive analysis of all results"""
        
        # Group by scenario
        scenario_groups = {}
        for result in results:
            if result.scenario not in scenario_groups:
                scenario_groups[result.scenario] = []
            scenario_groups[result.scenario].append(result)
        
        analysis = {
            'test_config': {
                'iterations': iterations,
                'scenarios_per_iteration': 4,
                'total_tests': len(results),
                'total_test_time': total_time
            },
            'overall': {
                'total_tests': len(results),
                'successful_tests': len([r for r in results if r.success]),
                'failed_tests': len([r for r in results if not r.success]),
                'overall_success_rate': len([r for r in results if r.success]) / len(results) * 100
            },
            'scenario_analysis': {},
            'iteration_analysis': {},
            'response_times': {},
            'failure_analysis': {}
        }
        
        # Scenario-specific analysis
        for scenario, scenario_results in scenario_groups.items():
            successful = [r for r in scenario_results if r.success]
            failed = [r for r in scenario_results if not r.success]
            
            analysis['scenario_analysis'][scenario] = {
                'name': self.scenarios.get(scenario, scenario),
                'total': len(scenario_results),
                'successful': len(successful),
                'failed': len(failed),
                'success_rate': len(successful) / len(scenario_results) * 100,
                'avg_time': statistics.mean([r.total_time for r in scenario_results]),
                'min_time': min([r.total_time for r in scenario_results]),
                'max_time': max([r.total_time for r in scenario_results]),
                'std_dev': statistics.stdev([r.total_time for r in scenario_results]) if len(scenario_results) > 1 else 0
            }
        
        # Iteration analysis
        for i in range(1, iterations + 1):
            iteration_results = [r for r in results if r.iteration == i]
            successful_in_iteration = len([r for r in iteration_results if r.success])
            
            analysis['iteration_analysis'][i] = {
                'total_scenarios': len(iteration_results),
                'successful_scenarios': successful_in_iteration,
                'success_rate': successful_in_iteration / len(iteration_results) * 100,
                'total_time': sum([r.total_time for r in iteration_results])
            }
        
        # Response time analysis
        for step, times in self.response_times.items():
            if times:
                analysis['response_times'][step] = {
                    'count': len(times),
                    'average': statistics.mean(times),
                    'median': statistics.median(times),
                    'min': min(times),
                    'max': max(times),
                    'std_dev': statistics.stdev(times) if len(times) > 1 else 0
                }
        
        # Failure analysis
        failed_results = [r for r in results if not r.success]
        for result in failed_results:
            error = result.error or 'Unknown error'
            key = f"{result.scenario}:{error}"
            analysis['failure_analysis'][key] = analysis['failure_analysis'].get(key, 0) + 1
        
        return analysis

    def generate_report(self, analysis: Dict[str, Any]):
        """Generate comprehensive load test report"""
        logger.info(f"\n{'='*120}")
        logger.info("📋 COMPREHENSIVE LOAD TEST REPORT")
        logger.info("="*120)
        
        # Test Configuration
        config = analysis['test_config']
        logger.info(f"🎯 TEST CONFIGURATION:")
        logger.info(f"   Iterations: {config['iterations']}")
        logger.info(f"   Scenarios per iteration: {config['scenarios_per_iteration']}")
        logger.info(f"   Total tests executed: {config['total_tests']}")
        logger.info(f"   Total test time: {config['total_test_time']:.2f}s")
        logger.info(f"   Average time per iteration: {config['total_test_time'] / config['iterations']:.2f}s")
        
        # Overall Results
        overall = analysis['overall']
        logger.info(f"\n📊 OVERALL RESULTS:")
        logger.info(f"   Total Tests: {overall['total_tests']}")
        logger.info(f"   Successful: {overall['successful_tests']}")
        logger.info(f"   Failed: {overall['failed_tests']}")
        logger.info(f"   Overall Success Rate: {overall['overall_success_rate']:.1f}%")
        
        # Scenario-Specific Results
        logger.info(f"\n🎭 SCENARIO-SPECIFIC ANALYSIS:")
        for scenario, data in analysis['scenario_analysis'].items():
            logger.info(f"   {data['name'].upper()}:")
            logger.info(f"     Success Rate: {data['success_rate']:.1f}% ({data['successful']}/{data['total']})")
            logger.info(f"     Avg Time: {data['avg_time']:.2f}s")
            logger.info(f"     Time Range: {data['min_time']:.2f}s - {data['max_time']:.2f}s")
            logger.info(f"     Std Dev: {data['std_dev']:.2f}s")
        
        # Iteration Analysis
        logger.info(f"\n🔄 ITERATION-BY-ITERATION ANALYSIS:")
        for iteration, data in analysis['iteration_analysis'].items():
            logger.info(f"   Iteration {iteration}:")
            logger.info(f"     Success Rate: {data['success_rate']:.1f}% ({data['successful_scenarios']}/{data['total_scenarios']})")
            logger.info(f"     Total Time: {data['total_time']:.2f}s")
        
        # Response Time Analysis
        logger.info(f"\n⚡ RESPONSE TIME ANALYSIS:")
        for step, metrics in analysis['response_times'].items():
            logger.info(f"   {step.upper()}:")
            logger.info(f"     Average: {metrics['average']:.3f}s ({metrics['count']} calls)")
            logger.info(f"     Range: {metrics['min']:.3f}s - {metrics['max']:.3f}s")
            logger.info(f"     Std Dev: {metrics['std_dev']:.3f}s")
        
        # Failure Analysis
        if analysis['failure_analysis']:
            logger.info(f"\n❌ FAILURE ANALYSIS:")
            for failure, count in analysis['failure_analysis'].items():
                logger.info(f"   {failure}: {count} occurrences")
        else:
            logger.info(f"\n✅ NO FAILURES DETECTED")
        
        # Performance Insights
        logger.info(f"\n🔍 PERFORMANCE INSIGHTS:")
        
        # Overall system stability
        if overall['overall_success_rate'] >= 95:
            logger.info("   ✅ EXCELLENT: System is highly stable under load")
        elif overall['overall_success_rate'] >= 85:
            logger.info("   ✅ GOOD: System shows good stability with minor issues")
        elif overall['overall_success_rate'] >= 70:
            logger.info("   ⚠️  MODERATE: System has stability concerns that should be addressed")
        else:
            logger.info("   ❌ POOR: System shows significant stability issues under load")
        
        # Scenario reliability comparison
        scenario_rates = [(s, data['success_rate']) for s, data in analysis['scenario_analysis'].items()]
        scenario_rates.sort(key=lambda x: x[1], reverse=True)
        
        logger.info("   📈 SCENARIO RELIABILITY RANKING:")
        for i, (scenario, rate) in enumerate(scenario_rates, 1):
            scenario_name = analysis['scenario_analysis'][scenario]['name']
            logger.info(f"     {i}. {scenario_name}: {rate:.1f}%")
        
        # Response time performance
        avg_response_time = statistics.mean([
            metrics['average'] for metrics in analysis['response_times'].values()
        ])
        
        if avg_response_time < 1.0:
            logger.info("   ⚡ EXCELLENT: Response times are optimal across all operations")
        elif avg_response_time < 2.0:
            logger.info("   ✅ GOOD: Response times are acceptable for production use")
        else:
            logger.info("   ⚠️  SLOW: Response times may impact user experience")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        
        most_reliable = max(scenario_rates, key=lambda x: x[1])
        least_reliable = min(scenario_rates, key=lambda x: x[1])
        
        if most_reliable[1] - least_reliable[1] > 20:
            logger.info(f"   • Focus on improving reliability of {analysis['scenario_analysis'][least_reliable[0]]['name']}")
        
        if avg_response_time > 1.5:
            logger.info("   • Consider optimizing API response times")
        
        if overall['overall_success_rate'] < 90:
            logger.info("   • Investigate and resolve stability issues before production deployment")
        
        logger.info(f"\nCompleted at: {datetime.now().isoformat()}")
        logger.info(f"📁 Full logs saved to: multi_scenario_load_test_{int(time.time())}.log")

def main():
    """Main load test runner"""
    load_test = MultiScenarioLoadTest()
    
    # Run 5 iterations of all 4 successful scenarios
    results = load_test.run_load_test(iterations=5)
    
    return results

if __name__ == "__main__":
    main()
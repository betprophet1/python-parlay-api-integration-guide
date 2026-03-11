#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE PARLAY LOAD TEST - MULTIPLE SCENARIOS x 10 ITERATIONS

Advanced load testing that runs multiple successful scenarios:
- Scenario 1: Basic Single SP Success (most reliable)
- Scenario 4: Complete Multi-Tier Success (when both SPs work)
- Configurable iterations per scenario
- Concurrent and sequential execution modes
- Detailed performance analytics and bottleneck identification
- System stability and reliability testing
"""

import requests
import json
import time
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import concurrent.futures
import threading
from dataclasses import dataclass
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'comprehensive_load_test_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    scenario: str
    iteration: int
    success: bool
    total_time: float
    steps: Dict[str, float]
    error: Optional[str] = None
    parlay_id: Optional[str] = None

class ComprehensiveLoadTest:
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
        self.test_results = []
        self.response_times = {
            'auth': [],
            'create_parlay': [],
            'sp_offer': [],
            'user_confirm': [],
            'sp_accept': [],
            'user_view': []
        }
        self.lock = threading.Lock()
        
        # Test configurations
        self.scenarios = {
            "single_sp_success": "Basic Single SP Success - Most Reliable",
            "multi_tier_success": "Complete Multi-Tier Success - Both SPs Accept"
        }

    def log_step(self, step: str, status_code: int = None, error: str = None):
        """Minimal logging for load test performance"""
        if error:
            logger.warning(f"{step}: ❌ {error}")
        elif status_code == 200:
            logger.info(f"{step}: ✅")
        else:
            logger.warning(f"{step}: ⚠️  {status_code}")

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
                "signature": "test_signature_load_test"
            }
            
            response = requests.post(url, json=payload, headers=headers, params=params)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['sp_accept'].append(response_time)
            
            return response.status_code == 200, response_time
            
        except Exception as e:
            return False, time.time() - start_time

    def verify_user_view(self, user_token: str, parlay_id: str) -> Tuple[int, float]:
        """Verify user view and count finalized parlays"""
        url = f"{self.base_url}/parlay/api/v1/user/list?limit=50"
        headers = {"Authorization": f"Bearer {user_token}"}
        
        start_time = time.time()
        max_attempts = 3  # Reduced for load test
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    matching_parlays = [
                        order for order in user_data["data"]["orders"]
                        if order["parlayId"] == parlay_id
                    ]
                    
                    finalized_parlays = [p for p in matching_parlays if p.get("status") == "finalized"]
                    
                    if finalized_parlays:
                        response_time = time.time() - start_time
                        with self.lock:
                            self.response_times['user_view'].append(response_time)
                        return len(finalized_parlays), response_time
                    
                    if attempt < max_attempts - 1:
                        time.sleep(2)  # Shorter wait for load test
                        
            except Exception as e:
                if attempt == max_attempts - 1:
                    break
                time.sleep(2)
                
        response_time = time.time() - start_time
        with self.lock:
            self.response_times['user_view'].append(response_time)
        return 0, response_time

    def run_single_sp_scenario(self, iteration: int) -> TestResult:
        """Run single SP success scenario"""
        scenario = "single_sp_success"
        logger.info(f"🔄 {scenario.upper()} - Iteration {iteration}")
        
        test_start = time.time()
        steps = {}
        
        try:
            # Step 1: User auth
            user_token, step_time = self.get_user_token()
            steps['user_auth'] = step_time
            if user_token == "fallback_token":
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "User auth failed")
            
            # Step 2: SP auth
            sp_token, step_time = self.authenticate_sp(self.sp1_credentials)
            steps['sp_auth'] = step_time
            if not sp_token:
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "SP auth failed")
            
            # Step 3: Create parlay
            parlay_id, step_time = self.create_parlay(user_token)
            steps['create_parlay'] = step_time
            if not parlay_id:
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "Create parlay failed")
            
            # Step 4: SP offer
            offer_success, step_time = self.sp_offer(parlay_id, sp_token, 800, 200)
            steps['sp_offer'] = step_time
            if not offer_success:
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "SP offer failed")
            
            # Step 5: User confirm
            confirm_success, step_time = self.user_confirm(parlay_id, user_token, 800, 100)
            steps['user_confirm'] = step_time
            if not confirm_success:
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "User confirm failed")
            
            # Wait for processing
            time.sleep(3)
            
            # Step 6: SP accept
            accept_success, step_time = self.sp_accept(sp_token, parlay_id, 100, 800)
            steps['sp_accept'] = step_time
            if not accept_success:
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "SP accept failed")
            
            # Step 7: Verify
            finalized_count, step_time = self.verify_user_view(user_token, parlay_id)
            steps['user_view'] = step_time
            
            success = finalized_count >= 1
            total_time = time.time() - test_start
            
            if success:
                logger.info(f"✅ {scenario.upper()} - Iteration {iteration}: SUCCESS ({finalized_count} parlays)")
            else:
                logger.warning(f"⚠️  {scenario.upper()} - Iteration {iteration}: No finalized parlays")
            
            return TestResult(scenario, iteration, success, total_time, steps, 
                            None if success else "No finalized parlays", parlay_id)
            
        except Exception as e:
            total_time = time.time() - test_start
            logger.error(f"❌ {scenario.upper()} - Iteration {iteration}: ERROR - {str(e)}")
            return TestResult(scenario, iteration, False, total_time, steps, f"Exception: {str(e)}")

    def run_multi_tier_scenario(self, iteration: int) -> TestResult:
        """Run multi-tier success scenario (both SPs)"""
        scenario = "multi_tier_success"
        logger.info(f"🔄 {scenario.upper()} - Iteration {iteration}")
        
        test_start = time.time()
        steps = {}
        
        try:
            # Step 1: User auth
            user_token, step_time = self.get_user_token()
            steps['user_auth'] = step_time
            if user_token == "fallback_token":
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "User auth failed")
            
            # Step 2: Both SP auths
            sp1_token, step_time1 = self.authenticate_sp(self.sp1_credentials)
            sp2_token, step_time2 = self.authenticate_sp(self.sp2_credentials)
            steps['sp_auth'] = max(step_time1, step_time2)
            if not sp1_token or not sp2_token:
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "SP auth failed")
            
            # Step 3: Create parlay
            parlay_id, step_time = self.create_parlay(user_token)
            steps['create_parlay'] = step_time
            if not parlay_id:
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "Create parlay failed")
            
            # Step 4: Both SP offers
            sp1_offer, step_time1 = self.sp_offer(parlay_id, sp1_token, 850, 100)  # Better odds, limited capacity
            sp2_offer, step_time2 = self.sp_offer(parlay_id, sp2_token, 800, 150)  # Worse odds, more capacity
            steps['sp_offer'] = max(step_time1, step_time2)
            if not sp1_offer or not sp2_offer:
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "SP offers failed")
            
            # Step 5: User confirm (stake requiring both tiers)
            confirm_success, step_time = self.user_confirm(parlay_id, user_token, 850, 200)  # High stake
            steps['user_confirm'] = step_time
            if not confirm_success:
                return TestResult(scenario, iteration, False, time.time() - test_start, steps, "User confirm failed")
            
            # Wait for processing
            time.sleep(3)
            
            # Step 6: Both SPs accept
            sp1_accept, step_time1 = self.sp_accept(sp1_token, parlay_id, 100, 850)  # First tier
            sp2_accept, step_time2 = self.sp_accept(sp2_token, parlay_id, 100, 800)  # Second tier
            steps['sp_accept'] = max(step_time1, step_time2)
            
            # Step 7: Verify
            finalized_count, step_time = self.verify_user_view(user_token, parlay_id)
            steps['user_view'] = step_time
            
            success = sp1_accept and sp2_accept and finalized_count >= 2
            total_time = time.time() - test_start
            
            if success:
                logger.info(f"✅ {scenario.upper()} - Iteration {iteration}: SUCCESS ({finalized_count} parlays)")
            else:
                error_msg = f"SP1:{sp1_accept}, SP2:{sp2_accept}, Finalized:{finalized_count}"
                logger.warning(f"⚠️  {scenario.upper()} - Iteration {iteration}: {error_msg}")
            
            return TestResult(scenario, iteration, success, total_time, steps, 
                            None if success else "Multi-tier matching failed", parlay_id)
            
        except Exception as e:
            total_time = time.time() - test_start
            logger.error(f"❌ {scenario.upper()} - Iteration {iteration}: ERROR - {str(e)}")
            return TestResult(scenario, iteration, False, total_time, steps, f"Exception: {str(e)}")

    def run_comprehensive_load_test(self, 
                                  single_sp_iterations: int = 10,
                                  multi_tier_iterations: int = 5,
                                  concurrent: bool = False) -> Dict[str, Any]:
        """Run comprehensive load test with multiple scenarios"""
        
        logger.info(f"\n{'='*120}")
        logger.info(f"🚀 COMPREHENSIVE PARLAY LOAD TEST")
        logger.info(f"Started at: {datetime.now().isoformat()}")
        logger.info(f"Single SP iterations: {single_sp_iterations}")
        logger.info(f"Multi-tier iterations: {multi_tier_iterations}")
        logger.info(f"Concurrent: {'Yes' if concurrent else 'No'}")
        logger.info("="*120)
        
        test_start_time = time.time()
        
        # Prepare test tasks
        tasks = []
        
        # Single SP tasks
        for i in range(single_sp_iterations):
            tasks.append(('single_sp', i+1))
        
        # Multi-tier tasks  
        for i in range(multi_tier_iterations):
            tasks.append(('multi_tier', i+1))
        
        # Shuffle for better load distribution
        random.shuffle(tasks)
        
        results = []
        
        if concurrent:
            # Run tests concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for task_type, iteration in tasks:
                    if task_type == 'single_sp':
                        future = executor.submit(self.run_single_sp_scenario, iteration)
                    else:
                        future = executor.submit(self.run_multi_tier_scenario, iteration)
                    futures.append(future)
                
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
        else:
            # Run tests sequentially
            for task_type, iteration in tasks:
                if task_type == 'single_sp':
                    result = self.run_single_sp_scenario(iteration)
                else:
                    result = self.run_multi_tier_scenario(iteration)
                results.append(result)
                
                # Brief pause between tests
                time.sleep(1)
        
        total_test_time = time.time() - test_start_time
        
        # Analyze and report
        analysis = self.analyze_comprehensive_results(results, total_test_time)
        self.print_comprehensive_summary(analysis)
        
        return analysis

    def analyze_comprehensive_results(self, results: List[TestResult], total_time: float) -> Dict[str, Any]:
        """Analyze comprehensive test results"""
        
        # Separate by scenario
        single_sp_results = [r for r in results if r.scenario == 'single_sp_success']
        multi_tier_results = [r for r in results if r.scenario == 'multi_tier_success']
        
        analysis = {
            'total_tests': len(results),
            'total_test_time': total_time,
            'scenarios': {
                'single_sp_success': {
                    'total': len(single_sp_results),
                    'successful': len([r for r in single_sp_results if r.success]),
                    'failed': len([r for r in single_sp_results if not r.success]),
                    'success_rate': len([r for r in single_sp_results if r.success]) / len(single_sp_results) * 100 if single_sp_results else 0,
                    'avg_time': statistics.mean([r.total_time for r in single_sp_results]) if single_sp_results else 0,
                    'results': single_sp_results
                },
                'multi_tier_success': {
                    'total': len(multi_tier_results),
                    'successful': len([r for r in multi_tier_results if r.success]),
                    'failed': len([r for r in multi_tier_results if not r.success]),
                    'success_rate': len([r for r in multi_tier_results if r.success]) / len(multi_tier_results) * 100 if multi_tier_results else 0,
                    'avg_time': statistics.mean([r.total_time for r in multi_tier_results]) if multi_tier_results else 0,
                    'results': multi_tier_results
                }
            },
            'overall_success_rate': len([r for r in results if r.success]) / len(results) * 100,
            'response_times': {},
            'failure_analysis': {}
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

    def print_comprehensive_summary(self, analysis: Dict[str, Any]):
        """Print comprehensive test summary"""
        logger.info(f"\n{'='*120}")
        logger.info("📊 COMPREHENSIVE LOAD TEST RESULTS")
        logger.info("="*120)
        
        # Overall performance
        logger.info(f"🎯 OVERALL PERFORMANCE:")
        logger.info(f"   Total Tests: {analysis['total_tests']}")
        logger.info(f"   Overall Success Rate: {analysis['overall_success_rate']:.1f}%")
        logger.info(f"   Total Test Time: {analysis['total_test_time']:.2f}s")
        
        # Scenario-specific results
        logger.info(f"\n📋 SCENARIO-SPECIFIC RESULTS:")
        
        for scenario_name, scenario_data in analysis['scenarios'].items():
            if scenario_data['total'] > 0:
                logger.info(f"   {scenario_name.upper().replace('_', ' ')}:")
                logger.info(f"     Tests: {scenario_data['total']}")
                logger.info(f"     Successful: {scenario_data['successful']}")
                logger.info(f"     Failed: {scenario_data['failed']}")
                logger.info(f"     Success Rate: {scenario_data['success_rate']:.1f}%")
                logger.info(f"     Avg Time: {scenario_data['avg_time']:.2f}s")
        
        # Response time analysis
        logger.info(f"\n⚡ RESPONSE TIME ANALYSIS:")
        for step, metrics in analysis['response_times'].items():
            logger.info(f"   {step.upper()}:")
            logger.info(f"     Average: {metrics['average']:.3f}s")
            logger.info(f"     Median:  {metrics['median']:.3f}s")
            logger.info(f"     Range:   {metrics['min']:.3f}s - {metrics['max']:.3f}s")
            logger.info(f"     Std Dev: {metrics['std_dev']:.3f}s")
        
        # Failure analysis
        if analysis['failure_analysis']:
            logger.info(f"\n❌ FAILURE ANALYSIS:")
            for failure, count in analysis['failure_analysis'].items():
                logger.info(f"   {failure}: {count} occurrences")
        
        # Performance insights
        logger.info(f"\n🔍 PERFORMANCE INSIGHTS:")
        if analysis['overall_success_rate'] >= 90:
            logger.info("   ✅ Excellent overall success rate - system is very stable")
        elif analysis['overall_success_rate'] >= 70:
            logger.info("   ⚠️  Good overall success rate - some minor issues")
        else:
            logger.info("   ❌ Poor overall success rate - significant stability concerns")
        
        # Scenario comparison
        single_sp_rate = analysis['scenarios']['single_sp_success']['success_rate']
        multi_tier_rate = analysis['scenarios']['multi_tier_success']['success_rate'] 
        
        if single_sp_rate > multi_tier_rate + 20:
            logger.info("   📊 Single SP scenario significantly more reliable than multi-tier")
        elif abs(single_sp_rate - multi_tier_rate) <= 10:
            logger.info("   📊 Both scenarios show similar reliability")
        else:
            logger.info("   📊 Multi-tier scenario showing good reliability")
        
        # Response time insights
        avg_response_time = statistics.mean([
            metrics['average'] for metrics in analysis['response_times'].values()
        ])
        
        if avg_response_time < 1.0:
            logger.info("   ⚡ Excellent response times across all operations")
        elif avg_response_time < 2.0:
            logger.info("   ✅ Good response times - system is performing well")
        else:
            logger.info("   ⚠️  Response times could be improved")
        
        logger.info(f"\nCompleted at: {datetime.now().isoformat()}")
        logger.info(f"📁 Full logs saved to: comprehensive_load_test_{int(time.time())}.log")

def main():
    """Main comprehensive load test runner"""
    load_test = ComprehensiveLoadTest()
    
    # Run comprehensive load test
    # 10 single SP tests (most reliable) + 5 multi-tier tests (more complex)
    results = load_test.run_comprehensive_load_test(
        single_sp_iterations=10,
        multi_tier_iterations=5,
        concurrent=False  # Set to True for concurrent testing (more aggressive)
    )
    
    return results

if __name__ == "__main__":
    main()
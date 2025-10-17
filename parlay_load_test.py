#!/usr/bin/env python3
"""
🚀 PARLAY LOAD TEST - 10 ITERATIONS

Runs successful parlay scenarios multiple times to test system performance under load:
- Tests successful scenarios (Scenario 1: Basic Single SP Success)
- Runs each successful scenario 10 times
- Tracks performance metrics (response times, success rates)
- Provides detailed statistical analysis
"""

import requests
import json
import time
import logging
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime
import concurrent.futures
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'parlay_load_test_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ParlayLoadTest:
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

    def log_request_response(self, step: str, method: str, url: str, 
                           headers: Dict = None, payload: Dict = None, 
                           response: requests.Response = None, params: Dict = None, 
                           show_full_log: bool = False):
        """Log request and response details (abbreviated for load test)"""
        if show_full_log:
            logger.info(f"📤 {step} - {method} {response.status_code if response else 'REQUEST'}")
            if response and response.status_code != 200:
                logger.warning(f"⚠️  {step} - Status: {response.status_code}")
                try:
                    logger.warning(f"Response: {response.json()}")
                except:
                    logger.warning(f"Response: {response.text}")
        else:
            # Minimal logging for load test
            status = f"✅ {response.status_code}" if response and response.status_code == 200 else f"❌ {response.status_code if response else 'ERROR'}"
            logger.info(f"{step}: {status}")

    def get_fresh_user_token(self) -> str:
        """Get fresh user authentication token"""
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
            
            self.log_request_response("USER AUTH", "POST", url, payload=payload, response=response)
            
            if response.status_code == 200:
                token = response.json().get("accessToken")
                return token
            else:
                logger.error(f"❌ Failed to get user token: {response.status_code}")
                return "fallback_token"
        except Exception as e:
            logger.error(f"❌ Error getting user token: {e}")
            return "fallback_token"

    def authenticate_sp(self, credentials: Dict[str, str], sp_name: str) -> Optional[str]:
        """Authenticate Service Provider and return access token"""
        url = f"{self.base_url}/partner/auth/login"
        
        start_time = time.time()
        try:
            response = requests.post(url, json=credentials, headers={
                "Content-Type": "application/json"
            })
            
            response_time = time.time() - start_time
            with self.lock:
                self.response_times['auth'].append(response_time)
            
            self.log_request_response(f"{sp_name} AUTH", "POST", url, response=response)
            
            if response.status_code == 200:
                token = response.json()["data"]["access_token"]
                return token
            else:
                logger.error(f"❌ {sp_name} Authentication FAILED: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ {sp_name} Authentication ERROR: {str(e)}")
            return None

    def create_parlay_request(self, user_token: str) -> Optional[str]:
        """Create parlay request and return parlay ID"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        
        payload = {
            "marketLines": self.market_lines
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
                self.response_times['create_parlay'].append(response_time)
            
            self.log_request_response("CREATE PARLAY", "POST", url, response=response)
            
            if response.status_code == 200:
                parlay_id = response.json()["data"]["parlayId"]
                return parlay_id
            else:
                logger.error(f"❌ Create parlay failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Create parlay error: {str(e)}")
            return None

    def provide_sp_offer(self, parlay_id: str, sp_token: str, odds: int, 
                        max_risk: int, sp_name: str) -> bool:
        """SP provides offer for parlay"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        
        # Calculate valid_until (60 seconds from now in nanoseconds since Unix epoch)
        valid_until = int((time.time() + 60) * 1e9)
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": odds,
                    "max_risk": max_risk,
                    "valid_until": valid_until,
                    "estimated_prices": [
                        {
                            "line_id": "01e69752c33c3835e18578752565934a",
                            "odds": odds
                        },
                        {
                            "line_id": "b823a3699ec9461c8cebec1b5724dfa0",
                            "odds": odds
                        }
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
            
            self.log_request_response(f"{sp_name} OFFER", "POST", url, response=response)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ {sp_name} offer error: {str(e)}")
            return False

    def user_confirm_bet(self, parlay_id: str, user_token: str, odds: int, stake: int) -> bool:
        """User confirms bet with specific odds and stake"""
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
            
            self.log_request_response("USER CONFIRM", "POST", url, response=response)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ User confirm error: {str(e)}")
            return False

    def sp_acknowledge_confirmation(self, sp_token: str, parlay_id: str, stake: int, 
                                  odds: int, sp_name: str, accept: bool = True) -> bool:
        """SP acknowledges confirmation (accept/reject)"""
        # First get the order UUID
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            orders_response = requests.get(orders_url, headers=headers)
            if orders_response.status_code != 200:
                return False
            
            orders_data = orders_response.json()
            target_order = None
            
            for order in orders_data["data"]["orders"]:
                if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
                    target_order = order
                    break
            
            if not target_order:
                return False
            
            order_uuid = target_order["order_uuid"]
            
        except Exception as e:
            logger.error(f"❌ {sp_name} get orders error: {str(e)}")
            return False
        
        # Now acknowledge the confirmation
        url = f"{self.base_url}/parlay/sp/orders/confirmations"
        params = {"order_uuid": order_uuid}
        
        # Calculate probability for accept scenario
        probability = 1.0 / (abs(odds) / 100.0 + 1.0) if odds < 0 else 100.0 / (odds + 100.0)
        max_risk_cents = int((stake * probability) * 100)
        
        payload = {
            "action": "accept" if accept else "reject",
            "confirmed_stake": stake,
            "price_probability": [
                {
                    "lines": [
                        {
                            "line_id": "01e69752c33c3835e18578752565934a",
                            "probability": probability
                        },
                        {
                            "line_id": "b823a3699ec9461c8cebec1b5724dfa0",
                            "probability": probability
                        }
                    ],
                    "max_risk": max_risk_cents,
                    "vig": 0.1
                }
            ],
            "signature": f"test_signature_{sp_name.lower()}"
        }
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, headers=headers, params=params)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['sp_accept'].append(response_time)
            
            self.log_request_response(f"{sp_name} {'ACCEPT' if accept else 'REJECT'}", 
                                    "POST", url, response=response)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ {sp_name} acknowledge error: {str(e)}")
            return False

    def get_user_view_parlays(self, user_token: str, parlay_id: str) -> List[Dict]:
        """Get user's parlay view to verify final status"""
        url = f"{self.base_url}/parlay/api/v1/user/list?limit=50"
        headers = {"Authorization": f"Bearer {user_token}"}
        
        max_attempts = 5
        for attempt in range(max_attempts):
            start_time = time.time()
            try:
                response = requests.get(url, headers=headers)
                response_time = time.time() - start_time
                
                with self.lock:
                    self.response_times['user_view'].append(response_time)
                
                self.log_request_response(f"USER VIEW (attempt {attempt+1})", "GET", url, response=response)
                
                if response.status_code == 200:
                    user_data = response.json()
                    matching_parlays = [
                        order for order in user_data["data"]["orders"]
                        if order["parlayId"] == parlay_id
                    ]
                    
                    if matching_parlays:
                        return matching_parlays
                    else:
                        if attempt < max_attempts - 1:
                            time.sleep(4)  # Wait before retry
                        
            except Exception as e:
                logger.error(f"❌ User view error: {str(e)}")
                
        return []

    def run_single_successful_scenario(self, iteration: int) -> Dict[str, Any]:
        """Run a single instance of the most successful scenario (Scenario 1: Basic Single SP Success)"""
        logger.info(f"\n🔄 ITERATION {iteration}: Basic Single SP Success")
        
        test_start_time = time.time()
        result = {
            'iteration': iteration,
            'success': False,
            'total_time': 0,
            'steps': {},
            'error': None
        }
        
        try:
            # Step 1: Get user token
            step_start = time.time()
            user_token = self.get_fresh_user_token()
            result['steps']['user_auth'] = time.time() - step_start
            
            if user_token == "fallback_token":
                result['error'] = "User authentication failed"
                return result
            
            # Step 2: Authenticate SP1
            step_start = time.time()
            sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            result['steps']['sp1_auth'] = time.time() - step_start
            
            if not sp1_token:
                result['error'] = "SP1 authentication failed"
                return result
            
            # Step 3: Create parlay
            step_start = time.time()
            parlay_id = self.create_parlay_request(user_token)
            result['steps']['create_parlay'] = time.time() - step_start
            
            if not parlay_id:
                result['error'] = "Create parlay failed"
                return result
            
            # Step 4: SP1 provides offer
            step_start = time.time()
            sp1_offer_success = self.provide_sp_offer(parlay_id, sp1_token, 800, 200, "SP1")
            result['steps']['sp1_offer'] = time.time() - step_start
            
            if not sp1_offer_success:
                result['error'] = "SP1 offer failed"
                return result
            
            # Step 5: User confirms bet
            step_start = time.time()
            user_confirm_success = self.user_confirm_bet(parlay_id, user_token, 800, 100)
            result['steps']['user_confirm'] = time.time() - step_start
            
            if not user_confirm_success:
                result['error'] = "User confirm failed"
                return result
            
            # Wait a moment for order processing
            time.sleep(4)
            
            # Step 6: SP1 accepts confirmation
            step_start = time.time()
            sp1_accept_success = self.sp_acknowledge_confirmation(sp1_token, parlay_id, 100, 800, "SP1", True)
            result['steps']['sp1_accept'] = time.time() - step_start
            
            if not sp1_accept_success:
                result['error'] = "SP1 accept failed"
                return result
            
            # Step 7: Verify user view
            step_start = time.time()
            user_parlays = self.get_user_view_parlays(user_token, parlay_id)
            result['steps']['user_view'] = time.time() - step_start
            
            finalized_parlays = [p for p in user_parlays if p.get("status") == "finalized"]
            
            if len(finalized_parlays) >= 1:
                result['success'] = True
                logger.info(f"✅ ITERATION {iteration}: SUCCESS - Found {len(finalized_parlays)} finalized parlays")
            else:
                result['error'] = f"No finalized parlays found - got {len(user_parlays)} total parlays"
                logger.warning(f"⚠️  ITERATION {iteration}: {result['error']}")
            
        except Exception as e:
            result['error'] = f"Exception: {str(e)}"
            logger.error(f"❌ ITERATION {iteration}: ERROR - {str(e)}")
        
        result['total_time'] = time.time() - test_start_time
        return result

    def run_load_test(self, iterations: int = 10, concurrent: bool = False) -> Dict[str, Any]:
        """Run the load test with specified number of iterations"""
        logger.info(f"\n{'='*100}")
        logger.info(f"🚀 PARLAY LOAD TEST - {iterations} ITERATIONS")
        logger.info(f"Started at: {datetime.now().isoformat()}")
        logger.info(f"Concurrent: {'Yes' if concurrent else 'No'}")
        logger.info("="*100)
        
        test_start_time = time.time()
        
        if concurrent:
            # Run tests concurrently (be careful with API rate limits)
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(self.run_single_successful_scenario, i+1) 
                    for i in range(iterations)
                ]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
        else:
            # Run tests sequentially
            results = []
            for i in range(iterations):
                result = self.run_single_successful_scenario(i+1)
                results.append(result)
                # Brief pause between iterations to avoid overwhelming the API
                time.sleep(1)
        
        total_test_time = time.time() - test_start_time
        
        # Analyze results
        analysis = self.analyze_results(results, total_test_time)
        
        # Print summary
        self.print_summary(analysis)
        
        return analysis

    def analyze_results(self, results: List[Dict], total_time: float) -> Dict[str, Any]:
        """Analyze test results and calculate performance metrics"""
        successful_tests = [r for r in results if r['success']]
        failed_tests = [r for r in results if not r['success']]
        
        analysis = {
            'total_iterations': len(results),
            'successful_iterations': len(successful_tests),
            'failed_iterations': len(failed_tests),
            'success_rate': len(successful_tests) / len(results) * 100,
            'total_test_time': total_time,
            'average_iteration_time': statistics.mean([r['total_time'] for r in results]),
            'response_times': {},
            'failure_reasons': {},
            'successful_results': successful_tests,
            'failed_results': failed_tests
        }
        
        # Analyze response times for each step
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
        
        # Analyze failure reasons
        for failed_test in failed_tests:
            reason = failed_test.get('error', 'Unknown error')
            analysis['failure_reasons'][reason] = analysis['failure_reasons'].get(reason, 0) + 1
        
        return analysis

    def print_summary(self, analysis: Dict[str, Any]):
        """Print detailed test summary"""
        logger.info(f"\n{'='*100}")
        logger.info("📊 LOAD TEST RESULTS SUMMARY")
        logger.info("="*100)
        
        # Overall results
        logger.info(f"🎯 OVERALL PERFORMANCE:")
        logger.info(f"   Total Iterations: {analysis['total_iterations']}")
        logger.info(f"   Successful: {analysis['successful_iterations']}")
        logger.info(f"   Failed: {analysis['failed_iterations']}")
        logger.info(f"   Success Rate: {analysis['success_rate']:.1f}%")
        logger.info(f"   Total Test Time: {analysis['total_test_time']:.2f}s")
        logger.info(f"   Average Iteration Time: {analysis['average_iteration_time']:.2f}s")
        
        # Response time analysis
        logger.info(f"\n⚡ RESPONSE TIME ANALYSIS:")
        for step, metrics in analysis['response_times'].items():
            logger.info(f"   {step.upper()}:")
            logger.info(f"     Average: {metrics['average']:.3f}s")
            logger.info(f"     Median:  {metrics['median']:.3f}s")
            logger.info(f"     Range:   {metrics['min']:.3f}s - {metrics['max']:.3f}s")
            logger.info(f"     Std Dev: {metrics['std_dev']:.3f}s")
        
        # Failure analysis
        if analysis['failure_reasons']:
            logger.info(f"\n❌ FAILURE ANALYSIS:")
            for reason, count in analysis['failure_reasons'].items():
                logger.info(f"   {reason}: {count} occurrences")
        
        # Performance recommendations
        logger.info(f"\n🔍 PERFORMANCE INSIGHTS:")
        if analysis['success_rate'] >= 90:
            logger.info("   ✅ Excellent success rate - system is stable under load")
        elif analysis['success_rate'] >= 70:
            logger.info("   ⚠️  Good success rate - minor issues detected")
        else:
            logger.info("   ❌ Poor success rate - significant stability issues")
        
        avg_response_time = statistics.mean([
            metrics['average'] for metrics in analysis['response_times'].values()
        ])
        
        if avg_response_time < 1.0:
            logger.info("   ⚡ Excellent response times - system is performant")
        elif avg_response_time < 3.0:
            logger.info("   ✅ Good response times - acceptable performance")
        else:
            logger.info("   ⚠️  Slow response times - consider performance optimization")
        
        logger.info(f"\nCompleted at: {datetime.now().isoformat()}")
        logger.info(f"📁 Full logs saved to: parlay_load_test_{int(time.time())}.log")

def main():
    """Main load test runner"""
    load_test = ParlayLoadTest()
    
    # Run 10 iterations of the successful scenario
    results = load_test.run_load_test(iterations=10, concurrent=False)
    
    return results

if __name__ == "__main__":
    main()
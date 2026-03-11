#!/usr/bin/env python3
"""
10-Minute Load Test - Scenario 1: Basic Single SP Success

Runs the successful Scenario 1 repeatedly for 10 minutes to test system stability and performance:
- Authenticates user and SP
- Creates parlay
- SP provides offer
- User confirms bet
- SP accepts confirmation
- Verifies finalized parlays in user view

Features:
- 10-minute duration with configurable interval between iterations
- Comprehensive performance metrics and statistics
- Success/failure tracking with detailed error logging
- Real-time progress updates every minute
- Final summary report with performance insights
"""

import requests
import time
import json
import logging
import statistics
import threading
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import signal
import sys

# Configure logging
log_filename = f'load_test_scenario_1_{int(time.time())}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LoadTestRunner:
    def __init__(self, duration_minutes: int = 10, interval_seconds: float = 30):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.duration_minutes = duration_minutes
        self.interval_seconds = interval_seconds
        self.start_time = None
        self.end_time = None
        
        # Fresh market lines data from working test
        self.market_lines = [
            {
                "line": -1.5,
                "lineId": "6a23fd8b84bf441704f7741094d2fb9d",
                "marketId": 410,
                "outcomeId": 1714,
                "sportEventId": 30024075
            },
            {
                "line": 228.5,
                "lineId": "2556b82f0b1955061eda2e8d5e280cda",
                "marketId": 225,
                "outcomeId": 12,
                "sportEventId": 20022435
            }
        ]
        
        # SP1 credentials (working)
        self.sp1_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        
        # Metrics tracking
        self.lock = threading.Lock()
        self.metrics = {
            'total_iterations': 0,
            'successful_iterations': 0,
            'failed_iterations': 0,
            'response_times': {
                'user_auth': [],
                'sp_auth': [],
                'create_parlay': [],
                'sp_offer': [],
                'user_confirm': [],
                'sp_acknowledge': [],
                'user_view': [],
                'total_iteration': []
            },
            'error_counts': defaultdict(int),
            'parlays_created': [],
            'finalized_parlays': 0,
            'timestamps': []
        }
        
        # Control flags
        self.running = True
        self.last_progress_time = time.time()
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(self, signum, frame):
        logger.info("🛑 Received interrupt signal. Shutting down gracefully...")
        self.running = False

    def get_user_token(self) -> Tuple[Optional[str], float]:
        """Authenticate user and return token"""
        url = f"{self.base_url}/api/v1/auth/login"
        payload = {
            "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
            "email": "lam.tran+usr004@betprophet.co",
            "password": "Kh0ngbiet1"
        }
        headers = {"Content-Type": "application/json"}
        
        start = time.time()
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            duration = time.time() - start
            
            if resp.status_code == 200:
                token = resp.json().get("accessToken")
                return token, duration
            else:
                logger.warning(f"User auth failed: {resp.status_code}")
                return None, duration
        except Exception as e:
            duration = time.time() - start
            logger.error(f"User auth exception: {e}")
            return None, duration

    def authenticate_sp(self) -> Tuple[Optional[str], float]:
        """Authenticate SP and return token"""
        url = f"{self.base_url}/partner/auth/login"
        headers = {"Content-Type": "application/json"}
        
        start = time.time()
        try:
            resp = requests.post(url, json=self.sp1_credentials, headers=headers, timeout=30)
            duration = time.time() - start
            
            if resp.status_code == 200:
                token = resp.json().get("data", {}).get("access_token")
                return token, duration
            else:
                logger.warning(f"SP auth failed: {resp.status_code}")
                return None, duration
        except Exception as e:
            duration = time.time() - start
            logger.error(f"SP auth exception: {e}")
            return None, duration

    def create_parlay(self, user_token: str) -> Tuple[Optional[str], float]:
        """Create parlay and return parlay ID"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        payload = {"marketLines": self.market_lines}
        headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
        
        start = time.time()
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            duration = time.time() - start
            
            if resp.status_code == 200:
                parlay_id = resp.json().get("data", {}).get("parlayId")
                return parlay_id, duration
            else:
                logger.warning(f"Create parlay failed: {resp.status_code}")
                return None, duration
        except Exception as e:
            duration = time.time() - start
            logger.error(f"Create parlay exception: {e}")
            return None, duration

    def provide_sp_offer(self, parlay_id: str, sp_token: str) -> Tuple[bool, float]:
        """SP provides offer for parlay"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        valid_until = int((time.time() + 60) * 1e9)  # 60 seconds validity
        payload = {
            "parlay_id": parlay_id,
            "offers": [{
                "odds": 800,
                "max_risk": 200,
                "valid_until": valid_until,
                "estimated_prices": [
                    {"line_id": self.market_lines[0]["lineId"], "odds": 800},
                    {"line_id": self.market_lines[1]["lineId"], "odds": 800}
                ]
            }]
        }
        headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
        
        start = time.time()
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            duration = time.time() - start
            
            if resp.status_code == 200:
                return True, duration
            else:
                logger.warning(f"SP offer failed: {resp.status_code}")
                return False, duration
        except Exception as e:
            duration = time.time() - start
            logger.error(f"SP offer exception: {e}")
            return False, duration

    def user_confirm_bet(self, parlay_id: str, user_token: str) -> Tuple[bool, float]:
        """User confirms bet"""
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        payload = {"parlayId": parlay_id, "odds": 800, "stake": 100}
        headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
        
        start = time.time()
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            duration = time.time() - start
            
            if resp.status_code == 200:
                return True, duration
            else:
                logger.warning(f"User confirm failed: {resp.status_code}")
                return False, duration
        except Exception as e:
            duration = time.time() - start
            logger.error(f"User confirm exception: {e}")
            return False, duration

    def sp_acknowledge_confirmation(self, sp_token: str, parlay_id: str) -> Tuple[bool, float]:
        """SP acknowledges confirmation"""
        # First get orders to find order_uuid
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        start = time.time()
        try:
            orders_resp = requests.get(orders_url, headers=headers, timeout=30)
            if orders_resp.status_code != 200:
                logger.warning(f"SP get orders failed: {orders_resp.status_code}")
                return False, time.time() - start
                
            orders = orders_resp.json().get("data", {}).get("orders", [])
            target_order = next((o for o in orders if o.get("p_id") == parlay_id and o.get("status") == "sent_confirmation"), None)
            
            if not target_order:
                logger.warning(f"SP no order in sent_confirmation for parlay {parlay_id}")
                return False, time.time() - start
                
            order_uuid = target_order.get("order_uuid")
            
            # Now send acknowledgment
            url = f"{self.base_url}/parlay/sp/orders/confirmations"
            params = {"order_uuid": order_uuid}
            probability = 100.0 / (800 + 100.0)
            max_risk_cents = int(100 * (800 / 100.0) * 100)  # Convert to cents
            payload = {
                "action": "accept",
                "confirmed_stake": 100,
                "price_probability": [{
                    "lines": [
                        {"line_id": self.market_lines[0]["lineId"], "probability": probability},
                        {"line_id": self.market_lines[1]["lineId"], "probability": probability}
                    ],
                    "max_risk": max_risk_cents,
                    "vig": 0.1
                }],
                "signature": "test_signature_sp1_accept"
            }
            
            resp = requests.post(url, json=payload, headers=headers, params=params, timeout=30)
            duration = time.time() - start
            
            if resp.status_code == 200:
                return True, duration
            else:
                logger.warning(f"SP acknowledge failed: {resp.status_code}")
                return False, duration
                
        except Exception as e:
            duration = time.time() - start
            logger.error(f"SP acknowledge exception: {e}")
            return False, duration

    def verify_finalization(self, user_token: str, parlay_id: str) -> Tuple[bool, float]:
        """Verify parlay is finalized"""
        url = f"{self.base_url}/parlay/api/v1/user/list?limit=50"
        headers = {"Authorization": f"Bearer {user_token}"}
        
        start = time.time()
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            duration = time.time() - start
            
            if resp.status_code == 200:
                user_data = resp.json()
                matching_parlays = [p for p in user_data.get("data", {}).get("orders", []) 
                                   if p.get("parlayId") == parlay_id and p.get("status") == "finalized"]
                return len(matching_parlays) > 0, duration
            else:
                logger.warning(f"User view failed: {resp.status_code}")
                return False, duration
        except Exception as e:
            duration = time.time() - start
            logger.error(f"User view exception: {e}")
            return False, duration

    def run_single_iteration(self, iteration: int) -> bool:
        """Run a single iteration of Scenario 1"""
        iteration_start = time.time()
        step_times = {}
        
        try:
            # Step 1: User Authentication
            user_token, auth_time = self.get_user_token()
            step_times['user_auth'] = auth_time
            if not user_token:
                self.record_error("user_auth_failed")
                return False
            
            # Step 2: SP Authentication  
            sp_token, sp_auth_time = self.authenticate_sp()
            step_times['sp_auth'] = sp_auth_time
            if not sp_token:
                self.record_error("sp_auth_failed")
                return False
            
            # Step 3: Create Parlay
            parlay_id, create_time = self.create_parlay(user_token)
            step_times['create_parlay'] = create_time
            if not parlay_id:
                self.record_error("create_parlay_failed")
                return False
            
            # Step 4: SP Offer
            offer_success, offer_time = self.provide_sp_offer(parlay_id, sp_token)
            step_times['sp_offer'] = offer_time
            if not offer_success:
                self.record_error("sp_offer_failed")
                return False
            
            # Step 5: User Confirm
            confirm_success, confirm_time = self.user_confirm_bet(parlay_id, user_token)
            step_times['user_confirm'] = confirm_time
            if not confirm_success:
                self.record_error("user_confirm_failed")
                return False
            
            # Brief wait for processing
            time.sleep(3)
            
            # Step 6: SP Acknowledge
            ack_success, ack_time = self.sp_acknowledge_confirmation(sp_token, parlay_id)
            step_times['sp_acknowledge'] = ack_time
            if not ack_success:
                self.record_error("sp_acknowledge_failed")
                return False
            
            # Brief wait for finalization
            time.sleep(2)
            
            # Step 7: Verify Finalization
            finalized, verify_time = self.verify_finalization(user_token, parlay_id)
            step_times['user_view'] = verify_time
            
            total_time = time.time() - iteration_start
            step_times['total_iteration'] = total_time
            
            # Record metrics
            with self.lock:
                for step, duration in step_times.items():
                    self.metrics['response_times'][step].append(duration)
                self.metrics['parlays_created'].append(parlay_id)
                if finalized:
                    self.metrics['finalized_parlays'] += 1
            
            logger.info(f"✅ Iteration {iteration}: SUCCESS in {total_time:.2f}s (Finalized: {finalized})")
            return True
            
        except Exception as e:
            total_time = time.time() - iteration_start
            logger.error(f"❌ Iteration {iteration}: EXCEPTION in {total_time:.2f}s - {e}")
            self.record_error("iteration_exception")
            return False

    def record_error(self, error_type: str):
        """Record an error in metrics"""
        with self.lock:
            self.metrics['error_counts'][error_type] += 1

    def log_progress_report(self):
        """Log progress report"""
        with self.lock:
            elapsed = time.time() - self.start_time
            total = self.metrics['total_iterations']
            success = self.metrics['successful_iterations']
            failed = self.metrics['failed_iterations']
            success_rate = (success / total * 100) if total > 0 else 0
            
            logger.info(f"\n📊 PROGRESS REPORT - {elapsed/60:.1f} minutes elapsed")
            logger.info(f"   Iterations: {total} total, {success} success, {failed} failed ({success_rate:.1f}% success rate)")
            logger.info(f"   Finalized Parlays: {self.metrics['finalized_parlays']}")
            
            # Average response times
            if self.metrics['response_times']['total_iteration']:
                avg_iteration_time = statistics.mean(self.metrics['response_times']['total_iteration'])
                logger.info(f"   Average iteration time: {avg_iteration_time:.2f}s")

    def generate_final_report(self):
        """Generate comprehensive final report"""
        elapsed = self.end_time - self.start_time
        total = self.metrics['total_iterations']
        success = self.metrics['successful_iterations'] 
        failed = self.metrics['failed_iterations']
        success_rate = (success / total * 100) if total > 0 else 0
        
        logger.info(f"\n{'='*80}")
        logger.info(f"📋 FINAL LOAD TEST REPORT")
        logger.info(f"{'='*80}")
        logger.info(f"Duration: {elapsed/60:.2f} minutes ({elapsed:.1f} seconds)")
        logger.info(f"Total Iterations: {total}")
        logger.info(f"Successful: {success} ({success_rate:.1f}%)")
        logger.info(f"Failed: {failed} ({100-success_rate:.1f}%)")
        logger.info(f"Finalized Parlays: {self.metrics['finalized_parlays']}")
        
        # Throughput
        iterations_per_minute = total / (elapsed / 60) if elapsed > 0 else 0
        logger.info(f"Throughput: {iterations_per_minute:.2f} iterations/minute")
        
        # Response time statistics
        logger.info(f"\n📈 RESPONSE TIME STATISTICS:")
        for step, times in self.metrics['response_times'].items():
            if times:
                avg = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                p95 = sorted(times)[int(len(times) * 0.95)] if len(times) >= 20 else max_time
                logger.info(f"   {step}: avg={avg:.3f}s, min={min_time:.3f}s, max={max_time:.3f}s, p95={p95:.3f}s")
        
        # Error breakdown
        if self.metrics['error_counts']:
            logger.info(f"\n❌ ERROR BREAKDOWN:")
            for error_type, count in self.metrics['error_counts'].items():
                percentage = (count / total * 100) if total > 0 else 0
                logger.info(f"   {error_type}: {count} ({percentage:.1f}%)")
        
        logger.info(f"\n📁 Detailed log saved to: {log_filename}")
        logger.info(f"{'='*80}")

    def run_load_test(self):
        """Run the main load test"""
        self.start_time = time.time()
        end_time = self.start_time + (self.duration_minutes * 60)
        
        logger.info(f"🚀 Starting 10-minute load test - Scenario 1: Basic Single SP Success")
        logger.info(f"⚙️  Configuration: {self.duration_minutes} minutes, {self.interval_seconds}s interval between iterations")
        logger.info(f"📊 Progress reports every minute")
        logger.info(f"🔄 Press Ctrl+C to stop gracefully\n")
        
        iteration = 0
        
        while self.running and time.time() < end_time:
            iteration += 1
            
            # Run iteration
            with self.lock:
                self.metrics['total_iterations'] += 1
                
            success = self.run_single_iteration(iteration)
            
            with self.lock:
                if success:
                    self.metrics['successful_iterations'] += 1
                else:
                    self.metrics['failed_iterations'] += 1
                    
                self.metrics['timestamps'].append(time.time())
            
            # Progress report every minute
            if time.time() - self.last_progress_time >= 60:
                self.log_progress_report()
                self.last_progress_time = time.time()
            
            # Wait before next iteration (if we still have time)
            if time.time() < end_time - self.interval_seconds:
                remaining = end_time - time.time()
                wait_time = min(self.interval_seconds, remaining)
                if wait_time > 0:
                    time.sleep(wait_time)
        
        self.end_time = time.time()
        self.generate_final_report()

def main():
    """Main execution function"""
    # Configuration
    DURATION_MINUTES = 10
    INTERVAL_SECONDS = 30  # 30 seconds between iterations
    
    runner = LoadTestRunner(duration_minutes=DURATION_MINUTES, interval_seconds=INTERVAL_SECONDS)
    
    try:
        runner.run_load_test()
    except KeyboardInterrupt:
        logger.info("🛑 Test interrupted by user")
        if runner.start_time:
            runner.end_time = time.time()
            runner.generate_final_report()
    except Exception as e:
        logger.error(f"💥 Unexpected error: {e}")
        if runner.start_time:
            runner.end_time = time.time()
            runner.generate_final_report()

if __name__ == "__main__":
    main()
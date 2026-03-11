#!/usr/bin/env python3
"""
Aggressive 10-Minute Load Test - Scenario 1: Basic Single SP Success

High-intensity load test with:
- 5-second intervals between iterations (vs 30s in previous test)
- Concurrent execution with multiple worker threads
- Reduced wait times for faster iteration cycles
- Higher request frequency to stress test the system
- Real-time monitoring and adaptive throttling

Features:
- 10-minute duration with aggressive 5s intervals
- Multi-threaded execution (3 concurrent workers)
- Comprehensive performance metrics and statistics
- Success/failure tracking with detailed error logging
- Real-time progress updates every 30 seconds
- Automatic throttling if error rate exceeds threshold
"""

import requests
import time
import json
import logging
import statistics
import threading
import concurrent.futures
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import signal
import sys
import queue

# Configure logging
log_filename = f'aggressive_load_test_scenario_1_{int(time.time())}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AggressiveLoadTestRunner:
    def __init__(self, duration_minutes: int = 10, interval_seconds: float = 5, max_workers: int = 3):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.duration_minutes = duration_minutes
        self.interval_seconds = interval_seconds
        self.max_workers = max_workers
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
            'timestamps': [],
            'concurrent_executions': 0,
            'peak_concurrent': 0
        }
        
        # Control flags
        self.running = True
        self.last_progress_time = time.time()
        self.throttle_enabled = False
        self.error_threshold = 0.3  # Throttle if error rate > 30%
        
        # Task queue for worker coordination
        self.task_queue = queue.Queue()
        
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
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            duration = time.time() - start
            
            if resp.status_code == 200:
                token = resp.json().get("accessToken")
                return token, duration
            else:
                return None, duration
        except Exception as e:
            duration = time.time() - start
            return None, duration

    def authenticate_sp(self) -> Tuple[Optional[str], float]:
        """Authenticate SP and return token"""
        url = f"{self.base_url}/partner/auth/login"
        headers = {"Content-Type": "application/json"}
        
        start = time.time()
        try:
            resp = requests.post(url, json=self.sp1_credentials, headers=headers, timeout=15)
            duration = time.time() - start
            
            if resp.status_code == 200:
                token = resp.json().get("data", {}).get("access_token")
                return token, duration
            else:
                return None, duration
        except Exception as e:
            duration = time.time() - start
            return None, duration

    def create_parlay(self, user_token: str) -> Tuple[Optional[str], float]:
        """Create parlay and return parlay ID"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        payload = {"marketLines": self.market_lines}
        headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
        
        start = time.time()
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            duration = time.time() - start
            
            if resp.status_code == 200:
                parlay_id = resp.json().get("data", {}).get("parlayId")
                return parlay_id, duration
            else:
                return None, duration
        except Exception as e:
            duration = time.time() - start
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
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            duration = time.time() - start
            
            if resp.status_code == 200:
                return True, duration
            else:
                return False, duration
        except Exception as e:
            duration = time.time() - start
            return False, duration

    def user_confirm_bet(self, parlay_id: str, user_token: str) -> Tuple[bool, float]:
        """User confirms bet"""
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        payload = {"parlayId": parlay_id, "odds": 800, "stake": 100}
        headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
        
        start = time.time()
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            duration = time.time() - start
            
            if resp.status_code == 200:
                return True, duration
            else:
                return False, duration
        except Exception as e:
            duration = time.time() - start
            return False, duration

    def sp_acknowledge_confirmation(self, sp_token: str, parlay_id: str) -> Tuple[bool, float]:
        """SP acknowledges confirmation"""
        # First get orders to find order_uuid
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        start = time.time()
        try:
            orders_resp = requests.get(orders_url, headers=headers, timeout=15)
            if orders_resp.status_code != 200:
                return False, time.time() - start
                
            orders = orders_resp.json().get("data", {}).get("orders", [])
            target_order = next((o for o in orders if o.get("p_id") == parlay_id and o.get("status") == "sent_confirmation"), None)
            
            if not target_order:
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
            
            resp = requests.post(url, json=payload, headers=headers, params=params, timeout=15)
            duration = time.time() - start
            
            if resp.status_code == 200:
                return True, duration
            else:
                return False, duration
                
        except Exception as e:
            duration = time.time() - start
            return False, duration

    def verify_finalization(self, user_token: str, parlay_id: str) -> Tuple[bool, float]:
        """Verify parlay is finalized"""
        url = f"{self.base_url}/parlay/api/v1/user/list?limit=50"
        headers = {"Authorization": f"Bearer {user_token}"}
        
        start = time.time()
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            duration = time.time() - start
            
            if resp.status_code == 200:
                user_data = resp.json()
                matching_parlays = [p for p in user_data.get("data", {}).get("orders", []) 
                                   if p.get("parlayId") == parlay_id and p.get("status") == "finalized"]
                return len(matching_parlays) > 0, duration
            else:
                return False, duration
        except Exception as e:
            duration = time.time() - start
            return False, duration

    def run_single_iteration(self, iteration: int, worker_id: int) -> bool:
        """Run a single iteration of Scenario 1"""
        iteration_start = time.time()
        step_times = {}
        
        # Track concurrent execution
        with self.lock:
            self.metrics['concurrent_executions'] += 1
            if self.metrics['concurrent_executions'] > self.metrics['peak_concurrent']:
                self.metrics['peak_concurrent'] = self.metrics['concurrent_executions']
        
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
            
            # Reduced wait time for aggressive testing
            time.sleep(1)
            
            # Step 6: SP Acknowledge
            ack_success, ack_time = self.sp_acknowledge_confirmation(sp_token, parlay_id)
            step_times['sp_acknowledge'] = ack_time
            if not ack_success:
                self.record_error("sp_acknowledge_failed")
                return False
            
            # Reduced wait time
            time.sleep(1)
            
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
            
            logger.info(f"✅ Worker{worker_id} Iteration {iteration}: SUCCESS in {total_time:.2f}s (Finalized: {finalized})")
            return True
            
        except Exception as e:
            total_time = time.time() - iteration_start
            logger.error(f"❌ Worker{worker_id} Iteration {iteration}: EXCEPTION in {total_time:.2f}s - {e}")
            self.record_error("iteration_exception")
            return False
        finally:
            # Decrease concurrent counter
            with self.lock:
                self.metrics['concurrent_executions'] -= 1

    def record_error(self, error_type: str):
        """Record an error in metrics"""
        with self.lock:
            self.metrics['error_counts'][error_type] += 1

    def check_and_apply_throttle(self):
        """Check error rate and apply throttling if needed"""
        with self.lock:
            total = self.metrics['total_iterations']
            failed = self.metrics['failed_iterations']
            
            if total > 5:  # Only check after some iterations
                error_rate = failed / total
                if error_rate > self.error_threshold and not self.throttle_enabled:
                    self.throttle_enabled = True
                    logger.warning(f"⚠️  High error rate ({error_rate:.1%}) detected. Enabling throttling...")
                elif error_rate <= 0.1 and self.throttle_enabled:  # Re-enable if error rate drops
                    self.throttle_enabled = False
                    logger.info("✅ Error rate improved. Disabling throttling...")

    def log_progress_report(self):
        """Log progress report"""
        with self.lock:
            elapsed = time.time() - self.start_time
            total = self.metrics['total_iterations']
            success = self.metrics['successful_iterations']
            failed = self.metrics['failed_iterations']
            success_rate = (success / total * 100) if total > 0 else 0
            
            logger.info(f"\n🚀 AGGRESSIVE PROGRESS REPORT - {elapsed/60:.1f} minutes elapsed")
            logger.info(f"   Iterations: {total} total, {success} success, {failed} failed ({success_rate:.1f}% success rate)")
            logger.info(f"   Finalized Parlays: {self.metrics['finalized_parlays']}")
            logger.info(f"   Peak Concurrent: {self.metrics['peak_concurrent']}")
            logger.info(f"   Throttling: {'ENABLED' if self.throttle_enabled else 'DISABLED'}")
            
            # Average response times
            if self.metrics['response_times']['total_iteration']:
                avg_iteration_time = statistics.mean(self.metrics['response_times']['total_iteration'])
                throughput = total / (elapsed / 60) if elapsed > 0 else 0
                logger.info(f"   Average iteration time: {avg_iteration_time:.2f}s")
                logger.info(f"   Current throughput: {throughput:.2f} iterations/minute")

    def worker_thread(self, worker_id: int):
        """Worker thread that processes tasks from the queue"""
        while self.running:
            try:
                iteration = self.task_queue.get(timeout=1)
                if iteration is None:  # Shutdown signal
                    break
                    
                success = self.run_single_iteration(iteration, worker_id)
                
                with self.lock:
                    if success:
                        self.metrics['successful_iterations'] += 1
                    else:
                        self.metrics['failed_iterations'] += 1
                    self.metrics['timestamps'].append(time.time())
                
                self.task_queue.task_done()
                
                # Throttling: sleep if error rate is high
                if self.throttle_enabled:
                    time.sleep(2)
                    
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} exception: {e}")

    def generate_final_report(self):
        """Generate comprehensive final report"""
        elapsed = self.end_time - self.start_time
        total = self.metrics['total_iterations']
        success = self.metrics['successful_iterations'] 
        failed = self.metrics['failed_iterations']
        success_rate = (success / total * 100) if total > 0 else 0
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🔥 AGGRESSIVE LOAD TEST FINAL REPORT")
        logger.info(f"{'='*80}")
        logger.info(f"Duration: {elapsed/60:.2f} minutes ({elapsed:.1f} seconds)")
        logger.info(f"Configuration: {self.max_workers} workers, {self.interval_seconds}s intervals")
        logger.info(f"Total Iterations: {total}")
        logger.info(f"Successful: {success} ({success_rate:.1f}%)")
        logger.info(f"Failed: {failed} ({100-success_rate:.1f}%)")
        logger.info(f"Finalized Parlays: {self.metrics['finalized_parlays']}")
        logger.info(f"Peak Concurrent Executions: {self.metrics['peak_concurrent']}")
        
        # Throughput
        iterations_per_minute = total / (elapsed / 60) if elapsed > 0 else 0
        logger.info(f"Average Throughput: {iterations_per_minute:.2f} iterations/minute")
        
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

    def run_aggressive_load_test(self):
        """Run the aggressive load test"""
        self.start_time = time.time()
        end_time = self.start_time + (self.duration_minutes * 60)
        
        logger.info(f"🔥 Starting AGGRESSIVE 10-minute load test - Scenario 1")
        logger.info(f"⚙️  Configuration: {self.duration_minutes} minutes, {self.interval_seconds}s intervals, {self.max_workers} workers")
        logger.info(f"📊 Progress reports every 30 seconds")
        logger.info(f"🔄 Press Ctrl+C to stop gracefully\n")
        
        # Start worker threads
        workers = []
        for i in range(self.max_workers):
            worker = threading.Thread(target=self.worker_thread, args=(i+1,))
            worker.start()
            workers.append(worker)
        
        iteration = 0
        
        try:
            while self.running and time.time() < end_time:
                iteration += 1
                
                # Add task to queue
                self.task_queue.put(iteration)
                
                with self.lock:
                    self.metrics['total_iterations'] += 1
                
                # Check throttling
                self.check_and_apply_throttle()
                
                # Progress report every 30 seconds
                if time.time() - self.last_progress_time >= 30:
                    self.log_progress_report()
                    self.last_progress_time = time.time()
                
                # Wait before next iteration
                if time.time() < end_time - self.interval_seconds:
                    sleep_time = self.interval_seconds
                    if self.throttle_enabled:
                        sleep_time *= 2  # Double interval when throttled
                    time.sleep(sleep_time)
        
        finally:
            # Shutdown workers
            logger.info("🔄 Shutting down workers...")
            self.running = False
            
            # Send shutdown signals
            for _ in range(self.max_workers):
                self.task_queue.put(None)
            
            # Wait for workers to finish
            for worker in workers:
                worker.join(timeout=5)
        
        self.end_time = time.time()
        self.generate_final_report()

def main():
    """Main execution function"""
    # Aggressive configuration
    DURATION_MINUTES = 10
    INTERVAL_SECONDS = 5  # More aggressive: 5 seconds vs 30s
    MAX_WORKERS = 3      # Concurrent execution
    
    runner = AggressiveLoadTestRunner(
        duration_minutes=DURATION_MINUTES, 
        interval_seconds=INTERVAL_SECONDS,
        max_workers=MAX_WORKERS
    )
    
    try:
        runner.run_aggressive_load_test()
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
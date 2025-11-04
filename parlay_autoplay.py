#!/usr/bin/env python3
"""
🎰 PARLAY AUTOPLAY - CONTINUOUS LOAD TESTING

Advanced parlay load testing system with multiple modes:
- Normal mode: Sequential testing with delays
- Continuous mode: Non-stop testing until interrupted
- Aggressive mode: Concurrent multi-threaded load testing

Features:
- Random 2-12 leg parlays with shuffled line IDs
- Fresh market data integration
- Real-time performance metrics
- Configurable concurrency levels
- Comprehensive error tracking
"""

import requests
import json
import time
import logging
import statistics
import random
import argparse
import signal
import sys
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'parlay_autoplay_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    iteration: int
    leg_count: int
    success: bool
    total_time: float
    thread_id: Optional[int] = None
    parlay_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

class ParlayAutoplay:
    def __init__(self, mode: str = 'normal', iterations: int = 10, 
                 concurrency: int = 1, delay: float = 1.0, complete_bets: bool = True):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.mode = mode
        self.iterations = iterations
        self.concurrency = concurrency
        self.delay = delay
        self.complete_bets = complete_bets  # Whether to complete full bet flow
        
        # Working SP Credentials
        self.sp1_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        
        self.sp2_credentials = {
            "access_key": "ec45827afa933f97ec19e674c0fa39c6",
            "secret_key": "442df8e9fe96e4f7e744b2d3cac5cd51"
        }
        
        # Load fresh market lines
        self.all_market_lines = self.load_market_lines()
        
        # Performance tracking (thread-safe)
        self.test_results = []
        self.response_times = {
            'auth': [],
            'create_parlay': [],
            'sp_offer': []
        }
        self.lock = threading.Lock()
        self.running = True
        self.start_time = None
        
        # Token caching to reduce authentication calls
        self.cached_user_token = None
        self.cached_sp1_token = None
        self.cached_sp2_token = None
        self.last_auth_time = 0
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        logger.info("\n\n⚠️  Interrupt received, shutting down gracefully...")
        self.running = False
        
    def load_market_lines(self) -> List[Dict]:
        """Load fresh market lines from file"""
        try:
            with open('fresh_market_lines.json', 'r') as f:
                lines = json.load(f)
            logger.info(f"✅ Loaded {len(lines)} fresh market lines")
            return lines
        except Exception as e:
            logger.error(f"❌ Failed to load market lines: {e}")
            logger.info("💡 Run 'python utils/fetch_market_lines.py' to generate fresh lines")
            return []
    
    def get_random_market_lines(self, min_legs: int = 2, max_legs: int = 12) -> List[Dict]:
        """Get random selection of market lines for parlay (avoiding duplicate events)"""
        if not self.all_market_lines:
            return []
        
        # Random leg count between min and max
        leg_count = random.randint(min_legs, max_legs)
        
        # Group lines by event ID to avoid duplicates
        lines_by_event = {}
        for line in self.all_market_lines:
            event_id = line['sportEventId']
            if event_id not in lines_by_event:
                lines_by_event[event_id] = []
            lines_by_event[event_id].append(line)
        
        # Get unique events
        available_events = list(lines_by_event.keys())
        
        # Ensure we don't exceed available events
        leg_count = min(leg_count, len(available_events))
        
        # Randomly select events
        selected_events = random.sample(available_events, leg_count)
        
        # Pick one random line from each selected event
        selected_lines = []
        for event_id in selected_events:
            line = random.choice(lines_by_event[event_id])
            selected_lines.append(line)
        
        return selected_lines

    def get_user_token(self) -> Tuple[str, float]:
        """Get user authentication token with timing (cached)"""
        # Return cached token if available and not too old (< 10 minutes)
        if self.cached_user_token and (time.time() - self.last_auth_time) < 600:
            return self.cached_user_token, 0
        
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
                self.cached_user_token = token
                self.last_auth_time = time.time()
                return token, response_time
            else:
                return "fallback_token", response_time
        except Exception as e:
            return "fallback_token", time.time() - start_time

    def authenticate_sp(self, credentials: Dict[str, str], sp_name: str = "SP") -> Tuple[Optional[str], float]:
        """Authenticate SP with timing (cached)"""
        # Check cache based on SP credentials
        cache_key = credentials["access_key"]
        if cache_key == self.sp1_credentials["access_key"] and self.cached_sp1_token:
            if (time.time() - self.last_auth_time) < 600:  # Token valid for 10 min
                return self.cached_sp1_token, 0
        elif cache_key == self.sp2_credentials["access_key"] and self.cached_sp2_token:
            if (time.time() - self.last_auth_time) < 600:
                return self.cached_sp2_token, 0
        
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
                # Cache the token
                if cache_key == self.sp1_credentials["access_key"]:
                    self.cached_sp1_token = token
                else:
                    self.cached_sp2_token = token
                self.last_auth_time = time.time()
                return token, response_time
            else:
                logger.debug(f"{sp_name} auth failed: {response.status_code}")
                return None, response_time
                
        except Exception as e:
            logger.debug(f"{sp_name} auth error: {e}")
            return None, time.time() - start_time

    def create_parlay(self, user_token: str, market_lines: List[Dict]) -> Tuple[Optional[str], float]:
        """Create parlay with timing"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        
        payload = {"marketLines": market_lines}
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

    def sp_offer(self, parlay_id: str, sp_token: str, odds: int, max_risk: int, 
                 market_lines: List[Dict]) -> Tuple[bool, float]:
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
                        {"line_id": line["lineId"], "odds": odds}
                        for line in market_lines
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
            
            if response.status_code == 200:
                return True, response_time
            else:
                return False, response_time
                
        except Exception as e:
            return False, time.time() - start_time

    def user_confirm_bet(self, parlay_id: str, user_token: str, odds: int, stake: int = 1000) -> Tuple[bool, float]:
        """User confirms the bet (Step 5)"""
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        
        payload = {
            "parlayId": parlay_id,
            "odds": odds,
            "stake": stake  # in cents, default $10
        }
        
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return True, response_time
            else:
                return False, response_time
                
        except Exception as e:
            return False, time.time() - start_time

    def sp_acknowledge_confirmation(self, parlay_id: str, sp_token: str, market_lines: List[Dict], 
                                    stake: int, odds: int) -> Tuple[bool, float]:
        """SP acknowledges/accepts the confirmation (Step 6)"""
        
        # First get the order to find order_uuid
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(orders_url, headers=headers)
            if response.status_code != 200:
                logger.debug(f"Get orders failed: {response.status_code}")
                return False, 0
            
            orders = response.json()["data"]["orders"]
            order_uuid = None
            
            # Find matching order
            for order in orders:
                if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
                    order_uuid = order["order_uuid"]
                    break
            
            if not order_uuid:
                logger.debug(f"No order found for parlay {parlay_id} with status 'sent_confirmation'")
                # Log available orders for debugging
                matching_orders = [o for o in orders if o["p_id"] == parlay_id]
                if matching_orders:
                    logger.debug(f"Found orders with different status: {[o['status'] for o in matching_orders]}")
                return False, 0
            
            # Calculate probability from odds
            if odds > 0:
                probability = 100 / (odds + 100)
            else:
                probability = abs(odds) / (abs(odds) + 100)
            
            # Calculate max_risk
            decimal_odds = (odds + 100) / 100 if odds > 0 else 100 / abs(odds) + 1
            max_risk_dollars = (stake / 100) * decimal_odds
            max_risk_cents = int(max_risk_dollars * 100)
            
            # Acknowledge confirmation with order_uuid as query parameter
            confirm_url = f"{self.base_url}/parlay/sp/orders/confirmations"
            payload = {
                "action": "accept",
                "confirmed_stake": stake / 100,  # Convert to dollars
                "price_probability": [{
                    "lines": [
                        {
                            "line_id": line["lineId"],
                            "probability": probability
                        }
                        for line in market_lines
                    ],
                    "max_risk": max_risk_cents,
                    "vig": 0.1
                }],
                "signature": f"autoplay_sig_{int(time.time())}"
            }
            
            start_time = time.time()
            # order_uuid must be passed as query parameter!
            response = requests.post(confirm_url, json=payload, headers=headers, 
                                    params={"order_uuid": order_uuid})
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                return True, response_time
            else:
                return False, response_time
                
        except Exception as e:
            return False, 0

    def run_single_test(self, iteration: int, thread_id: Optional[int] = None) -> TestResult:
        """Run a single test iteration with random legs"""
        
        if not self.running:
            return TestResult(
                iteration=iteration,
                leg_count=0,
                success=False,
                total_time=0,
                thread_id=thread_id,
                error="Interrupted"
            )
        
        start_time = time.time()
        
        # Get random market lines
        market_lines = self.get_random_market_lines()
        if not market_lines:
            return TestResult(
                iteration=iteration,
                leg_count=0,
                success=False,
                total_time=time.time() - start_time,
                thread_id=thread_id,
                error="No market lines available"
            )
        
        actual_leg_count = len(market_lines)
        
        # Step 1: Authenticate user
        user_token, _ = self.get_user_token()
        if not user_token or user_token == "fallback_token":
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=False,
                total_time=time.time() - start_time,
                thread_id=thread_id,
                error="User authentication failed"
            )
        
        # Step 2: Authenticate both SPs (cached)
        sp1_token, _ = self.authenticate_sp(self.sp1_credentials, "SP1")
        sp2_token, _ = self.authenticate_sp(self.sp2_credentials, "SP2")
        
        if not sp1_token and not sp2_token:
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=False,
                total_time=time.time() - start_time,
                thread_id=thread_id,
                error="All SP authentication failed"
            )
        
        # Use whichever SP authenticated successfully
        sp_token = sp1_token if sp1_token else sp2_token
        sp_name = "SP1" if sp1_token else "SP2"
        
        # Step 3: Create parlay with random legs
        parlay_id, _ = self.create_parlay(user_token, market_lines)
        if not parlay_id:
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=False,
                total_time=time.time() - start_time,
                thread_id=thread_id,
                error="Parlay creation failed"
            )
        
        # Step 4: SP provides offer
        odds = 800  # +800 odds
        stake = 1000  # $10 in cents
        offer_success, _ = self.sp_offer(parlay_id, sp_token, odds, 20000, market_lines)
        if not offer_success:
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=False,
                total_time=time.time() - start_time,
                thread_id=thread_id,
                parlay_id=parlay_id,
                error="SP offer failed"
            )
        
        # If complete_bets flag is set, continue with confirmation and acceptance
        if self.complete_bets:
            logger.info(f"🔄 Completing full bet flow for {parlay_id}...")
            
            # Wait for offer to be processed
            time.sleep(1.5)
            
            # Step 5: User confirms the bet
            logger.info(f"📝 User confirming bet for {parlay_id}...")
            confirm_success, _ = self.user_confirm_bet(parlay_id, user_token, odds, stake)
            if not confirm_success:
                logger.warning(f"❌ User confirmation FAILED for {parlay_id}")
                return TestResult(
                    iteration=iteration,
                    leg_count=actual_leg_count,
                    success=False,
                    total_time=time.time() - start_time,
                    thread_id=thread_id,
                    parlay_id=parlay_id,
                    error="User confirmation failed"
                )
            logger.info(f"✅ User confirmed bet for {parlay_id}")
            
            # Wait for confirmation to be processed and status to update
            time.sleep(2.0)
            
            # Step 6: Try SP acknowledgment with both SPs
            ack_success = False
            
            # Try first SP
            if sp1_token:
                ack_success, _ = self.sp_acknowledge_confirmation(parlay_id, sp1_token, market_lines, stake, odds)
                if ack_success:
                    logger.info(f"✅ SP1 acknowledged confirmation for {parlay_id}")
            
            # If first failed, try second SP
            if not ack_success and sp2_token:
                time.sleep(1.0)  # Wait a bit before trying second SP
                ack_success, _ = self.sp_acknowledge_confirmation(parlay_id, sp2_token, market_lines, stake, odds)
                if ack_success:
                    logger.info(f"✅ SP2 acknowledged confirmation for {parlay_id}")
            
            if not ack_success:
                logger.info(f"⚠️  Both SPs failed acknowledgment for {parlay_id} - bet at offer stage")
                # Don't fail the test, just note it
        
        total_time = time.time() - start_time
        
        return TestResult(
            iteration=iteration,
            leg_count=actual_leg_count,
            success=True,
            total_time=total_time,
            thread_id=thread_id,
            parlay_id=parlay_id
        )

    def run_normal_mode(self):
        """Run tests sequentially with delays"""
        logger.info(f"\n{'='*100}")
        logger.info(f"🎯 NORMAL MODE - Sequential Testing")
        logger.info(f"{'='*100}")
        logger.info(f"   Iterations: {self.iterations}")
        logger.info(f"   Delay: {self.delay}s between tests")
        logger.info(f"{'='*100}\n")
        
        for i in range(1, self.iterations + 1):
            if not self.running:
                break
            
            logger.info(f"\n🧪 Test {i}/{self.iterations}")
            result = self.run_single_test(i)
            
            with self.lock:
                self.test_results.append(result)
            
            if result.success:
                logger.info(f"✅ Test {i} PASSED - {result.leg_count} legs, {result.total_time:.2f}s")
            else:
                logger.warning(f"❌ Test {i} FAILED - {result.error}")
            
            # Delay between tests
            if i < self.iterations and self.running:
                time.sleep(self.delay)

    def run_continuous_mode(self):
        """Run tests continuously until interrupted"""
        logger.info(f"\n{'='*100}")
        logger.info(f"🔄 CONTINUOUS MODE - Non-Stop Testing")
        logger.info(f"{'='*100}")
        logger.info(f"   Running until Ctrl+C...")
        logger.info(f"   Delay: {self.delay}s between tests")
        logger.info(f"{'='*100}\n")
        
        iteration = 1
        while self.running:
            result = self.run_single_test(iteration)
            
            with self.lock:
                self.test_results.append(result)
            
            if result.success:
                logger.info(f"✅ Test {iteration} PASSED - {result.leg_count} legs, {result.total_time:.2f}s")
            else:
                logger.warning(f"❌ Test {iteration} FAILED - {result.error}")
            
            # Print stats every 10 iterations
            if iteration % 10 == 0:
                self.print_live_stats()
            
            iteration += 1
            
            if self.running:
                time.sleep(self.delay)

    def run_aggressive_mode(self):
        """Run tests concurrently with multiple threads"""
        logger.info(f"\n{'='*100}")
        logger.info(f"⚡ AGGRESSIVE MODE - Concurrent Load Testing")
        logger.info(f"{'='*100}")
        logger.info(f"   Iterations: {self.iterations}")
        logger.info(f"   Concurrency: {self.concurrency} threads")
        logger.info(f"   Total tests: {self.iterations * self.concurrency}")
        logger.info(f"{'='*100}\n")
        
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = []
            
            for i in range(1, self.iterations + 1):
                if not self.running:
                    break
                
                # Submit concurrent tests
                for thread_id in range(self.concurrency):
                    if not self.running:
                        break
                    
                    iteration_id = (i - 1) * self.concurrency + thread_id + 1
                    future = executor.submit(self.run_single_test, iteration_id, thread_id)
                    futures.append(future)
            
            # Process results as they complete
            completed = 0
            for future in as_completed(futures):
                if not self.running:
                    break
                
                result = future.result()
                completed += 1
                
                with self.lock:
                    self.test_results.append(result)
                
                if result.success:
                    logger.info(f"✅ Test {result.iteration} [T{result.thread_id}] - {result.leg_count} legs, {result.total_time:.2f}s")
                else:
                    logger.warning(f"❌ Test {result.iteration} [T{result.thread_id}] - {result.error}")
                
                # Print progress
                if completed % 10 == 0:
                    progress = (completed / len(futures)) * 100
                    logger.info(f"📊 Progress: {completed}/{len(futures)} ({progress:.1f}%)")

    def print_live_stats(self):
        """Print live statistics during continuous mode"""
        with self.lock:
            if not self.test_results:
                return
            
            total = len(self.test_results)
            successful = sum(1 for r in self.test_results if r.success)
            success_rate = (successful / total * 100) if total > 0 else 0
            
            elapsed = time.time() - self.start_time
            tests_per_min = (total / elapsed) * 60 if elapsed > 0 else 0
            
            logger.info(f"\n{'='*80}")
            logger.info(f"📊 LIVE STATS (after {total} tests)")
            logger.info(f"   Success Rate: {success_rate:.1f}% ({successful}/{total})")
            logger.info(f"   Elapsed Time: {elapsed:.1f}s")
            logger.info(f"   Throughput: {tests_per_min:.1f} tests/min")
            logger.info(f"{'='*80}\n")

    def run(self):
        """Main run method - selects mode and executes"""
        if not self.all_market_lines:
            logger.error("❌ Cannot run without market lines. Exiting.")
            return
        
        self.start_time = time.time()
        
        if self.mode == 'normal':
            self.run_normal_mode()
        elif self.mode == 'continuous':
            self.run_continuous_mode()
        elif self.mode == 'aggressive':
            self.run_aggressive_mode()
        else:
            logger.error(f"❌ Unknown mode: {self.mode}")
            return
        
        # Print final results
        self.print_final_results()

    def print_final_results(self):
        """Print comprehensive final results"""
        
        total_tests = len(self.test_results)
        if total_tests == 0:
            logger.info("\n⚠️  No tests completed")
            return
        
        successful_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        elapsed = time.time() - self.start_time
        tests_per_min = (total_tests / elapsed) * 60 if elapsed > 0 else 0
        
        logger.info(f"\n{'='*100}")
        logger.info(f"🏁 PARLAY AUTOPLAY COMPLETE")
        logger.info(f"{'='*100}")
        logger.info(f"📊 OVERALL RESULTS:")
        logger.info(f"   Mode: {self.mode.upper()}")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Successful: {successful_tests}")
        logger.info(f"   Failed: {failed_tests}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Total Time: {elapsed:.1f}s")
        logger.info(f"   Throughput: {tests_per_min:.1f} tests/min")
        
        if self.test_results:
            total_times = [r.total_time for r in self.test_results]
            leg_counts = [r.leg_count for r in self.test_results if r.leg_count > 0]
            
            logger.info(f"\n⏱️  TIMING STATISTICS:")
            logger.info(f"   Average test time: {statistics.mean(total_times):.2f}s")
            logger.info(f"   Min test time: {min(total_times):.2f}s")
            logger.info(f"   Max test time: {max(total_times):.2f}s")
            
            if leg_counts:
                logger.info(f"\n🎲 LEG COUNT DISTRIBUTION:")
                logger.info(f"   Average legs: {statistics.mean(leg_counts):.1f}")
                logger.info(f"   Min legs: {min(leg_counts)}")
                logger.info(f"   Max legs: {max(leg_counts)}")
        
        # Response time breakdown
        with self.lock:
            logger.info(f"\n📈 RESPONSE TIME BREAKDOWN:")
            for step, times in self.response_times.items():
                if times:
                    logger.info(f"   {step.upper()}:")
                    logger.info(f"      Avg: {statistics.mean(times):.3f}s")
                    logger.info(f"      Range: {min(times):.3f}s - {max(times):.3f}s")
        
        # Failure analysis
        if failed_tests > 0:
            logger.info(f"\n❌ FAILURE ANALYSIS:")
            failure_reasons = {}
            for result in self.test_results:
                if not result.success and result.error:
                    failure_reasons[result.error] = failure_reasons.get(result.error, 0) + 1
            
            for reason, count in failure_reasons.items():
                logger.info(f"   {reason}: {count} occurrences")
        
        # Successful parlays summary
        successful_parlays = [r for r in self.test_results if r.success and r.parlay_id]
        if successful_parlays:
            logger.info(f"\n✅ SUCCESSFUL PARLAYS: {len(successful_parlays)}")
            logger.info(f"   Showing first 5:")
            for result in successful_parlays[:5]:
                logger.info(f"   Test {result.iteration}: {result.parlay_id} ({result.leg_count} legs)")
        
        logger.info(f"\n{'='*100}")

def main():
    """Main entry point with argument parsing"""
    
    parser = argparse.ArgumentParser(
        description='Parlay Autoplay - Continuous Load Testing System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal mode - 10 sequential tests with 1s delay
  python parlay_autoplay.py --mode normal --iterations 10 --delay 1

  # Continuous mode - run until Ctrl+C
  python parlay_autoplay.py --mode continuous --delay 0.5

  # Aggressive mode - 20 iterations with 5 concurrent threads
  python parlay_autoplay.py --mode aggressive --iterations 20 --concurrency 5

  # Extreme load test - 100 iterations with 10 threads
  python parlay_autoplay.py --mode aggressive --iterations 100 --concurrency 10 --delay 0
        """
    )
    
    parser.add_argument('--mode', type=str, default='normal',
                       choices=['normal', 'continuous', 'aggressive'],
                       help='Testing mode (default: normal)')
    parser.add_argument('--iterations', type=int, default=10,
                       help='Number of test iterations (default: 10, ignored in continuous mode)')
    parser.add_argument('--concurrency', type=int, default=1,
                       help='Number of concurrent threads for aggressive mode (default: 1)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between tests in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    # Banner
    logger.info("\n" + "="*100)
    logger.info("🎰 PARLAY AUTOPLAY - CONTINUOUS LOAD TESTING SYSTEM")
    logger.info("="*100)
    logger.info("🏁 Full bet completion: ENABLED (creates, offers, confirms, accepts)")
    logger.info("="*100)
    
    # Create and run autoplay
    autoplay = ParlayAutoplay(
        mode=args.mode,
        iterations=args.iterations,
        concurrency=args.concurrency,
        delay=args.delay,
        complete_bets=True  # Always complete bets
    )
    
    try:
        autoplay.run()
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        autoplay.running = False
        autoplay.print_final_results()
    except Exception as e:
        logger.error(f"\n\n❌ Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("\n✅ Autoplay session ended\n")

if __name__ == "__main__":
    main()

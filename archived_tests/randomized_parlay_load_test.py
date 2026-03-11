#!/usr/bin/env python3
"""
🎲 RANDOMIZED PARLAY LOAD TEST - DYNAMIC LEG SHUFFLING

Advanced load testing with randomized parlay legs:
- Random leg count: 2-12 legs per parlay
- Shuffled line IDs for each bet
- Fresh market line data
- Multiple test iterations
- Comprehensive performance tracking
"""

import requests
import json
import time
import logging
import statistics
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'randomized_load_test_{int(time.time())}.log'),
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
    parlay_id: Optional[str] = None
    error: Optional[str] = None

class RandomizedParlayLoadTest:
    def __init__(self, iterations: int = 10):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.iterations = iterations
        
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
        
        # Performance tracking
        self.test_results = []
        self.response_times = {
            'auth': [],
            'create_parlay': [],
            'sp_offer': [],
            'user_confirm': [],
            'sp_accept': []
        }
        
    def load_market_lines(self) -> List[Dict]:
        """Load fresh market lines from file"""
        try:
            with open('fresh_market_lines.json', 'r') as f:
                lines = json.load(f)
            logger.info(f"✅ Loaded {len(lines)} fresh market lines")
            return lines
        except Exception as e:
            logger.error(f"❌ Failed to load market lines: {e}")
            return []
    
    def get_random_market_lines(self, min_legs: int = 2, max_legs: int = 12) -> List[Dict]:
        """Get random selection of market lines for parlay (avoiding duplicate events)"""
        if not self.all_market_lines:
            logger.error("❌ No market lines available")
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
        
        logger.info(f"🎲 Selected {leg_count} random legs from {leg_count} unique events")
        return selected_lines

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
            self.response_times['auth'].append(response_time)
            
            if response.status_code == 200:
                token = response.json().get("accessToken")
                return token, response_time
            else:
                logger.warning(f"⚠️  User auth failed: {response.status_code}")
                return "fallback_token", response_time
        except Exception as e:
            logger.error(f"❌ User auth error: {e}")
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
            self.response_times['auth'].append(response_time)
            
            if response.status_code == 200:
                token = response.json()["data"]["access_token"]
                return token, response_time
            else:
                logger.warning(f"⚠️  SP auth failed: {response.status_code}")
                return None, response_time
                
        except Exception as e:
            logger.error(f"❌ SP auth error: {e}")
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
            self.response_times['create_parlay'].append(response_time)
            
            if response.status_code == 200:
                parlay_id = response.json()["data"]["parlayId"]
                logger.info(f"✅ Parlay created: {parlay_id} ({len(market_lines)} legs)")
                return parlay_id, response_time
            else:
                logger.warning(f"⚠️  Parlay creation failed: {response.status_code}")
                logger.debug(f"Response: {response.text}")
                return None, response_time
                
        except Exception as e:
            logger.error(f"❌ Parlay creation error: {e}")
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
            self.response_times['sp_offer'].append(response_time)
            
            if response.status_code == 200:
                return True, response_time
            else:
                logger.warning(f"⚠️  SP offer failed: {response.status_code}")
                return False, response_time
                
        except Exception as e:
            logger.error(f"❌ SP offer error: {e}")
            return False, time.time() - start_time

    def run_single_test(self, iteration: int, leg_count: int = None) -> TestResult:
        """Run a single test iteration with random legs"""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🧪 TEST ITERATION {iteration}/{self.iterations}")
        logger.info(f"{'='*80}")
        
        start_time = time.time()
        
        # Get random market lines
        market_lines = self.get_random_market_lines()
        if not market_lines:
            return TestResult(
                iteration=iteration,
                leg_count=0,
                success=False,
                total_time=time.time() - start_time,
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
                error="User authentication failed"
            )
        
        # Step 2: Authenticate SPs
        sp1_token, _ = self.authenticate_sp(self.sp1_credentials)
        if not sp1_token:
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=False,
                total_time=time.time() - start_time,
                error="SP1 authentication failed"
            )
        
        # Step 3: Create parlay with random legs
        parlay_id, _ = self.create_parlay(user_token, market_lines)
        if not parlay_id:
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=False,
                total_time=time.time() - start_time,
                error="Parlay creation failed"
            )
        
        # Step 4: SP provides offer
        offer_success, _ = self.sp_offer(parlay_id, sp1_token, 800, 20000, market_lines)
        if not offer_success:
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=False,
                total_time=time.time() - start_time,
                parlay_id=parlay_id,
                error="SP offer failed"
            )
        
        total_time = time.time() - start_time
        
        logger.info(f"✅ Test {iteration} PASSED - {actual_leg_count} legs, {total_time:.2f}s")
        
        return TestResult(
            iteration=iteration,
            leg_count=actual_leg_count,
            success=True,
            total_time=total_time,
            parlay_id=parlay_id
        )

    def run_load_test(self):
        """Run full load test with multiple iterations"""
        
        logger.info(f"\n{'='*100}")
        logger.info(f"🚀 RANDOMIZED PARLAY LOAD TEST STARTING")
        logger.info(f"{'='*100}")
        logger.info(f"📊 Configuration:")
        logger.info(f"   - Iterations: {self.iterations}")
        logger.info(f"   - Leg range: 2-12 per parlay")
        logger.info(f"   - Available lines: {len(self.all_market_lines)}")
        logger.info(f"   - Random shuffling: ✅ Enabled")
        logger.info(f"{'='*100}\n")
        
        # Run all test iterations
        for i in range(1, self.iterations + 1):
            result = self.run_single_test(i)
            self.test_results.append(result)
            
            # Small delay between tests
            if i < self.iterations:
                time.sleep(1)
        
        # Print comprehensive results
        self.print_results()

    def print_results(self):
        """Print comprehensive test results"""
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\n{'='*100}")
        logger.info(f"🏁 RANDOMIZED PARLAY LOAD TEST COMPLETE")
        logger.info(f"{'='*100}")
        logger.info(f"📊 OVERALL RESULTS:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Successful: {successful_tests}")
        logger.info(f"   Failed: {failed_tests}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        
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
        
        # Successful parlays
        successful_parlays = [r for r in self.test_results if r.success and r.parlay_id]
        if successful_parlays:
            logger.info(f"\n✅ SUCCESSFUL PARLAY IDs ({len(successful_parlays)}):")
            for result in successful_parlays[:10]:  # Show first 10
                logger.info(f"   Iteration {result.iteration}: {result.parlay_id} ({result.leg_count} legs)")
            if len(successful_parlays) > 10:
                logger.info(f"   ... and {len(successful_parlays) - 10} more")
        
        logger.info(f"\n{'='*100}")

def main():
    """Main test runner"""
    
    # Configuration
    ITERATIONS = 10  # Number of test iterations
    
    logger.info("🎲 Initializing Randomized Parlay Load Test...")
    
    test = RandomizedParlayLoadTest(iterations=ITERATIONS)
    test.run_load_test()
    
    logger.info("\n✅ Load test completed!")

if __name__ == "__main__":
    main()

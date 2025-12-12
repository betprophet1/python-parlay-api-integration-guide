#!/usr/bin/env python3
"""
🎰 PARLAY AUTOPLAY - E2E CHAOTIC TESTING WITH VALIDATION

Advanced parlay testing system with chaos engineering and validation:
- Normal mode: Sequential testing with delays
- Continuous mode: Non-stop testing until interrupted
- Aggressive mode: Concurrent multi-threaded load testing
- Chaos mode: Mixed valid/invalid parlays to verify API validation

Features:
- Random 2-12 leg parlays with chaotic combinations
- Validation rule testing (both sides moneyline, negative spreads, etc.)
- Full E2E bet completion (create → offer → confirm → accept)
- Fresh market data integration
- Real-time performance metrics and validation tracking
- Configurable concurrency levels
- Comprehensive error and validation tracking
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
import os
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

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
    # Chaos testing fields
    parlay_type: str = "valid"  # 'valid' or violation type
    expected_result: str = "accept"  # 'accept' or 'reject'
    actual_result: str = "unknown"  # 'accepted', 'rejected', 'error'
    validation_passed: bool = False  # True if actual matches expected
    # Probability type
    probability_type: str = "invalid"  # 'valid' (same-game) or 'invalid' (multi-event)

class ParlayAutoplay:
    def __init__(self, mode: str = 'normal', iterations: int = 10, 
                 concurrency: int = 1, delay: float = 1.0, complete_bets: bool = True,
                 chaos_mode: bool = False, chaos_invalid_rate: float = 0.5,
                 same_game_rate: float = 0.5, min_legs: int = 2, max_legs: int = 12):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.mode = mode
        self.iterations = iterations
        self.concurrency = concurrency
        self.delay = delay
        self.complete_bets = complete_bets  # Whether to complete full bet flow
        self.chaos_mode = chaos_mode  # Whether to enable chaos testing
        self.chaos_invalid_rate = chaos_invalid_rate  # % of invalid parlays in chaos mode
        self.same_game_rate = same_game_rate  # % of same-game parlays (valid probability)
        self.min_legs = min_legs  # Minimum number of legs per parlay
        self.max_legs = max_legs  # Maximum number of legs per parlay
        
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
        
        # Group lines by event for chaos testing
        self.lines_by_event = self._group_lines_by_event() if chaos_mode else {}
        
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
        
        # Chaos testing validation tracking
        self.validation_stats = {
            'valid_accepted': 0,
            'valid_rejected': 0,
            'rule1_rejected': 0,
            'rule1_accepted': 0,
            'rule2_rejected': 0,
            'rule2_accepted': 0,
            'rule3_rejected': 0,
            'rule3_accepted': 0,
            'rule4_rejected': 0,
            'rule4_accepted': 0,
            'rule5_rejected': 0,
            'rule5_accepted': 0
        }
        
        # Probability type tracking
        self.probability_stats = {
            'same_game_accepted': 0,      # Valid probability
            'same_game_rejected': 0,
            'multi_event_accepted': 0,    # Invalid probability
            'multi_event_rejected': 0
        }
        
        # Token caching to reduce authentication calls
        # Reduced cache time to 3 minutes for faster expiration detection
        self.cached_user_token = None
        self.cached_sp1_token = None
        self.cached_sp2_token = None
        self.last_user_auth_time = 0
        self.last_sp1_auth_time = 0
        self.last_sp2_auth_time = 0
        self.token_cache_duration = 180  # 3 minutes instead of 5
        
        # Track consecutive failures for auto-restart
        self.consecutive_sp_failures = 0
        self.max_consecutive_failures = 5  # Restart after 5 consecutive failures
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        logger.info("\n\n⚠️  Interrupt received, shutting down gracefully...")
        self.running = False
    
    def check_token_expiration_and_restart(self, error_msg: str):
        """Check if error is due to token expiration and raise exception to trigger restart"""
        # Increment consecutive failure counter
        self.consecutive_sp_failures += 1
        
        if self.consecutive_sp_failures >= self.max_consecutive_failures:
            logger.warning(f"\n{'='*100}")
            logger.warning(f"⚠️  DETECTED {self.consecutive_sp_failures} CONSECUTIVE SP OFFER FAILURES")
            logger.warning(f"{'='*100}")
            logger.warning("🔄 Likely cause: Token expiration or API rate limit")
            logger.warning("🔄 Triggering session restart...\n")
            
            # Raise exception to trigger restart at outer level
            raise Exception("TokenExpirationRestart")
        
        return False
    
    def reset_failure_counter(self):
        """Reset consecutive failure counter on successful test"""
        self.consecutive_sp_failures = 0
        
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
    
    def _get_market_name(self, market_id: int) -> str:
        """Get human-readable market name from market ID"""
        market_names = {
            11: "ML",
            16: "Spread",
            18: "Total",
            219: "ML",
            223: "Spread",
            225: "TeamTotal",
            256: "Spread",
            258: "AltTotal",
            406: "Market406",  # Custom market
            410: "Market410",  # Custom market
            412: "Market412"   # Custom market
        }
        return market_names.get(market_id, f"Market{market_id}")
    
    def _odds_to_probability(self, american_odds: int) -> float:
        """Convert American odds to implied probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)
    
    def _generate_valid_leg_probabilities(self, num_legs: int, target_combined_prob: float) -> List[float]:
        """Generate leg probabilities that multiply to approximately the target probability
        
        This ensures the combined probability matches the parlay odds for valid probability.
        
        Args:
            num_legs: Number of legs in the parlay
            target_combined_prob: Target combined probability (derived from parlay odds)
            
        Returns:
            List of leg probabilities that multiply close to target
        """
        # Start with equal distribution
        avg_prob = target_combined_prob ** (1 / num_legs)
        
        # Add some randomness while keeping product close to target
        probabilities = []
        for i in range(num_legs - 1):
            # Vary each leg by ±20% from average
            variation = random.uniform(0.8, 1.2)
            prob = avg_prob * variation
            # Clamp to realistic range
            prob = max(0.20, min(0.85, prob))
            probabilities.append(round(prob, 8))
        
        # Calculate last probability to hit target exactly
        product_so_far = 1.0
        for p in probabilities:
            product_so_far *= p
        
        last_prob = target_combined_prob / product_so_far
        # Clamp to realistic range
        last_prob = max(0.20, min(0.85, last_prob))
        probabilities.append(round(last_prob, 8))
        
        return probabilities
    
    def _group_lines_by_event(self) -> Dict:
        """Group lines by event and categorize by market type for chaos testing"""
        grouped = defaultdict(lambda: {
            'moneylines': [],
            'spreads': [],
            'totals': [],
            'all': []
        })
        
        for line in self.all_market_lines:
            event_id = line['sportEventId']
            market_id = line['marketId']
            
            grouped[event_id]['all'].append(line)
            
            # Categorize by market type
            if market_id in [11, 219]:  # Moneyline
                grouped[event_id]['moneylines'].append(line)
            elif market_id in [16, 223, 256, 410]:  # Spreads (added 410)
                grouped[event_id]['spreads'].append(line)
            elif market_id in [18, 225, 258, 412]:  # Totals (added 412)
                grouped[event_id]['totals'].append(line)
        
        return dict(grouped)
    
    def get_random_market_lines(self) -> Tuple[str, List[Dict], str]:
        """Get random selection of market lines for parlay
        
        Uses configured min_legs and max_legs from instance.
        
        Returns:
            Tuple[str, List[Dict], str]: (parlay_type, market_lines, probability_type)
            parlay_type: 'valid', 'rule1_both_sides_moneyline', etc.
            probability_type: 'valid' (same-game) or 'invalid' (multi-event)
        """
        if not self.all_market_lines:
            return "valid", [], "invalid"
        
        # If chaos mode is enabled, randomly generate valid or invalid parlays
        if self.chaos_mode:
            should_be_invalid = random.random() < self.chaos_invalid_rate
            
            if should_be_invalid:
                # Randomly choose which rule to violate
                violation_type = random.choice(['rule1', 'rule2', 'rule3', 'rule4', 'rule5'])
                
                if violation_type == 'rule1':
                    parlay_type, lines = self._generate_rule1_violation()
                    return parlay_type, lines, "invalid"  # Multi-event
                elif violation_type == 'rule2':
                    parlay_type, lines = self._generate_rule2_violation()
                    return parlay_type, lines, "invalid"
                elif violation_type == 'rule3':
                    parlay_type, lines = self._generate_rule3_violation()
                    return parlay_type, lines, "invalid"
                elif violation_type == 'rule4':
                    parlay_type, lines = self._generate_rule4_violation()
                    return parlay_type, lines, "invalid"
                elif violation_type == 'rule5':
                    parlay_type, lines = self._generate_rule5_violation()
                    return parlay_type, lines, "invalid"
        
        # Decide between same-game (valid probability) or multi-event (invalid probability)
        should_be_same_game = random.random() < self.same_game_rate
        
        if should_be_same_game:
            return self._generate_same_game_parlay(self.min_legs, self.max_legs)
        else:
            return self._generate_multi_event_parlay(self.min_legs, self.max_legs)
    
    def _generate_same_game_parlay(self, min_legs: int = 2, max_legs: int = 6) -> Tuple[str, List[Dict], str]:
        """Generate a same-game parlay (valid probability)
        
        Returns legs from the SAME event with different market types.
        This creates valid probability calculations.
        """
        if not self.all_market_lines:
            return "valid", [], "valid"
        
        # Random leg count (2-6 for same-game, typically smaller)
        leg_count = random.randint(min_legs, min(max_legs, 6))
        
        # Group lines by event
        lines_by_event = {}
        for line in self.all_market_lines:
            event_id = line['sportEventId']
            if event_id not in lines_by_event:
                lines_by_event[event_id] = []
            lines_by_event[event_id].append(line)
        
        # Find events with enough different market types
        suitable_events = []
        for event_id, lines in lines_by_event.items():
            # Count unique market types in this event
            market_types = set(line['marketId'] for line in lines)
            if len(market_types) >= leg_count:
                suitable_events.append(event_id)
        
        if not suitable_events:
            # Fallback to multi-event if no suitable same-game found
            return self._generate_multi_event_parlay(min_legs, max_legs)
        
        # Pick a random event
        selected_event = random.choice(suitable_events)
        event_lines = lines_by_event[selected_event]
        
        # Group by market type within this event
        lines_by_market = {}
        for line in event_lines:
            market_id = line['marketId']
            if market_id not in lines_by_market:
                lines_by_market[market_id] = []
            lines_by_market[market_id].append(line)
        
        # Pick one random line from different market types
        selected_markets = random.sample(list(lines_by_market.keys()), leg_count)
        selected_lines = []
        for market_id in selected_markets:
            line = random.choice(lines_by_market[market_id])
            selected_lines.append(line)
        
        return "valid", selected_lines, "valid"
    
    def _generate_multi_event_parlay(self, min_legs: int = 2, max_legs: int = 12) -> Tuple[str, List[Dict], str]:
        """Generate a multi-event parlay (invalid probability)
        
        Returns one line per event from DIFFERENT events.
        This creates invalid probability calculations.
        """
        if not self.all_market_lines:
            return "valid", [], "invalid"
        
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
        
        return "valid", selected_lines, "invalid"
    
    def _generate_rule1_violation(self) -> Tuple[str, List[Dict]]:
        """Rule 1: Both sides of moneyline from same event + valid legs (2-12 total legs)"""
        events_with_moneylines = [
            event_id for event_id, data in self.lines_by_event.items()
            if len(data['moneylines']) >= 2
        ]
        
        if not events_with_moneylines:
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        violation_event_id = random.choice(events_with_moneylines)
        moneylines = self.lines_by_event[violation_event_id]['moneylines']
        
        # Find opposing sides (different outcomeIds)
        unique_outcomes = {}
        for ml in moneylines:
            outcome_id = ml['outcomeId']
            if outcome_id not in unique_outcomes:
                unique_outcomes[outcome_id] = ml
        
        if len(unique_outcomes) < 2:
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        # Start with the violation: both sides of moneyline
        lines = list(unique_outcomes.values())[:2]
        
        # Add 0-10 more valid legs from different events
        num_additional_legs = random.randint(0, 10)
        available_events = [eid for eid in self.lines_by_event.keys() if eid != violation_event_id]
        
        if available_events and num_additional_legs > 0:
            num_to_add = min(num_additional_legs, len(available_events))
            additional_events = random.sample(available_events, num_to_add)
            
            for event_id in additional_events:
                line = random.choice(self.lines_by_event[event_id]['all'])
                lines.append(line)
        
        return "rule1_both_sides_moneyline", lines
    
    def _generate_rule2_violation(self) -> Tuple[str, List[Dict]]:
        """Rule 2: Moneyline + negative spread of opposite team + valid legs (2-12 total)"""
        suitable_events = [
            event_id for event_id, data in self.lines_by_event.items()
            if data['moneylines'] and data['spreads']
        ]
        
        if not suitable_events:
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        violation_event_id = random.choice(suitable_events)
        data = self.lines_by_event[violation_event_id]
        
        # Find a negative spread
        negative_spreads = [s for s in data['spreads'] if s['line'] < 0]
        
        if not negative_spreads or not data['moneylines']:
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        ml = random.choice(data['moneylines'])
        spread = random.choice(negative_spreads)
        
        # Check if they're opposite teams (different outcomeId parity)
        if (ml['outcomeId'] % 2) == (spread['outcomeId'] % 2):
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        # Start with violation
        lines = [ml, spread]
        
        # Add 0-10 more valid legs from different events
        num_additional_legs = random.randint(0, 10)
        available_events = [eid for eid in self.lines_by_event.keys() if eid != violation_event_id]
        
        if available_events and num_additional_legs > 0:
            num_to_add = min(num_additional_legs, len(available_events))
            additional_events = random.sample(available_events, num_to_add)
            
            for event_id in additional_events:
                line = random.choice(self.lines_by_event[event_id]['all'])
                lines.append(line)
        
        return "rule2_moneyline_negative_spread", lines
    
    def _generate_rule3_violation(self) -> Tuple[str, List[Dict]]:
        """Rule 3: Opposing spreads where sum <= 0 + valid legs (2-12 total)"""
        events_with_spreads = [
            event_id for event_id, data in self.lines_by_event.items()
            if len(data['spreads']) >= 2
        ]
        
        if not events_with_spreads:
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        violation_event_id = random.choice(events_with_spreads)
        spreads = self.lines_by_event[violation_event_id]['spreads']
        
        # Find opposing spreads where sum <= 0
        violation_pair = None
        for i, s1 in enumerate(spreads):
            for s2 in spreads[i+1:]:
                # Check if opposite teams and sum <= 0
                if (s1['outcomeId'] % 2) != (s2['outcomeId'] % 2):
                    if s1['line'] + s2['line'] <= 0:
                        violation_pair = [s1, s2]
                        break
            if violation_pair:
                break
        
        if not violation_pair:
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        lines = violation_pair
        
        # Add 0-10 more valid legs from different events
        num_additional_legs = random.randint(0, 10)
        available_events = [eid for eid in self.lines_by_event.keys() if eid != violation_event_id]
        
        if available_events and num_additional_legs > 0:
            num_to_add = min(num_additional_legs, len(available_events))
            additional_events = random.sample(available_events, num_to_add)
            
            for event_id in additional_events:
                line = random.choice(self.lines_by_event[event_id]['all'])
                lines.append(line)
        
        return "rule3_opposing_spreads_sum_lte_0", lines
    
    def _generate_rule4_violation(self) -> Tuple[str, List[Dict]]:
        """Rule 4: Opposing totals where over_line - under_line >= 0 + valid legs (2-12 total)"""
        events_with_totals = [
            event_id for event_id, data in self.lines_by_event.items()
            if len(data['totals']) >= 2
        ]
        
        if not events_with_totals:
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        violation_event_id = random.choice(events_with_totals)
        totals = self.lines_by_event[violation_event_id]['totals']
        
        # Find opposing totals where over - under >= 0
        # Assumption: even outcomeId is "over", odd outcomeId is "under"
        violation_pair = None
        for i, t1 in enumerate(totals):
            for t2 in totals[i+1:]:
                # Check if opposite sides (different outcomeId parity)
                if (t1['outcomeId'] % 2) != (t2['outcomeId'] % 2):
                    # Determine which is over and which is under
                    if t1['outcomeId'] % 2 == 0:  # t1 is over (even)
                        over_line = t1['line']
                        under_line = t2['line']
                    else:  # t2 is over (even)
                        over_line = t2['line']
                        under_line = t1['line']
                    
                    # Check if over - under >= 0 (violation)
                    if over_line - under_line >= 0:
                        violation_pair = [t1, t2]
                        break
            if violation_pair:
                break
        
        if not violation_pair:
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        lines = violation_pair
        
        # Add 0-10 more valid legs from different events
        num_additional_legs = random.randint(0, 10)
        available_events = [eid for eid in self.lines_by_event.keys() if eid != violation_event_id]
        
        if available_events and num_additional_legs > 0:
            num_to_add = min(num_additional_legs, len(available_events))
            additional_events = random.sample(available_events, num_to_add)
            
            for event_id in additional_events:
                line = random.choice(self.lines_by_event[event_id]['all'])
                lines.append(line)
        
        return "rule4_opposing_totals_diff_gte_0", lines
    
    def _generate_rule5_violation(self) -> Tuple[str, List[Dict]]:
        """Rule 5: Parlay with 13+ legs (exceeds maximum allowed)"""
        if not self.all_market_lines:
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        # Generate parlay with 13-20 legs
        num_legs = random.randint(13, 20)
        
        # Group lines by event ID to ensure one line per event
        lines_by_event = {}
        for line in self.all_market_lines:
            event_id = line['sportEventId']
            if event_id not in lines_by_event:
                lines_by_event[event_id] = []
            lines_by_event[event_id].append(line)
        
        # Get unique events
        available_events = list(lines_by_event.keys())
        
        # Ensure we have enough events
        if len(available_events) < num_legs:
            num_legs = len(available_events)
        
        # If we still can't get 13+ legs, fallback
        if num_legs < 13:
            parlay_type, lines, prob_type = self._generate_multi_event_parlay(); return (parlay_type, lines)  # Fallback
        
        # Randomly select events
        selected_events = random.sample(available_events, num_legs)
        
        # Pick one random line from each selected event
        lines = []
        for event_id in selected_events:
            line = random.choice(lines_by_event[event_id])
            lines.append(line)
        
        return "rule5_too_many_legs", lines

    def get_user_token(self) -> Tuple[str, float]:
        """Get user authentication token with timing (cached)"""
        # Return cached token if available and not too old
        if self.cached_user_token and (time.time() - self.last_user_auth_time) < self.token_cache_duration:
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
                self.last_user_auth_time = time.time()
                logger.debug(f"✅ User auth successful, token cached")
                return token, response_time
            else:
                logger.warning(f"❌ User auth failed: HTTP {response.status_code}")
                return "fallback_token", response_time
        except Exception as e:
            return "fallback_token", time.time() - start_time

    def authenticate_sp(self, credentials: Dict[str, str], sp_name: str = "SP") -> Tuple[Optional[str], float]:
        """Authenticate SP with timing (cached)"""
        # Check cache based on SP credentials
        cache_key = credentials["access_key"]
        if cache_key == self.sp1_credentials["access_key"] and self.cached_sp1_token:
            if (time.time() - self.last_sp1_auth_time) < self.token_cache_duration:
                return self.cached_sp1_token, 0
        elif cache_key == self.sp2_credentials["access_key"] and self.cached_sp2_token:
            if (time.time() - self.last_sp2_auth_time) < self.token_cache_duration:
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
                    self.last_sp1_auth_time = time.time()
                else:
                    self.cached_sp2_token = token
                    self.last_sp2_auth_time = time.time()
                return token, response_time
            else:
                logger.debug(f"{sp_name} auth failed: {response.status_code}")
                return None, response_time
                
        except Exception as e:
            logger.debug(f"{sp_name} auth error: {e}")
            return None, time.time() - start_time

    def create_parlay(self, user_token: str, market_lines: List[Dict]) -> Tuple[Optional[str], float, Optional[str]]:
        """Create parlay with timing
        
        Returns:
            Tuple[Optional[str], float, Optional[str]]: (parlay_id, response_time, error_message)
        """
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
                return parlay_id, response_time, None
            else:
                # Extract error message from response
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", f"HTTP {response.status_code}")
                    # If message is a dict or complex, extract details
                    if isinstance(error_message, dict):
                        error_message = json.dumps(error_message)
                except:
                    error_message = f"HTTP {response.status_code}"
                
                return None, response_time, error_message
                
        except Exception as e:
            return None, time.time() - start_time, str(e)

    def sp_offer(self, parlay_id: str, sp_token: str, odds: int, max_risk: int, 
                 market_lines: List[Dict]) -> Tuple[bool, float]:
        """SP provides offer with timing"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        
        # Generate random realistic odds for each leg
        leg_odds = []
        for _ in market_lines:
            # Generate random American odds
            # 50% chance of favorite (negative) or underdog (positive)
            if random.random() < 0.5:
                # Favorite: -110 to -500
                leg_odd = random.randint(-500, -110)
            else:
                # Underdog: +110 to +500
                leg_odd = random.randint(110, 500)
            leg_odds.append(leg_odd)
        
        valid_until = int((time.time() + 60) * 1e9)
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": odds,
                    "max_risk": max_risk,
                    "valid_until": valid_until,
                    "estimated_prices": [
                        {"line_id": line["lineId"], "odds": leg_odds[idx]}
                        for idx, line in enumerate(market_lines)
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
                    statuses = [o['status'] for o in matching_orders]
                    logger.info(f"⚠️  Parlay {parlay_id} order status: {statuses} (expected 'sent_confirmation')")
                else:
                    logger.info(f"⚠️  No orders found for parlay {parlay_id}")
                return False, 0
            
            # Calculate target probability from confirmed odds
            # This ensures the combined leg probabilities match the parlay odds
            target_combined_prob = self._odds_to_probability(odds)
            
            # Generate leg probabilities that multiply to target
            leg_probabilities = self._generate_valid_leg_probabilities(len(market_lines), target_combined_prob)
            
            # Verify combined probability
            combined_probability = 1.0
            for prob in leg_probabilities:
                combined_probability *= prob
            
            # Log probability validation for debugging
            logger.debug(f"Probability Validation for {parlay_id}:")
            logger.debug(f"  Odds: {odds} → Target Prob: {target_combined_prob:.8f}")
            logger.debug(f"  Leg Probabilities: {[f'{p:.8f}' for p in leg_probabilities]}")
            logger.debug(f"  Combined Probability: {combined_probability:.8f}")
            logger.debug(f"  Difference: {abs(combined_probability - target_combined_prob):.8f} ({abs(combined_probability - target_combined_prob) / target_combined_prob * 100:.2f}%)")
            
            # Calculate max_risk based on combined probability
            # max_risk = stake * (1/probability - 1) which is the potential payout
            max_risk_dollars = (stake / 100) * (1 / combined_probability - 1)
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
                            "probability": leg_probabilities[idx]
                        }
                        for idx, line in enumerate(market_lines)
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
        """Run a single test iteration with random legs and chaos validation"""
        
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
        
        # Get random market lines (with chaos testing and probability type)
        parlay_type, market_lines, probability_type = self.get_random_market_lines()
        if not market_lines:
            return TestResult(
                iteration=iteration,
                leg_count=0,
                success=False,
                total_time=time.time() - start_time,
                thread_id=thread_id,
                error="No market lines available",
                parlay_type=parlay_type,
                probability_type="invalid"
            )
        
        # Determine expected result based on parlay type
        expected_result = "reject" if parlay_type.startswith("rule") else "accept"
        actual_result = "unknown"
        validation_passed = False
        
        actual_leg_count = len(market_lines)
        
        # Check if same-game parlay
        event_ids = set(line['sportEventId'] for line in market_lines)
        is_same_game = len(event_ids) == 1
        prob_label = "VALID" if is_same_game else "INVALID"
        
        # Log test info
        logger.info(f"\n{'─'*100}")
        logger.info(f"🧪 Test {iteration}: {parlay_type.upper()} | Probability: {prob_label}")
        logger.info(f"{'─'*100}")
        logger.info(f"📦 Legs: {actual_leg_count} | Events: {len(event_ids)} | Same-Game: {is_same_game}")
        
        if self.chaos_mode:
            logger.info(f"🎯 Expected: API should {expected_result.upper()}")
            
            # Show the legs for invalid tests
            if parlay_type.startswith("rule"):
                for idx, line in enumerate(market_lines, 1):
                    market_name = self._get_market_name(line['marketId'])
                    logger.info(f"   Leg {idx}: Event {line['sportEventId']} - {market_name} (outcome={line['outcomeId']}, line={line['line']})")
        
        # Step 1: Authenticate user
        user_token, _ = self.get_user_token()
        if not user_token or user_token == "fallback_token":
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=False,
                total_time=time.time() - start_time,
                thread_id=thread_id,
                error="User authentication failed",
                parlay_type=parlay_type,
                expected_result=expected_result,
                actual_result="error",
                validation_passed=False
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
                error="All SP authentication failed",
                parlay_type=parlay_type,
                expected_result=expected_result,
                actual_result="error",
                validation_passed=False
            )
        
        # Use whichever SP authenticated successfully
        sp_token = sp1_token if sp1_token else sp2_token
        sp_name = "SP1" if sp1_token else "SP2"
        
        # Step 3: Create parlay with random legs
        parlay_id, _, api_error = self.create_parlay(user_token, market_lines)
        
        # Check if parlay was rejected (chaos testing validation)
        if not parlay_id:
            actual_result = "rejected"
            validation_passed = (expected_result == "reject")
            
            # Always log the API error for debugging
            if api_error:
                logger.info(f"💬 API Error: {api_error}")
            
            # Update validation stats
            if self.chaos_mode:
                with self.lock:
                    if parlay_type == "valid":
                        self.validation_stats['valid_rejected'] += 1
                    elif parlay_type == "rule1_both_sides_moneyline":
                        self.validation_stats['rule1_rejected'] += 1
                    elif parlay_type == "rule2_moneyline_negative_spread":
                        self.validation_stats['rule2_rejected'] += 1
                    elif parlay_type == "rule3_opposing_spreads_sum_lte_0":
                        self.validation_stats['rule3_rejected'] += 1
                    elif parlay_type == "rule4_opposing_totals_diff_gte_0":
                        self.validation_stats['rule4_rejected'] += 1
                    elif parlay_type == "rule5_too_many_legs":
                        self.validation_stats['rule5_rejected'] += 1
                
                if validation_passed:
                    logger.info(f"✅ VALIDATION PASSED - API rejected as expected")
                    if api_error:
                        logger.info(f"   💬 API Response: {api_error}")
                else:
                    logger.warning(f"❌ VALIDATION FAILED - API rejected but expected acceptance")
                    if api_error:
                        logger.warning(f"   💬 API Response: {api_error}")
            
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=validation_passed,  # Success if validation passed
                total_time=time.time() - start_time,
                thread_id=thread_id,
                error="Parlay creation failed" if not validation_passed else None,
                parlay_id=None,
                parlay_type=parlay_type,
                expected_result=expected_result,
                actual_result=actual_result,
                validation_passed=validation_passed
            )
        
        # Parlay was accepted
        actual_result = "accepted"
        validation_passed = (expected_result == "accept")
        
        # Update validation stats for accepted parlays
        if self.chaos_mode:
            with self.lock:
                if parlay_type == "valid":
                    self.validation_stats['valid_accepted'] += 1
                elif parlay_type == "rule1_both_sides_moneyline":
                    self.validation_stats['rule1_accepted'] += 1
                elif parlay_type == "rule2_moneyline_negative_spread":
                    self.validation_stats['rule2_accepted'] += 1
                elif parlay_type == "rule3_opposing_spreads_sum_lte_0":
                    self.validation_stats['rule3_accepted'] += 1
                elif parlay_type == "rule4_opposing_totals_diff_gte_0":
                    self.validation_stats['rule4_accepted'] += 1
                elif parlay_type == "rule5_too_many_legs":
                    self.validation_stats['rule5_accepted'] += 1
            
            if not validation_passed:
                logger.warning(f"❌ VALIDATION FAILED - API accepted but should have rejected {parlay_type}")
            else:
                logger.info(f"✅ VALIDATION PASSED - API accepted as expected")
        
        # For chaos mode, if we reached here with invalid parlay, it's a validation failure
        # Only proceed with bet completion for valid parlays OR if not in chaos mode
        should_complete_bet = self.complete_bets and (not self.chaos_mode or parlay_type == "valid")
        
        if not should_complete_bet:
            # Just track validation result and return
            total_time = time.time() - start_time
            self.reset_failure_counter()
            
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=validation_passed,
                total_time=total_time,
                thread_id=thread_id,
                parlay_id=parlay_id,
                parlay_type=parlay_type,
                expected_result=expected_result,
                actual_result=actual_result,
                validation_passed=validation_passed
            )
        
        # Step 4: SP provides offer (only for valid parlays in chaos mode)
        # Generate random realistic odds and stake
        # Odds range: +100 to +1000 (common parlay odds)
        odds = random.randint(100, 1000)
        
        # Stake range: $10 to $500 in cents (1000 to 50000 cents)
        stake = random.randint(1000, 50000)
        
        # Calculate max_risk based on odds and stake
        if odds > 0:
            decimal_odds = (odds + 100) / 100
        else:
            decimal_odds = 100 / abs(odds) + 1
        max_risk_dollars = (stake / 100) * decimal_odds
        max_risk_cents = int(max_risk_dollars * 100)
        
        logger.info(f"💰 Random Odds: +{odds} | Stake: ${stake/100:.2f} | Max Risk: ${max_risk_cents/100:.2f}")
        
        offer_success, _ = self.sp_offer(parlay_id, sp_token, odds, max_risk_cents, market_lines)
        if not offer_success:
            # Check if we should restart due to token expiration
            should_restart = self.check_token_expiration_and_restart("SP offer failed")
            if should_restart:
                logger.info("🔄 Retrying test after token refresh...")
                # Don't return failure, let it continue to next iteration
            
            return TestResult(
                iteration=iteration,
                leg_count=actual_leg_count,
                success=False,
                total_time=time.time() - start_time,
                thread_id=thread_id,
                parlay_id=parlay_id,
                error="SP offer failed",
                parlay_type=parlay_type,
                expected_result=expected_result,
                actual_result=actual_result,
                validation_passed=validation_passed
            )
        
        # Continue with full bet completion
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
                error="User confirmation failed",
                parlay_type=parlay_type,
                expected_result=expected_result,
                actual_result=actual_result,
                validation_passed=validation_passed
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
        
        # Reset failure counter on success
        self.reset_failure_counter()
        
        return TestResult(
            iteration=iteration,
            leg_count=actual_leg_count,
            success=True,
            total_time=total_time,
            thread_id=thread_id,
            parlay_id=parlay_id,
            parlay_type=parlay_type,
            expected_result=expected_result,
            actual_result=actual_result,
            validation_passed=validation_passed
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
        
        # Chaos testing validation summary
        if self.chaos_mode:
            logger.info(f"\n🎲 CHAOS TESTING VALIDATION SUMMARY:")
            logger.info(f"\n   🟢 VALID PARLAYS:")
            total_valid = self.validation_stats['valid_accepted'] + self.validation_stats['valid_rejected']
            if total_valid > 0:
                valid_success_rate = (self.validation_stats['valid_accepted'] / total_valid * 100)
                logger.info(f"      Accepted: {self.validation_stats['valid_accepted']}/{total_valid} ({valid_success_rate:.1f}%)")
                logger.info(f"      Rejected: {self.validation_stats['valid_rejected']}/{total_valid}")
            
            logger.info(f"\n   🔴 RULE VIOLATIONS:")
            
            # Rule 1
            total_rule1 = self.validation_stats['rule1_accepted'] + self.validation_stats['rule1_rejected']
            if total_rule1 > 0:
                rule1_validation_rate = (self.validation_stats['rule1_rejected'] / total_rule1 * 100)
                logger.info(f"      Rule 1 (Both Sides Moneyline):")
                logger.info(f"         Rejected (correct): {self.validation_stats['rule1_rejected']}/{total_rule1} ({rule1_validation_rate:.1f}%)")
                logger.info(f"         Accepted (wrong): {self.validation_stats['rule1_accepted']}/{total_rule1}")
            
            # Rule 2
            total_rule2 = self.validation_stats['rule2_accepted'] + self.validation_stats['rule2_rejected']
            if total_rule2 > 0:
                rule2_validation_rate = (self.validation_stats['rule2_rejected'] / total_rule2 * 100)
                logger.info(f"      Rule 2 (Moneyline + Negative Spread):")
                logger.info(f"         Rejected (correct): {self.validation_stats['rule2_rejected']}/{total_rule2} ({rule2_validation_rate:.1f}%)")
                logger.info(f"         Accepted (wrong): {self.validation_stats['rule2_accepted']}/{total_rule2}")
            
            # Rule 3
            total_rule3 = self.validation_stats['rule3_accepted'] + self.validation_stats['rule3_rejected']
            if total_rule3 > 0:
                rule3_validation_rate = (self.validation_stats['rule3_rejected'] / total_rule3 * 100)
                logger.info(f"      Rule 3 (Opposing Spreads Sum ≤ 0):")
                logger.info(f"         Rejected (correct): {self.validation_stats['rule3_rejected']}/{total_rule3} ({rule3_validation_rate:.1f}%)")
                logger.info(f"         Accepted (wrong): {self.validation_stats['rule3_accepted']}/{total_rule3}")
            
            # Rule 4
            total_rule4 = self.validation_stats['rule4_accepted'] + self.validation_stats['rule4_rejected']
            if total_rule4 > 0:
                rule4_validation_rate = (self.validation_stats['rule4_rejected'] / total_rule4 * 100)
                logger.info(f"      Rule 4 (Opposing Totals Over-Under ≥ 0):")
                logger.info(f"         Rejected (correct): {self.validation_stats['rule4_rejected']}/{total_rule4} ({rule4_validation_rate:.1f}%)")
                logger.info(f"         Accepted (wrong): {self.validation_stats['rule4_accepted']}/{total_rule4}")
            
            # Rule 5
            total_rule5 = self.validation_stats['rule5_accepted'] + self.validation_stats['rule5_rejected']
            if total_rule5 > 0:
                rule5_validation_rate = (self.validation_stats['rule5_rejected'] / total_rule5 * 100)
                logger.info(f"      Rule 5 (Too Many Legs 13+):")
                logger.info(f"         Rejected (correct): {self.validation_stats['rule5_rejected']}/{total_rule5} ({rule5_validation_rate:.1f}%)")
                logger.info(f"         Accepted (wrong): {self.validation_stats['rule5_accepted']}/{total_rule5}")
            
            # Overall validation success
            total_tests_with_validation = len([r for r in self.test_results if hasattr(r, 'validation_passed')])
            passed_validation = len([r for r in self.test_results if hasattr(r, 'validation_passed') and r.validation_passed])
            if total_tests_with_validation > 0:
                overall_validation_rate = (passed_validation / total_tests_with_validation * 100)
                logger.info(f"\n   🎯 OVERALL VALIDATION:")
                logger.info(f"      Success Rate: {passed_validation}/{total_tests_with_validation} ({overall_validation_rate:.1f}%)")
        
        logger.info(f"\n{'='*100}")

def run_autoplay_with_restart(args):
    """Run autoplay with automatic restart on authentication failures"""
    restart_count = 0
    max_restarts = 100  # Prevent infinite loops, but allow many restarts
    
    while restart_count < max_restarts:
        try:
            logger.info(f"\n{'='*100}")
            if restart_count > 0:
                logger.info(f"🔄 RESTART #{restart_count} - Starting fresh autoplay session...")
            logger.info(f"{'='*100}\n")
            
            # Create new autoplay instance
            autoplay = ParlayAutoplay(
                mode=args.mode,
                iterations=args.iterations,
                concurrency=args.concurrency,
                delay=args.delay,
                complete_bets=True,
                chaos_mode=args.chaos,
                chaos_invalid_rate=args.chaos_invalid_rate,
                same_game_rate=args.same_game_rate,
                min_legs=args.min_legs,
                max_legs=args.max_legs
            )
            
            # Run the autoplay
            autoplay.run()
            
            # If we get here and running is False, user interrupted - exit gracefully
            if not autoplay.running:
                logger.info("\n✅ Session ended by user")
                autoplay.print_final_results()
                break
            
            # Normal completion (only happens in non-continuous modes)
            autoplay.print_final_results()
            break
            
        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Interrupted by user")
            try:
                autoplay.print_final_results()
            except:
                pass
            break
            
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a token expiration restart (intentional)
            if "TokenExpirationRestart" in error_str:
                restart_count += 1
                logger.warning(f"\n🔄 Token expiration detected - restarting session ({restart_count}/{max_restarts})...")
                time.sleep(5)  # Wait before restart
                continue
            
            # Log unexpected errors
            logger.error(f"\n\n❌ Unexpected error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Check if it's an authentication-related error
            error_str_lower = error_str.lower()
            if any(keyword in error_str_lower for keyword in ['auth', 'token', 'unauthorized', '401', '403']):
                restart_count += 1
                logger.warning(f"\n🔄 Authentication error detected - restarting session ({restart_count}/{max_restarts})...")
                time.sleep(5)  # Wait before restart
                continue
            else:
                # Non-auth error - still restart in continuous mode
                if args.mode == 'continuous':
                    restart_count += 1
                    logger.warning(f"\n🔄 Error in continuous mode - restarting session ({restart_count}/{max_restarts})...")
                    time.sleep(5)
                    continue
                else:
                    break
    
    if restart_count >= max_restarts:
        logger.error(f"\n❌ Maximum restart limit ({max_restarts}) reached. Exiting.")

def main():
    """Main entry point with argument parsing"""
    
    parser = argparse.ArgumentParser(
        description='Parlay Autoplay - Continuous Load Testing System with Auto-Restart',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal mode - 10 sequential tests with 1s delay
  python parlay_autoplay.py --mode normal --iterations 10 --delay 1

  # Continuous mode - run until Ctrl+C (auto-restarts on errors)
  python parlay_autoplay.py --mode continuous --delay 0.5

  # 2-leg parlays only (for testing same-game valid probability)
  python parlay_autoplay.py --mode continuous --min-legs 2 --max-legs 2 --same-game-rate 1.0

  # 100% multi-event parlays (invalid probability)
  python parlay_autoplay.py --mode continuous --same-game-rate 0.0

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
    parser.add_argument('--chaos', action='store_true',
                       help='Enable chaos testing mode (mix valid/invalid parlays)')
    parser.add_argument('--chaos-invalid-rate', type=float, default=0.5,
                       help='Percentage of invalid parlays in chaos mode (default: 0.5)')
    parser.add_argument('--same-game-rate', type=float, default=0.5,
                       help='Percentage of same-game parlays vs multi-event (default: 0.5)')
    parser.add_argument('--min-legs', type=int, default=2,
                       help='Minimum number of legs per parlay (default: 2)')
    parser.add_argument('--max-legs', type=int, default=12,
                       help='Maximum number of legs per parlay (default: 12)')
    
    args = parser.parse_args()
    
    # Banner
    logger.info("\n" + "="*100)
    if args.chaos:
        logger.info("🎲 PARLAY AUTOPLAY - E2E CHAOTIC TESTING WITH VALIDATION")
        logger.info("="*100)
        logger.info(f"🧪 Chaos Mode: ENABLED ({int(args.chaos_invalid_rate * 100)}% invalid parlays)")
        logger.info("🏁 Full E2E: Creates + validates API rules + completes valid bets")
    else:
        logger.info("🎰 PARLAY AUTOPLAY - CONTINUOUS LOAD TESTING SYSTEM")
        logger.info("="*100)
        logger.info("🏁 Full bet completion: ENABLED (creates, offers, confirms, accepts)")
    
    if args.mode == 'continuous':
        logger.info("🔄 Auto-restart: ENABLED (restarts on auth/token errors)")
    
    # Show configuration
    logger.info(f"📊 Parlay Config: {args.min_legs}-{args.max_legs} legs | Same-Game: {int(args.same_game_rate * 100)}%")
    logger.info("="*100)
    
    # Run with auto-restart wrapper
    run_autoplay_with_restart(args)
    
    logger.info("\n✅ Autoplay session ended\n")

if __name__ == "__main__":
    main()

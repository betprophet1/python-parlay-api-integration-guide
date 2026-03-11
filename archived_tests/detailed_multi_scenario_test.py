#!/usr/bin/env python3
"""
🎯 DETAILED MULTI-SCENARIO PARLAY TEST - COMPREHENSIVE REPORTING

Enhanced load testing with detailed tracking:
- Parlay IDs and Order UUIDs for each test
- Complete verification steps with timestamps
- Detailed failure reasons and API responses
- Step-by-step execution tracking
- Complete audit trail for debugging
"""

import requests
import json
import time
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import threading
from dataclasses import dataclass, field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'detailed_multi_scenario_test_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class DetailedScenarioResult:
    scenario: str
    scenario_name: str
    iteration: int
    success: bool
    total_time: float
    steps: Dict[str, float]
    error: Optional[str] = None
    parlay_id: Optional[str] = None
    order_ids: List[str] = field(default_factory=list)
    verification_steps: Dict[str, Any] = field(default_factory=dict)
    api_responses: Dict[str, Any] = field(default_factory=dict)
    execution_timeline: List[Dict] = field(default_factory=list)

class DetailedMultiScenarioTest:
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

    def log_timeline(self, result: DetailedScenarioResult, step: str, status: str, details: Dict = None):
        """Add timestamped event to execution timeline"""
        timeline_entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "status": status,
            "details": details or {}
        }
        result.execution_timeline.append(timeline_entry)

    def get_user_token(self, result: DetailedScenarioResult) -> Tuple[str, float]:
        """Get user authentication token with detailed logging"""
        url = f"{self.base_url}/api/v1/auth/login"
        payload = {
            "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
            "email": "lam.tran+usr004@betprophet.co",
            "password": "Kh0ngbiet1"
        }
        
        self.log_timeline(result, "user_auth_start", "initiated", {"url": url})
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['auth'].append(response_time)
            
            # Store API response details
            result.api_responses['user_auth'] = {
                "status_code": response.status_code,
                "response_time": response_time,
                "headers": dict(response.headers),
                "success": response.status_code == 200
            }
            
            if response.status_code == 200:
                response_data = response.json()
                token = response_data.get("accessToken")
                
                self.log_timeline(result, "user_auth_complete", "success", {
                    "token_length": len(token) if token else 0,
                    "response_time": response_time
                })
                
                return token, response_time
            else:
                error_details = {"status_code": response.status_code, "response": response.text[:200]}
                self.log_timeline(result, "user_auth_complete", "failed", error_details)
                result.api_responses['user_auth']['error'] = error_details
                return "fallback_token", response_time
                
        except Exception as e:
            error_details = {"exception": str(e)}
            self.log_timeline(result, "user_auth_complete", "error", error_details)
            result.api_responses['user_auth'] = {"error": error_details}
            return "fallback_token", time.time() - start_time

    def authenticate_sp(self, credentials: Dict[str, str], sp_name: str, result: DetailedScenarioResult) -> Tuple[Optional[str], float]:
        """Authenticate SP with detailed logging"""
        url = f"{self.base_url}/partner/auth/login"
        
        self.log_timeline(result, f"{sp_name.lower()}_auth_start", "initiated", {"url": url})
        
        start_time = time.time()
        try:
            response = requests.post(url, json=credentials, headers={
                "Content-Type": "application/json"
            })
            
            response_time = time.time() - start_time
            with self.lock:
                self.response_times['auth'].append(response_time)
            
            # Store API response details
            result.api_responses[f'{sp_name.lower()}_auth'] = {
                "status_code": response.status_code,
                "response_time": response_time,
                "headers": dict(response.headers),
                "success": response.status_code == 200
            }
            
            if response.status_code == 200:
                response_data = response.json()
                token = response_data["data"]["access_token"]
                
                self.log_timeline(result, f"{sp_name.lower()}_auth_complete", "success", {
                    "token_length": len(token),
                    "response_time": response_time
                })
                
                return token, response_time
            else:
                error_details = {"status_code": response.status_code, "response": response.text[:200]}
                self.log_timeline(result, f"{sp_name.lower()}_auth_complete", "failed", error_details)
                result.api_responses[f'{sp_name.lower()}_auth']['error'] = error_details
                return None, response_time
                
        except Exception as e:
            error_details = {"exception": str(e)}
            self.log_timeline(result, f"{sp_name.lower()}_auth_complete", "error", error_details)
            result.api_responses[f'{sp_name.lower()}_auth'] = {"error": error_details}
            return None, time.time() - start_time

    def create_parlay(self, user_token: str, result: DetailedScenarioResult) -> Tuple[Optional[str], float]:
        """Create parlay with detailed logging"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        
        payload = {"marketLines": self.market_lines}
        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
        
        self.log_timeline(result, "create_parlay_start", "initiated", {"url": url, "market_lines": len(self.market_lines)})
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['create_parlay'].append(response_time)
            
            # Store API response details
            result.api_responses['create_parlay'] = {
                "status_code": response.status_code,
                "response_time": response_time,
                "headers": dict(response.headers),
                "success": response.status_code == 200
            }
            
            if response.status_code == 200:
                response_data = response.json()
                parlay_id = response_data["data"]["parlayId"]
                request_id = response_data["data"]["parlayRequestId"]
                
                result.parlay_id = parlay_id
                
                self.log_timeline(result, "create_parlay_complete", "success", {
                    "parlay_id": parlay_id,
                    "request_id": request_id,
                    "response_time": response_time
                })
                
                return parlay_id, response_time
            else:
                error_details = {"status_code": response.status_code, "response": response.text[:200]}
                self.log_timeline(result, "create_parlay_complete", "failed", error_details)
                result.api_responses['create_parlay']['error'] = error_details
                return None, response_time
                
        except Exception as e:
            error_details = {"exception": str(e)}
            self.log_timeline(result, "create_parlay_complete", "error", error_details)
            result.api_responses['create_parlay'] = {"error": error_details}
            return None, time.time() - start_time

    def sp_offer(self, parlay_id: str, sp_token: str, odds: int, max_risk: int, sp_name: str, result: DetailedScenarioResult) -> Tuple[bool, float]:
        """SP provides offer with detailed logging"""
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
        
        self.log_timeline(result, f"{sp_name.lower()}_offer_start", "initiated", {
            "parlay_id": parlay_id,
            "odds": odds,
            "max_risk": max_risk
        })
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['sp_offer'].append(response_time)
            
            # Store API response details
            result.api_responses[f'{sp_name.lower()}_offer'] = {
                "status_code": response.status_code,
                "response_time": response_time,
                "headers": dict(response.headers),
                "success": response.status_code == 200,
                "offer_details": {"odds": odds, "max_risk": max_risk}
            }
            
            success = response.status_code == 200
            
            self.log_timeline(result, f"{sp_name.lower()}_offer_complete", "success" if success else "failed", {
                "success": success,
                "response_time": response_time,
                "status_code": response.status_code
            })
            
            if not success:
                result.api_responses[f'{sp_name.lower()}_offer']['error'] = response.text[:200]
            
            return success, response_time
            
        except Exception as e:
            error_details = {"exception": str(e)}
            self.log_timeline(result, f"{sp_name.lower()}_offer_complete", "error", error_details)
            result.api_responses[f'{sp_name.lower()}_offer'] = {"error": error_details}
            return False, time.time() - start_time

    def user_confirm(self, parlay_id: str, user_token: str, odds: int, stake: int, result: DetailedScenarioResult) -> Tuple[bool, float]:
        """User confirms bet with detailed logging"""
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
        
        self.log_timeline(result, "user_confirm_start", "initiated", {
            "parlay_id": parlay_id,
            "odds": odds,
            "stake": stake
        })
        
        start_time = time.time()
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['user_confirm'].append(response_time)
            
            # Store API response details
            result.api_responses['user_confirm'] = {
                "status_code": response.status_code,
                "response_time": response_time,
                "headers": dict(response.headers),
                "success": response.status_code == 200,
                "confirm_details": {"odds": odds, "stake": stake}
            }
            
            success = response.status_code == 200
            
            if success:
                response_data = response.json()
                created_at = response_data.get("data", {}).get("createdAt")
                
                self.log_timeline(result, "user_confirm_complete", "success", {
                    "success": success,
                    "response_time": response_time,
                    "created_at": created_at
                })
            else:
                error_details = {"status_code": response.status_code, "response": response.text[:200]}
                self.log_timeline(result, "user_confirm_complete", "failed", error_details)
                result.api_responses['user_confirm']['error'] = error_details
            
            return success, response_time
            
        except Exception as e:
            error_details = {"exception": str(e)}
            self.log_timeline(result, "user_confirm_complete", "error", error_details)
            result.api_responses['user_confirm'] = {"error": error_details}
            return False, time.time() - start_time

    def get_sp_orders(self, sp_token: str, parlay_id: str, sp_name: str, result: DetailedScenarioResult) -> Tuple[List[Dict], float]:
        """Get SP orders with detailed logging"""
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        self.log_timeline(result, f"{sp_name.lower()}_get_orders_start", "initiated", {"parlay_id": parlay_id})
        
        start_time = time.time()
        try:
            orders_response = requests.get(orders_url, headers=headers)
            response_time = time.time() - start_time
            
            if orders_response.status_code != 200:
                error_details = {"status_code": orders_response.status_code}
                self.log_timeline(result, f"{sp_name.lower()}_get_orders_complete", "failed", error_details)
                return [], response_time
            
            orders_data = orders_response.json()
            matching_orders = []
            
            for order in orders_data["data"]["orders"]:
                if order["p_id"] == parlay_id:
                    matching_orders.append(order)
                    if order["order_uuid"] not in result.order_ids:
                        result.order_ids.append(order["order_uuid"])
            
            self.log_timeline(result, f"{sp_name.lower()}_get_orders_complete", "success", {
                "matching_orders": len(matching_orders),
                "total_orders": len(orders_data["data"]["orders"]),
                "response_time": response_time
            })
            
            return matching_orders, response_time
            
        except Exception as e:
            error_details = {"exception": str(e)}
            self.log_timeline(result, f"{sp_name.lower()}_get_orders_complete", "error", error_details)
            return [], time.time() - start_time

    def sp_accept(self, sp_token: str, parlay_id: str, stake: int, odds: int, sp_name: str, result: DetailedScenarioResult) -> Tuple[bool, float]:
        """SP accepts confirmation with detailed logging"""
        # First get the orders
        orders, _ = self.get_sp_orders(sp_token, parlay_id, sp_name, result)
        
        start_time = time.time()
        
        if not orders:
            self.log_timeline(result, f"{sp_name.lower()}_accept_complete", "failed", {"reason": "No orders found"})
            return False, time.time() - start_time
        
        # Find the order that needs confirmation
        target_order = None
        for order in orders:
            if order["status"] == "sent_confirmation":
                target_order = order
                break
        
        if not target_order:
            available_statuses = [order["status"] for order in orders]
            self.log_timeline(result, f"{sp_name.lower()}_accept_complete", "failed", {
                "reason": "No order in sent_confirmation status",
                "available_statuses": available_statuses
            })
            return False, time.time() - start_time
        
        order_uuid = target_order["order_uuid"]
        
        self.log_timeline(result, f"{sp_name.lower()}_accept_start", "initiated", {
            "order_uuid": order_uuid,
            "stake": stake,
            "odds": odds
        })
        
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
            "signature": f"test_signature_{sp_name.lower()}_detailed"
        }
        
        try:
            response = requests.post(url, json=payload, headers={"Authorization": f"Bearer {sp_token}"}, params=params)
            response_time = time.time() - start_time
            
            with self.lock:
                self.response_times['sp_accept'].append(response_time)
            
            # Store API response details
            result.api_responses[f'{sp_name.lower()}_accept'] = {
                "status_code": response.status_code,
                "response_time": response_time,
                "headers": dict(response.headers),
                "success": response.status_code == 200,
                "order_uuid": order_uuid,
                "accept_details": {"stake": stake, "odds": odds, "probability": probability}
            }
            
            success = response.status_code == 200
            
            if success:
                response_data = response.json()
                confirmed_odds = response_data.get("data", {}).get("confirmed_odds")
                confirmed_stake = response_data.get("data", {}).get("confirmed_stake")
                
                self.log_timeline(result, f"{sp_name.lower()}_accept_complete", "success", {
                    "order_uuid": order_uuid,
                    "confirmed_odds": confirmed_odds,
                    "confirmed_stake": confirmed_stake,
                    "response_time": response_time
                })
            else:
                error_details = {"status_code": response.status_code, "response": response.text[:200]}
                self.log_timeline(result, f"{sp_name.lower()}_accept_complete", "failed", error_details)
                result.api_responses[f'{sp_name.lower()}_accept']['error'] = error_details
            
            return success, response_time
            
        except Exception as e:
            error_details = {"exception": str(e)}
            self.log_timeline(result, f"{sp_name.lower()}_accept_complete", "error", error_details)
            result.api_responses[f'{sp_name.lower()}_accept'] = {"error": error_details}
            return False, time.time() - start_time

    def verify_user_view(self, user_token: str, parlay_id: str, result: DetailedScenarioResult) -> Tuple[List[Dict], float]:
        """Verify user view and return matching parlays with detailed logging"""
        url = f"{self.base_url}/parlay/api/v1/user/list?limit=50"
        headers = {"Authorization": f"Bearer {user_token}"}
        
        self.log_timeline(result, "user_view_start", "initiated", {"parlay_id": parlay_id})
        
        start_time = time.time()
        max_attempts = 3
        all_attempts = []
        
        for attempt in range(max_attempts):
            attempt_start = time.time()
            try:
                response = requests.get(url, headers=headers)
                attempt_time = time.time() - attempt_start
                
                attempt_info = {
                    "attempt": attempt + 1,
                    "status_code": response.status_code,
                    "response_time": attempt_time
                }
                
                if response.status_code == 200:
                    user_data = response.json()
                    total_orders = len(user_data["data"]["orders"])
                    
                    matching_parlays = [
                        order for order in user_data["data"]["orders"]
                        if order["parlayId"] == parlay_id
                    ]
                    
                    attempt_info.update({
                        "total_orders": total_orders,
                        "matching_parlays": len(matching_parlays)
                    })
                    
                    all_attempts.append(attempt_info)
                    
                    if matching_parlays or attempt == max_attempts - 1:
                        response_time = time.time() - start_time
                        with self.lock:
                            self.response_times['user_view'].append(response_time)
                        
                        # Store detailed verification results
                        result.verification_steps['user_view'] = {
                            "attempts": all_attempts,
                            "final_matching_parlays": len(matching_parlays),
                            "total_response_time": response_time,
                            "parlay_details": []
                        }
                        
                        # Store details of each matching parlay
                        for parlay in matching_parlays:
                            parlay_detail = {
                                "uuid": parlay.get("uuid"),
                                "status": parlay.get("status"),
                                "requested_stake": parlay.get("requestedStake"),
                                "confirmed_stake": parlay.get("confirmedStake"),
                                "requested_odds": parlay.get("requestedOdds"),
                                "confirmed_odds": parlay.get("confirmedOdds"),
                                "settlement_status": parlay.get("settlementStatus"),
                                "max_profit": parlay.get("maxProfit")
                            }
                            result.verification_steps['user_view']['parlay_details'].append(parlay_detail)
                        
                        self.log_timeline(result, "user_view_complete", "success", {
                            "matching_parlays": len(matching_parlays),
                            "total_attempts": len(all_attempts),
                            "total_response_time": response_time
                        })
                        
                        return matching_parlays, response_time
                    
                    if attempt < max_attempts - 1:
                        time.sleep(2)
                        
                else:
                    attempt_info["error"] = response.text[:200]
                    all_attempts.append(attempt_info)
                        
            except Exception as e:
                attempt_info["exception"] = str(e)
                all_attempts.append(attempt_info)
                if attempt == max_attempts - 1:
                    break
                time.sleep(2)
                
        response_time = time.time() - start_time
        with self.lock:
            self.response_times['user_view'].append(response_time)
        
        result.verification_steps['user_view'] = {
            "attempts": all_attempts,
            "final_matching_parlays": 0,
            "total_response_time": response_time,
            "error": "Failed to get matching parlays"
        }
        
        self.log_timeline(result, "user_view_complete", "failed", {
            "total_attempts": len(all_attempts),
            "total_response_time": response_time
        })
        
        return [], response_time

    def run_scenario_1(self, iteration: int) -> DetailedScenarioResult:
        """Scenario 1: Basic Single SP Success"""
        scenario = "scenario_1"
        scenario_name = self.scenarios[scenario]
        
        result = DetailedScenarioResult(
            scenario=scenario,
            scenario_name=scenario_name,
            iteration=iteration,
            success=False,
            total_time=0,
            steps={}
        )
        
        logger.info(f"  🔄 S1: {scenario_name}")
        self.log_timeline(result, "scenario_start", "initiated", {"scenario": scenario_name})
        
        test_start = time.time()
        
        try:
            # Step 1: Get user token
            user_token, step_time = self.get_user_token(result)
            result.steps['user_auth'] = step_time
            if user_token == "fallback_token":
                result.error = "User authentication failed"
                result.total_time = time.time() - test_start
                return result
            
            # Step 2: Authenticate SP1
            sp1_token, step_time = self.authenticate_sp(self.sp1_credentials, "SP1", result)
            result.steps['sp_auth'] = step_time
            if not sp1_token:
                result.error = "SP1 authentication failed"
                result.total_time = time.time() - test_start
                return result
            
            # Step 3: Create parlay
            parlay_id, step_time = self.create_parlay(user_token, result)
            result.steps['create_parlay'] = step_time
            if not parlay_id:
                result.error = "Create parlay failed"
                result.total_time = time.time() - test_start
                return result
            
            # Step 4: SP1 offer
            offer_success, step_time = self.sp_offer(parlay_id, sp1_token, 800, 200, "SP1", result)
            result.steps['sp_offer'] = step_time
            if not offer_success:
                result.error = "SP1 offer failed"
                result.total_time = time.time() - test_start
                return result
            
            # Step 5: User confirm
            confirm_success, step_time = self.user_confirm(parlay_id, user_token, 800, 100, result)
            result.steps['user_confirm'] = step_time
            if not confirm_success:
                result.error = "User confirm failed"
                result.total_time = time.time() - test_start
                return result
            
            time.sleep(3)
            
            # Step 6: SP1 accept
            accept_success, step_time = self.sp_accept(sp1_token, parlay_id, 100, 800, "SP1", result)
            result.steps['sp_accept'] = step_time
            if not accept_success:
                result.error = "SP1 accept failed"
                result.total_time = time.time() - test_start
                return result
            
            # Step 7: Verify user view
            parlays, step_time = self.verify_user_view(user_token, parlay_id, result)
            result.steps['user_view'] = step_time
            
            finalized_parlays = [p for p in parlays if p.get("status") == "finalized"]
            result.success = len(finalized_parlays) >= 1
            
            if not result.success:
                result.error = f"Expected ≥1 finalized parlays, got {len(finalized_parlays)}"
            
            result.total_time = time.time() - test_start
            
            self.log_timeline(result, "scenario_complete", "success" if result.success else "failed", {
                "success": result.success,
                "finalized_parlays": len(finalized_parlays),
                "total_time": result.total_time
            })
            
            return result
            
        except Exception as e:
            result.error = f"Exception: {str(e)}"
            result.total_time = time.time() - test_start
            self.log_timeline(result, "scenario_complete", "error", {"exception": str(e)})
            return result

    def run_detailed_test(self, iterations: int = 5) -> Dict[str, Any]:
        """Run detailed test with comprehensive reporting"""
        logger.info(f"\n{'='*120}")
        logger.info(f"🎯 DETAILED MULTI-SCENARIO PARLAY TEST")
        logger.info(f"Started at: {datetime.now().isoformat()}")
        logger.info(f"Iterations: {iterations} (focusing on Scenario 1 for detailed analysis)")
        logger.info("="*120)
        
        test_start_time = time.time()
        all_results = []
        
        # Run iterations (focusing on Scenario 1 for detailed analysis)
        for i in range(iterations):
            logger.info(f"\n🚀 ITERATION {i+1}: Basic Single SP Success (Detailed)")
            result = self.run_scenario_1(i + 1)
            all_results.append(result)
            
            # Log iteration summary
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            logger.info(f"  📊 Iteration {i+1}: {status}")
            if result.error:
                logger.info(f"     Error: {result.error}")
            
            if i < iterations - 1:
                time.sleep(2)
        
        total_test_time = time.time() - test_start_time
        
        # Generate detailed report
        self.generate_detailed_report(all_results, total_test_time)
        
        return {"results": all_results, "total_time": total_test_time}

    def generate_detailed_report(self, results: List[DetailedScenarioResult], total_time: float):
        """Generate comprehensive detailed report"""
        logger.info(f"\n{'='*120}")
        logger.info("📋 DETAILED TEST REPORT WITH COMPLETE AUDIT TRAIL")
        logger.info("="*120)
        
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        # Overall Summary
        logger.info(f"🎯 TEST SUMMARY:")
        logger.info(f"   Total Iterations: {len(results)}")
        logger.info(f"   Successful: {len(successful_results)}")
        logger.info(f"   Failed: {len(failed_results)}")
        logger.info(f"   Success Rate: {len(successful_results)/len(results)*100:.1f}%")
        logger.info(f"   Total Test Time: {total_time:.2f}s")
        
        # Detailed Results for Each Iteration
        logger.info(f"\n📊 DETAILED ITERATION RESULTS:")
        
        for result in results:
            status = "✅ SUCCESS" if result.success else "❌ FAILED"
            logger.info(f"\n   🔄 ITERATION {result.iteration}: {status}")
            logger.info(f"      Scenario: {result.scenario_name}")
            logger.info(f"      Total Time: {result.total_time:.2f}s")
            
            if result.parlay_id:
                logger.info(f"      Parlay ID: {result.parlay_id}")
            
            if result.order_ids:
                logger.info(f"      Order IDs: {', '.join(result.order_ids)}")
            
            if result.error:
                logger.info(f"      Error: {result.error}")
            
            # Step-by-step timing
            logger.info(f"      Step Timings:")
            for step, timing in result.steps.items():
                logger.info(f"        - {step}: {timing:.3f}s")
            
            # API Response Summary
            logger.info(f"      API Responses:")
            for api_call, response_data in result.api_responses.items():
                if isinstance(response_data, dict):
                    status_code = response_data.get('status_code', 'N/A')
                    response_time = response_data.get('response_time', 0)
                    success = response_data.get('success', False)
                    logger.info(f"        - {api_call}: {status_code} ({'✅' if success else '❌'}) {response_time:.3f}s")
                    
                    if 'error' in response_data:
                        logger.info(f"          Error: {response_data['error']}")
            
            # Verification Steps
            if result.verification_steps:
                logger.info(f"      Verification Details:")
                for verification, details in result.verification_steps.items():
                    if verification == 'user_view':
                        attempts = details.get('attempts', [])
                        matching_parlays = details.get('final_matching_parlays', 0)
                        logger.info(f"        - User View: {matching_parlays} matching parlays after {len(attempts)} attempts")
                        
                        parlay_details = details.get('parlay_details', [])
                        for i, parlay in enumerate(parlay_details):
                            logger.info(f"          Parlay {i+1}:")
                            logger.info(f"            UUID: {parlay.get('uuid')}")
                            logger.info(f"            Status: {parlay.get('status')}")
                            logger.info(f"            Requested: ${parlay.get('requested_stake')} @ {parlay.get('requested_odds')}")
                            logger.info(f"            Confirmed: ${parlay.get('confirmed_stake')} @ {parlay.get('confirmed_odds')}")
                            logger.info(f"            Max Profit: ${parlay.get('max_profit')}")
            
            # Execution Timeline (showing key events)
            logger.info(f"      Key Timeline Events:")
            key_events = [event for event in result.execution_timeline 
                         if event['step'].endswith('_complete') or event['step'] in ['scenario_start', 'scenario_complete']]
            
            for event in key_events[-10:]:  # Show last 10 key events
                timestamp = event['timestamp'].split('T')[1][:8]  # HH:MM:SS
                step = event['step'].replace('_complete', '').replace('_start', '')
                status_emoji = {'success': '✅', 'failed': '❌', 'error': '💥', 'initiated': '🔄'}.get(event['status'], '❓')
                logger.info(f"        {timestamp} {status_emoji} {step}")
        
        # Response Time Analysis
        logger.info(f"\n⚡ RESPONSE TIME ANALYSIS:")
        for step, times in self.response_times.items():
            if times:
                logger.info(f"   {step.upper()}:")
                logger.info(f"     Average: {statistics.mean(times):.3f}s")
                logger.info(f"     Range: {min(times):.3f}s - {max(times):.3f}s")
                logger.info(f"     Total Calls: {len(times)}")
        
        # Failure Analysis
        if failed_results:
            logger.info(f"\n❌ FAILURE ANALYSIS:")
            failure_reasons = {}
            for result in failed_results:
                reason = result.error or "Unknown error"
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
            
            for reason, count in failure_reasons.items():
                logger.info(f"   {reason}: {count} occurrences")
        
        # Success Pattern Analysis
        if successful_results:
            logger.info(f"\n✅ SUCCESS PATTERN ANALYSIS:")
            avg_total_time = statistics.mean([r.total_time for r in successful_results])
            logger.info(f"   Average Success Time: {avg_total_time:.2f}s")
            
            # Step timing analysis for successful tests
            step_times = {}
            for result in successful_results:
                for step, timing in result.steps.items():
                    if step not in step_times:
                        step_times[step] = []
                    step_times[step].append(timing)
            
            logger.info(f"   Step Performance (Successful Tests):")
            for step, times in step_times.items():
                logger.info(f"     {step}: {statistics.mean(times):.3f}s average")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        
        success_rate = len(successful_results) / len(results) * 100
        if success_rate >= 90:
            logger.info("   ✅ System shows excellent reliability")
        elif success_rate >= 70:
            logger.info("   ⚠️  System stability should be improved")
        else:
            logger.info("   ❌ Critical stability issues need immediate attention")
        
        if self.response_times:
            avg_response = statistics.mean([statistics.mean(times) for times in self.response_times.values() if times])
            if avg_response > 2.0:
                logger.info("   • Consider performance optimization for API calls")
        
        logger.info(f"\nCompleted at: {datetime.now().isoformat()}")
        logger.info(f"📁 Full detailed logs saved to: detailed_multi_scenario_test_{int(time.time())}.log")

def main():
    """Main detailed test runner"""
    test = DetailedMultiScenarioTest()
    
    # Run 5 iterations with detailed tracking
    results = test.run_detailed_test(iterations=5)
    
    return results

if __name__ == "__main__":
    main()
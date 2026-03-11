#!/usr/bin/env python3
"""
🎯 COMPLETE PARLAY TEST SUITE WITH FULL REQUEST/RESPONSE LOGGING

Tests all 10 scenarios with detailed API logging:
- Full request payloads
- Complete response data
- Timing analysis
- Status tracking

Uses fresh market lines data provided.
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'complete_test_detailed_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompleteTestSuite:
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
        
        # Fresh working market lines data (updated 2025-10-27)
        self.market_lines = [
            {
                "line": 5.5,
                "lineId": "b9ebf6bb1eb7b11b8b0c222b3aac0db4",
                "marketId": 223,
                "outcomeId": 1714,
                "sportEventId": 19069
            },
            {
                "line": 0,
                "lineId": "555f11f70d23541f860a0b3c43500824",
                "marketId": 219,
                "outcomeId": 4,
                "sportEventId": 19069
            }
        ]
        
        # Get fresh user token
        self.user_token = self.get_fresh_user_token()
        
        # Authentication tokens
        self.sp1_token = None
        self.sp2_token = None
        
        # Test results
        self.test_results = {}

    def log_request_response(self, step: str, method: str, url: str, 
                           headers: Dict = None, payload: Dict = None, 
                           response: requests.Response = None, params: Dict = None):
        """Log full request and response details"""
        logger.info(f"\n📤 {step} - {method} REQUEST")
        logger.info(f"URL: {url}")
        
        if params:
            logger.info(f"PARAMS: {json.dumps(params, indent=2)}")
            
        if headers:
            # Hide sensitive tokens
            safe_headers = {k: ("Bearer ***" if k == "Authorization" and v.startswith("Bearer") else v) 
                          for k, v in headers.items()}
            logger.info(f"HEADERS: {json.dumps(safe_headers, indent=2)}")
            
        if payload:
            logger.info(f"PAYLOAD: {json.dumps(payload, indent=2)}")
            
        if response:
            logger.info(f"\n📥 {step} - RESPONSE")
            logger.info(f"STATUS: {response.status_code}")
            logger.info(f"HEADERS: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                
                # Shorten SP orders responses to save space
                if '/parlay/sp/orders' in url and 'data' in response_data and 'orders' in response_data['data']:
                    orders = response_data['data']['orders']
                    if len(orders) > 3:
                        # Keep first 3 orders and add summary
                        shortened_data = response_data.copy()
                        shortened_data['data'] = response_data['data'].copy()
                        shortened_data['data']['orders'] = orders[:3]
                        logger.info(f"BODY (showing first 3 of {len(orders)} orders): {json.dumps(shortened_data, indent=2)}")
                        logger.info(f"... ({len(orders) - 3} more orders truncated for brevity)")
                    else:
                        logger.info(f"BODY: {json.dumps(response_data, indent=2)}")
                # Shorten user view responses with large order lists
                elif '/parlay/api/v1/user/list' in url and 'data' in response_data and 'orders' in response_data['data']:
                    orders = response_data['data']['orders']
                    if len(orders) > 5:
                        # Keep first 5 orders and add summary
                        shortened_data = response_data.copy()
                        shortened_data['data'] = response_data['data'].copy()
                        shortened_data['data']['orders'] = orders[:5]
                        logger.info(f"BODY (showing first 5 of {len(orders)} orders): {json.dumps(shortened_data, indent=2)}")
                        logger.info(f"... ({len(orders) - 5} more orders truncated for brevity)")
                    else:
                        logger.info(f"BODY: {json.dumps(response_data, indent=2)}")
                else:
                    logger.info(f"BODY: {json.dumps(response_data, indent=2)}")
            except:
                logger.info(f"BODY (raw): {response.text}")
                
        logger.info("="*80)

    def get_fresh_user_token(self) -> str:
        """Get fresh user authentication token"""
        url = f"{self.base_url}/api/v1/auth/login"
        payload = {
            "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
            "email": "lam.tran+usr004@betprophet.co",
            "password": "Kh0ngbiet1"
        }
        
        try:
            response = requests.post(url, json=payload)
            self.log_request_response("USER AUTH", "POST", url, payload=payload, response=response)
            
            if response.status_code == 200:
                token = response.json().get("accessToken")
                logger.info("✅ Fresh user token obtained")
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
        
        try:
            response = requests.post(url, json=credentials, headers={
                "Content-Type": "application/json"
            })
            
            self.log_request_response(f"{sp_name} AUTH", "POST", url, 
                                    headers={"Content-Type": "application/json"}, 
                                    payload=credentials, response=response)
            
            if response.status_code == 200:
                token = response.json()["data"]["access_token"]
                logger.info(f"✅ {sp_name} Authentication SUCCESS")
                return token
            else:
                logger.error(f"❌ {sp_name} Authentication FAILED: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ {sp_name} Authentication ERROR: {str(e)}")
            return None

    def create_parlay_request(self) -> Optional[str]:
        """Create parlay request and return parlay ID"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        
        payload = {
            "marketLines": self.market_lines
        }
        
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            self.log_request_response("CREATE PARLAY", "POST", url, headers=headers, 
                                    payload=payload, response=response)
            
            if response.status_code == 200:
                parlay_id = response.json()["data"]["parlayId"]
                logger.info(f"✅ Parlay created successfully - ID: {parlay_id}")
                return parlay_id
            else:
                logger.error(f"❌ Parlay creation FAILED: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Parlay creation ERROR: {str(e)}")
            return None

    def provide_sp_offer(self, parlay_id: str, sp_token: str, odds: int, max_risk: int, 
                        sp_name: str, validity_seconds: int = 60) -> bool:
        """Service Provider provides offer"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": odds,
                    "max_risk": max_risk,
                    "valid_until": int((time.time() + validity_seconds) * 1_000_000_000),
                    "estimated_prices": [
                        {
                            "line_id": line["lineId"],
                            "odds": odds
                        }
                        for line in self.market_lines
                    ]
                }
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {sp_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            self.log_request_response(f"{sp_name} OFFER", "POST", url, headers=headers, 
                                    payload=payload, response=response)
            
            if response.status_code == 200:
                logger.info(f"✅ {sp_name} offer sent successfully (odds={odds}, max_risk=${max_risk}, validity={validity_seconds}s)")
                return True
            else:
                logger.error(f"❌ {sp_name} offer FAILED: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ {sp_name} offer ERROR: {str(e)}")
            return False

    def user_confirm_bet(self, parlay_id: str, odds: int, stake: int) -> bool:
        """User confirms the bet"""
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        
        payload = {
            "parlayId": parlay_id,
            "odds": odds,
            "stake": stake
        }
        
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            self.log_request_response("USER CONFIRM", "POST", url, headers=headers, 
                                    payload=payload, response=response)
            
            if response.status_code == 200:
                logger.info("✅ User bet confirmed successfully")
                return True
            else:
                logger.error(f"❌ User bet confirmation FAILED: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ User bet confirmation ERROR: {str(e)}")
            return False

    def sp_acknowledge_confirmation(self, sp_token: str, parlay_id: str, stake: int, 
                                  odds: int, sp_name: str, should_accept: bool = True) -> bool:
        """SP acknowledges the confirmation"""
        # First get orders
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(orders_url, headers=headers)
            self.log_request_response(f"{sp_name} GET ORDERS", "GET", orders_url, 
                                    headers=headers, response=response)
            
            if response.status_code != 200:
                logger.error(f"❌ {sp_name} get orders FAILED: {response.status_code}")
                return False
            
            orders = response.json()["data"]["orders"]
            order_uuid = None
            
            # Find matching order
            matching_orders = [order for order in orders if order["p_id"] == parlay_id]
            logger.info(f"🔍 {sp_name} found {len(matching_orders)} orders for parlay {parlay_id}")
            
            for order in orders:
                if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
                    order_uuid = order["order_uuid"]
                    break
            
            if not order_uuid:
                logger.error(f"❌ {sp_name} order UUID not found for parlay {parlay_id}")
                if matching_orders:
                    logger.error(f"   Available statuses: {[o.get('status') for o in matching_orders]}")
                return False
            
            logger.info(f"📋 Found {sp_name} order UUID: {order_uuid}")
            
            # Acknowledge confirmation
            confirm_url = f"{self.base_url}/parlay/sp/orders/confirmations"
            
            if should_accept:
                # Calculate proper values
                decimal_odds = (odds + 100) / 100 if odds > 0 else 100 / abs(odds) + 1
                max_risk_dollars = stake * decimal_odds
                max_risk_cents = int(max_risk_dollars * 100)
                
                # Calculate probability
                if odds > 0:
                    probability = 100 / (odds + 100)
                else:
                    probability = abs(odds) / (abs(odds) + 100)
                probability = round(probability, 10)
                
                payload = {
                    "action": "accept",
                    "confirmed_stake": stake,
                    "price_probability": [
                        {
                            "lines": [
                                {
                                    "line_id": line["lineId"],
                                    "probability": probability
                                }
                                for line in self.market_lines
                            ],
                            "max_risk": max_risk_cents,
                            "vig": 0.1
                        }
                    ],
                    "signature": f"test_signature_{sp_name.lower()}"
                }
                
                action_str = "ACCEPT"
                logger.info(f"📋 {sp_name} ACCEPT calculations:")
                logger.info(f"   confirmed_stake: ${stake:.2f}")
                logger.info(f"   odds: +{odds}")
                logger.info(f"   probability: {probability:.10f}")
                logger.info(f"   max_risk (cents): {max_risk_cents}")
            else:
                payload = {
                    "action": "reject",
                    "signature": f"test_signature_{sp_name.lower()}"
                }
                action_str = "REJECT"
                logger.info(f"📋 {sp_name} REJECT")
            
            params = {"order_uuid": order_uuid}
            response = requests.post(confirm_url, json=payload, headers=headers, params=params)
            
            self.log_request_response(f"{sp_name} {action_str}", "POST", confirm_url, 
                                    headers=headers, payload=payload, response=response, params=params)
            
            if response.status_code == 200:
                logger.info(f"✅ {sp_name} confirmation {action_str.lower()}ed successfully")
                return True
            else:
                logger.error(f"❌ {sp_name} {action_str.lower()} FAILED: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ {sp_name} acknowledgment ERROR: {str(e)}")
            return False

    def get_user_view_parlays(self, parlay_id: str, max_retries: int = 5) -> List[Dict]:
        """Get parlays from user view API"""
        user_orders_url = f"{self.base_url}/parlay/api/v1/user/list"
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{user_orders_url}?limit=50", headers=headers)
                
                self.log_request_response(f"USER VIEW (attempt {attempt+1})", "GET", 
                                        f"{user_orders_url}?limit=50", headers=headers, response=response)
                
                if response.status_code == 200:
                    data = response.json()
                    orders = data.get("data", {}).get("orders", [])
                    
                    # Filter for our specific parlay
                    matching_orders = [
                        order for order in orders 
                        if order.get("parlayId") == parlay_id
                    ]
                    
                    if matching_orders or attempt == max_retries - 1:
                        logger.info(f"📊 User view (attempt {attempt + 1}): Found {len(matching_orders)} parlays for {parlay_id}")
                        return matching_orders
                    else:
                        logger.info(f"📊 User view (attempt {attempt + 1}): No parlays yet, retrying in 4s...")
                        time.sleep(4)
                else:
                    logger.error(f"❌ Failed to get user view (attempt {attempt + 1}): {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(4)
                        
            except Exception as e:
                logger.error(f"❌ User view error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(4)
        
        return []

    def get_sp_orders(self, sp_token: str, parlay_id: str, sp_name: str) -> List[Dict]:
        """Get orders from SP orders API"""
        sp_orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(sp_orders_url, headers=headers)
            self.log_request_response(f"{sp_name} GET ALL ORDERS", "GET", sp_orders_url, 
                                    headers=headers, response=response)
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("data", {}).get("orders", [])
                
                # Filter for our specific parlay
                matching_orders = [
                    order for order in orders 
                    if order.get("p_id") == parlay_id
                ]
                
                logger.info(f"📊 {sp_name} orders: Found {len(matching_orders)} orders for {parlay_id}")
                return matching_orders
            else:
                logger.error(f"❌ Failed to get {sp_name} orders: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ {sp_name} orders error: {e}")
            return []

    # ===========================================
    # SCENARIO TESTS WITH FULL REQUEST/RESPONSE
    # ===========================================

    def test_scenario_01(self) -> bool:
        """Scenario 1: Basic Single SP Success"""
        logger.info(f"\n{'='*100}")
        logger.info("🧪 SCENARIO 1: Basic Single SP Success")
        logger.info("="*100)
        logger.info("Expected: Single SP provides best odds, user confirms, SP accepts → finalized parlay")
        
        try:
            # Fresh authentication
            self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            if not self.sp1_token:
                return False
            
            # Create parlay request
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # SP1 provides offer
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 800, 200, "SP1")
            if not sp1_offer:
                return False
            
            # User confirms bet
            user_confirm = self.user_confirm_bet(parlay_id, 800, 100)
            if not user_confirm:
                return False
            
            time.sleep(3)  # Allow processing
            
            # SP1 accepts
            sp1_ack = self.sp_acknowledge_confirmation(self.sp1_token, parlay_id, 100, 800, "SP1", True)
            if not sp1_ack:
                return False
            
            # Check results
            time.sleep(5)  # Allow propagation
            user_parlays = self.get_user_view_parlays(parlay_id)
            sp1_orders = self.get_sp_orders(self.sp1_token, parlay_id, "SP1")
            
            finalized_parlays = [p for p in user_parlays if p.get("status") == "finalized"]
            
            success = len(finalized_parlays) >= 1 and len(sp1_orders) >= 1
            
            logger.info(f"\n📊 SCENARIO 1 RESULTS:")
            logger.info(f"   SP1 offer: ✅")
            logger.info(f"   User confirm: ✅") 
            logger.info(f"   SP1 accept: ✅")
            logger.info(f"   Finalized parlays: {len(finalized_parlays)}")
            logger.info(f"   SP1 orders: {len(sp1_orders)}")
            logger.info(f"   Success: {'✅ PASSED' if success else '❌ FAILED'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SCENARIO 1 ERROR: {str(e)}")
            return False

    def test_scenario_02(self) -> bool:
        """Scenario 2: Best Odds Tier - One Rejects (STOP)"""
        logger.info(f"\n{'='*100}")
        logger.info("🧪 SCENARIO 2: Best Odds Tier - One Rejects (STOP)")
        logger.info("="*100)
        logger.info("Expected: Both SPs same tier, SP1 accepts, SP2 REJECTS → failed parlay (STOP)")
        
        try:
            # Fresh authentication
            self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            self.sp2_token = self.authenticate_sp(self.sp2_credentials, "SP2")
            if not self.sp1_token or not self.sp2_token:
                return False
            
            # Create parlay request
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # Both SPs provide same best odds (same tier)
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 800, 100, "SP1")
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 800, 150, "SP2")
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms bet requiring both SPs
            user_confirm = self.user_confirm_bet(parlay_id, 800, 200)
            if not user_confirm:
                return False
            
            time.sleep(3)
            
            # SP1 accepts, SP2 INTENTIONALLY REJECTS
            sp1_ack = self.sp_acknowledge_confirmation(self.sp1_token, parlay_id, 100, 800, "SP1", True)
            sp2_ack = self.sp_acknowledge_confirmation(self.sp2_token, parlay_id, 100, 800, "SP2", False)  # REJECT
            
            # Check results
            time.sleep(5)
            user_parlays = self.get_user_view_parlays(parlay_id)
            
            failed_parlays = [p for p in user_parlays if p.get("status") == "failed"]
            
            # Success criteria: SP1 accepted, SP2 rejected, failed parlay created (STOP behavior)
            success = sp1_ack and sp2_ack and len(failed_parlays) > 0
            
            logger.info(f"\n📊 SCENARIO 2 RESULTS:")
            logger.info(f"   SP1 accept: {'✅' if sp1_ack else '❌'}")
            logger.info(f"   SP2 reject: {'✅' if sp2_ack else '❌'}")
            logger.info(f"   Failed parlays: {len(failed_parlays)}")
            logger.info(f"   Success: {'✅ PASSED' if success else '❌ FAILED'} - {'STOP behavior working' if success else 'STOP behavior broken'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SCENARIO 2 ERROR: {str(e)}")
            return False

    def test_scenario_05(self) -> bool:
        """Scenario 5: Odds Expire Before User Confirmation (TIMEOUT)"""
        logger.info(f"\n{'='*100}")
        logger.info("🧪 SCENARIO 5: Odds Expire Before User Confirmation (TIMEOUT)")
        logger.info("="*100)
        logger.info("Expected: SP offers expire, user confirmation should fail")
        
        try:
            # Fresh authentication
            self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            if not self.sp1_token:
                return False
            
            # Create parlay request
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # SP provides SHORT validity offer (6 seconds)
            offer_time = time.time()
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 800, 100, "SP1", validity_seconds=6)
            if not sp1_offer:
                return False
            
            # Wait for offer to expire
            logger.info("⏰ Waiting for offers to expire (8 seconds)...")
            time.sleep(8)
            
            # User attempts to confirm AFTER expiry (should fail)
            confirm_time = time.time()
            user_confirm = self.user_confirm_bet(parlay_id, 800, 100)
            
            # Success criteria: User confirmation should FAIL due to expired offers
            success = not user_confirm
            
            logger.info(f"\n📊 SCENARIO 5 RESULTS:")
            logger.info(f"   Offer time: {offer_time:.2f}")
            logger.info(f"   Expiry time: {offer_time + 6:.2f}")
            logger.info(f"   Confirm time: {confirm_time:.2f}")
            logger.info(f"   Time after expiry: {confirm_time - (offer_time + 6):.2f}s")
            logger.info(f"   User confirm failed: {'✅' if not user_confirm else '❌'}")
            logger.info(f"   Success: {'✅ PASSED' if success else '❌ FAILED'} - {'TIMEOUT working' if success else '🐛 BUG: accepts expired offers'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SCENARIO 5 ERROR: {str(e)}")
            return False

    def test_scenario_04(self) -> bool:
        """Scenario 4: Complete Multi-Tier Success"""
        logger.info(f"\n{'='*100}")
        logger.info("🧪 SCENARIO 4: Complete Multi-Tier Success")
        logger.info("="*100)
        logger.info("Expected: Both SPs same tier, user needs both, both accept → 2 finalized parlays")
        
        try:
            # Fresh authentication
            self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            self.sp2_token = self.authenticate_sp(self.sp2_credentials, "SP2")
            if not self.sp1_token or not self.sp2_token:
                return False
            
            # Create parlay request
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # Both SPs provide same odds, limited capacity each
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 800, 100, "SP1")
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 800, 100, "SP2")
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms bet requiring both SPs (total stake > individual capacity)
            user_confirm = self.user_confirm_bet(parlay_id, 800, 180)
            if not user_confirm:
                return False
            
            time.sleep(3)
            
            # Both SPs accept their portions
            sp1_ack = self.sp_acknowledge_confirmation(self.sp1_token, parlay_id, 90, 800, "SP1", True)
            sp2_ack = self.sp_acknowledge_confirmation(self.sp2_token, parlay_id, 90, 800, "SP2", True)
            
            # Check results
            time.sleep(8)  # Allow extra propagation time
            user_parlays = self.get_user_view_parlays(parlay_id)
            
            finalized_parlays = [p for p in user_parlays if p.get("status") == "finalized"]
            
            # Success criteria: Both accepted, 2 finalized parlays created
            success = sp1_ack and sp2_ack and len(finalized_parlays) >= 2
            
            logger.info(f"\n📊 SCENARIO 4 RESULTS:")
            logger.info(f"   SP1 accept: {'✅' if sp1_ack else '❌'}")
            logger.info(f"   SP2 accept: {'✅' if sp2_ack else '❌'}")
            logger.info(f"   Total parlays: {len(user_parlays)}")
            logger.info(f"   Finalized parlays: {len(finalized_parlays)}")
            logger.info(f"   Success: {'✅ PASSED' if success else '❌ FAILED'} - {'Multi-tier working' if success else 'Multi-tier failed'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SCENARIO 4 ERROR: {str(e)}")
            return False

    def test_scenario_06(self) -> bool:
        """Scenario 6: Odds Expire During Matching Process (Critical)"""
        logger.info(f"\n{'='*100}")
        logger.info("🧪 SCENARIO 6: Odds Expire During Matching Process ⚠️ CRITICAL")
        logger.info("="*100)
        logger.info("Expected: SP1 short validity, SP2 long validity, user confirms, SP1 expires during processing")
        
        try:
            # Fresh authentication
            self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            self.sp2_token = self.authenticate_sp(self.sp2_credentials, "SP2")
            if not self.sp1_token or not self.sp2_token:
                return False
            
            # Create parlay request
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # SP1 short validity (6s), SP2 long validity (60s)
            offer_time = time.time()
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 900, 100, "SP1", validity_seconds=6)
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 800, 150, "SP2", validity_seconds=60)
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms quickly (within SP1 validity)
            user_confirm = self.user_confirm_bet(parlay_id, 900, 200)
            if not user_confirm:
                return False
            
            # Wait for SP1 to expire during processing
            logger.info("⏰ Waiting for SP1 to expire during matching (8s = 6s validity + 2s buffer)...")
            time.sleep(8)
            
            # Attempt SP acknowledgments (SP1 should fail due to expiry)
            confirm_time = time.time()
            sp1_ack = self.sp_acknowledge_confirmation(self.sp1_token, parlay_id, 100, 900, "SP1", True)
            
            logger.info(f"\n📊 SCENARIO 6 RESULTS:")
            logger.info(f"   Offer time: {offer_time:.2f}")
            logger.info(f"   SP1 expiry: {offer_time + 6:.2f}")
            logger.info(f"   SP1 ack time: {confirm_time:.2f}")
            logger.info(f"   Time after expiry: {confirm_time - (offer_time + 6):.2f}s")
            logger.info(f"   SP1 ack result: {'✅ Accepted' if sp1_ack else '❌ Rejected (correct)'}")
            
            # Success criteria: SP1 acknowledgment should FAIL due to expiry
            success = not sp1_ack
            
            if success:
                logger.info(f"   Success: ✅ PASSED - System properly rejected expired SP acknowledgment")
            else:
                logger.error(f"   Success: ❌ FAILED - 🐛 BUG: SP acknowledged expired odds")
                logger.error(f"   🐛 BUG CONFIRMED - Parlay ID: {parlay_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SCENARIO 6 ERROR: {str(e)}")
            return False

    def test_scenario_03(self) -> bool:
        """Scenario 3: Second Tier Matching with STOP"""
        logger.info(f"\n{'='*100}")
        logger.info("🧪 SCENARIO 3: Second Tier Matching with STOP")
        logger.info("="*100)
        logger.info("Expected: SP1 best odds (limited), SP2 second tier, SP2 rejects → STOP")
        
        try:
            # Fresh authentication
            self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            self.sp2_token = self.authenticate_sp(self.sp2_credentials, "SP2")
            if not self.sp1_token or not self.sp2_token:
                return False
            
            # Create parlay request
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # SP1 best odds, limited capacity; SP2 worse odds
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 900, 50, "SP1")
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 800, 200, "SP2")
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms bet requiring both tiers (stake > SP1 capacity)
            user_confirm = self.user_confirm_bet(parlay_id, 900, 150)  # Needs both SPs
            if not user_confirm:
                return False
            
            time.sleep(3)
            
            # SP1 accepts (first tier), SP2 rejects (second tier → STOP)
            sp1_ack = self.sp_acknowledge_confirmation(self.sp1_token, parlay_id, 50, 900, "SP1", True)
            sp2_ack = self.sp_acknowledge_confirmation(self.sp2_token, parlay_id, 100, 800, "SP2", False)  # Reject
            
            # Check results
            time.sleep(8)
            user_parlays = self.get_user_view_parlays(parlay_id)
            
            failed_parlays = [p for p in user_parlays if p.get("status") == "failed"]
            finalized_parlays = [p for p in user_parlays if p.get("status") == "finalized"]
            
            # Success criteria: SP2 rejection should STOP process, only partial from SP1
            success = sp1_ack and not sp2_ack and len(failed_parlays) >= 1
            
            logger.info(f"\n📊 SCENARIO 3 RESULTS:")
            logger.info(f"   SP1 accept: {'✅' if sp1_ack else '❌'}")
            logger.info(f"   SP2 reject: {'✅' if not sp2_ack else '❌'}")
            logger.info(f"   Failed parlays: {len(failed_parlays)}")
            logger.info(f"   Finalized parlays: {len(finalized_parlays)}")
            logger.info(f"   Success: {'✅ PASSED' if success else '❌ FAILED'} - {'STOP working' if success else 'STOP failed'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SCENARIO 3 ERROR: {str(e)}")
            return False

    def test_scenario_07(self) -> bool:
        """Scenario 7: Mixed Validity Periods"""
        logger.info(f"\n{'='*100}")
        logger.info("🧪 SCENARIO 7: Mixed Validity Periods")
        logger.info("="*100)
        logger.info("Expected: SP1 best odds (short validity), SP2 worse odds (long validity), SP1 expires → STOP")
        
        try:
            # Fresh authentication
            self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            self.sp2_token = self.authenticate_sp(self.sp2_credentials, "SP2")
            if not self.sp1_token or not self.sp2_token:
                return False
            
            # Create parlay request
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # SP1 best odds, short validity; SP2 worse odds, long validity
            offer_time = time.time()
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 950, 100, "SP1", validity_seconds=5)
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 750, 200, "SP2", validity_seconds=60)
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms best odds quickly
            user_confirm = self.user_confirm_bet(parlay_id, 950, 120)
            if not user_confirm:
                return False
            
            # Wait for SP1 to expire
            logger.info("⏰ Waiting for SP1 to expire (7s = 5s validity + 2s buffer)...")
            time.sleep(7)
            
            # Attempt acknowledgments (SP1 should fail due to expiry)
            confirm_time = time.time()
            sp1_ack = self.sp_acknowledge_confirmation(self.sp1_token, parlay_id, 100, 950, "SP1", True)
            
            # Check results
            time.sleep(5)
            user_parlays = self.get_user_view_parlays(parlay_id)
            failed_parlays = [p for p in user_parlays if p.get("status") == "failed"]
            
            # Success criteria: System should STOP rather than fallback to SP2's worse odds
            success = not sp1_ack
            
            logger.info(f"\n📊 SCENARIO 7 RESULTS:")
            logger.info(f"   Offer time: {offer_time:.2f}")
            logger.info(f"   SP1 expiry: {offer_time + 5:.2f}")
            logger.info(f"   Ack time: {confirm_time:.2f}")
            logger.info(f"   Time after expiry: {confirm_time - (offer_time + 5):.2f}s")
            logger.info(f"   SP1 ack result: {'❌ Rejected (correct)' if not sp1_ack else '✅ Accepted (wrong)'}")
            logger.info(f"   Failed parlays: {len(failed_parlays)}")
            logger.info(f"   Success: {'✅ PASSED' if success else '❌ FAILED'} - {'No worse odds fallback' if success else 'Worse odds fallback detected'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SCENARIO 7 ERROR: {str(e)}")
            return False

    def test_scenario_08(self) -> bool:
        """Scenario 8: No SP Responses"""
        logger.info(f"\n{'='*100}")
        logger.info("🧪 SCENARIO 8: No SP Responses")
        logger.info("="*100)
        logger.info("Expected: User creates parlay, no SPs provide offers, timeout gracefully")
        
        try:
            # Create parlay request without SP offers
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # Wait some time for potential offers (none expected)
            time.sleep(10)
            
            # Attempt user confirmation without offers
            logger.info("🔍 Attempting user confirmation without any SP offers...")
            user_confirm = self.user_confirm_bet(parlay_id, 800, 100)  # Should fail
            
            # Success criteria: Confirmation should fail gracefully
            success = not user_confirm
            
            logger.info(f"\n📊 SCENARIO 8 RESULTS:")
            logger.info(f"   User confirm result: {'❌ Failed (correct)' if not user_confirm else '✅ Passed (wrong)'}")
            logger.info(f"   Success: {'✅ PASSED' if success else '❌ FAILED'} - {'Graceful failure' if success else 'Unexpected success'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SCENARIO 8 ERROR: {str(e)}")
            return False

    def test_scenario_09(self) -> bool:
        """Scenario 9: All SPs Reject Best Tier"""
        logger.info(f"\n{'='*100}")
        logger.info("🧪 SCENARIO 9: All SPs Reject Best Tier")
        logger.info("="*100)
        logger.info("Expected: Multiple SPs same best odds, all reject → STOP, no fallback")
        
        try:
            # Fresh authentication
            self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            self.sp2_token = self.authenticate_sp(self.sp2_credentials, "SP2")
            if not self.sp1_token or not self.sp2_token:
                return False
            
            # Create parlay request
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # Both SPs provide same best odds
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 850, 100, "SP1")
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 850, 150, "SP2")
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms bet
            user_confirm = self.user_confirm_bet(parlay_id, 850, 180)
            if not user_confirm:
                return False
            
            time.sleep(3)
            
            # Both SPs reject
            sp1_ack = self.sp_acknowledge_confirmation(self.sp1_token, parlay_id, 100, 850, "SP1", False)
            sp2_ack = self.sp_acknowledge_confirmation(self.sp2_token, parlay_id, 80, 850, "SP2", False)
            
            # Check results
            time.sleep(8)
            user_parlays = self.get_user_view_parlays(parlay_id)
            failed_parlays = [p for p in user_parlays if p.get("status") == "failed"]
            
            # Success criteria: Both reject → complete failure, no fallback
            success = not sp1_ack and not sp2_ack and len(failed_parlays) >= 1
            
            logger.info(f"\n📊 SCENARIO 9 RESULTS:")
            logger.info(f"   SP1 reject: {'✅' if not sp1_ack else '❌'}")
            logger.info(f"   SP2 reject: {'✅' if not sp2_ack else '❌'}")
            logger.info(f"   Failed parlays: {len(failed_parlays)}")
            logger.info(f"   Success: {'✅ PASSED' if success else '❌ FAILED'} - {'Complete failure' if success else 'Unexpected success'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SCENARIO 9 ERROR: {str(e)}")
            return False

    def test_scenario_10(self) -> bool:
        """Scenario 10: Stake Exceeds SP Capacity"""
        logger.info(f"\n{'='*100}")
        logger.info("🧪 SCENARIO 10: Stake Exceeds SP Capacity")
        logger.info("="*100)
        logger.info("Expected: Limited SP capacity (300), user stake (500) → partial match only")
        
        try:
            # Fresh authentication
            self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            self.sp2_token = self.authenticate_sp(self.sp2_credentials, "SP2")
            if not self.sp1_token or not self.sp2_token:
                return False
            
            # Create parlay request
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # SPs with limited combined capacity (300 total)
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 800, 150, "SP1")  # $150 max
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 800, 150, "SP2")  # $150 max
            if not sp1_offer or not sp2_offer:
                return False
            
            # User requests stake beyond capacity (500 > 300)
            user_confirm = self.user_confirm_bet(parlay_id, 800, 500)
            if not user_confirm:
                return False
            
            time.sleep(3)
            
            # SPs accept what they can (partial fills)
            sp1_ack = self.sp_acknowledge_confirmation(self.sp1_token, parlay_id, 150, 800, "SP1", True)
            sp2_ack = self.sp_acknowledge_confirmation(self.sp2_token, parlay_id, 150, 800, "SP2", True)
            
            # Check results
            time.sleep(8)
            user_parlays = self.get_user_view_parlays(parlay_id)
            finalized_parlays = [p for p in user_parlays if p.get("status") == "finalized"]
            
            total_confirmed_stake = sum(p.get("confirmedStake", 0) for p in finalized_parlays)
            
            # Success criteria: Partial match (≤300), doesn't fail entirely
            success = sp1_ack and sp2_ack and total_confirmed_stake <= 300 and len(finalized_parlays) >= 2
            
            logger.info(f"\n📊 SCENARIO 10 RESULTS:")
            logger.info(f"   SP1 accept: {'✅' if sp1_ack else '❌'}")
            logger.info(f"   SP2 accept: {'✅' if sp2_ack else '❌'}")
            logger.info(f"   Finalized parlays: {len(finalized_parlays)}")
            logger.info(f"   Total confirmed stake: ${total_confirmed_stake}")
            logger.info(f"   Success: {'✅ PASSED' if success else '❌ FAILED'} - {'Partial fill working' if success else 'Partial fill failed'}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ SCENARIO 10 ERROR: {str(e)}")
            return False

    def run_all_scenarios(self):
        """Run all 10 test scenarios with full logging"""
        logger.info(f"\n{'='*120}")
        logger.info("🎯 COMPLETE PARLAY TEST SUITE - ALL 10 SCENARIOS")
        logger.info(f"Started at: {datetime.now().isoformat()}")
        logger.info("="*120)
        
        # All 10 test scenarios from TEST_SCENARIOS.md
        scenarios = [
            ("Scenario 1: Best Odds Tier - All Accept Success", self.test_scenario_01),
            ("Scenario 2: Best Odds Tier - One Rejects STOP", self.test_scenario_02),
            ("Scenario 3: Second Tier Matching with STOP", self.test_scenario_03),
            ("Scenario 4: Complete Multi-Tier Success", self.test_scenario_04),
            ("Scenario 5: Odds Expire Before User Confirmation", self.test_scenario_05),
            ("Scenario 6: Odds Expire During Matching (CRITICAL)", self.test_scenario_06),
            ("Scenario 7: Mixed Validity Periods", self.test_scenario_07),
            ("Scenario 8: No SP Responses", self.test_scenario_08),
            ("Scenario 9: All SPs Reject Best Tier", self.test_scenario_09),
            ("Scenario 10: Stake Exceeds SP Capacity", self.test_scenario_10)
        ]
        
        results = {}
        
        for scenario_name, test_func in scenarios:
            logger.info(f"\n🚀 Starting {scenario_name}...")
            try:
                results[scenario_name] = test_func()
            except Exception as e:
                logger.error(f"❌ {scenario_name} CRASHED: {str(e)}")
                results[scenario_name] = False
            
            # Brief pause between scenarios
            time.sleep(2)
        
        # Final summary
        logger.info(f"\n{'='*120}")
        logger.info("🏁 COMPLETE TEST RESULTS SUMMARY")
        logger.info("="*120)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        logger.info(f"📊 OVERALL: {passed}/{total} scenarios passed")
        
        for scenario_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"   {status}: {scenario_name}")
        
        logger.info(f"\nCompleted at: {datetime.now().isoformat()}")
        logger.info(f"📁 Full request/response logs saved to: complete_test_detailed_{int(time.time())}.log")
        
        return results

def main():
    """Main test runner"""
    suite = CompleteTestSuite()
    results = suite.run_all_scenarios()
    return results

if __name__ == "__main__":
    main()
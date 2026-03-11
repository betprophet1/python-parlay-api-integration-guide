#!/usr/bin/env python3
"""
🔄 RETRY FAILED SCENARIOS

Retries only the 6 failed test scenarios from the comprehensive test suite:
- Scenario 2: Best Odds Tier - One Rejects STOP
- Scenario 4: Complete Multi-Tier Success  
- Scenario 5: Odds Expire Before User Confirmation
- Scenario 6: Odds Expire During Matching Process (Critical)
- Scenario 7: Mixed Validity Periods
- Scenario 9: All SPs Reject Best Tier

Uses the same working foundation but focuses on understanding failure patterns.
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'retry_failed_scenarios_{int(time.time())}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RetryFailedScenarios:
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
        
        # Get fresh user token
        self.user_token = self.get_fresh_user_token()
        
        # Tokens for authenticated sessions
        self.sp1_token = None
        self.sp2_token = None
        
        # Working test data
        self.market_lines = [
            {
                "line": 0,
                "lineId": "99fe18eea332562ac5cd04d4b3c772d0",
                "marketId": 406,
                "outcomeId": 4,
                "sportEventId": 30023983
            },
            {
                "line": -1.5,
                "lineId": "b3ac37f3974eb98f726a5f852f07f9f6",
                "marketId": 410,
                "outcomeId": 1714,
                "sportEventId": 30023984
            }
        ]
        
        # Results tracking
        self.retry_results = {}
    
    def get_fresh_user_token(self) -> str:
        """Get fresh user authentication token"""
        login_url = "https://api-ss-sandbox.betprophet.co/api/v1/auth/login"
        payload = {
            "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
            "email": "lam.tran+usr004@betprophet.co",
            "password": "Kh0ngbiet1"
        }
        
        try:
            response = requests.post(login_url, json=payload)
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
    
    def calculate_probability_from_odds(self, odds: int) -> float:
        """Calculate probability from American odds (CORRECTED VERSION)"""
        if odds > 0:
            probability = 100 / (odds + 100)
        else:
            probability = abs(odds) / (abs(odds) + 100)
        return round(probability, 10)

    def authenticate_sp(self, credentials: Dict[str, str], sp_name: str) -> Optional[str]:
        """Authenticate Service Provider and return access token"""
        url = f"{self.base_url}/partner/auth/login"
        
        try:
            response = requests.post(url, json=credentials, headers={
                "Content-Type": "application/json"
            })
            
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
            
            if response.status_code == 200:
                parlay_id = response.json()["data"]["parlayId"]
                logger.info(f"✅ Parlay created successfully - ID: {parlay_id}")
                return parlay_id
            else:
                logger.error(f"❌ Parlay creation FAILED: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Parlay creation ERROR: {str(e)}")
            return None

    def provide_sp_offer(self, parlay_id: str, sp_token: str, odds: int, max_risk: int, 
                        sp_name: str, validity_seconds: int = 50) -> bool:
        """Service Provider provides offer with customizable validity"""
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
            
            if response.status_code == 200:
                logger.info(f"✅ {sp_name} offer sent successfully (odds={odds}, max_risk=${max_risk}, validity={validity_seconds}s)")
                return True
            else:
                logger.error(f"❌ {sp_name} offer FAILED: {response.status_code} - {response.text}")
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
            
            if response.status_code == 200:
                logger.info("✅ User bet confirmed successfully")
                return True
            else:
                logger.error(f"❌ User bet confirmation FAILED: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ User bet confirmation ERROR: {str(e)}")
            return False

    def sp_acknowledge_confirmation_corrected(self, sp_token: str, parlay_id: str, stake: int, 
                                            odds: int, sp_name: str, should_accept: bool = True) -> bool:
        """SP acknowledges the confirmation with option to accept or reject"""
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(orders_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ {sp_name} get orders FAILED: {response.status_code}")
                return False
            
            orders = response.json()["data"]["orders"]
            order_uuid = None
            
            # Find matching order for this parlay
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
            
            # Calculate proper max_risk and CORRECT probability
            decimal_odds = (odds + 100) / 100 if odds > 0 else 100 / abs(odds) + 1
            max_risk_dollars = stake * decimal_odds
            max_risk_cents = int(max_risk_dollars * 100)
            
            # Calculate CORRECT probabilities from odds
            probability = self.calculate_probability_from_odds(odds)
            
            action = "accept" if should_accept else "reject"
            logger.info(f"📋 {sp_name} {action.upper()} with calculations:")
            logger.info(f"   confirmed_stake: ${stake:.2f}")
            logger.info(f"   odds: +{odds}")
            logger.info(f"   probability (calculated): {probability:.10f}")
            if should_accept:
                logger.info(f"   max_risk (cents): {max_risk_cents}")
            
            # Acknowledge confirmation
            confirm_url = f"{self.base_url}/parlay/sp/orders/confirmations"
            
            if should_accept:
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
            else:
                payload = {
                    "action": "reject",
                    "signature": f"test_signature_{sp_name.lower()}"
                }
            
            response = requests.post(confirm_url, json=payload, headers=headers, params={"order_uuid": order_uuid})
            
            if response.status_code == 200:
                logger.info(f"✅ {sp_name} confirmation {action}ed successfully")
                return True
            else:
                logger.error(f"❌ {sp_name} {action} FAILED: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ {sp_name} acknowledgment ERROR: {str(e)}")
            return False

    def get_user_view_parlays_with_retry(self, parlay_id: str, max_retries: int = 5) -> List[Dict]:
        """Get parlays from user view API with extended retry logic for failed scenarios"""
        user_orders_url = f"{self.base_url}/parlay/api/v1/user/list"
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{user_orders_url}?limit=50", headers=headers)
                
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
                        time.sleep(4)  # Longer delay for failed scenarios
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

    # =================
    # RETRY SCENARIOS
    # =================

    def retry_scenario_02(self) -> bool:
        """RETRY Scenario 2: Best Odds Tier - One Rejects STOP"""
        logger.info("\n🔄 RETRY SCENARIO 2: Best Odds Tier - One Rejects STOP")
        logger.info("="*80)
        
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
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 800, 100, "SP1")
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 800, 150, "SP2")
            
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms bet
            user_confirm = self.user_confirm_bet(parlay_id, 800, 200)
            if not user_confirm:
                return False
            
            time.sleep(3)
            
            # SP1 accepts, SP2 rejects
            sp1_ack = self.sp_acknowledge_confirmation_corrected(self.sp1_token, parlay_id, 100, 800, "SP1", True)
            sp2_ack = self.sp_acknowledge_confirmation_corrected(self.sp2_token, parlay_id, 100, 800, "SP2", False)
            
            # Get user parlays with extended retry
            logger.info("⏰ Getting user parlays with extended retry logic...")
            user_parlays = self.get_user_view_parlays_with_retry(parlay_id, max_retries=5)
            has_failed_parlay = any(p.get("status") == "failed" for p in user_parlays)
            
            logger.info(f"🔍 Found {len(user_parlays)} user parlays, has failed parlay: {has_failed_parlay}")
            
            # Success criteria: SP1 accepted, SP2 rejected, failed parlay created
            success = sp1_ack and not sp2_ack and has_failed_parlay
            
            if success:
                logger.info("✅ RETRY SCENARIO 2 PASSED: STOP behavior working - failed parlay created")
            else:
                logger.error("❌ RETRY SCENARIO 2 FAILED")
                logger.error(f"   SP1 ack: {sp1_ack}, SP2 ack: {sp2_ack}, failed parlay: {has_failed_parlay}")
                if user_parlays:
                    for i, p in enumerate(user_parlays):
                        logger.error(f"   Parlay {i+1}: status={p.get('status')}, confirmed=${p.get('confirmedStake', 0)}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ RETRY SCENARIO 2 ERROR: {str(e)}")
            return False

    def retry_scenario_04(self) -> bool:
        """RETRY Scenario 4: Complete Multi-Tier Success"""
        logger.info("\n🔄 RETRY SCENARIO 4: Complete Multi-Tier Success")
        logger.info("="*80)
        
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
            
            # Both SPs provide same odds for multi-tier capacity test
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 800, 100, "SP1")
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 800, 100, "SP2")
            
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms large stake requiring both SPs
            user_confirm = self.user_confirm_bet(parlay_id, 800, 180)
            if not user_confirm:
                return False
            
            time.sleep(3)
            
            # Both SPs accept their portions
            sp1_ack = self.sp_acknowledge_confirmation_corrected(self.sp1_token, parlay_id, 90, 800, "SP1", True)
            sp2_ack = self.sp_acknowledge_confirmation_corrected(self.sp2_token, parlay_id, 90, 800, "SP2", True)
            
            # Extended retry for user view
            logger.info("⏰ Getting user parlays with extended retry logic...")
            user_parlays = self.get_user_view_parlays_with_retry(parlay_id, max_retries=5)
            
            # Count finalized parlays
            finalized_parlays = [p for p in user_parlays if p.get("status") == "finalized"]
            
            logger.info(f"🔍 Found {len(user_parlays)} total parlays, {len(finalized_parlays)} finalized")
            
            # Success: Both SPs accepted and created finalized parlays
            success = sp1_ack and sp2_ack and len(finalized_parlays) == 2
            
            if success:
                logger.info("✅ RETRY SCENARIO 4 PASSED: Multi-tier matching successful")
                for i, p in enumerate(finalized_parlays):
                    logger.info(f"   Parlay {i+1}: ${p.get('requestedStake', 0)} → ${p.get('confirmedStake', 0)}, status: {p.get('status')}")
            else:
                logger.error("❌ RETRY SCENARIO 4 FAILED")
                logger.error(f"   SP1 ack: {sp1_ack}, SP2 ack: {sp2_ack}, finalized parlays: {len(finalized_parlays)}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ RETRY SCENARIO 4 ERROR: {str(e)}")
            return False

    def retry_scenario_05(self) -> bool:
        """RETRY Scenario 5: Odds Expire Before User Confirmation"""
        logger.info("\n🔄 RETRY SCENARIO 5: Odds Expire Before User Confirmation")
        logger.info("="*80)
        
        try:
            # Fresh authentication
            self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
            if not self.sp1_token:
                return False
            
            # Create parlay request
            parlay_id = self.create_parlay_request()
            if not parlay_id:
                return False
            
            # SP provides short-validity odds (6 seconds minimum)
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 800, 100, "SP1", validity_seconds=6)
            if not sp1_offer:
                return False
            
            # Wait for odds to expire + buffer
            logger.info("⏰ Waiting for odds to expire (8 seconds = 6s validity + 2s buffer)...")
            time.sleep(8)
            
            # User attempts to confirm after expiry
            logger.info("📤 User attempting to confirm expired odds...")
            user_confirm = self.user_confirm_bet(parlay_id, 800, 100)
            
            # Success criteria: User confirmation should fail due to expired odds
            success = not user_confirm  # Should fail
            
            if success:
                logger.info("✅ RETRY SCENARIO 5 PASSED: System correctly rejected expired odds")
            else:
                logger.error("❌ RETRY SCENARIO 5 FAILED: System accepted expired odds")
                logger.error(f"🐛 BUG CONFIRMED - Parlay ID: {parlay_id}")
                logger.error("🐛 Odds expired but system accepted user confirmation")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ RETRY SCENARIO 5 ERROR: {str(e)}")
            return False

    def retry_scenario_06(self) -> bool:
        """RETRY Scenario 6: Odds Expire During Matching Process (Critical)"""
        logger.info("\n🔄 RETRY SCENARIO 6: Odds Expire During Matching Process ⚠️ CRITICAL")
        logger.info("="*80)
        
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
            
            # SP1 short validity, SP2 long validity
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 900, 100, "SP1", validity_seconds=6)
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 800, 150, "SP2", validity_seconds=60)
            
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms quickly (within SP1 validity)
            user_confirm = self.user_confirm_bet(parlay_id, 900, 200)
            if not user_confirm:
                return False
            
            # Wait for SP1 to expire during processing + buffer
            logger.info("⏰ Waiting for SP1 odds to expire during processing (8s = 6s validity + 2s buffer)...")
            time.sleep(8)
            
            # Attempt SP acknowledgments (SP1 should fail due to expiry)
            sp1_ack = self.sp_acknowledge_confirmation_corrected(self.sp1_token, parlay_id, 100, 900, "SP1", True)
            
            # Check for bug
            if sp1_ack:
                logger.error(f"🐛 BUG CONFIRMED - Parlay ID: {parlay_id}")
                logger.error("🐛 SP1 acknowledgment succeeded despite odds being expired (6s + 2s buffer)")
            
            # Success criteria: SP1 fails due to expiry, matching stops
            success = not sp1_ack
            
            if success:
                logger.info("✅ RETRY SCENARIO 6 PASSED: System properly rejected expired SP acknowledgment")
            else:
                logger.error("❌ RETRY SCENARIO 6 FAILED: SP acknowledgment succeeded despite expiry")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ RETRY SCENARIO 6 ERROR: {str(e)}")
            return False

    def retry_scenario_07(self) -> bool:
        """RETRY Scenario 7: Mixed Validity Periods"""
        logger.info("\n🔄 RETRY SCENARIO 7: Mixed Validity Periods")
        logger.info("="*80)
        
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
            
            # Mixed validity setup
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 900, 100, "SP1", validity_seconds=6)
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 750, 150, "SP2", validity_seconds=60)
            
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms best odds
            user_confirm = self.user_confirm_bet(parlay_id, 900, 150)
            if not user_confirm:
                return False
            
            # Wait for SP1 to expire + buffer
            logger.info("⏰ Waiting for SP1 best odds to expire (8s = 6s validity + 2s buffer)...")
            time.sleep(8)
            
            # Attempt acknowledgments
            sp1_ack = self.sp_acknowledge_confirmation_corrected(self.sp1_token, parlay_id, 100, 900, "SP1", True)
            
            # Check for bug
            if sp1_ack:
                logger.error(f"🐛 BUG CONFIRMED - Parlay ID: {parlay_id}")
                logger.error("🐛 SP1 best odds acknowledgment succeeded despite being expired")
            
            # Success: SP1 expires, system doesn't fallback to worse SP2 odds
            success = not sp1_ack
            
            if success:
                logger.info("✅ RETRY SCENARIO 7 PASSED: System properly handled expired best odds")
            else:
                logger.error("❌ RETRY SCENARIO 7 FAILED: Expired odds were accepted")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ RETRY SCENARIO 7 ERROR: {str(e)}")
            return False

    def retry_scenario_09(self) -> bool:
        """RETRY Scenario 9: All SPs Reject Best Tier"""
        logger.info("\n🔄 RETRY SCENARIO 9: All SPs Reject Best Tier")
        logger.info("="*80)
        
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
            sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 800, 100, "SP1")
            sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 800, 150, "SP2")
            
            if not sp1_offer or not sp2_offer:
                return False
            
            # User confirms bet
            user_confirm = self.user_confirm_bet(parlay_id, 800, 200)
            if not user_confirm:
                return False
            
            time.sleep(3)
            
            # Both SPs reject
            sp1_ack = self.sp_acknowledge_confirmation_corrected(self.sp1_token, parlay_id, 100, 800, "SP1", False)
            sp2_ack = self.sp_acknowledge_confirmation_corrected(self.sp2_token, parlay_id, 100, 800, "SP2", False)
            
            # Extended retry for user view
            logger.info("⏰ Getting user parlays with extended retry logic...")
            user_parlays = self.get_user_view_parlays_with_retry(parlay_id, max_retries=5)
            failed_parlays = [p for p in user_parlays if p.get("status") == "failed"]
            
            logger.info(f"🔍 Found {len(user_parlays)} total parlays, {len(failed_parlays)} failed")
            
            # Success: Both rejected, failed parlays created (correct STOP behavior)
            success = not sp1_ack and not sp2_ack and len(failed_parlays) >= 2
            
            if success:
                logger.info("✅ RETRY SCENARIO 9 PASSED: STOP behavior working - failed parlays created")
                for i, p in enumerate(failed_parlays):
                    logger.info(f"   Failed parlay {i+1}: ${p.get('requestedStake', 0)} → status: {p.get('status')}")
            else:
                logger.error("❌ RETRY SCENARIO 9 FAILED")
                logger.error(f"   SP1 ack: {sp1_ack}, SP2 ack: {sp2_ack}, failed parlays: {len(failed_parlays)}")
                for i, p in enumerate(user_parlays):
                    logger.error(f"   Parlay {i+1}: status={p.get('status')}, confirmed=${p.get('confirmedStake', 0)}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ RETRY SCENARIO 9 ERROR: {str(e)}")
            return False

    def run_retry_tests(self):
        """Run all retry tests for failed scenarios"""
        logger.info("\n🔄 RETRYING ALL FAILED SCENARIOS")
        logger.info("="*100)
        logger.info("🎯 Focusing on the 6 scenarios that failed in the comprehensive test")
        logger.info("⏰ Using extended retry logic and deeper investigation")
        logger.info("="*100)
        
        # Run retry tests
        results = {}
        results["scenario_02"] = self.retry_scenario_02()
        results["scenario_04"] = self.retry_scenario_04() 
        results["scenario_05"] = self.retry_scenario_05()
        results["scenario_06"] = self.retry_scenario_06()
        results["scenario_07"] = self.retry_scenario_07()
        results["scenario_09"] = self.retry_scenario_09()
        
        # Calculate results
        passed = sum(1 for r in results.values() if r)
        failed = len(results) - passed
        
        # Summary
        logger.info(f"\n{'='*100}")
        logger.info("🏁 RETRY TESTS COMPLETE")
        logger.info("="*100)
        logger.info(f"📊 RETRY RESULTS: {passed}/{len(results)} scenarios passed")
        logger.info(f"✅ PASSED: {passed}")
        logger.info(f"❌ FAILED: {failed}")
        
        logger.info(f"\n📋 DETAILED RETRY RESULTS:")
        for scenario, result in results.items():
            status_emoji = "✅" if result else "❌"
            logger.info(f"   {status_emoji} {scenario}: {'PASSED' if result else 'FAILED'}")
        
        if passed > 0:
            logger.info(f"\n🎉 RETRY SUCCESS! {passed} scenarios now working")
        
        if failed > 0:
            logger.info(f"\n🔧 {failed} scenarios still need investigation")
            logger.info("   Check logs for bug confirmations and detailed error analysis")
        
        logger.info(f"\n📁 Detailed retry logs saved to: retry_failed_scenarios_{int(time.time())}.log")
        
        return results

def main():
    """Main retry runner"""
    retry_suite = RetryFailedScenarios()
    results = retry_suite.run_retry_tests()
    return results

if __name__ == "__main__":
    main()
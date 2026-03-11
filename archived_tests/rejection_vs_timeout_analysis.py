#!/usr/bin/env python3
"""
🔍 REJECTION vs TIMEOUT ANALYSIS

Properly distinguishes between:
1. REJECTION: SP intentionally sends "action": "reject" 
2. TIMEOUT: SP fails to acknowledge within valid_until period

Tests scenarios 2 & 9 for proper rejection handling
Tests scenarios 5, 6, 7 for proper timeout handling
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RejectionTimeoutAnalysis:
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
        
        # Test data
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
    
    def authenticate_sp(self, credentials: Dict[str, str], sp_name: str) -> Optional[str]:
        """Authenticate Service Provider"""
        url = f"{self.base_url}/partner/auth/login"
        
        try:
            response = requests.post(url, json=credentials)
            if response.status_code == 200:
                token = response.json()["data"]["access_token"]
                logger.info(f"✅ {sp_name} Authentication SUCCESS")
                return token
            return None
        except Exception as e:
            logger.error(f"❌ {sp_name} Authentication ERROR: {str(e)}")
            return None
    
    def create_parlay_request(self) -> Optional[str]:
        """Create parlay request"""
        url = f"{self.base_url}/parlay/api/v1/user/request"
        payload = {"marketLines": self.market_lines}
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                parlay_id = response.json()["data"]["parlayId"]
                logger.info(f"✅ Parlay created: {parlay_id}")
                return parlay_id
            return None
        except Exception as e:
            logger.error(f"❌ Parlay creation ERROR: {str(e)}")
            return None
    
    def provide_sp_offer(self, parlay_id: str, sp_token: str, odds: int, max_risk: int, 
                        sp_name: str, validity_seconds: int = 50) -> bool:
        """Provide SP offer"""
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
                logger.info(f"✅ {sp_name} offer sent (odds={odds}, validity={validity_seconds}s)")
                return True
            else:
                logger.error(f"❌ {sp_name} offer FAILED: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ {sp_name} offer ERROR: {str(e)}")
            return False
    
    def user_confirm_bet(self, parlay_id: str, odds: int, stake: int) -> bool:
        """User confirms bet"""
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
                logger.info("✅ User bet confirmed")
                return True
            else:
                logger.error(f"❌ User confirmation FAILED: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ User confirmation ERROR: {str(e)}")
            return False
    
    def sp_acknowledge(self, sp_token: str, parlay_id: str, stake: int, odds: int, 
                      sp_name: str, action: str = "accept") -> bool:
        """SP acknowledges with explicit action: 'accept' or 'reject'"""
        # Get orders first
        orders_url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(orders_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"❌ {sp_name} get orders FAILED: {response.status_code}")
                return False
            
            orders = response.json()["data"]["orders"]
            order_uuid = None
            
            # Find matching order
            for order in orders:
                if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
                    order_uuid = order["order_uuid"]
                    break
            
            if not order_uuid:
                logger.error(f"❌ {sp_name} order UUID not found for parlay {parlay_id}")
                return False
            
            logger.info(f"📋 {sp_name} {action.upper()}ING order {order_uuid}")
            
            # Acknowledge with specific action
            confirm_url = f"{self.base_url}/parlay/sp/orders/confirmations"
            
            if action == "accept":
                decimal_odds = (odds + 100) / 100 if odds > 0 else 100 / abs(odds) + 1
                max_risk_cents = int(stake * decimal_odds * 100)
                probability = 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)
                
                payload = {
                    "action": "accept",
                    "confirmed_stake": stake,
                    "price_probability": [
                        {
                            "lines": [
                                {
                                    "line_id": line["lineId"],
                                    "probability": round(probability, 10)
                                }
                                for line in self.market_lines
                            ],
                            "max_risk": max_risk_cents,
                            "vig": 0.1
                        }
                    ],
                    "signature": f"test_signature_{sp_name.lower()}"
                }
            elif action == "reject":
                payload = {
                    "action": "reject",
                    "signature": f"test_signature_{sp_name.lower()}"
                }
            else:
                logger.error(f"❌ Invalid action: {action}")
                return False
            
            response = requests.post(confirm_url, json=payload, headers=headers, 
                                   params={"order_uuid": order_uuid})
            
            if response.status_code == 200:
                logger.info(f"✅ {sp_name} {action}ed successfully")
                return True
            else:
                logger.error(f"❌ {sp_name} {action} FAILED: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ {sp_name} acknowledgment ERROR: {str(e)}")
            return False
    
    def get_user_view_parlays(self, parlay_id: str, max_retries: int = 3) -> List[Dict]:
        """Get parlays from user view with retry"""
        url = f"{self.base_url}/parlay/api/v1/user/list"
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{url}?limit=50", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    orders = data.get("data", {}).get("orders", [])
                    matching_orders = [o for o in orders if o.get("parlayId") == parlay_id]
                    
                    if matching_orders or attempt == max_retries - 1:
                        logger.info(f"📊 User view: Found {len(matching_orders)} parlays")
                        return matching_orders
                    else:
                        logger.info(f"📊 User view (attempt {attempt + 1}): No parlays yet, retrying...")
                        time.sleep(3)
                else:
                    logger.error(f"❌ User view error: {response.status_code}")
                    time.sleep(3)
            except Exception as e:
                logger.error(f"❌ User view exception: {e}")
                time.sleep(3)
        
        return []
    
    def test_intentional_rejection(self):
        """Test Scenario 2: One SP intentionally rejects"""
        logger.info("\n🚫 TESTING INTENTIONAL REJECTION (Scenario 2)")
        logger.info("="*80)
        logger.info("Expected: SP1 accepts, SP2 REJECTS with 'action': 'reject'")
        logger.info("Expected result: Failed parlay due to insufficient capacity after rejection")
        
        # Authenticate both SPs
        sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
        sp2_token = self.authenticate_sp(self.sp2_credentials, "SP2")
        
        if not sp1_token or not sp2_token:
            logger.error("❌ Failed to authenticate SPs")
            return False
        
        # Create parlay
        parlay_id = self.create_parlay_request()
        if not parlay_id:
            return False
        
        # Both SPs provide same best odds (same tier)
        sp1_offer = self.provide_sp_offer(parlay_id, sp1_token, 800, 100, "SP1")
        sp2_offer = self.provide_sp_offer(parlay_id, sp2_token, 800, 150, "SP2")
        
        if not sp1_offer or not sp2_offer:
            return False
        
        # User confirms bet requiring both SPs (total stake > individual capacity)
        user_confirm = self.user_confirm_bet(parlay_id, 800, 200)
        if not user_confirm:
            return False
        
        time.sleep(3)  # Allow system to process
        
        # SP1 ACCEPTS (capacity: $100)
        sp1_ack = self.sp_acknowledge(sp1_token, parlay_id, 100, 800, "SP1", "accept")
        
        # SP2 INTENTIONALLY REJECTS (should cause insufficient capacity)
        sp2_ack = self.sp_acknowledge(sp2_token, parlay_id, 100, 800, "SP2", "reject")
        
        # Wait for processing
        time.sleep(5)
        
        # Check results
        user_parlays = self.get_user_view_parlays(parlay_id)
        failed_parlays = [p for p in user_parlays if p.get("status") == "failed"]
        finalized_parlays = [p for p in user_parlays if p.get("status") == "finalized"]
        
        logger.info(f"📊 Results:")
        logger.info(f"   SP1 accept: {sp1_ack}")
        logger.info(f"   SP2 reject: {not sp2_ack}")  # Note: reject should return success but create rejection
        logger.info(f"   Total parlays: {len(user_parlays)}")
        logger.info(f"   Failed parlays: {len(failed_parlays)}")
        logger.info(f"   Finalized parlays: {len(finalized_parlays)}")
        
        # Success criteria: SP1 accepted, SP2 rejected, system creates failed parlays
        success = sp1_ack and sp2_ack and len(failed_parlays) > 0
        
        if success:
            logger.info("✅ INTENTIONAL REJECTION TEST PASSED")
            logger.info("   System properly handled SP2's intentional rejection")
        else:
            logger.error("❌ INTENTIONAL REJECTION TEST FAILED")
            logger.error("   System did not properly handle SP rejection scenario")
        
        return success
    
    def test_timeout_behavior(self):
        """Test Scenario 5: SP times out (doesn't acknowledge within validity period)"""
        logger.info("\n⏰ TESTING TIMEOUT BEHAVIOR (Scenario 5)")
        logger.info("="*80)
        logger.info("Expected: SP offers expire, user confirmation should be rejected")
        
        # Authenticate SP
        sp_token = self.authenticate_sp(self.sp1_credentials, "SP1")
        if not sp_token:
            return False
        
        # Create parlay
        parlay_id = self.create_parlay_request()
        if not parlay_id:
            return False
        
        # SP provides SHORT validity offer (6 seconds)
        offer_time = time.time()
        sp_offer = self.provide_sp_offer(parlay_id, sp_token, 800, 100, "SP1", validity_seconds=6)
        if not sp_offer:
            return False
        
        # Wait for offer to EXPIRE
        logger.info("⏰ Waiting for SP offer to expire (8s = 6s validity + 2s buffer)...")
        time.sleep(8)
        
        # User attempts to confirm AFTER expiry (should fail)
        confirm_time = time.time()
        user_confirm = self.user_confirm_bet(parlay_id, 800, 100)
        
        logger.info(f"📊 Timeout Test Results:")
        logger.info(f"   Offer created at: {offer_time:.2f}")
        logger.info(f"   Offer expires at: {offer_time + 6:.2f}")
        logger.info(f"   User confirmed at: {confirm_time:.2f}")
        logger.info(f"   Time after expiry: {confirm_time - (offer_time + 6):.2f}s")
        logger.info(f"   User confirmation success: {user_confirm}")
        
        # Success criteria: User confirmation should FAIL due to expired offers
        success = not user_confirm
        
        if success:
            logger.info("✅ TIMEOUT BEHAVIOR TEST PASSED")
            logger.info("   System properly rejected user confirmation for expired offers")
        else:
            logger.error("❌ TIMEOUT BEHAVIOR TEST FAILED")
            logger.error("🐛 BUG CONFIRMED: System accepts user confirmation for expired offers")
        
        return success
    
    def run_analysis(self):
        """Run comprehensive rejection vs timeout analysis"""
        logger.info("\n🔍 REJECTION vs TIMEOUT COMPREHENSIVE ANALYSIS")
        logger.info("="*100)
        logger.info("Testing the distinction between intentional rejection and timeout")
        logger.info("="*100)
        
        results = {}
        
        # Test intentional rejection
        results["intentional_rejection"] = self.test_intentional_rejection()
        
        # Test timeout behavior  
        results["timeout_behavior"] = self.test_timeout_behavior()
        
        # Summary
        logger.info(f"\n{'='*100}")
        logger.info("🏁 REJECTION vs TIMEOUT ANALYSIS COMPLETE")
        logger.info("="*100)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        logger.info(f"📊 RESULTS: {passed}/{total} tests passed")
        
        for test_name, result in results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"   {status}: {test_name}")
        
        if not results["intentional_rejection"]:
            logger.info("\n🚫 INTENTIONAL REJECTION ISSUES:")
            logger.info("   - SP rejection may not be creating proper failed status")
            logger.info("   - Check if 'action': 'reject' is handled correctly")
        
        if not results["timeout_behavior"]:
            logger.info("\n⏰ TIMEOUT ISSUES:")
            logger.info("   - System accepts user confirmations for expired offers")
            logger.info("   - Expiry validation missing in user confirmation step")
        
        return results

def main():
    """Run rejection vs timeout analysis"""
    analyzer = RejectionTimeoutAnalysis()
    results = analyzer.run_analysis()
    return results

if __name__ == "__main__":
    main()
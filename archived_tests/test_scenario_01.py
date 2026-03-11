#!/usr/bin/env python3
"""
Test Scenario 1: Best Odds Tier - All Accept Success

Setup: Two SPs provide same best odds (800)
Action: User confirms bet, both SPs accept
Expected: Process continues to next tier if stake not fully matched
Validation: Both SPs process orders successfully
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestScenario1:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        
        # SP Credentials
        self.sp1_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        
        self.sp2_credentials = {
            "access_key": "ec45827afa933f97ec19e674c0fa39c6", 
            "secret_key": "442df8e9fe96e4f7e744b2d3cac5cd51"
        }
        
        # User token (pre-authenticated)
        self.user_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6InNpbTIifQ.eyJhY2NvdW50VHlwZSI6MCwiZXhwIjoxNzU5ODQwMjk0LCJleHRyYU9ubGluZVRpbWUiOjAsImlzT3RwRXhwaXJlZCI6ZmFsc2UsImlzU3VzcGVuZGVkIjpmYWxzZSwiaXNzIjoiaHR0cDovL21vdGhlcnNoaXAubW90aGVyc2hpcC1zYW5kYm94IiwianRpIjoiYTExOTQ4NDEtNzNiOC00ZGFjLTg0OTUtMTdiMGIyZTZmNjZiIiwia2JhQW5zd2Vyc0luZm8iOiJOL0EiLCJreWNJbmZvIjoiU3VjY2VzcyIsInBlbmRpbmdCeUFkbWluIjpmYWxzZSwicHVzaGVySW5mbyI6eyJhdXRoQ2hhbm5lbCI6InVzZXIuYXV0aGVudGljYXRpb24uYTExOTQ4NDEtNzNiOC00ZGFjLTg0OTUtMTdiMGIyZTZmNjZiIiwiYmFsYW5jZVVwZGF0ZWRFdmVudCI6IndhbGxldC5iYWxhbmNlLnVwZGF0ZWQiLCJjbHVzdGVyIjoibXQxIiwiaWQiOiJjMjBmYTM2ZmJjM2MzYzMwOGZmYSIsImluZm9DaGFubmVsIjoidXNlci5pbmZvcm1hdGlvbi5lZjVjM2JlMy1hZDRkLTRlMGYtYWNlNy05NzA1NjkwYzgyNmUiLCJpbmZvcm1hdGlvblVwZGF0ZWRFdmVudCI6InVzZXIuaW5mb3JtYXRpb24udXBkYXRlZCIsImtiYUNoYWxsZW5nZVF1ZXN0aW9uc0V2ZW50IjoidXNlci5rYmEuY2hhbGxlbmdlIiwic2Vzc2lvblRlcm1pbmF0ZWRFdmVudCI6InNlc3Npb24udGVybWluYXRlZCJ9LCJyZWdpb24iOiJOWSIsInN1YiI6ImxhbS50cmFuK3VzcjAwNEBiZXRwcm9waGV0LmNvIiwidXNlcklkIjoiZWY1YzNiZTMtYWQ0ZC00ZTBmLWFjZTctOTcwNTY5MGM4MjZlIn0.ROwm0BsQJvoHOLKcBamPazgDV3GGp6dK0efAOvaxipA"
        
        # Tokens for authenticated sessions
        self.sp1_token = None
        self.sp2_token = None
        
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
                logger.error(f"❌ Parlay creation FAILED: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Parlay creation ERROR: {str(e)}")
            return None

    def provide_sp_offer(self, parlay_id: str, sp_token: str, odds: int, max_risk: int, sp_name: str) -> bool:
        """Service Provider provides offer"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": odds,
                    "max_risk": max_risk,
                    "valid_until": int((time.time() + 50) * 1_000_000_000),  # 50 seconds
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
                logger.info(f"✅ {sp_name} offer sent successfully")
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
            
            if response.status_code == 200:
                logger.info("✅ User bet confirmed successfully")
                return True
            else:
                logger.error(f"❌ User bet confirmation FAILED: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ User bet confirmation ERROR: {str(e)}")
            return False

    def sp_acknowledge_confirmation(self, sp_token: str, parlay_id: str, stake: int, sp_name: str) -> bool:
        """SP acknowledges the confirmation"""
        # First get SP orders to find the order UUID
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
            for order in orders:
                if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
                    order_uuid = order["order_uuid"]
                    break
            
            if not order_uuid:
                logger.error(f"❌ {sp_name} order UUID not found for parlay {parlay_id}")
                return False
            
            logger.info(f"📋 Found {sp_name} order UUID: {order_uuid}")
            
            # Acknowledge the confirmation with CORRECTED probability and max_risk calculation
            confirm_url = f"{self.base_url}/parlay/sp/orders/confirmations"
            
            # Calculate proper max_risk based on confirmed_stake and odds
            # For our test scenario, we're using odds=800, so decimal_odds = 9.0
            decimal_odds = 9.0  # (800 + 100) / 100
            max_risk_dollars = stake * decimal_odds
            max_risk_cents = int(max_risk_dollars * 100)
            
            # Calculate CORRECT probabilities from odds (this was the missing piece!)
            odds = 800  # Our test scenario odds
            probability = 100 / (odds + 100)  # For positive odds: 100/(800+100) = 0.1111
            probability_rounded = round(probability, 10)  # Round to 10 decimal places
            
            logger.info(f"📋 {sp_name} CORRECTED calculations:")
            logger.info(f"   confirmed_stake: ${stake:.2f}")
            logger.info(f"   odds: +{odds}")
            logger.info(f"   decimal_odds: {decimal_odds}")
            logger.info(f"   max_risk: ${stake:.2f} × {decimal_odds} = ${max_risk_dollars:.2f}")
            logger.info(f"   max_risk (cents): {max_risk_cents}")
            logger.info(f"   probability (calculated): {probability_rounded:.10f} (was 0.5 - WRONG!)")
            
            payload = {
                "action": "accept",
                "confirmed_stake": stake,
                "price_probability": [
                    {
                        "lines": [
                            {
                                "line_id": line["lineId"],
                                "probability": probability_rounded  # CORRECTED: Use calculated probability
                            }
                            for line in self.market_lines
                        ],
                        "max_risk": max_risk_cents,  # CORRECTED: Use calculated max_risk
                        "vig": 0.1
                    }
                ],
                "signature": f"test_signature_{sp_name.lower()}"
            }
            
            response = requests.post(confirm_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"✅ {sp_name} confirmation acknowledged successfully")
                return True
            else:
                logger.error(f"❌ {sp_name} acknowledgment FAILED: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ {sp_name} acknowledgment ERROR: {str(e)}")
            return False

    def get_sp_orders_status(self, sp_token: str, parlay_id: str, sp_name: str) -> Optional[str]:
        """Get SP order status for verification"""
        url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                orders = response.json()["data"]["orders"]
                for order in orders:
                    if order["p_id"] == parlay_id:
                        return order["status"]
                return None
            else:
                logger.error(f"❌ {sp_name} get orders FAILED: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ {sp_name} get orders ERROR: {str(e)}")
            return None

    def run_test(self) -> bool:
        """Execute Test Scenario 1"""
        logger.info("🧪 STARTING TEST SCENARIO 1: Best Odds Tier - All Accept Success")
        logger.info("="*80)
        
        # Step 1: Authenticate SPs
        logger.info("🔐 STEP 1: Authenticating Service Providers")
        self.sp1_token = self.authenticate_sp(self.sp1_credentials, "SP1")
        self.sp2_token = self.authenticate_sp(self.sp2_credentials, "SP2")
        
        if not self.sp1_token or not self.sp2_token:
            logger.error("❌ SP Authentication failed")
            return False
        
        # Step 2: Create parlay request
        logger.info("\n📋 STEP 2: Creating Parlay Request")
        parlay_id = self.create_parlay_request()
        if not parlay_id:
            logger.error("❌ Parlay creation failed")
            return False
        
        # Step 3: SPs provide offers (same best odds)
        logger.info("\n💰 STEP 3: SPs Providing Offers")
        logger.info("📤 SP1 sending offer: odds=800, max_risk=$100")
        sp1_offer = self.provide_sp_offer(parlay_id, self.sp1_token, 800, 100, "SP1")
        
        logger.info("📤 SP2 sending offer: odds=800, max_risk=$150")  
        sp2_offer = self.provide_sp_offer(parlay_id, self.sp2_token, 800, 150, "SP2")
        
        if not sp1_offer or not sp2_offer:
            logger.error("❌ SP offers failed")
            return False
        
        # Step 4: User confirms bet
        logger.info("\n🎯 STEP 4: User Confirming Bet")
        logger.info("📤 User confirming bet: odds=800, stake=$200")
        user_confirm = self.user_confirm_bet(parlay_id, 800, 200)
        if not user_confirm:
            logger.error("❌ User confirmation failed")
            return False
        
        # Step 5: SPs acknowledge confirmations
        logger.info("\n✅ STEP 5: SPs Acknowledging Confirmations")
        logger.info("📤 SP1 acknowledging confirmation with stake=$100")
        sp1_ack = self.sp_acknowledge_confirmation(self.sp1_token, parlay_id, 100, "SP1")
        
        logger.info("📤 SP2 acknowledging confirmation with stake=$100")
        sp2_ack = self.sp_acknowledge_confirmation(self.sp2_token, parlay_id, 100, "SP2")
        
        if not sp1_ack or not sp2_ack:
            logger.error("❌ SP acknowledgments failed")
            return False
        
        # Step 6: Verify final status
        logger.info("\n🔍 STEP 6: Verifying Final Status")
        time.sleep(2)  # Allow processing time
        
        sp1_status = self.get_sp_orders_status(self.sp1_token, parlay_id, "SP1")
        sp2_status = self.get_sp_orders_status(self.sp2_token, parlay_id, "SP2")
        
        logger.info(f"📊 SP1 Final Status: {sp1_status}")
        logger.info(f"📊 SP2 Final Status: {sp2_status}")
        
        # Validation
        success = (sp1_status == "finalized" and sp2_status == "finalized")
        
        if success:
            logger.info("✅ TEST SCENARIO 1 PASSED: Both SPs successfully processed orders")
        else:
            logger.error("❌ TEST SCENARIO 1 FAILED: Orders not properly finalized")
        
        return success

if __name__ == "__main__":
    test = TestScenario1()
    result = test.run_test()
    exit(0 if result else 1)
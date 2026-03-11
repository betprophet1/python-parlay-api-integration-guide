#!/usr/bin/env python3
"""
🔍 BUG ANALYSIS SCRIPT

Investigates the specific API responses and behaviors to understand:
1. Why expired odds are being accepted
2. SP rejection behavior patterns  
3. Status propagation timing
4. Response payload analysis
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BugAnalysis:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        
        # Working SP Credentials
        self.sp1_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
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
    
    def authenticate_sp(self, credentials: Dict[str, str]) -> Optional[str]:
        """Authenticate Service Provider"""
        url = f"{self.base_url}/partner/auth/login"
        
        try:
            response = requests.post(url, json=credentials)
            if response.status_code == 200:
                return response.json()["data"]["access_token"]
            return None
        except Exception as e:
            logger.error(f"❌ SP Authentication ERROR: {str(e)}")
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
                return response.json()["data"]["parlayId"]
            return None
        except Exception as e:
            logger.error(f"❌ Parlay creation ERROR: {str(e)}")
            return None
    
    def provide_sp_offer_with_analysis(self, parlay_id: str, sp_token: str, 
                                     validity_seconds: int = 6) -> Dict:
        """Provide SP offer and return full response analysis"""
        url = f"{self.base_url}/parlay/sp/orders/offers"
        
        current_time = time.time()
        valid_until = int((current_time + validity_seconds) * 1_000_000_000)
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": 800,
                    "max_risk": 100,
                    "valid_until": valid_until,
                    "estimated_prices": [
                        {
                            "line_id": line["lineId"],
                            "odds": 800
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
            
            analysis = {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "current_time": current_time,
                "valid_until_timestamp": valid_until,
                "validity_seconds": validity_seconds,
                "response_data": response.json() if response.status_code == 200 else response.text,
                "calculated_expiry": current_time + validity_seconds
            }
            
            logger.info(f"📊 SP Offer Analysis:")
            logger.info(f"   Current time: {current_time}")
            logger.info(f"   Valid until: {valid_until} (timestamp)")
            logger.info(f"   Expires at: {current_time + validity_seconds}")
            logger.info(f"   Status: {response.status_code}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ SP offer ERROR: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def user_confirm_with_analysis(self, parlay_id: str, delay_seconds: float = 0) -> Dict:
        """User confirms bet with timing analysis"""
        if delay_seconds > 0:
            logger.info(f"⏰ Waiting {delay_seconds}s before user confirmation...")
            time.sleep(delay_seconds)
        
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        payload = {
            "parlayId": parlay_id,
            "odds": 800,
            "stake": 100
        }
        headers = {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json"
        }
        
        confirmation_time = time.time()
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            analysis = {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "confirmation_time": confirmation_time,
                "response_data": response.json() if response.status_code == 200 else response.text,
                "delay_used": delay_seconds
            }
            
            logger.info(f"📊 User Confirmation Analysis:")
            logger.info(f"   Confirmation time: {confirmation_time}")
            logger.info(f"   Delay used: {delay_seconds}s")
            logger.info(f"   Status: {response.status_code}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ User confirmation ERROR: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_sp_orders_detailed(self, sp_token: str, parlay_id: str) -> Dict:
        """Get SP orders with detailed analysis"""
        url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            current_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("data", {}).get("orders", [])
                matching_orders = [o for o in orders if o.get("p_id") == parlay_id]
                
                analysis = {
                    "success": True,
                    "current_time": current_time,
                    "total_orders": len(orders),
                    "matching_orders": len(matching_orders),
                    "orders_data": matching_orders,
                    "all_orders": orders
                }
                
                logger.info(f"📊 SP Orders Analysis:")
                logger.info(f"   Current time: {current_time}")
                logger.info(f"   Total orders: {len(orders)}")
                logger.info(f"   Matching orders: {len(matching_orders)}")
                
                for i, order in enumerate(matching_orders):
                    logger.info(f"   Order {i+1}:")
                    logger.info(f"     Status: {order.get('status')}")
                    logger.info(f"     Order UUID: {order.get('order_uuid')}")
                    logger.info(f"     Valid Until: {order.get('valid_until')}")
                    if order.get('valid_until'):
                        # Convert nanoseconds to seconds
                        valid_until_seconds = order.get('valid_until') / 1_000_000_000
                        is_expired = current_time > valid_until_seconds
                        logger.info(f"     Expired: {is_expired} (current: {current_time}, expires: {valid_until_seconds})")
                
                return analysis
            else:
                return {"success": False, "status_code": response.status_code}
                
        except Exception as e:
            logger.error(f"❌ SP orders ERROR: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def sp_acknowledge_with_analysis(self, sp_token: str, parlay_id: str, 
                                   delay_seconds: float = 0) -> Dict:
        """SP acknowledges with detailed timing analysis"""
        if delay_seconds > 0:
            logger.info(f"⏰ Waiting {delay_seconds}s before SP acknowledgment...")
            time.sleep(delay_seconds)
        
        # First get orders to understand current state
        orders_analysis = self.get_sp_orders_detailed(sp_token, parlay_id)
        if not orders_analysis["success"] or not orders_analysis["matching_orders"]:
            return {"success": False, "reason": "No matching orders found"}
        
        # Find the order to acknowledge
        matching_orders = orders_analysis["orders_data"]
        order_uuid = None
        for order in matching_orders:
            if order["status"] == "sent_confirmation":
                order_uuid = order["order_uuid"]
                break
        
        if not order_uuid:
            return {"success": False, "reason": "No order with sent_confirmation status"}
        
        # Attempt acknowledgment
        url = f"{self.base_url}/parlay/sp/orders/confirmations"
        payload = {
            "action": "accept",
            "confirmed_stake": 100,
            "price_probability": [
                {
                    "lines": [
                        {
                            "line_id": line["lineId"],
                            "probability": 0.1111111111
                        }
                        for line in self.market_lines
                    ],
                    "max_risk": 9000,
                    "vig": 0.1
                }
            ],
            "signature": "test_signature_analysis"
        }
        
        headers = {"Authorization": f"Bearer {sp_token}"}
        acknowledgment_time = time.time()
        
        try:
            response = requests.post(url, json=payload, headers=headers, 
                                   params={"order_uuid": order_uuid})
            
            analysis = {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "acknowledgment_time": acknowledgment_time,
                "delay_used": delay_seconds,
                "order_uuid": order_uuid,
                "orders_before_ack": orders_analysis,
                "response_data": response.json() if response.status_code == 200 else response.text
            }
            
            logger.info(f"📊 SP Acknowledgment Analysis:")
            logger.info(f"   Acknowledgment time: {acknowledgment_time}")
            logger.info(f"   Delay used: {delay_seconds}s")
            logger.info(f"   Order UUID: {order_uuid}")
            logger.info(f"   Status: {response.status_code}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ SP acknowledgment ERROR: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def analyze_expired_odds_bug(self):
        """Deep analysis of the expired odds bug"""
        logger.info("\n🔍 ANALYZING EXPIRED ODDS BUG")
        logger.info("="*80)
        
        # Get SP token
        sp_token = self.authenticate_sp(self.sp1_credentials)
        if not sp_token:
            logger.error("❌ Failed to get SP token")
            return
        
        # Create parlay
        parlay_id = self.create_parlay_request()
        if not parlay_id:
            logger.error("❌ Failed to create parlay")
            return
        
        logger.info(f"✅ Created parlay: {parlay_id}")
        
        # Provide SP offer with 6s validity
        offer_analysis = self.provide_sp_offer_with_analysis(parlay_id, sp_token, 6)
        if not offer_analysis["success"]:
            logger.error("❌ Failed to provide SP offer")
            return
        
        # Test 1: User confirmation after expiry
        logger.info("\n🧪 TEST 1: User confirmation after expiry")
        user_analysis = self.user_confirm_with_analysis(parlay_id, delay_seconds=8)
        
        if user_analysis["success"]:
            logger.error("🐛 BUG CONFIRMED: User confirmation succeeded after expiry")
            logger.error(f"   Offer expired at: {offer_analysis['calculated_expiry']}")
            logger.error(f"   User confirmed at: {user_analysis['confirmation_time']}")
            logger.error(f"   Difference: {user_analysis['confirmation_time'] - offer_analysis['calculated_expiry']:.2f}s")
        else:
            logger.info("✅ User confirmation properly rejected after expiry")
        
        # If user confirmation succeeded, test SP acknowledgment
        if user_analysis["success"]:
            time.sleep(2)  # Give system time to process
            
            logger.info("\n🧪 TEST 2: SP acknowledgment of expired odds")
            ack_analysis = self.sp_acknowledge_with_analysis(sp_token, parlay_id, delay_seconds=2)
            
            if ack_analysis["success"]:
                logger.error("🐛 BUG CONFIRMED: SP acknowledgment succeeded for expired odds")
                logger.error(f"   Original expiry: {offer_analysis['calculated_expiry']}")
                logger.error(f"   SP acknowledged at: {ack_analysis['acknowledgment_time']}")
                logger.error(f"   Difference: {ack_analysis['acknowledgment_time'] - offer_analysis['calculated_expiry']:.2f}s")
            else:
                logger.info("✅ SP acknowledgment properly rejected for expired odds")
        
        logger.info("\n📊 FINAL BUG ANALYSIS SUMMARY:")
        logger.info(f"   User confirmation after expiry: {'BUG' if user_analysis['success'] else 'OK'}")
        if user_analysis["success"]:
            if 'ack_analysis' in locals():
                logger.info(f"   SP acknowledgment of expired: {'BUG' if ack_analysis['success'] else 'OK'}")
        
        return {
            "parlay_id": parlay_id,
            "offer_analysis": offer_analysis,
            "user_analysis": user_analysis,
            "sp_analysis": ack_analysis if 'ack_analysis' in locals() else None
        }

def main():
    """Run bug analysis"""
    analyzer = BugAnalysis()
    results = analyzer.analyze_expired_odds_bug()
    return results

if __name__ == "__main__":
    main()
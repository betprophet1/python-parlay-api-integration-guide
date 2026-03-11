#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC: SP WORKFLOW UNDERSTANDING

Simple test to understand the SP order creation workflow and timing.
"""

import requests
import json
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SPWorkflowDiagnostic:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.user_token = self.get_user_token()
        
        self.sp1_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        
        self.market_lines = [
            {
                "line": -4.5,
                "lineId": "04f2da44cbba365fd807c2bf6c5f09ab",
                "marketId": 223,
                "outcomeId": 1714,
                "sportEventId": 19191
            },
            {
                "line": -1.5,
                "lineId": "b6cb5cf18a0148dfac0ae113e3ee6852",
                "marketId": 223,
                "outcomeId": 1714,
                "sportEventId": 19192
            }
        ]

    def get_user_token(self):
        """Get fresh user token"""
        url = f"{self.base_url}/api/v1/auth/login"
        payload = {
            "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
            "email": "lam.tran+usr004@betprophet.co",
            "password": "Kh0ngbiet1"
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("accessToken")
        return None

    def authenticate_sp(self):
        """Authenticate SP"""
        url = f"{self.base_url}/partner/auth/login"
        
        try:
            response = requests.post(url, json=self.sp1_credentials)
            if response.status_code == 200:
                token = response.json()["data"]["access_token"]
                logger.info("✅ SP1 Authentication SUCCESS")
                return token
            else:
                logger.error(f"❌ SP1 Authentication FAILED: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ SP1 Authentication ERROR: {str(e)}")
            return None

    def create_parlay(self):
        """Create parlay"""
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
            else:
                logger.error(f"❌ Parlay creation FAILED: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ Parlay creation ERROR: {str(e)}")
            return None

    def check_all_sp_orders(self, sp_token, step_name):
        """Check all SP orders at this step"""
        logger.info(f"\n🔍 CHECKING ALL SP ORDERS - {step_name}")
        logger.info("-" * 60)
        
        url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {sp_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                orders = data.get("data", {}).get("orders", [])
                
                logger.info(f"📊 Total SP orders: {len(orders)}")
                
                if orders:
                    # Show recent orders
                    recent_orders = sorted(orders, key=lambda x: x.get('created_at', 0), reverse=True)[:3]
                    logger.info("📋 Recent orders:")
                    
                    for i, order in enumerate(recent_orders, 1):
                        logger.info(f"   {i}. ID: {order.get('p_id', 'N/A')}")
                        logger.info(f"      Status: {order.get('status', 'N/A')}")
                        logger.info(f"      UUID: {order.get('order_uuid', 'N/A')}")
                        logger.info(f"      Created: {order.get('created_at', 'N/A')}")
                        logger.info(f"      Updated: {order.get('updated_at', 'N/A')}")
                
                return orders
            else:
                logger.error(f"❌ Failed to get SP orders: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ Error getting SP orders: {str(e)}")
            return []

    def provide_sp_offer(self, parlay_id, sp_token):
        """SP provides offer"""
        logger.info(f"\n📤 SP PROVIDING OFFER for parlay {parlay_id}")
        
        url = f"{self.base_url}/parlay/sp/orders/offers"
        
        payload = {
            "parlay_id": parlay_id,
            "offers": [
                {
                    "odds": 800,
                    "max_risk": 100,
                    "valid_until": int((time.time() + 50) * 1_000_000_000),
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
        
        headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
        
        logger.info(f"📋 Offer payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            logger.info(f"📥 Offer response: Status {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(f"📋 Response data: {json.dumps(response_data, indent=2)}")
                except:
                    logger.info(f"📋 Raw response: {response.text}")
                logger.info("✅ SP offer sent successfully")
                return True
            else:
                logger.error(f"❌ SP offer FAILED: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ SP offer ERROR: {str(e)}")
            return False

    def user_confirm_bet(self, parlay_id):
        """User confirms bet"""
        logger.info(f"\n🎯 USER CONFIRMING BET for parlay {parlay_id}")
        
        url = f"{self.base_url}/parlay/api/v1/user/confirm"
        payload = {
            "parlayId": parlay_id,
            "odds": 800,
            "stake": 10000  # $100 in cents
        }
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        logger.info(f"📋 Confirm payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            logger.info(f"📥 Confirm response: Status {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.info(f"📋 Response data: {json.dumps(response_data, indent=2)}")
                except:
                    logger.info(f"📋 Raw response: {response.text}")
                logger.info("✅ User confirmed bet successfully")
                return True
            else:
                logger.error(f"❌ User confirmation FAILED: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ User confirmation ERROR: {str(e)}")
            return False

    def run_diagnostic(self):
        """Run comprehensive diagnostic"""
        logger.info("🔍 STARTING SP WORKFLOW DIAGNOSTIC")
        logger.info("=" * 80)
        
        # Step 1: Authenticate SP
        sp_token = self.authenticate_sp()
        if not sp_token:
            return
        
        # Step 2: Check initial SP orders
        self.check_all_sp_orders(sp_token, "INITIAL STATE")
        
        # Step 3: Create parlay
        parlay_id = self.create_parlay()
        if not parlay_id:
            return
        
        # Step 4: Check SP orders after parlay creation
        time.sleep(2)
        self.check_all_sp_orders(sp_token, "AFTER PARLAY CREATION")
        
        # Step 5: SP provides offer
        if not self.provide_sp_offer(parlay_id, sp_token):
            return
        
        # Step 6: Check SP orders after offer
        time.sleep(2)
        orders_after_offer = self.check_all_sp_orders(sp_token, "AFTER SP OFFER")
        
        # Step 7: User confirms bet
        if not self.user_confirm_bet(parlay_id):
            return
        
        # Step 8: Check SP orders after user confirmation
        time.sleep(3)
        orders_after_confirm = self.check_all_sp_orders(sp_token, "AFTER USER CONFIRMATION")
        
        # Step 9: Look for our specific parlay
        logger.info(f"\n🎯 SEARCHING FOR OUR PARLAY: {parlay_id}")
        logger.info("-" * 60)
        
        matching_orders = [order for order in orders_after_confirm if order.get("p_id") == parlay_id]
        
        if matching_orders:
            logger.info(f"✅ Found {len(matching_orders)} matching orders!")
            for i, order in enumerate(matching_orders, 1):
                logger.info(f"   Order {i}:")
                logger.info(f"      Status: {order.get('status')}")
                logger.info(f"      UUID: {order.get('order_uuid')}")
                logger.info(f"      Created: {order.get('created_at')}")
                logger.info(f"      Updated: {order.get('updated_at')}")
        else:
            logger.error(f"❌ No orders found for parlay {parlay_id}")
            
            # Check if the parlay ID format has changed
            logger.info("🔍 Checking if any orders have similar IDs...")
            for order in orders_after_confirm[:5]:  # Check first 5 orders
                order_id = order.get("p_id", "")
                if parlay_id[:-10] in order_id or order_id[:-10] in parlay_id:
                    logger.info(f"   Similar ID found: {order_id} (status: {order.get('status')})")
        
        logger.info("\n🏁 DIAGNOSTIC COMPLETE")

if __name__ == "__main__":
    diagnostic = SPWorkflowDiagnostic()
    diagnostic.run_diagnostic()
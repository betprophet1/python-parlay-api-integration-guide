#!/usr/bin/env python3
"""
SP Order Status Checker - Separate utility for checking SP order status
This utility allows you to check the status of SP orders without cluttering the main test runs.
"""

import requests
import json
from datetime import datetime
import sys

class SPOrderChecker:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.mm1_credentials = {
            "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
            "secret_key": "67344329e054349f07e7a29249dcadeb"
        }
        self.mm2_credentials = {
            "access_key": "ec45827afa933f97ec19e674c0fa39c6", 
            "secret_key": "442df8e9fe96e4f7e744b2d3cac5cd51"
        }
        self.tokens = {}
        
    def authenticate_sp(self, sp_name: str, credentials: dict) -> bool:
        """Authenticate SP and store token"""
        url = f"{self.base_url}/partner/auth/login"
        response = requests.post(url, json=credentials)
        
        if response.status_code == 200:
            data = response.json()
            self.tokens[sp_name] = data["data"]["access_token"]
            print(f"✅ {sp_name} Authentication SUCCESS")
            return True
        else:
            print(f"❌ {sp_name} Authentication FAILED: {response.status_code}")
            return False
            
    def get_sp_orders(self, sp_name: str, limit: int = 10) -> dict:
        """Get SP orders with detailed information"""
        if sp_name not in self.tokens:
            print(f"❌ {sp_name} not authenticated")
            return {"success": False}
            
        url = f"{self.base_url}/parlay/sp/orders"
        headers = {"Authorization": f"Bearer {self.tokens[sp_name]}"}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            try:
                data = response.json()
                return {"success": True, "data": data}
            except:
                return {"success": False, "error": "Failed to parse response"}
        else:
            return {"success": False, "status_code": response.status_code, "error": response.text}
            
    def display_orders(self, sp_name: str, orders_data: dict, show_details: bool = False):
        """Display orders in a readable format"""
        print(f"\n🔍 {sp_name} ORDERS")
        print("="*50)
        
        if not orders_data.get("success"):
            print(f"❌ Failed to get orders: {orders_data.get('error', 'Unknown error')}")
            return
            
        data = orders_data.get("data", {})
        if 'data' not in data or 'orders' not in data['data']:
            print("❌ No orders found")
            return
            
        orders = data['data']['orders']
        print(f"📊 Found {len(orders)} total orders")
        
        # Group orders by status
        status_groups = {}
        for order in orders:
            status = order.get('status', 'unknown')
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append(order)
            
        # Display summary
        print(f"\n📈 Status Summary:")
        for status, order_list in status_groups.items():
            print(f"   {status}: {len(order_list)} orders")
            
        # Display detailed orders if requested
        if show_details:
            print(f"\n📋 Detailed Orders (showing first 10):")
            for i, order in enumerate(orders[:10]):
                print(f"\n   Order {i+1}:")
                print(f"     UUID: {order.get('order_uuid', 'N/A')}")
                print(f"     Parlay ID: {order.get('p_id', 'N/A')[:20]}...")
                print(f"     Status: {order.get('status', 'N/A')}")
                print(f"     Confirmed Odds: {order.get('confirmed_odds', 'N/A')}")
                print(f"     Confirmed Stake: {order.get('confirmed_stake', 'N/A')}")
                print(f"     Updated At: {datetime.fromtimestamp(order.get('updated_at', 0)).isoformat() if order.get('updated_at') else 'N/A'}")
                
                if order.get('legs'):
                    print(f"     Legs: {len(order.get('legs', []))} markets")
                    
    def find_orders_by_parlay_id(self, sp_name: str, parlay_id: str):
        """Find specific orders by parlay ID"""
        orders_data = self.get_sp_orders(sp_name)
        if not orders_data.get("success"):
            return []
            
        data = orders_data.get("data", {})
        if 'data' not in data or 'orders' not in data['data']:
            return []
            
        matching_orders = []
        for order in data['data']['orders']:
            if order.get('p_id') == parlay_id:
                matching_orders.append(order)
                
        return matching_orders
        
    def check_confirmable_orders(self, sp_name: str):
        """Find orders that can be confirmed (in final status)"""
        orders_data = self.get_sp_orders(sp_name)
        if not orders_data.get("success"):
            return []
            
        data = orders_data.get("data", {})
        if 'data' not in data or 'orders' not in data['data']:
            return []
            
        confirmable_statuses = ['rejected', 'failed', 'expired', 'settled']
        confirmable_orders = []
        
        for order in data['data']['orders']:
            if order.get('status') in confirmable_statuses:
                confirmable_orders.append(order)
                
        print(f"\n🎯 {sp_name} Confirmable Orders:")
        print(f"   Found {len(confirmable_orders)} orders ready for confirmation")
        
        for i, order in enumerate(confirmable_orders[:5]):  # Show first 5
            print(f"     {i+1}. UUID: {order.get('order_uuid', 'N/A')[:20]}...")
            print(f"        Status: {order.get('status', 'N/A')}")
            print(f"        Parlay: {order.get('p_id', 'N/A')[:20]}...")
            
        return confirmable_orders
        
    def run_check(self, show_details: bool = False, parlay_id: str = None):
        """Run the order check for both SPs"""
        print("🚀 SP ORDER STATUS CHECKER")
        print("="*40)
        print(f"🕐 Check Time: {datetime.now().isoformat()}")
        
        # Authenticate both SPs
        sp1_auth = self.authenticate_sp("SP1 (MM1)", self.mm1_credentials)
        sp2_auth = self.authenticate_sp("SP2 (MM2)", self.mm2_credentials)
        
        if not (sp1_auth and sp2_auth):
            print("❌ Authentication failed for one or more SPs")
            return False
            
        # Check orders for both SPs
        for sp_name in ["SP1 (MM1)", "SP2 (MM2)"]:
            if parlay_id:
                print(f"\n🔍 Searching for orders with Parlay ID: {parlay_id[:20]}...")
                matching_orders = self.find_orders_by_parlay_id(sp_name, parlay_id)
                if matching_orders:
                    print(f"✅ Found {len(matching_orders)} matching orders for {sp_name}")
                    for order in matching_orders:
                        print(f"   UUID: {order.get('order_uuid', 'N/A')}")
                        print(f"   Status: {order.get('status', 'N/A')}")
                else:
                    print(f"❌ No matching orders found for {sp_name}")
            else:
                orders_data = self.get_sp_orders(sp_name)
                self.display_orders(sp_name, orders_data, show_details)
                
        # Show confirmable orders
        print(f"\n🎯 CONFIRMABLE ORDERS SUMMARY")
        print("="*40)
        self.check_confirmable_orders("SP1 (MM1)")
        self.check_confirmable_orders("SP2 (MM2)")
        
        return True

def main():
    """Main function with command line options"""
    checker = SPOrderChecker()
    
    # Parse command line arguments
    show_details = "--details" in sys.argv or "-d" in sys.argv
    parlay_id = None
    
    # Look for --parlay-id argument
    for i, arg in enumerate(sys.argv):
        if arg.startswith("--parlay-id="):
            parlay_id = arg.split("=", 1)[1]
        elif arg == "--parlay-id" and i + 1 < len(sys.argv):
            parlay_id = sys.argv[i + 1]
            
    result = checker.run_check(show_details, parlay_id)
    
    if not result:
        sys.exit(1)
        
    print(f"\n🏁 Check completed successfully")
    print(f"\nUsage:")
    print(f"  python sp_order_checker.py                    # Basic check")
    print(f"  python sp_order_checker.py --details          # Detailed view")
    print(f"  python sp_order_checker.py --parlay-id=<id>   # Find specific parlay")

if __name__ == "__main__":
    main()
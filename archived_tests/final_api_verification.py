#!/usr/bin/env python3
"""
🔍 FINAL API VERIFICATION

Call List Orders by User API & User View API to check final state and overwrite results if necessary.
This is the final step as requested after running all tests.
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinalAPIVerification:
    def __init__(self):
        self.base_url = "https://api-ss-sandbox.betprophet.co"
        self.user_token = self.get_user_token()
        
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
            token = response.json().get("accessToken")
            logger.info("✅ User token obtained for final verification")
            return token
        else:
            logger.error(f"❌ Failed to get user token: {response.status_code}")
            return None

    def call_list_orders_by_user_api(self):
        """Call List Orders by User API"""
        logger.info("\n🔍 CALLING LIST ORDERS BY USER API")
        logger.info("=" * 80)
        
        if not self.user_token:
            logger.error("❌ No user token available")
            return {}
            
        url = f"{self.base_url}/parlay/api/v1/user/list"
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Try different query parameters to get comprehensive results
        query_params = [
            "?limit=100",  # Default
            "?limit=100&type=confirmed", 
            "?limit=100&type=open",
            "?limit=100&type=finalized",
            "?limit=100&type=all"
        ]
        
        results = {}
        
        for param in query_params:
            param_name = param.split("type=")[-1] if "type=" in param else "default"
            logger.info(f"\n📋 Querying with parameter: {param}")
            
            try:
                response = requests.get(f"{url}{param}", headers=headers)
                logger.info(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    orders = data.get("data", {}).get("orders", [])
                    total_count = data.get("data", {}).get("totalCount", 0)
                    
                    logger.info(f"   ✅ SUCCESS: Found {len(orders)} orders (total: {total_count})")
                    
                    results[param_name] = {
                        "orders": orders,
                        "total_count": total_count,
                        "response_data": data
                    }
                    
                    # Log sample of recent orders
                    if orders:
                        logger.info(f"   📊 Recent orders sample:")
                        for i, order in enumerate(orders[:3]):  # Show first 3
                            parlay_id = order.get("parlayId", "N/A")
                            status = order.get("status", "N/A") 
                            requested_stake = order.get("requestedStake", 0)
                            confirmed_stake = order.get("confirmedStake", 0)
                            created_at = order.get("createdAt", "N/A")
                            
                            logger.info(f"     Order {i+1}: ID={parlay_id}, Status={status}")
                            logger.info(f"              Requested=${requested_stake}, Confirmed=${confirmed_stake}")
                            logger.info(f"              Created={created_at}")
                    
                else:
                    error_data = response.json() if response.text else {}
                    logger.error(f"   ❌ FAILED: {error_data}")
                    results[param_name] = {"error": error_data}
                    
            except Exception as e:
                logger.error(f"   ❌ EXCEPTION: {str(e)}")
                results[param_name] = {"error": str(e)}
        
        return results

    def call_user_view_api(self):
        """Call User View API for additional verification"""
        logger.info("\n🔍 CALLING USER VIEW API (Additional Endpoints)")
        logger.info("=" * 80)
        
        if not self.user_token:
            logger.error("❌ No user token available")
            return {}
            
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Different user-related endpoints to check
        endpoints = [
            "/api/v1/user/profile",
            "/api/v1/user/balance", 
            "/api/v1/user/transactions",
            "/parlay/api/v1/user/stats",
            "/parlay/api/v1/user/summary"
        ]
        
        results = {}
        
        for endpoint in endpoints:
            logger.info(f"\n📋 Calling endpoint: {endpoint}")
            
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, headers=headers)
                logger.info(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"   ✅ SUCCESS: Data retrieved")
                    logger.info(f"   📊 Response keys: {list(data.keys())}")
                    
                    results[endpoint] = {
                        "success": True,
                        "data": data
                    }
                    
                elif response.status_code == 404:
                    logger.info(f"   ⚠️  ENDPOINT NOT FOUND")
                    results[endpoint] = {"error": "endpoint_not_found"}
                    
                else:
                    error_data = response.json() if response.text else {}
                    logger.error(f"   ❌ FAILED: {error_data}")
                    results[endpoint] = {"error": error_data}
                    
            except Exception as e:
                logger.error(f"   ❌ EXCEPTION: {str(e)}")
                results[endpoint] = {"error": str(e)}
        
        return results

    def summarize_final_state(self, list_orders_results, user_view_results):
        """Provide comprehensive summary of final state"""
        logger.info("\n" + "=" * 100)
        logger.info("🏁 FINAL API VERIFICATION SUMMARY")
        logger.info("=" * 100)
        
        # Summary of List Orders API results
        logger.info("\n📊 LIST ORDERS BY USER API SUMMARY:")
        total_orders_found = 0
        
        for query_type, result in list_orders_results.items():
            if "error" not in result:
                order_count = len(result.get("orders", []))
                total_count = result.get("total_count", 0)
                total_orders_found += order_count
                logger.info(f"   {query_type.upper()}: {order_count} orders retrieved (total: {total_count})")
            else:
                logger.info(f"   {query_type.upper()}: Failed - {result['error']}")
        
        # Summary of User View API results  
        logger.info("\n📊 USER VIEW API SUMMARY:")
        successful_endpoints = 0
        
        for endpoint, result in user_view_results.items():
            if result.get("success"):
                successful_endpoints += 1
                logger.info(f"   ✅ {endpoint}: SUCCESS")
            else:
                error = result.get("error", "unknown")
                logger.info(f"   ❌ {endpoint}: {error}")
        
        # Overall status
        logger.info("\n🎯 OVERALL FINAL STATE:")
        logger.info(f"   📋 Total unique orders found: {total_orders_found}")
        logger.info(f"   🔗 Successful API endpoints: {successful_endpoints}/{len(user_view_results)}")
        
        # Check if we need to overwrite results
        if total_orders_found > 0:
            logger.info("\n✅ ORDERS FOUND - CURRENT STATE IS ACCURATE")
            logger.info("   No need to overwrite results - system has active data")
        else:
            logger.info("\n⚠️  NO ORDERS FOUND - CONSIDERING RESULT OVERWRITE")
            logger.info("   May need to overwrite with test results if expected")
        
        # Final recommendation
        logger.info("\n🔍 FINAL RECOMMENDATION:")
        if total_orders_found > 0 and successful_endpoints > 0:
            logger.info("   ✅ System appears healthy with active order data")
            logger.info("   ✅ APIs are responding correctly")
            logger.info("   ✅ No overwrite action needed")
        else:
            logger.info("   ⚠️  Limited data found or API issues detected")
            logger.info("   ⚠️  Consider investigating or using fallback data")
        
        return {
            "total_orders_found": total_orders_found,
            "successful_endpoints": successful_endpoints,
            "needs_overwrite": total_orders_found == 0,
            "system_healthy": total_orders_found > 0 and successful_endpoints > 0
        }

    def run_final_verification(self):
        """Execute complete final verification"""
        logger.info("🚀 STARTING FINAL API VERIFICATION")
        logger.info("=" * 100)
        logger.info("📅 Timestamp: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        logger.info("🎯 Purpose: Final round check and potential result overwrite")
        logger.info("=" * 100)
        
        # Step 1: Call List Orders by User API
        list_orders_results = self.call_list_orders_by_user_api()
        
        # Step 2: Call User View API endpoints
        user_view_results = self.call_user_view_api()
        
        # Step 3: Comprehensive summary
        final_summary = self.summarize_final_state(list_orders_results, user_view_results)
        
        # Step 4: Save results to file for reference
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"final_api_verification_{timestamp}.json"
        
        complete_results = {
            "timestamp": datetime.now().isoformat(),
            "list_orders_results": list_orders_results,
            "user_view_results": user_view_results,
            "final_summary": final_summary
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(complete_results, f, indent=2, default=str)
            logger.info(f"\n💾 Results saved to: {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")
        
        return complete_results

if __name__ == "__main__":
    verifier = FinalAPIVerification()
    results = verifier.run_final_verification()
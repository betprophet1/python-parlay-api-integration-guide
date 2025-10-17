#!/usr/bin/env python3
"""
🔍 FIND ACTIVE SPORT EVENTS

Finds currently active sport events and market lines that can be used for testing.
This will help us get fresh, working data for our comprehensive test suite.
"""

import requests
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_user_token():
    """Get user token"""
    url = "https://api-ss-sandbox.betprophet.co/api/v1/auth/login"
    payload = {
        "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
        "email": "lam.tran+usr004@betprophet.co",
        "password": "Kh0ngbiet1"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get("accessToken")
    return None

def find_active_events():
    """Find currently active sport events"""
    logger.info("🔍 SEARCHING FOR ACTIVE SPORT EVENTS")
    logger.info("="*80)
    
    user_token = get_user_token()
    if not user_token:
        logger.error("❌ Failed to get user token")
        return
    
    logger.info("✅ User token obtained")
    
    # This is a hypothetical endpoint - we might need to explore the API structure
    # Let's try a few common endpoints to find active events
    
    base_url = "https://api-ss-sandbox.betprophet.co"
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    # Try various endpoints that might contain active events
    endpoints_to_try = [
        "/api/v1/events",
        "/api/v1/sports/events", 
        "/api/v1/markets",
        "/parlay/api/v1/events",
        "/parlay/api/v1/sports",
        "/parlay/api/v1/markets",
        "/api/v1/sports",
        "/api/v1/events/active"
    ]
    
    for endpoint in endpoints_to_try:
        logger.info(f"\n🔍 Trying endpoint: {endpoint}")
        url = f"{base_url}{endpoint}"
        
        try:
            response = requests.get(url, headers=headers)
            logger.info(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("   ✅ Success! Found data:")
                try:
                    data = response.json()
                    logger.info(f"   Data sample: {json.dumps(data, indent=2)[:500]}...")
                    
                    # Look for sport events or market data
                    if isinstance(data, dict):
                        if "events" in data:
                            logger.info(f"   📊 Found {len(data['events'])} events")
                        if "markets" in data:
                            logger.info(f"   📊 Found {len(data['markets'])} markets")
                        if "data" in data and isinstance(data["data"], dict):
                            for key, value in data["data"].items():
                                if isinstance(value, list):
                                    logger.info(f"   📊 Found {len(value)} {key}")
                    elif isinstance(data, list):
                        logger.info(f"   📊 Found {len(data)} items")
                        
                except Exception as e:
                    logger.info(f"   Raw response: {response.text[:300]}...")
                    
            elif response.status_code == 404:
                logger.info("   ❌ Not found")
            elif response.status_code == 401:
                logger.info("   ❌ Unauthorized")
            elif response.status_code == 403:
                logger.info("   ❌ Forbidden")
            else:
                logger.info(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"   ❌ Exception: {str(e)}")
    
    logger.info("\n" + "="*80)
    logger.info("🎯 NEXT STEPS:")
    logger.info("1. If any endpoints returned data, examine the structure")
    logger.info("2. Look for active sportEventId, marketId, lineId values")
    logger.info("3. Create fresh market lines using active data")
    logger.info("4. Test parlay creation with the new data")
    
    # Let's also try to understand the error better
    logger.info("\n🔍 UNDERSTANDING THE ERROR")
    logger.info("Error: 'sport event not open'")
    logger.info("- This means the sportEventId values are expired/closed")
    logger.info("- We need sportEventId values for events that are currently open")
    logger.info("- These are typically upcoming games/matches accepting bets")

def test_simple_parlay_formats():
    """Test different parlay request formats to understand the API better"""
    logger.info("\n🧪 TESTING SIMPLE PARLAY FORMATS")
    logger.info("="*60)
    
    user_token = get_user_token()
    if not user_token:
        return
    
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    url = "https://api-ss-sandbox.betprophet.co/parlay/api/v1/user/request"
    
    # Test with minimal data to see what's required
    test_cases = [
        {
            "name": "Single market line",
            "payload": {
                "marketLines": [
                    {
                        "line": 0.5,
                        "lineId": "test-line-id",
                        "marketId": 123456,
                        "outcomeId": 1,
                        "sportEventId": 999999
                    }
                ]
            }
        }
    ]
    
    for test_case in test_cases:
        logger.info(f"\n📤 Testing: {test_case['name']}")
        logger.info(f"Payload: {json.dumps(test_case['payload'], indent=2)}")
        
        try:
            response = requests.post(url, json=test_case['payload'], headers=headers)
            logger.info(f"Status: {response.status_code}")
            
            try:
                data = response.json()
                logger.info(f"Response: {json.dumps(data, indent=2)}")
            except:
                logger.info(f"Raw response: {response.text}")
                
        except Exception as e:
            logger.error(f"Error: {str(e)}")

def main():
    """Main finder"""
    find_active_events()
    test_simple_parlay_formats()

if __name__ == "__main__":
    main()
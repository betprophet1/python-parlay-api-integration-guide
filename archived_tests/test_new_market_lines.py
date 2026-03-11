#!/usr/bin/env python3
"""
🔍 TEST NEW MARKET LINES

Tests the updated market lines data to ensure they work before running full suite.
"""

import requests
import json
import logging

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

def test_new_market_lines():
    """Test the new market lines data"""
    logger.info("🔍 TESTING NEW MARKET LINES DATA")
    logger.info("="*80)
    
    user_token = get_user_token()
    if not user_token:
        logger.error("❌ Failed to get user token")
        return False
    
    logger.info("✅ User token obtained")
    
    # NEW market lines data
    market_lines = [
        {
            "line": -7.5,
            "lineId": "a102f77a638ed82df7ce3dc924b90d08",
            "marketId": 223,
            "outcomeId": 1714,
            "sportEventId": 20022433
        },
        {
            "line": 0,
            "lineId": "1a5bf373e470b0137ea0bd4a04df7c54",
            "marketId": 219,
            "outcomeId": 4,
            "sportEventId": 20022433
        }
    ]
    
    # Test parlay creation
    url = "https://api-ss-sandbox.betprophet.co/parlay/api/v1/user/request"
    payload = {"marketLines": market_lines}
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    logger.info("📤 TESTING NEW MARKET LINES")
    logger.info(f"URL: {url}")
    logger.info(f"PAYLOAD: {json.dumps(payload, indent=2)}")
    
    response = requests.post(url, json=payload, headers=headers)
    
    logger.info(f"\n📥 PARLAY CREATION RESPONSE")
    logger.info(f"STATUS: {response.status_code}")
    logger.info(f"HEADERS: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        logger.info(f"BODY: {json.dumps(response_data, indent=2)}")
    except:
        logger.info(f"BODY (raw): {response.text}")
    
    if response.status_code == 200:
        logger.info("🎉 SUCCESS! NEW MARKET LINES DATA WORKING!")
        parlay_id = response_data.get("data", {}).get("parlayId")
        logger.info(f"✅ Parlay created: {parlay_id}")
        return True
    else:
        logger.error("❌ NEW MARKET LINES DATA FAILED")
        return False

def main():
    """Test new market lines"""
    success = test_new_market_lines()
    
    if success:
        logger.info("\n🚀 READY TO RUN COMPLETE TEST SUITE!")
        logger.info("The new market lines work - we can proceed with full testing")
    else:
        logger.info("\n⚠️ NEED TO TROUBLESHOOT MARKET LINES FIRST")
        
    return success

if __name__ == "__main__":
    main()
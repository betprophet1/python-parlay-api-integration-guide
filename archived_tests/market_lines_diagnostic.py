#!/usr/bin/env python3
"""
🔍 MARKET LINES DIAGNOSTIC

Tests the fresh market lines data to see why parlay creation is failing.
Shows full error details.
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

def test_market_lines():
    """Test the fresh market lines data"""
    logger.info("🔍 TESTING FRESH MARKET LINES DATA")
    logger.info("="*80)
    
    user_token = get_user_token()
    if not user_token:
        logger.error("❌ Failed to get user token")
        return
    
    logger.info("✅ User token obtained")
    
    # Fresh market lines data
    market_lines = [
        {
            "line": 0.5,
            "lineId": "fd52113cf73c54a922b19da1eb2dcd5e",
            "marketId": 150002758,
            "outcomeId": 12,
            "sportEventId": 30023974
        },
        {
            "line": 0.5,
            "lineId": "46ab2343070ae065138bdc6af633f325",
            "marketId": 150000559,
            "outcomeId": 12,
            "sportEventId": 30023974
        }
    ]
    
    # Test parlay creation
    url = "https://api-ss-sandbox.betprophet.co/parlay/api/v1/user/request"
    payload = {"marketLines": market_lines}
    headers = {
        "Authorization": f"Bearer {user_token}",
        "Content-Type": "application/json"
    }
    
    logger.info("📤 TESTING PARLAY CREATION REQUEST")
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
        logger.info("✅ FRESH MARKET LINES DATA WORKING!")
        parlay_id = response_data.get("data", {}).get("parlayId")
        logger.info(f"✅ Parlay created: {parlay_id}")
    else:
        logger.error("❌ FRESH MARKET LINES DATA FAILED")
        logger.error("🔍 This explains why all scenarios are failing")
        
        # Try with old working market lines for comparison
        logger.info("\n🔄 TESTING WITH OLD WORKING MARKET LINES FOR COMPARISON...")
        
        old_market_lines = [
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
        
        old_payload = {"marketLines": old_market_lines}
        logger.info(f"OLD PAYLOAD: {json.dumps(old_payload, indent=2)}")
        
        old_response = requests.post(url, json=old_payload, headers=headers)
        
        logger.info(f"\n📥 OLD MARKET LINES RESPONSE")
        logger.info(f"STATUS: {old_response.status_code}")
        
        try:
            old_response_data = old_response.json()
            logger.info(f"BODY: {json.dumps(old_response_data, indent=2)}")
        except:
            logger.info(f"BODY (raw): {old_response.text}")
        
        if old_response.status_code == 200:
            logger.info("✅ OLD MARKET LINES STILL WORKING")
            old_parlay_id = old_response_data.get("data", {}).get("parlayId")
            logger.info(f"✅ Old parlay created: {old_parlay_id}")
        else:
            logger.error("❌ OLD MARKET LINES ALSO FAILING")

def main():
    """Run market lines diagnostic"""
    test_market_lines()

if __name__ == "__main__":
    main()
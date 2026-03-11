#!/usr/bin/env python3
"""
🔍 SIMPLE REJECTION vs TIMEOUT TEST

Clear demonstration of the difference between:
1. REJECTION: SP sends "action": "reject" intentionally
2. TIMEOUT: User tries to confirm expired offers
"""

import requests
import json
import time
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

def get_sp_token():
    """Get SP1 token"""
    url = "https://api-ss-sandbox.betprophet.co/partner/auth/login"
    credentials = {
        "access_key": "e85df05bd1bd885fbc0fc4b24fdd2500",
        "secret_key": "67344329e054349f07e7a29249dcadeb"
    }
    
    response = requests.post(url, json=credentials)
    if response.status_code == 200:
        return response.json()["data"]["access_token"]
    return None

def test_rejection_scenario():
    """Test: SP intentionally rejects with 'action': 'reject'"""
    logger.info("\n🚫 TEST 1: INTENTIONAL REJECTION")
    logger.info("="*60)
    
    user_token = get_user_token()
    sp_token = get_sp_token()
    
    if not user_token or not sp_token:
        logger.error("❌ Authentication failed")
        return False
    
    # Market lines for parlay
    market_lines = [
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
    
    # 1. Create parlay request
    parlay_url = "https://api-ss-sandbox.betprophet.co/parlay/api/v1/user/request"
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
    
    response = requests.post(parlay_url, json={"marketLines": market_lines}, headers=headers)
    if response.status_code != 200:
        logger.error(f"❌ Parlay creation failed: {response.status_code}")
        return False
    
    parlay_id = response.json()["data"]["parlayId"]
    logger.info(f"✅ Parlay created: {parlay_id}")
    
    # 2. SP provides offer
    offer_url = "https://api-ss-sandbox.betprophet.co/parlay/sp/orders/offers"
    offer_payload = {
        "parlay_id": parlay_id,
        "offers": [
            {
                "odds": 800,
                "max_risk": 100,
                "valid_until": int((time.time() + 60) * 1_000_000_000),  # 60s validity
                "estimated_prices": [
                    {"line_id": line["lineId"], "odds": 800}
                    for line in market_lines
                ]
            }
        ]
    }
    
    sp_headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
    response = requests.post(offer_url, json=offer_payload, headers=sp_headers)
    
    if response.status_code != 200:
        logger.error(f"❌ SP offer failed: {response.status_code}")
        return False
    
    logger.info("✅ SP offer sent")
    
    # 3. User confirms bet
    confirm_url = "https://api-ss-sandbox.betprophet.co/parlay/api/v1/user/confirm"
    confirm_payload = {
        "parlayId": parlay_id,
        "odds": 800,
        "stake": 100
    }
    
    response = requests.post(confirm_url, json=confirm_payload, headers=headers)
    if response.status_code != 200:
        logger.error(f"❌ User confirmation failed: {response.status_code}")
        return False
    
    logger.info("✅ User confirmed bet")
    time.sleep(3)  # Allow processing
    
    # 4. SP INTENTIONALLY REJECTS
    orders_url = "https://api-ss-sandbox.betprophet.co/parlay/sp/orders"
    response = requests.get(orders_url, headers=sp_headers)
    
    if response.status_code != 200:
        logger.error(f"❌ Get orders failed: {response.status_code}")
        return False
    
    orders = response.json()["data"]["orders"]
    order_uuid = None
    
    # Find the order to reject
    for order in orders:
        if order["p_id"] == parlay_id and order["status"] == "sent_confirmation":
            order_uuid = order["order_uuid"]
            break
    
    if not order_uuid:
        logger.error("❌ No order found to reject")
        return False
    
    # SP sends INTENTIONAL REJECTION
    reject_url = "https://api-ss-sandbox.betprophet.co/parlay/sp/orders/confirmations"
    reject_payload = {
        "action": "reject",
        "signature": "test_rejection_signature"
    }
    
    logger.info(f"🚫 SP INTENTIONALLY REJECTING order {order_uuid}")
    response = requests.post(reject_url, json=reject_payload, headers=sp_headers, 
                           params={"order_uuid": order_uuid})
    
    if response.status_code == 200:
        logger.info("✅ SP REJECTION sent successfully")
        logger.info("📋 This is REJECTION: SP deliberately chose to reject")
        return True
    else:
        logger.error(f"❌ SP rejection failed: {response.status_code} - {response.text}")
        return False

def test_timeout_scenario():
    """Test: User tries to confirm after offers expire (TIMEOUT)"""
    logger.info("\n⏰ TEST 2: TIMEOUT BEHAVIOR")
    logger.info("="*60)
    
    user_token = get_user_token()
    sp_token = get_sp_token()
    
    if not user_token or not sp_token:
        logger.error("❌ Authentication failed")
        return False
    
    # Market lines for parlay
    market_lines = [
        {
            "line": 0,
            "lineId": "99fe18eea332562ac5cd04d4b3c772d0",
            "marketId": 406,
            "outcomeId": 4,
            "sportEventId": 30023983
        }
    ]
    
    # 1. Create parlay request
    parlay_url = "https://api-ss-sandbox.betprophet.co/parlay/api/v1/user/request"
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
    
    response = requests.post(parlay_url, json={"marketLines": market_lines}, headers=headers)
    if response.status_code != 200:
        logger.error(f"❌ Parlay creation failed: {response.status_code}")
        return False
    
    parlay_id = response.json()["data"]["parlayId"]
    logger.info(f"✅ Parlay created: {parlay_id}")
    
    # 2. SP provides SHORT-LIVED offer (6 seconds)
    offer_time = time.time()
    offer_url = "https://api-ss-sandbox.betprophet.co/parlay/sp/orders/offers"
    offer_payload = {
        "parlay_id": parlay_id,
        "offers": [
            {
                "odds": 800,
                "max_risk": 100,
                "valid_until": int((offer_time + 6) * 1_000_000_000),  # Only 6s validity!
                "estimated_prices": [
                    {"line_id": line["lineId"], "odds": 800}
                    for line in market_lines
                ]
            }
        ]
    }
    
    sp_headers = {"Authorization": f"Bearer {sp_token}", "Content-Type": "application/json"}
    response = requests.post(offer_url, json=offer_payload, headers=sp_headers)
    
    if response.status_code != 200:
        logger.error(f"❌ SP offer failed: {response.status_code}")
        return False
    
    logger.info("✅ SP offer sent with 6s validity")
    logger.info(f"📊 Offer expires at: {offer_time + 6:.2f}")
    
    # 3. WAIT FOR OFFER TO EXPIRE
    logger.info("⏰ Waiting 8 seconds for offer to expire...")
    time.sleep(8)
    
    # 4. User tries to confirm AFTER expiry (should fail)
    confirm_time = time.time()
    confirm_url = "https://api-ss-sandbox.betprophet.co/parlay/api/v1/user/confirm"
    confirm_payload = {
        "parlayId": parlay_id,
        "odds": 800,
        "stake": 100
    }
    
    logger.info(f"📊 User confirming at: {confirm_time:.2f}")
    logger.info(f"📊 Time after expiry: {confirm_time - (offer_time + 6):.2f}s")
    
    response = requests.post(confirm_url, json=confirm_payload, headers=headers)
    
    if response.status_code == 200:
        logger.error("🐛 BUG CONFIRMED: User confirmation succeeded for expired offers")
        logger.error("📋 This shows TIMEOUT handling is broken")
        return False
    else:
        logger.info("✅ User confirmation properly rejected for expired offers")
        logger.info("📋 This is proper TIMEOUT behavior")
        return True

def main():
    """Run both tests to show the difference"""
    logger.info("🔍 REJECTION vs TIMEOUT DEMONSTRATION")
    logger.info("="*80)
    logger.info("🚫 REJECTION = SP sends 'action': 'reject'")
    logger.info("⏰ TIMEOUT = User confirms after offers expire")
    logger.info("="*80)
    
    # Test rejection (SP behavior)
    rejection_works = test_rejection_scenario()
    
    # Test timeout (system validation)
    timeout_works = test_timeout_scenario()
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("🏁 FINAL RESULTS")
    logger.info("="*80)
    logger.info(f"🚫 REJECTION handling: {'✅ WORKS' if rejection_works else '❌ BROKEN'}")
    logger.info(f"⏰ TIMEOUT handling: {'✅ WORKS' if timeout_works else '❌ BROKEN'}")
    
    if not rejection_works:
        logger.info("\n🚫 REJECTION ISSUE: SP 'action': 'reject' may not be processed correctly")
    
    if not timeout_works:
        logger.info("\n⏰ TIMEOUT ISSUE: System accepts user confirmations for expired offers")
        logger.info("   This is the critical bug we found earlier")
    
    logger.info(f"\n📋 DISTINCTION SUMMARY:")
    logger.info("   🚫 REJECTION = Business decision by SP (intentional)")
    logger.info("   ⏰ TIMEOUT = System validation failure (bug)")

if __name__ == "__main__":
    main()
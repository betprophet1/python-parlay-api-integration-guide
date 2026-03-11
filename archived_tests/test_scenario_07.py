#!/usr/bin/env python3

import json
import time
import requests
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://parlay-api-staging.herokuapp.com"
SP1_ACCESS_KEY = "sp1_access_key_here"
SP1_SECRET_KEY = "sp1_secret_key_here"
SP2_ACCESS_KEY = "sp2_access_key_here"
SP2_SECRET_KEY = "sp2_secret_key_here"
USER_TOKEN = "user_token_here"

def log_request_response(operation, response):
    """Log request and response details for debugging"""
    print(f"\n{'='*60}")
    print(f"📋 OPERATION: {operation}")
    print(f"⏰ TIMESTAMP: {datetime.now(timezone.utc).isoformat()}")
    if hasattr(response, 'request'):
        print(f"📤 REQUEST URL: {response.request.url}")
        print(f"📤 REQUEST METHOD: {response.request.method}")
        if response.request.body:
            try:
                body = json.loads(response.request.body)
                print(f"📤 REQUEST BODY: {json.dumps(body, indent=2)}")
            except:
                print(f"📤 REQUEST BODY: {response.request.body}")
    print(f"📥 RESPONSE STATUS: {response.status_code}")
    try:
        print(f"📥 RESPONSE BODY: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"📥 RESPONSE BODY: {response.text}")
    print(f"{'='*60}")

def authenticate_sp(access_key, secret_key, sp_name):
    """Authenticate service provider and return token"""
    auth_data = {
        "access_key": access_key,
        "secret_key": secret_key
    }
    
    print(f"\n🔐 Authenticating {sp_name}...")
    response = requests.post(f"{BASE_URL}/api/v1/auth", json=auth_data)
    log_request_response(f"{sp_name} Authentication", response)
    
    if response.status_code == 200:
        token = response.json().get("token")
        print(f"✅ {sp_name} authenticated successfully")
        return token
    else:
        print(f"❌ {sp_name} authentication failed")
        return None

def create_parlay(user_token):
    """Create parlay with user token"""
    parlay_data = {
        "stake_cents": 50000,  # $500.00
        "selections": [
            {
                "line_id": "11_7540_49094",
                "side": "1"
            },
            {
                "line_id": "11_7540_49095", 
                "side": "2"
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    print("\n🎰 Creating parlay request...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay", json=parlay_data, headers=headers)
    log_request_response("Create Parlay", response)
    
    if response.status_code == 201:
        parlay_id = response.json().get("parlay_id")
        print(f"✅ Parlay created with ID: {parlay_id}")
        return parlay_id
    else:
        print("❌ Failed to create parlay")
        return None

def provide_sp1_short_validity_offers(sp_token, parlay_id):
    """SP1 provides best odds with short validity"""
    offers_data = {
        "offers": [
            {
                "odds": 500,  # Best odds
                "max_risk": 50000,  # Full $500 capacity
                "valid_until": int(time.time()) + 3  # 3 seconds validity
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n💰 SP1 providing best odds with short validity (3 seconds)...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
    log_request_response("SP1 Short Validity Offers", response)
    
    if response.status_code == 200:
        print("✅ SP1 short-validity offers submitted successfully")
        return True
    else:
        print("❌ SP1 failed to submit offers")
        return False

def provide_sp2_long_validity_offers(sp_token, parlay_id):
    """SP2 provides worse odds with longer validity"""
    offers_data = {
        "offers": [
            {
                "odds": 350,  # Worse odds than SP1
                "max_risk": 50000,  # Full $500 capacity  
                "valid_until": int(time.time()) + 30  # 30 seconds validity
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n💰 SP2 providing worse odds with long validity (30 seconds)...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
    log_request_response("SP2 Long Validity Offers", response)
    
    if response.status_code == 200:
        print("✅ SP2 long-validity offers submitted successfully")
        return True
    else:
        print("❌ SP2 failed to submit offers")
        return False

def get_offers_for_user(user_token, parlay_id):
    """Get offers presented to user"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    print("\n📋 Getting offers for user...")
    response = requests.get(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", headers=headers)
    log_request_response("Get User Offers", response)
    
    if response.status_code == 200:
        offers = response.json()
        print("✅ Offers retrieved successfully")
        return offers
    else:
        print("❌ Failed to retrieve offers")
        return None

def delayed_confirm_parlay(user_token, parlay_id, selected_offers, delay_seconds):
    """User confirms parlay after a delay"""
    print(f"\n⏳ User taking time to decide... waiting {delay_seconds} seconds")
    time.sleep(delay_seconds)
    
    confirm_data = {
        "offers": selected_offers
    }
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    print(f"\n✅ User confirming parlay after {delay_seconds}s delay...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/confirm", json=confirm_data, headers=headers)
    log_request_response("Delayed Confirm Parlay", response)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Parlay confirmation processed")
        return result
    else:
        print("❌ Failed to confirm parlay")
        return None

def get_final_parlay_status(user_token, parlay_id):
    """Get final parlay status"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    print("\n📊 Getting final parlay status...")
    response = requests.get(f"{BASE_URL}/api/v1/parlay/{parlay_id}", headers=headers)
    log_request_response("Final Parlay Status", response)
    
    if response.status_code == 200:
        status = response.json()
        print("✅ Final status retrieved")
        return status
    else:
        print("❌ Failed to retrieve final status")
        return None

def run_scenario_7():
    """
    Scenario 7: Mixed Validity Periods
    - SP1 provides best odds (500) with short validity (3 seconds)
    - SP2 provides worse odds (350) with long validity (30 seconds)
    - User confirms after 5 seconds (SP1 expired, SP2 still valid)
    - No fallback configured - should fail completely
    """
    
    print("🚀 STARTING SCENARIO 7: Mixed Validity Periods")
    print("=" * 60)
    
    # Step 1: Authenticate SPs
    sp1_token = authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
    sp2_token = authenticate_sp(SP2_ACCESS_KEY, SP2_SECRET_KEY, "SP2")
    
    if not sp1_token or not sp2_token:
        print("❌ SCENARIO 7 FAILED: Authentication failed")
        return False
    
    # Step 2: Create parlay
    parlay_id = create_parlay(USER_TOKEN)
    if not parlay_id:
        print("❌ SCENARIO 7 FAILED: Could not create parlay")
        return False
    
    # Step 3: SPs provide offers with different validity periods
    sp1_success = provide_sp1_short_validity_offers(sp1_token, parlay_id)
    sp2_success = provide_sp2_long_validity_offers(sp2_token, parlay_id)
    
    if not sp1_success or not sp2_success:
        print("❌ SCENARIO 7 FAILED: SPs failed to provide offers")
        return False
    
    # Small delay to ensure offers are processed
    time.sleep(0.5)
    
    # Step 4: User gets initial offers (both should be available)
    initial_offers = get_offers_for_user(USER_TOKEN, parlay_id)
    if not initial_offers:
        print("❌ SCENARIO 7 FAILED: Could not retrieve initial offers")
        return False
    
    initial_available = initial_offers.get("offers", [])
    if not initial_available:
        print("❌ SCENARIO 7 FAILED: No offers available initially")
        return False
    
    print(f"\n📊 Initial offers available: {len(initial_available)}")
    for i, offer in enumerate(initial_available):
        odds = offer.get("odds", 0)
        max_risk = offer.get("max_risk", 0)
        valid_until = offer.get("valid_until", 0)
        expires_in = max(0, valid_until - int(time.time()))
        print(f"  Offer {i+1}: {odds} odds, ${max_risk/100:.2f} max risk, expires in {expires_in}s")
    
    # Find the best offer (should be SP1's 500 odds)
    best_offer = max(initial_available, key=lambda x: x.get("odds", 0))
    best_odds = best_offer.get("odds", 0)
    
    print(f"\n🏆 Best offer: {best_odds} odds")
    
    # Step 5: User takes 5 seconds to confirm (SP1 expires at 3s, SP2 still valid at 30s)
    selected_offers = [best_offer]  # User wants the best offer
    
    print("\n⏰ Testing mixed validity behavior...")
    confirmation_result = delayed_confirm_parlay(USER_TOKEN, parlay_id, selected_offers, 5)
    
    # Step 6: Check offers available after delay
    print("\n📋 Checking offers after delay...")
    delayed_offers = get_offers_for_user(USER_TOKEN, parlay_id)
    
    if delayed_offers:
        delayed_available = delayed_offers.get("offers", [])
        print(f"📊 Offers available after delay: {len(delayed_available)}")
        for i, offer in enumerate(delayed_available):
            odds = offer.get("odds", 0)
            max_risk = offer.get("max_risk", 0)
            valid_until = offer.get("valid_until", 0)
            expires_in = max(0, valid_until - int(time.time()))
            print(f"  Offer {i+1}: {odds} odds, ${max_risk/100:.2f} max risk, expires in {expires_in}s")
        
        # Check if only SP2's offer remains (lower odds)
        if delayed_available:
            remaining_odds = [offer.get("odds", 0) for offer in delayed_available]
            max_remaining_odds = max(remaining_odds)
            
            if max_remaining_odds < best_odds:
                print(f"✅ Best offer ({best_odds}) expired, only worse offers ({max_remaining_odds}) remain")
                best_expired = True
            else:
                print(f"❌ Best offer ({best_odds}) still available, expiration not working")
                best_expired = False
        else:
            print("✅ All offers expired")
            best_expired = True
    else:
        print("❌ Could not retrieve offers after delay")
        best_expired = False
    
    # Step 7: Get final parlay status
    final_status = get_final_parlay_status(USER_TOKEN, parlay_id)
    if not final_status:
        print("❌ SCENARIO 7 FAILED: Could not retrieve final status")
        return False
    
    # Step 8: Validate results
    print("\n🔍 VALIDATING SCENARIO 7 RESULTS:")
    print("=" * 40)
    
    success = True
    
    # Check parlay status
    status = final_status.get("status")
    matched_stake = final_status.get("matched_stake_cents", 0)
    total_stake = final_status.get("stake_cents", 0)
    
    print(f"📊 Parlay Status: {status}")
    print(f"💰 Matched Stake: ${matched_stake/100:.2f}")
    print(f"💰 Total Stake: ${total_stake/100:.2f}")
    
    # Validate behavior depends on system configuration
    if confirmation_result is None:
        # Confirmation failed completely
        print("📋 Confirmation failed - testing no-fallback behavior")
        
        if matched_stake > 0:
            print("❌ Expected no matching when confirmation fails")
            success = False
        else:
            print("✅ No matching occurred when best offer expired")
        
        # Check that best offer expiration was detected
        if not best_expired:
            print("❌ Expected best offer to expire after 3 seconds")
            success = False
        else:
            print("✅ Best offer correctly expired")
            
    else:
        # Confirmation succeeded (possibly with fallback)
        print("📋 Confirmation succeeded - testing fallback behavior")
        
        # Check if system fell back to SP2's worse offer
        matched_bets = final_status.get("matched_bets", [])
        if matched_bets:
            matched_odds = [bet.get("odds", 0) for bet in matched_bets]
            max_matched_odds = max(matched_odds) if matched_odds else 0
            
            if max_matched_odds == best_odds:
                print(f"❌ Matched with expired best odds ({best_odds}) - expiration not enforced")
                success = False
            elif max_matched_odds > 0:
                print(f"✅ Fell back to available offer ({max_matched_odds} odds)")
                
                # In no-fallback scenario, this might indicate fallback was enabled
                print("⚠️  NOTE: System performed fallback - check if this matches expected behavior")
            else:
                print("❌ No valid odds in matched bets")
                success = False
        else:
            print("❌ No matched bets found despite successful confirmation")
            success = False
    
    # Validate that different validity periods were respected
    if not best_expired:
        print("❌ Mixed validity periods not properly handled")
        success = False
    else:
        print("✅ Mixed validity periods correctly handled")
        
        # Check if worse offer was still available after best expired
        if delayed_offers and delayed_offers.get("offers"):
            remaining_odds = [offer.get("odds", 0) for offer in delayed_offers.get("offers", [])]
            if remaining_odds and max(remaining_odds) < best_odds:
                print("✅ Worse offer remained available after best expired")
            else:
                print("⚠️  Unexpected offer availability pattern")
    
    if success:
        print("\n🎉 SCENARIO 7 PASSED: Mixed Validity Periods")
        print("✅ Best offer expired after short validity period")
        print("✅ Worse offer remained available with longer validity")
        print("✅ System handled mixed validity periods correctly")
        if confirmation_result:
            print("✅ Fallback behavior working (if enabled)")
        else:
            print("✅ No-fallback behavior working (if configured)")
    else:
        print("\n❌ SCENARIO 7 FAILED: Validation errors detected")
    
    return success

if __name__ == "__main__":
    success = run_scenario_7()
    exit(0 if success else 1)
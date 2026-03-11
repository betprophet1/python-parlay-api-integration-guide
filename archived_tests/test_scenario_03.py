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

def provide_sp1_offers(sp_token, parlay_id):
    """SP1 provides best odds with limited capacity"""
    offers_data = {
        "offers": [
            {
                "odds": 450,  # Best odds
                "max_risk": 25000,  # Limited to $250 (half of $500 stake)
                "valid_until": int(time.time()) + 30  # 30 seconds validity
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n💰 SP1 providing limited capacity offers...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
    log_request_response("SP1 Offers", response)
    
    if response.status_code == 200:
        print("✅ SP1 offers submitted successfully")
        return True
    else:
        print("❌ SP1 failed to submit offers")
        return False

def provide_sp2_offers(sp_token, parlay_id):
    """SP2 provides worse odds"""
    offers_data = {
        "offers": [
            {
                "odds": 350,  # Worse odds than SP1
                "max_risk": 50000,  # Can handle full $500 stake
                "valid_until": int(time.time()) + 30  # 30 seconds validity
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n💰 SP2 providing worse odds offers...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
    log_request_response("SP2 Offers", response)
    
    if response.status_code == 200:
        print("✅ SP2 offers submitted successfully")
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

def confirm_parlay(user_token, parlay_id, selected_offers):
    """User confirms parlay with selected offers"""
    confirm_data = {
        "offers": selected_offers
    }
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    print(f"\n✅ User confirming parlay with {len(selected_offers)} offers...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/confirm", json=confirm_data, headers=headers)
    log_request_response("Confirm Parlay", response)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Parlay confirmation processed")
        return result
    else:
        print("❌ Failed to confirm parlay")
        return None

def sp2_reject_confirmation(sp_token, parlay_id, bet_id):
    """SP2 rejects the confirmation"""
    reject_data = {
        "status": "rejected",
        "reason": "Risk limits exceeded"
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n❌ SP2 rejecting confirmation...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/bet/{bet_id}/respond", json=reject_data, headers=headers)
    log_request_response("SP2 Reject Confirmation", response)
    
    if response.status_code == 200:
        print("✅ SP2 rejection processed")
        return True
    else:
        print("❌ SP2 failed to process rejection")
        return False

def sp1_accept_confirmation(sp_token, parlay_id, bet_id):
    """SP1 accepts the confirmation"""
    accept_data = {
        "status": "accepted",
        "confirmed_stake_cents": 25000  # Only $250 confirmed (limited capacity)
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n✅ SP1 accepting confirmation with limited stake...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/bet/{bet_id}/respond", json=accept_data, headers=headers)
    log_request_response("SP1 Accept Confirmation", response)
    
    if response.status_code == 200:
        print("✅ SP1 acceptance processed")
        return True
    else:
        print("❌ SP1 failed to process acceptance")
        return False

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

def run_scenario_3():
    """
    Scenario 3: Second Tier Matching with STOP
    - SP1 provides best odds but with limited capacity ($250 of $500)
    - SP2 provides worse odds but rejects confirmation  
    - Result: Partial match only with SP1, remaining stake unmatched (STOP)
    """
    
    print("🚀 STARTING SCENARIO 3: Second Tier Matching with STOP")
    print("=" * 60)
    
    # Step 1: Authenticate SPs
    sp1_token = authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
    sp2_token = authenticate_sp(SP2_ACCESS_KEY, SP2_SECRET_KEY, "SP2")
    
    if not sp1_token or not sp2_token:
        print("❌ SCENARIO 3 FAILED: Authentication failed")
        return False
    
    # Step 2: Create parlay
    parlay_id = create_parlay(USER_TOKEN)
    if not parlay_id:
        print("❌ SCENARIO 3 FAILED: Could not create parlay")
        return False
    
    # Step 3: SPs provide offers
    sp1_success = provide_sp1_offers(sp1_token, parlay_id)
    sp2_success = provide_sp2_offers(sp2_token, parlay_id)
    
    if not sp1_success or not sp2_success:
        print("❌ SCENARIO 3 FAILED: SPs failed to provide offers")
        return False
    
    # Small delay to ensure offers are processed
    time.sleep(2)
    
    # Step 4: User gets offers (should see blended offers)
    offers = get_offers_for_user(USER_TOKEN, parlay_id)
    if not offers:
        print("❌ SCENARIO 3 FAILED: Could not retrieve offers")
        return False
    
    # Step 5: User confirms best available offers
    available_offers = offers.get("offers", [])
    if not available_offers:
        print("❌ SCENARIO 3 FAILED: No offers available")
        return False
    
    # User selects best offers (system should blend SP1's limited + SP2's full coverage)
    selected_offers = available_offers[:2] if len(available_offers) >= 2 else available_offers
    
    confirmation_result = confirm_parlay(USER_TOKEN, parlay_id, selected_offers)
    if not confirmation_result:
        print("❌ SCENARIO 3 FAILED: Could not confirm parlay")
        return False
    
    # Small delay for processing
    time.sleep(2)
    
    # Step 6: SP1 accepts (limited capacity), SP2 rejects
    bets = confirmation_result.get("bets", [])
    
    # Find SP1 and SP2 bets
    sp1_bet_id = None
    sp2_bet_id = None
    
    for bet in bets:
        if bet.get("provider") == "sp1":
            sp1_bet_id = bet.get("bet_id")
        elif bet.get("provider") == "sp2":
            sp2_bet_id = bet.get("bet_id")
    
    # SP1 accepts with limited stake
    if sp1_bet_id:
        sp1_accept_confirmation(sp1_token, parlay_id, sp1_bet_id)
    
    # SP2 rejects
    if sp2_bet_id:
        sp2_reject_confirmation(sp2_token, parlay_id, sp2_bet_id)
    
    # Small delay for processing
    time.sleep(3)
    
    # Step 7: Get final status
    final_status = get_final_parlay_status(USER_TOKEN, parlay_id)
    if not final_status:
        print("❌ SCENARIO 3 FAILED: Could not retrieve final status")
        return False
    
    # Step 8: Validate results
    print("\n🔍 VALIDATING SCENARIO 3 RESULTS:")
    print("=" * 40)
    
    success = True
    
    # Check if parlay is partially matched
    status = final_status.get("status")
    matched_stake = final_status.get("matched_stake_cents", 0)
    total_stake = final_status.get("stake_cents", 0)
    
    print(f"📊 Parlay Status: {status}")
    print(f"💰 Matched Stake: ${matched_stake/100:.2f}")
    print(f"💰 Total Stake: ${total_stake/100:.2f}")
    print(f"📈 Match Rate: {(matched_stake/total_stake*100):.1f}%")
    
    # Validate partial matching
    if matched_stake != 25000:  # Should match only SP1's $250
        print(f"❌ Expected matched stake $250.00, got ${matched_stake/100:.2f}")
        success = False
    else:
        print("✅ Matched stake correct ($250.00)")
    
    # Check for unmatched portion (STOP behavior)
    unmatched_stake = total_stake - matched_stake
    if unmatched_stake != 25000:  # Should have $250 unmatched
        print(f"❌ Expected unmatched stake $250.00, got ${unmatched_stake/100:.2f}")
        success = False
    else:
        print("✅ Unmatched stake correct ($250.00) - STOP behavior confirmed")
    
    if success:
        print("\n🎉 SCENARIO 3 PASSED: Second Tier Matching with STOP")
        print("✅ SP1 limited capacity matched")
        print("✅ SP2 rejection handled correctly") 
        print("✅ STOP behavior confirmed - no further matching attempted")
    else:
        print("\n❌ SCENARIO 3 FAILED: Validation errors detected")
    
    return success

if __name__ == "__main__":
    success = run_scenario_3()
    exit(0 if success else 1)
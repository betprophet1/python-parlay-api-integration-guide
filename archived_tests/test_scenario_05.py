#!/usr/bin/env python3

import json
import time
import requests
from datetime import datetime, timezone

# Configuration
BASE_URL = "https://parlay-api-staging.herokuapp.com"
SP1_ACCESS_KEY = "sp1_access_key_here"
SP1_SECRET_KEY = "sp1_secret_key_here"
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
    """SP1 provides offers with very short validity period"""
    offers_data = {
        "offers": [
            {
                "odds": 450,  # Good odds
                "max_risk": 50000,  # Full $500 capacity
                "valid_until": int(time.time()) + 1  # Only 1 second validity!
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n💰 SP1 providing short-validity offers (1 second)...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
    log_request_response("SP1 Short Validity Offers", response)
    
    if response.status_code == 200:
        print("✅ SP1 short-validity offers submitted successfully")
        return True
    else:
        print("❌ SP1 failed to submit offers")
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
    """User confirms parlay after a delay (simulating slow user response)"""
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
        print("❌ Failed to confirm parlay - likely expired!")
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

def run_scenario_5():
    """
    Scenario 5: Odds Expire Before User Confirmation
    - SP provides offers with 1-second validity
    - User takes 2 seconds to confirm (simulating slow decision)
    - Result: Confirmation should fail due to expired offers
    """
    
    print("🚀 STARTING SCENARIO 5: Odds Expire Before User Confirmation")
    print("=" * 60)
    
    # Step 1: Authenticate SP1
    sp1_token = authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
    
    if not sp1_token:
        print("❌ SCENARIO 5 FAILED: Authentication failed")
        return False
    
    # Step 2: Create parlay
    parlay_id = create_parlay(USER_TOKEN)
    if not parlay_id:
        print("❌ SCENARIO 5 FAILED: Could not create parlay")
        return False
    
    # Step 3: SP1 provides offers with very short validity (1 second)
    sp1_success = provide_sp1_short_validity_offers(sp1_token, parlay_id)
    
    if not sp1_success:
        print("❌ SCENARIO 5 FAILED: SP1 failed to provide offers")
        return False
    
    # Small delay to ensure offers are processed
    time.sleep(0.5)
    
    # Step 4: User gets offers (should be available initially)
    offers = get_offers_for_user(USER_TOKEN, parlay_id)
    if not offers:
        print("❌ SCENARIO 5 FAILED: Could not retrieve offers")
        return False
    
    available_offers = offers.get("offers", [])
    if not available_offers:
        print("❌ SCENARIO 5 FAILED: No offers available")
        return False
    
    print(f"\n📊 Retrieved {len(available_offers)} offers")
    for i, offer in enumerate(available_offers):
        odds = offer.get("odds", 0)
        max_risk = offer.get("max_risk", 0)
        valid_until = offer.get("valid_until", 0)
        expires_in = valid_until - int(time.time())
        print(f"  Offer {i+1}: {odds} odds, ${max_risk/100:.2f} max risk, expires in {expires_in}s")
    
    # Step 5: User takes 2 seconds to confirm (longer than 1-second validity)
    selected_offers = available_offers[:1]  # Select first offer
    
    print("\n⏰ Testing expiration behavior...")
    confirmation_result = delayed_confirm_parlay(USER_TOKEN, parlay_id, selected_offers, 2)
    
    # Step 6: Check if confirmation failed due to expiration
    if confirmation_result is None:
        print("✅ Confirmation correctly failed due to expired offers")
        confirmation_failed = True
    else:
        print("❌ Confirmation unexpectedly succeeded despite expired offers")
        confirmation_failed = False
    
    # Small delay before checking final status
    time.sleep(1)
    
    # Step 7: Get final parlay status
    final_status = get_final_parlay_status(USER_TOKEN, parlay_id)
    if not final_status:
        print("❌ SCENARIO 5 FAILED: Could not retrieve final status")
        return False
    
    # Step 8: Validate results
    print("\n🔍 VALIDATING SCENARIO 5 RESULTS:")
    print("=" * 40)
    
    success = True
    
    # Check parlay status
    status = final_status.get("status")
    matched_stake = final_status.get("matched_stake_cents", 0)
    total_stake = final_status.get("stake_cents", 0)
    
    print(f"📊 Parlay Status: {status}")
    print(f"💰 Matched Stake: ${matched_stake/100:.2f}")
    print(f"💰 Total Stake: ${total_stake/100:.2f}")
    
    # Validate that no matching occurred due to expiration
    if matched_stake > 0:
        print(f"❌ Expected no matching due to expiration, but got ${matched_stake/100:.2f} matched")
        success = False
    else:
        print("✅ No matching occurred - correctly handled expiration")
    
    # Validate that confirmation failed
    if not confirmation_failed:
        print("❌ Expected confirmation to fail due to expiration")
        success = False
    else:
        print("✅ Confirmation correctly failed due to expired offers")
    
    # Check status reflects expiration/failure
    expected_statuses = ["expired", "failed", "rejected", "unmatched"]
    if status not in expected_statuses:
        print(f"❌ Expected status to be one of {expected_statuses}, got '{status}'")
        success = False
    else:
        print(f"✅ Status '{status}' correctly reflects expiration handling")
    
    # Test offer re-retrieval after expiration
    print("\n🔄 Testing offer availability after expiration...")
    time.sleep(1)
    expired_offers = get_offers_for_user(USER_TOKEN, parlay_id)
    
    if expired_offers:
        expired_available = expired_offers.get("offers", [])
        if len(expired_available) == 0:
            print("✅ No offers available after expiration - correct behavior")
        else:
            print("❌ Offers still available after expiration - incorrect behavior")
            success = False
    
    if success:
        print("\n🎉 SCENARIO 5 PASSED: Odds Expire Before User Confirmation")
        print("✅ Short validity period respected")
        print("✅ Confirmation correctly failed after expiration")
        print("✅ No matching occurred for expired offers")
        print("✅ System handled expiration gracefully")
    else:
        print("\n❌ SCENARIO 5 FAILED: Validation errors detected")
    
    return success

if __name__ == "__main__":
    success = run_scenario_5()
    exit(0 if success else 1)
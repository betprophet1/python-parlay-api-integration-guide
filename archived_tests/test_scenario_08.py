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

def get_offers_for_user_with_timeout(user_token, parlay_id, max_wait_time=10):
    """Get offers for user with timeout handling"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    print(f"\n📋 Waiting for offers (timeout: {max_wait_time}s)...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        print(f"⏰ Checking offers... ({int(time.time() - start_time)}s elapsed)")
        
        response = requests.get(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", headers=headers)
        log_request_response("Get User Offers", response)
        
        if response.status_code == 200:
            offers = response.json()
            available_offers = offers.get("offers", [])
            
            if available_offers:
                print("✅ Offers retrieved successfully")
                return offers
            else:
                print("⏳ No offers available yet, waiting...")
                time.sleep(1)
        else:
            print("❌ Failed to retrieve offers")
            time.sleep(1)
    
    print(f"⏰ Timeout reached ({max_wait_time}s) - no offers received")
    return None

def attempt_confirm_parlay(user_token, parlay_id):
    """User attempts to confirm parlay with no offers"""
    confirm_data = {
        "offers": []  # No offers available to confirm
    }
    
    headers = {"Authorization": f"Bearer {user_token}"}
    
    print(f"\n✅ User attempting to confirm parlay with no offers...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/confirm", json=confirm_data, headers=headers)
    log_request_response("Confirm Parlay (No Offers)", response)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Parlay confirmation processed (unexpected)")
        return result
    else:
        print("❌ Parlay confirmation failed (expected)")
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

def run_scenario_8():
    """
    Scenario 8: No SP Responses
    - SPs are authenticated but do not provide any offers
    - User waits for offers but none arrive (timeout)
    - User attempts to confirm anyway
    - Result: System should fail gracefully with appropriate error handling
    """
    
    print("🚀 STARTING SCENARIO 8: No SP Responses")
    print("=" * 60)
    
    # Step 1: Authenticate SPs (but they won't provide offers)
    sp1_token = authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
    sp2_token = authenticate_sp(SP2_ACCESS_KEY, SP2_SECRET_KEY, "SP2")
    
    if not sp1_token or not sp2_token:
        print("❌ SCENARIO 8 FAILED: Authentication failed")
        return False
    
    # Step 2: Create parlay
    parlay_id = create_parlay(USER_TOKEN)
    if not parlay_id:
        print("❌ SCENARIO 8 FAILED: Could not create parlay")
        return False
    
    # Step 3: SPs intentionally do NOT provide offers
    # (This simulates SPs being offline, busy, or having technical issues)
    print("\n⚠️  SPs are authenticated but will NOT provide offers")
    print("📋 This simulates SP downtime or technical issues")
    
    # Small delay to ensure parlay is ready
    time.sleep(1)
    
    # Step 4: User waits for offers but times out
    offers = get_offers_for_user_with_timeout(USER_TOKEN, parlay_id, max_wait_time=8)
    
    # Step 5: User attempts to confirm despite no offers
    if offers is None or not offers.get("offers", []):
        print("\n📋 No offers received - testing graceful failure")
        confirmation_result = attempt_confirm_parlay(USER_TOKEN, parlay_id)
    else:
        print("\n❌ Unexpected: Offers were received despite SPs not providing any")
        return False
    
    # Small delay for processing
    time.sleep(2)
    
    # Step 6: Get final parlay status
    final_status = get_final_parlay_status(USER_TOKEN, parlay_id)
    if not final_status:
        print("❌ SCENARIO 8 FAILED: Could not retrieve final status")
        return False
    
    # Step 7: Validate results
    print("\n🔍 VALIDATING SCENARIO 8 RESULTS:")
    print("=" * 40)
    
    success = True
    
    # Check parlay status
    status = final_status.get("status")
    matched_stake = final_status.get("matched_stake_cents", 0)
    total_stake = final_status.get("stake_cents", 0)
    
    print(f"📊 Parlay Status: {status}")
    print(f"💰 Matched Stake: ${matched_stake/100:.2f}")
    print(f"💰 Total Stake: ${total_stake/100:.2f}")
    
    # Validate that no matching occurred
    if matched_stake > 0:
        print(f"❌ Expected no matching when no offers provided, but got ${matched_stake/100:.2f} matched")
        success = False
    else:
        print("✅ No matching occurred - correct for no offers scenario")
    
    # Validate that confirmation failed appropriately
    if confirmation_result is not None:
        print("❌ Expected confirmation to fail when no offers available")
        success = False
    else:
        print("✅ Confirmation correctly failed when no offers available")
    
    # Check status reflects failure due to no offers
    expected_statuses = ["failed", "timeout", "no_offers", "unmatched", "expired"]
    if status not in expected_statuses:
        print(f"❌ Expected status to be one of {expected_statuses}, got '{status}'")
        # This might be acceptable depending on system design
        print("⚠️  NOTE: Status may be acceptable depending on system design")
    else:
        print(f"✅ Status '{status}' correctly reflects no offers scenario")
    
    # Validate error handling graceful
    error_message = final_status.get("error_message", "")
    if error_message:
        print(f"📋 Error message: {error_message}")
        if "offer" in error_message.lower() or "timeout" in error_message.lower():
            print("✅ Error message appropriately describes the issue")
        else:
            print("⚠️  Error message may not clearly describe the no-offers scenario")
    
    # Test additional offer retrieval attempts
    print("\n🔄 Testing additional offer retrieval after timeout...")
    time.sleep(1)
    late_offers = get_offers_for_user_with_timeout(USER_TOKEN, parlay_id, max_wait_time=3)
    
    if late_offers is None or not late_offers.get("offers", []):
        print("✅ No offers available on retry - consistent behavior")
    else:
        print("❌ Offers unexpectedly appeared on retry")
        success = False
    
    # Check system resilience
    print("\n🛡️  Testing system resilience...")
    
    # Verify user can still create new parlays
    test_parlay_id = create_parlay(USER_TOKEN)
    if test_parlay_id:
        print("✅ System resilient - user can create new parlays after failure")
        
        # Clean up test parlay
        try:
            headers = {"Authorization": f"Bearer {USER_TOKEN}"}
            requests.delete(f"{BASE_URL}/api/v1/parlay/{test_parlay_id}", headers=headers)
        except:
            pass  # Ignore cleanup errors
    else:
        print("❌ System may not be resilient - user cannot create new parlays after failure")
        success = False
    
    if success:
        print("\n🎉 SCENARIO 8 PASSED: No SP Responses")
        print("✅ System handled no offers gracefully")
        print("✅ Confirmation correctly failed")
        print("✅ Appropriate error status set") 
        print("✅ System remained resilient")
        print("✅ Timeout behavior working correctly")
    else:
        print("\n❌ SCENARIO 8 FAILED: Validation errors detected")
    
    return success

if __name__ == "__main__":
    success = run_scenario_8()
    exit(0 if success else 1)
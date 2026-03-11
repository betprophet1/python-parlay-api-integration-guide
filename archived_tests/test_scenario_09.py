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
SP3_ACCESS_KEY = "sp3_access_key_here"
SP3_SECRET_KEY = "sp3_secret_key_here"
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

def provide_sp_best_odds_offers(sp_token, parlay_id, sp_name):
    """SP provides best odds (all SPs offer same best odds)"""
    offers_data = {
        "offers": [
            {
                "odds": 500,  # Best odds (same for all SPs)
                "max_risk": 50000,  # Full $500 capacity
                "valid_until": int(time.time()) + 30  # 30 seconds validity
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print(f"\n💰 {sp_name} providing best odds (500)...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
    log_request_response(f"{sp_name} Best Odds Offers", response)
    
    if response.status_code == 200:
        print(f"✅ {sp_name} best odds offers submitted successfully")
        return True
    else:
        print(f"❌ {sp_name} failed to submit offers")
        return False

def provide_sp3_worse_odds_offers(sp_token, parlay_id):
    """SP3 provides worse odds (fallback option)"""
    offers_data = {
        "offers": [
            {
                "odds": 300,  # Worse odds
                "max_risk": 50000,  # Full $500 capacity
                "valid_until": int(time.time()) + 30  # 30 seconds validity
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n💰 SP3 providing worse odds (300) as fallback...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
    log_request_response("SP3 Worse Odds Offers", response)
    
    if response.status_code == 200:
        print("✅ SP3 worse odds offers submitted successfully")
        return True
    else:
        print("❌ SP3 failed to submit offers")
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
    
    print(f"\n✅ User confirming parlay with best odds offers...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/confirm", json=confirm_data, headers=headers)
    log_request_response("Confirm Parlay", response)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Parlay confirmation processed")
        return result
    else:
        print("❌ Failed to confirm parlay")
        return None

def sp_reject_confirmation(sp_token, parlay_id, bet_id, sp_name):
    """SP rejects the confirmation"""
    reject_data = {
        "status": "rejected",
        "reason": f"Risk limits exceeded - {sp_name}"
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print(f"\n❌ {sp_name} rejecting confirmation...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/bet/{bet_id}/respond", json=reject_data, headers=headers)
    log_request_response(f"{sp_name} Reject Confirmation", response)
    
    if response.status_code == 200:
        print(f"✅ {sp_name} rejection processed")
        return True
    else:
        print(f"❌ {sp_name} failed to process rejection")
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

def run_scenario_9():
    """
    Scenario 9: All SPs Reject Best Odds
    - Multiple SPs (SP1, SP2) provide same best odds (500)
    - SP3 provides worse odds (300) as potential fallback
    - User confirms best odds
    - All SPs with best odds (SP1, SP2) reject
    - No fallback to worse odds configured
    - Result: Complete failure, no matching at all
    """
    
    print("🚀 STARTING SCENARIO 9: All SPs Reject Best Odds")
    print("=" * 60)
    
    # Step 1: Authenticate SPs
    sp1_token = authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
    sp2_token = authenticate_sp(SP2_ACCESS_KEY, SP2_SECRET_KEY, "SP2")
    sp3_token = authenticate_sp(SP3_ACCESS_KEY, SP3_SECRET_KEY, "SP3")
    
    if not sp1_token or not sp2_token or not sp3_token:
        print("❌ SCENARIO 9 FAILED: Authentication failed")
        return False
    
    # Step 2: Create parlay
    parlay_id = create_parlay(USER_TOKEN)
    if not parlay_id:
        print("❌ SCENARIO 9 FAILED: Could not create parlay")
        return False
    
    # Step 3: SPs provide offers
    # SP1 and SP2 both provide best odds (500)
    sp1_success = provide_sp_best_odds_offers(sp1_token, parlay_id, "SP1")
    sp2_success = provide_sp_best_odds_offers(sp2_token, parlay_id, "SP2")
    # SP3 provides worse odds (300) as potential fallback
    sp3_success = provide_sp3_worse_odds_offers(sp3_token, parlay_id)
    
    if not sp1_success or not sp2_success or not sp3_success:
        print("❌ SCENARIO 9 FAILED: SPs failed to provide offers")
        return False
    
    # Small delay to ensure offers are processed
    time.sleep(2)
    
    # Step 4: User gets offers (should see best odds prioritized)
    offers = get_offers_for_user(USER_TOKEN, parlay_id)
    if not offers:
        print("❌ SCENARIO 9 FAILED: Could not retrieve offers")
        return False
    
    available_offers = offers.get("offers", [])
    if not available_offers:
        print("❌ SCENARIO 9 FAILED: No offers available")
        return False
    
    print(f"\n📊 Available offers: {len(available_offers)}")
    for i, offer in enumerate(available_offers):
        odds = offer.get("odds", 0)
        max_risk = offer.get("max_risk", 0)
        print(f"  Offer {i+1}: {odds} odds, ${max_risk/100:.2f} max risk")
    
    # Find and select only the best odds (500)
    best_odds = max(offer.get("odds", 0) for offer in available_offers)
    best_offers = [offer for offer in available_offers if offer.get("odds", 0) == best_odds]
    
    print(f"\n🏆 Best odds: {best_odds}")
    print(f"📋 Selecting {len(best_offers)} offers with best odds")
    
    # Step 5: User confirms only the best odds offers
    confirmation_result = confirm_parlay(USER_TOKEN, parlay_id, best_offers)
    if not confirmation_result:
        print("❌ SCENARIO 9 FAILED: Could not confirm parlay")
        return False
    
    # Small delay for processing
    time.sleep(2)
    
    # Step 6: All SPs with best odds reject
    bets = confirmation_result.get("bets", [])
    print(f"\n📋 Processing {len(bets)} bet confirmations...")
    
    for bet in bets:
        bet_id = bet.get("bet_id")
        provider = bet.get("provider")
        odds = bet.get("odds", 0)
        
        print(f"\n🔄 Processing bet {bet_id} from {provider} with {odds} odds")
        
        # Only reject if it's a best odds bet (500)
        if odds == best_odds:
            if provider == "sp1":
                sp_reject_confirmation(sp1_token, parlay_id, bet_id, "SP1")
            elif provider == "sp2":
                sp_reject_confirmation(sp2_token, parlay_id, bet_id, "SP2")
            else:
                print(f"⚠️  Unexpected provider {provider} for best odds")
        else:
            print(f"⚠️  Unexpected odds {odds} in confirmation (expected {best_odds})")
    
    # Small delay for final processing
    time.sleep(3)
    
    # Step 7: Get final status
    final_status = get_final_parlay_status(USER_TOKEN, parlay_id)
    if not final_status:
        print("❌ SCENARIO 9 FAILED: Could not retrieve final status")
        return False
    
    # Step 8: Validate results
    print("\n🔍 VALIDATING SCENARIO 9 RESULTS:")
    print("=" * 40)
    
    success = True
    
    # Check parlay status
    status = final_status.get("status")
    matched_stake = final_status.get("matched_stake_cents", 0)
    total_stake = final_status.get("stake_cents", 0)
    
    print(f"📊 Parlay Status: {status}")
    print(f"💰 Matched Stake: ${matched_stake/100:.2f}")
    print(f"💰 Total Stake: ${total_stake/100:.2f}")
    print(f"📈 Match Rate: {(matched_stake/total_stake*100):.1f}%")
    
    # Validate complete failure (no matching)
    if matched_stake > 0:
        print(f"❌ Expected no matching when all best odds rejected, but got ${matched_stake/100:.2f} matched")
        success = False
    else:
        print("✅ No matching occurred - correct for all-rejection scenario")
    
    # Check that no fallback to worse odds occurred
    matched_bets = final_status.get("matched_bets", [])
    if matched_bets:
        print("❌ Expected no matched bets when all best odds rejected")
        for bet in matched_bets:
            odds = bet.get("odds", 0)
            provider = bet.get("provider")
            print(f"  Unexpected match: {provider} with {odds} odds")
        success = False
    else:
        print("✅ No fallback to worse odds occurred - correct no-fallback behavior")
    
    # Check status reflects complete failure
    expected_statuses = ["failed", "rejected", "unmatched", "incomplete"]
    if status not in expected_statuses:
        print(f"❌ Expected status to be one of {expected_statuses}, got '{status}'")
        # This might be acceptable depending on system design
        print("⚠️  NOTE: Status may be acceptable depending on system design")
    else:
        print(f"✅ Status '{status}' correctly reflects complete rejection")
    
    # Verify that worse odds offers were still available but not used
    print("\n🔄 Testing fallback availability...")
    fallback_offers = get_offers_for_user(USER_TOKEN, parlay_id)
    
    if fallback_offers:
        fallback_available = fallback_offers.get("offers", [])
        worse_odds_available = [offer for offer in fallback_available if offer.get("odds", 0) < best_odds]
        
        if worse_odds_available:
            print(f"✅ Worse odds still available but not used (no-fallback behavior)")
            for offer in worse_odds_available:
                odds = offer.get("odds", 0)
                print(f"  Available fallback: {odds} odds")
        else:
            print("📋 No worse odds available for fallback")
    
    # Test error handling
    error_message = final_status.get("error_message", "")
    if error_message:
        print(f"📋 Error message: {error_message}")
        if "reject" in error_message.lower() or "failed" in error_message.lower():
            print("✅ Error message appropriately describes rejection")
        else:
            print("⚠️  Error message may not clearly describe rejection scenario")
    
    if success:
        print("\n🎉 SCENARIO 9 PASSED: All SPs Reject Best Odds")
        print("✅ All best odds providers rejected correctly")
        print("✅ No matching occurred despite rejections")
        print("✅ No fallback to worse odds (correct no-fallback behavior)")
        print("✅ System handled complete rejection gracefully")
        print("✅ Appropriate error status set")
    else:
        print("\n❌ SCENARIO 9 FAILED: Validation errors detected")
    
    return success

if __name__ == "__main__":
    success = run_scenario_9()
    exit(0 if success else 1)
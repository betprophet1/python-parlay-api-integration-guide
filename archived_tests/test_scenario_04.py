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
    """Create parlay with large stake requiring multiple tiers"""
    parlay_data = {
        "stake_cents": 100000,  # $1000.00 - Large stake
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
    
    print("\n🎰 Creating large stake parlay request...")
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
    """SP1 provides best odds with multiple tiers"""
    offers_data = {
        "offers": [
            {
                "odds": 500,  # Best odds - Tier 1
                "max_risk": 25000,  # $250
                "valid_until": int(time.time()) + 30
            },
            {
                "odds": 450,  # Good odds - Tier 2
                "max_risk": 35000,  # $350
                "valid_until": int(time.time()) + 30
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n💰 SP1 providing multi-tier offers...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
    log_request_response("SP1 Offers", response)
    
    if response.status_code == 200:
        print("✅ SP1 multi-tier offers submitted successfully")
        return True
    else:
        print("❌ SP1 failed to submit offers")
        return False

def provide_sp2_offers(sp_token, parlay_id):
    """SP2 provides medium odds with multiple tiers"""
    offers_data = {
        "offers": [
            {
                "odds": 400,  # Medium odds - Tier 1
                "max_risk": 30000,  # $300
                "valid_until": int(time.time()) + 30
            },
            {
                "odds": 350,  # Lower odds - Tier 2
                "max_risk": 40000,  # $400
                "valid_until": int(time.time()) + 30
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n💰 SP2 providing multi-tier offers...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
    log_request_response("SP2 Offers", response)
    
    if response.status_code == 200:
        print("✅ SP2 multi-tier offers submitted successfully")
        return True
    else:
        print("❌ SP2 failed to submit offers")
        return False

def provide_sp3_offers(sp_token, parlay_id):
    """SP3 provides lower odds but high capacity"""
    offers_data = {
        "offers": [
            {
                "odds": 300,  # Lower odds but high capacity
                "max_risk": 50000,  # $500
                "valid_until": int(time.time()) + 30
            }
        ]
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print("\n💰 SP3 providing high capacity offers...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/offers", json=offers_data, headers=headers)
    log_request_response("SP3 Offers", response)
    
    if response.status_code == 200:
        print("✅ SP3 high capacity offers submitted successfully")
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

def sp_accept_confirmation(sp_token, parlay_id, bet_id, confirmed_stake, sp_name):
    """SP accepts the confirmation with full stake"""
    accept_data = {
        "status": "accepted",
        "confirmed_stake_cents": confirmed_stake
    }
    
    headers = {"Authorization": f"Bearer {sp_token}"}
    
    print(f"\n✅ {sp_name} accepting confirmation with ${confirmed_stake/100:.2f}...")
    response = requests.post(f"{BASE_URL}/api/v1/parlay/{parlay_id}/bet/{bet_id}/respond", json=accept_data, headers=headers)
    log_request_response(f"{sp_name} Accept Confirmation", response)
    
    if response.status_code == 200:
        print(f"✅ {sp_name} acceptance processed")
        return True
    else:
        print(f"❌ {sp_name} failed to process acceptance")
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

def run_scenario_4():
    """
    Scenario 4: Complete Multi-Odds Success
    - Multiple SPs provide multiple tiers of offers
    - Large stake ($1000) requires multiple tiers for full matching
    - All SPs accept their portions
    - Result: Full matching across multiple tiers and providers
    """
    
    print("🚀 STARTING SCENARIO 4: Complete Multi-Odds Success")
    print("=" * 60)
    
    # Step 1: Authenticate SPs
    sp1_token = authenticate_sp(SP1_ACCESS_KEY, SP1_SECRET_KEY, "SP1")
    sp2_token = authenticate_sp(SP2_ACCESS_KEY, SP2_SECRET_KEY, "SP2")
    sp3_token = authenticate_sp(SP3_ACCESS_KEY, SP3_SECRET_KEY, "SP3")
    
    if not sp1_token or not sp2_token or not sp3_token:
        print("❌ SCENARIO 4 FAILED: Authentication failed")
        return False
    
    # Step 2: Create large stake parlay
    parlay_id = create_parlay(USER_TOKEN)
    if not parlay_id:
        print("❌ SCENARIO 4 FAILED: Could not create parlay")
        return False
    
    # Step 3: SPs provide multi-tier offers
    sp1_success = provide_sp1_offers(sp1_token, parlay_id)
    sp2_success = provide_sp2_offers(sp2_token, parlay_id)
    sp3_success = provide_sp3_offers(sp3_token, parlay_id)
    
    if not sp1_success or not sp2_success or not sp3_success:
        print("❌ SCENARIO 4 FAILED: SPs failed to provide offers")
        return False
    
    # Small delay to ensure offers are processed
    time.sleep(2)
    
    # Step 4: User gets optimally blended offers
    offers = get_offers_for_user(USER_TOKEN, parlay_id)
    if not offers:
        print("❌ SCENARIO 4 FAILED: Could not retrieve offers")
        return False
    
    # Step 5: User confirms all available offers for full coverage
    available_offers = offers.get("offers", [])
    if not available_offers:
        print("❌ SCENARIO 4 FAILED: No offers available")
        return False
    
    print(f"\n📊 Available offers: {len(available_offers)}")
    for i, offer in enumerate(available_offers):
        odds = offer.get("odds", 0)
        max_risk = offer.get("max_risk", 0)
        print(f"  Offer {i+1}: {odds} odds, ${max_risk/100:.2f} max risk")
    
    # User selects all available offers to ensure full matching
    selected_offers = available_offers
    
    confirmation_result = confirm_parlay(USER_TOKEN, parlay_id, selected_offers)
    if not confirmation_result:
        print("❌ SCENARIO 4 FAILED: Could not confirm parlay")
        return False
    
    # Small delay for processing
    time.sleep(2)
    
    # Step 6: All SPs accept their portions
    bets = confirmation_result.get("bets", [])
    print(f"\n📋 Processing {len(bets)} bet confirmations...")
    
    for bet in bets:
        bet_id = bet.get("bet_id")
        provider = bet.get("provider")
        stake_cents = bet.get("stake_cents", 0)
        
        print(f"\n🔄 Processing bet {bet_id} from {provider} for ${stake_cents/100:.2f}")
        
        # Determine which SP token to use
        if provider == "sp1":
            sp_accept_confirmation(sp1_token, parlay_id, bet_id, stake_cents, "SP1")
        elif provider == "sp2":
            sp_accept_confirmation(sp2_token, parlay_id, bet_id, stake_cents, "SP2")
        elif provider == "sp3":
            sp_accept_confirmation(sp3_token, parlay_id, bet_id, stake_cents, "SP3")
    
    # Small delay for final processing
    time.sleep(3)
    
    # Step 7: Get final status
    final_status = get_final_parlay_status(USER_TOKEN, parlay_id)
    if not final_status:
        print("❌ SCENARIO 4 FAILED: Could not retrieve final status")
        return False
    
    # Step 8: Validate results
    print("\n🔍 VALIDATING SCENARIO 4 RESULTS:")
    print("=" * 40)
    
    success = True
    
    # Check if parlay is fully matched
    status = final_status.get("status")
    matched_stake = final_status.get("matched_stake_cents", 0)
    total_stake = final_status.get("stake_cents", 0)
    
    print(f"📊 Parlay Status: {status}")
    print(f"💰 Matched Stake: ${matched_stake/100:.2f}")
    print(f"💰 Total Stake: ${total_stake/100:.2f}")
    print(f"📈 Match Rate: {(matched_stake/total_stake*100):.1f}%")
    
    # Validate full matching
    if matched_stake != total_stake:
        print(f"❌ Expected full matching, got ${matched_stake/100:.2f} of ${total_stake/100:.2f}")
        success = False
    else:
        print("✅ Full matching achieved!")
    
    # Check that multiple providers were used
    matched_bets = final_status.get("matched_bets", [])
    providers_used = set()
    
    for bet in matched_bets:
        provider = bet.get("provider")
        if provider:
            providers_used.add(provider)
    
    print(f"🏢 Providers used: {sorted(list(providers_used))}")
    
    if len(providers_used) < 2:
        print("❌ Expected multiple providers for large stake")
        success = False
    else:
        print(f"✅ {len(providers_used)} providers utilized for optimal matching")
    
    # Check tier distribution
    total_tiers_used = len(matched_bets)
    print(f"📊 Total tiers/offers matched: {total_tiers_used}")
    
    if total_tiers_used < 3:
        print("❌ Expected multiple tiers for large stake")
        success = False
    else:
        print("✅ Multiple tiers utilized for complete coverage")
    
    if success:
        print("\n🎉 SCENARIO 4 PASSED: Complete Multi-Odds Success")
        print("✅ Full stake matching achieved")
        print("✅ Multiple providers utilized")
        print("✅ Multiple tiers utilized")
        print("✅ Optimal blending algorithm working correctly")
    else:
        print("\n❌ SCENARIO 4 FAILED: Validation errors detected")
    
    return success

if __name__ == "__main__":
    success = run_scenario_4()
    exit(0 if success else 1)
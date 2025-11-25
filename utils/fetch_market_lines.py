#!/usr/bin/env python3
"""
🔄 FRESH LINE ID EXTRACTOR

Fetches fresh market data from ALL active events using batch API and extracts valid line IDs for parlay testing.
Integrates the optimized batch market seeding approach from mm-api-integration-guide.
"""

import requests
import json
import sys
import os
from typing import List, Dict

# Add src directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import config

def authenticate() -> str:
    """Authenticate and get access token"""
    login_url = f"{config.BASE_URL}/partner/auth/login"
    
    # Use credentials from config
    request_body = {
        'access_key': config.MM_KEYS.get('access_key'),
        'secret_key': config.MM_KEYS.get('secret_key'),
    }
    
    try:
        response = requests.post(login_url, json=request_body)
        if response.status_code == 200:
            token = response.json()['data']['access_token']
            print("✅ Authentication successful")
            return token
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def fetch_market_data_batch(access_token: str) -> List[Dict]:
    """Fetch fresh market data using optimized batch API approach"""
    
    if not access_token:
        print("❌ No access token available")
        return []
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    all_lines = []
    
    # Step 1: Get all tournaments
    print("\n🌱 Fetching tournaments...")
    tournaments_url = f"{config.BASE_URL}/partner/mm/get_tournaments"
    
    try:
        tournaments_response = requests.get(tournaments_url, headers=headers)
        if tournaments_response.status_code != 200:
            print(f"❌ Failed to fetch tournaments: {tournaments_response.status_code}")
            return []
        
        all_tournaments = tournaments_response.json().get('data', {}).get('tournaments', [])
        print(f"✅ Found {len(all_tournaments)} tournaments")
        
        # Step 2: Process each tournament of interest
        events_url = f"{config.BASE_URL}/partner/mm/get_sport_events"
        multiple_markets_url = f"{config.BASE_URL}/partner/mm/get_multiple_markets"
        
        tournaments_processed = 0
        for tournament in all_tournaments:
            # Filter by tournaments of interest or load all
            if tournament['name'] not in config.TOURNAMENTS_INTERESTED and not config.LOAD_ALL_TOURNAMENTS:
                continue
            
            tournaments_processed += 1
            print(f"\n🏆 Processing: {tournament['name']}")
            
            # Get events for this tournament
            events_response = requests.get(events_url, params={'tournament_id': tournament['id']}, headers=headers)
            if events_response.status_code != 200:
                print(f"   ⚠️  Failed to fetch events for {tournament['name']}")
                continue
            
            events = events_response.json().get('data', {}).get('sport_events', [])
            if not events:
                print(f"   ℹ️  No active events")
                continue
            
            print(f"   📅 Found {len(events)} events")
            
            # Step 3: Batch fetch markets for all events in this tournament
            event_ids = ','.join([str(event['event_id']) for event in events])
            markets_response = requests.get(multiple_markets_url, params={'event_ids': event_ids}, headers=headers)
            
            if markets_response.status_code != 200:
                print(f"   ❌ Failed to fetch markets: {markets_response.status_code}")
                continue
            
            map_market_by_event_id = markets_response.json().get('data', {})
            
            # Step 4: Extract line IDs from markets
            lines_extracted = 0
            for event in events:
                event_id_str = str(event['event_id'])
                if event_id_str not in map_market_by_event_id:
                    continue
                
                markets = map_market_by_event_id[event_id_str]
                for market in markets:
                    market_id = market.get('id')
                    
                    # Handle both 'selections' and 'market_lines' structures
                    if 'selections' in market:
                        for selections_group in market.get('selections', []):
                            for selection in selections_group:
                                line_id = selection.get('line_id')
                                outcome_id = selection.get('outcome_id')
                                line = selection.get('line', 0)
                                
                                if line_id:  # Only add if lineID exists
                                    all_lines.append({
                                        "line": line,
                                        "lineId": line_id,
                                        "marketId": market_id,
                                        "outcomeId": outcome_id,
                                        "sportEventId": event['event_id']
                                    })
                                    lines_extracted += 1
                    
                    elif 'market_lines' in market:
                        for market_line in market.get('market_lines', []):
                            for selections_group in market_line.get('selections', []):
                                for selection in selections_group:
                                    line_id = selection.get('line_id')
                                    outcome_id = selection.get('outcome_id')
                                    line = selection.get('line', 0)
                                    
                                    if line_id:  # Only add if lineID exists
                                        all_lines.append({
                                            "line": line,
                                            "lineId": line_id,
                                            "marketId": market_id,
                                            "outcomeId": outcome_id,
                                            "sportEventId": event['event_id']
                                        })
                                        lines_extracted += 1
            
            print(f"   ✅ Extracted {lines_extracted} line IDs")
        
        print(f"\n{'='*60}")
        print(f"✅ Total: Extracted {len(all_lines)} valid line IDs from {tournaments_processed} tournaments")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error fetching market data: {e}")
        import traceback
        traceback.print_exc()
    
    return all_lines

def main():
    """Extract and save fresh line IDs using batch API approach"""
    
    print("="*60)
    print("🔄 FRESH LINE ID EXTRACTOR - BATCH MODE")
    print("="*60)
    print(f"📋 Target Tournaments: {config.TOURNAMENTS_INTERESTED}")
    print(f"🔄 Load All Tournaments: {config.LOAD_ALL_TOURNAMENTS}")
    print("="*60)
    
    # Authenticate
    access_token = authenticate()
    if not access_token:
        print("❌ Cannot proceed without authentication")
        return
    
    # Fetch market data using batch approach
    lines = fetch_market_data_batch(access_token)
    
    if not lines:
        print("\n⚠️  No lines extracted. Check your configuration and API connectivity.")
        return
    
    # Save to file
    output_file = "fresh_market_lines.json"
    with open(output_file, 'w') as f:
        json.dump(lines, f, indent=2)
    
    print(f"\n💾 Saved {len(lines)} lines to {output_file}")
    
    # Print sample
    if lines:
        print(f"\n📋 Sample lines (first 10):")
        for i, line in enumerate(lines[:10], 1):
            print(f"   {i}. Event: {line['sportEventId']}, Market: {line['marketId']}, Line: {line['line']}, LineID: {line['lineId']}")
    
    print(f"\n✅ Ready for parlay autoplay testing!")

if __name__ == "__main__":
    main()

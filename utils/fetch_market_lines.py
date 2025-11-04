#!/usr/bin/env python3
"""
🔄 FRESH LINE ID EXTRACTOR

Fetches fresh market data and extracts valid line IDs for parlay testing.
"""

import requests
import json
from typing import List, Dict

def fetch_market_data() -> List[Dict]:
    """Fetch fresh market data from both API endpoints"""
    
    base_url = "https://api-ss-sandbox.betprophet.co"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'authorization': 'testtoken',
        'x-currency': 'cash'
    }
    
    # Event IDs from both curl commands
    event_ids_1 = "60070917,60070921,60070922,60070919,60068288,60069069,60069070"
    event_ids_2 = "60069581,60069700,60068504,60069071,60068740,60069236,60069702"
    
    all_lines = []
    
    for event_ids in [event_ids_1, event_ids_2]:
        url = f"{base_url}/partner/v2/public/get_multiple_markets"
        params = {
            'market_types': 'moneyline,spread,total',
            'event_ids': event_ids
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                # Extract line IDs from the response
                for event in data.get('data', []):
                    event_id = event.get('eventId')
                    for market in event.get('markets', []):
                        market_id = market.get('id')
                        for selections_group in market.get('selections', []):
                            for selection in selections_group:
                                line_id = selection.get('lineID')
                                outcome_id = selection.get('id')
                                line = selection.get('line', 0)
                                
                                if line_id:  # Only add if lineID exists
                                    all_lines.append({
                                        "line": line,
                                        "lineId": line_id,
                                        "marketId": market_id,
                                        "outcomeId": outcome_id,
                                        "sportEventId": event_id
                                    })
            else:
                print(f"❌ Failed to fetch data: {response.status_code}")
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
    
    print(f"✅ Extracted {len(all_lines)} valid line IDs")
    return all_lines

def main():
    """Extract and save fresh line IDs"""
    lines = fetch_market_data()
    
    # Save to file
    output_file = "fresh_market_lines.json"
    with open(output_file, 'w') as f:
        json.dump(lines, f, indent=2)
    
    print(f"💾 Saved {len(lines)} lines to {output_file}")
    
    # Print sample
    if lines:
        print(f"\n📋 Sample lines (first 5):")
        for line in lines[:5]:
            print(f"   Event: {line['sportEventId']}, Market: {line['marketId']}, Line: {line['line']}")

if __name__ == "__main__":
    main()

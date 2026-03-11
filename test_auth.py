#!/usr/bin/env python3
"""Quick authentication test"""
import requests
import json

base_url = "https://api-ss-sandbox.betprophet.co"

# Test user auth
print("Testing user authentication...")
user_payload = {
    "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
    "email": "lam.tran+usr004@betprophet.co",
    "password": "Kh0ngbiet1"
}

response = requests.post(f"{base_url}/api/v1/auth/login", json=user_payload)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Success! Token: {data.get('accessToken', 'N/A')[:50]}...")
    user_token = data.get('accessToken')
    
    # Test creating a parlay with dummy lines
    print("\nTesting parlay creation...")
    with open('fresh_market_lines.json', 'r') as f:
        lines = json.load(f)
    
    # Pick 3 random lines from different events
    events_seen = set()
    test_lines = []
    for line in lines:
        event_id = line['sportEventId']
        if event_id not in events_seen:
            test_lines.append(line)
            events_seen.add(event_id)
            if len(test_lines) >= 3:
                break
    
    parlay_response = requests.post(
        f"{base_url}/parlay/api/v1/user/request",
        json={"marketLines": test_lines},
        headers={
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }
    )
    print(f"Parlay creation status: {parlay_response.status_code}")
    print(f"Response: {parlay_response.text[:200]}")
else:
    print(f"Failed: {response.text}")

#!/usr/bin/env python3
"""
User Token Generator

Quick utility to get fresh user authentication tokens for testing.
This replaces the need to manually run curl commands.

Usage: python get_user_token.py
"""

import requests
import json
import sys

def get_fresh_user_token():
    """Get a fresh user authentication token"""
    
    login_url = "https://api-ss-sandbox.betprophet.co/api/v1/auth/login"
    
    payload = {
        "device_id": "e9594640-f309-11ec-9ad8-b75190c1f3c5",
        "email": "lam.tran+usr004@betprophet.co", 
        "password": "Kh0ngbiet1"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print("🔐 Authenticating user...")
        response = requests.post(login_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            access_token = data.get("accessToken")
            refresh_token = data.get("refreshToken") 
            exp = data.get("exp")
            
            if access_token:
                print("✅ Authentication successful!")
                print(f"🎫 Access Token: {access_token}")
                print(f"📅 Expires: {exp}")
                
                # Also save to file for easy use
                with open("current_user_token.txt", "w") as f:
                    f.write(access_token)
                print(f"💾 Token saved to current_user_token.txt")
                
                return access_token
            else:
                print("❌ Authentication failed: No access token in response")
                print(f"Response: {data}")
                return None
                
        else:
            print(f"❌ Authentication failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.RequestException as e:
        print(f"❌ Network error during authentication: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def test_token_validity(token):
    """Test if the token is valid by making a simple API call"""
    
    # Try to get user orders (this should work with a valid token)
    test_url = "https://api-ss-sandbox.betprophet.co/parlay/api/v1/user/list"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{test_url}?limit=1", headers=headers)
        
        if response.status_code == 200:
            print("✅ Token is valid and working!")
            return True
        else:
            print(f"❌ Token validation failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Token validation error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 USER TOKEN GENERATOR")
    print("=" * 50)
    
    # Get fresh token
    token = get_fresh_user_token()
    
    if token:
        print(f"\n🧪 Testing token validity...")
        if test_token_validity(token):
            print(f"\n🎉 SUCCESS! Fresh user token ready for testing.")
            print(f"\n📋 To use in other scripts:")
            print(f"   USER_TOKEN = \"{token}\"")
        else:
            print(f"\n⚠️  Token generated but validation failed.")
    else:
        print(f"\n❌ Failed to generate user token.")
        sys.exit(1)

if __name__ == "__main__":
    main()
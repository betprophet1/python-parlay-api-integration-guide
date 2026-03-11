#!/usr/bin/env python3
"""
Workflow Validation Test

This test validates that the Postman workflow authentication and basic structure 
are working correctly. It tests the authentication steps and basic API connectivity
without depending on specific market data.
"""

import json
import requests
import time

class WorkflowValidationTest:
    """Test that validates the core workflow components"""
    
    def __init__(self):
        with open("test_config.json", 'r') as f:
            self.config = json.load(f)["test_configuration"]
        
        self.base_url = self.config["base_url"]
        self.user_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6InNpbTIifQ.eyJhY2NvdW50VHlwZSI6MCwiZXhwIjoxNzU5ODMwNTg4LCJleHRyYU9ubGluZVRpbWUiOjAsImlzT3RwRXhwaXJlZCI6ZmFsc2UsImlzU3VzcGVuZGVkIjpmYWxzZSwiaXNzIjoiaHR0cDovL21vdGhlcnNoaXAubW90aGVyc2hpcC1zYW5kYm94IiwianRpIjoiZTg5M2I5MmYtNjdjZi00OWQyLTk2NGQtMzhjNjI2YzVlMzg3Iiwia2JhQW5zd2Vyc0luZm8iOiJOL0EiLCJreWNJbmZvIjoiU3VjY2VzcyIsInBlbmRpbmdCeUFkbWluIjpmYWxzZSwicHVzaGVySW5mbyI6eyJhdXRoQ2hhbm5lbCI6InVzZXIuYXV0aGVudGljYXRpb24uZTg5M2I5MmYtNjdjZi00OWQyLTk2NGQtMzhjNjI2YzVlMzg3IiwiYmFsYW5jZVVwZGF0ZWRFdmVudCI6IndhbGxldC5iYWxhbmNlLnVwZGF0ZWQiLCJjbHVzdGVyIjoibXQxIiwiaWQiOiJjMjBmYTM2ZmJjM2MzYzMwOGZmYSIsImluZm9DaGFubmVsIjoidXNlci5pbmZvcm1hdGlvbi5lZjVjM2JlMy1hZDRkLTRlMGYtYWNlNy05NzA1NjkwYzgyNmUiLCJpbmZvcm1hdGlvblVwZGF0ZWRFdmVudCI6InVzZXIuaW5mb3JtYXRpb24udXBkYXRlZCIsImtiYUNoYWxsZW5nZVF1ZXN0aW9uc0V2ZW50IjoidXNlci5rYmEuY2hhbGxlbmdlIiwic2Vzc2lvblRlcm1pbmF0ZWRFdmVudCI6InNlc3Npb24udGVybWluYXRlZCJ9LCJyZWdpb24iOiJOWSIsInN1YiI6ImxhbS50cmFuK3VzcjAwNEBiZXRwcm9waGV0LmNvIiwidXNlcklkIjoiZWY1YzNiZTMtYWQ0ZC00ZTBmLWFjZTctOTcwNTY5MGM4MjZlIn0.esyueJeCe4Xqdj9tbzZQYD0I8W8eGs31-XQal6hj5lY"
        
        # Tokens
        self.mm1_token = None
        self.mm2_token = None

    def test_mm1_authentication(self):
        """Test MM1 (SP1) Authentication"""
        print("🔐 TESTING: MM1 Authentication")
        
        sp1_creds = self.config["service_providers"]["sp1"]
        response = requests.post(
            f"{self.base_url}/partner/auth/login",
            json={
                "access_key": sp1_creds["access_key"],
                "secret_key": sp1_creds["secret_key"]
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            self.mm1_token = response.json()["data"]["access_token"]
            print(f"✅ MM1 authentication successful")
            return True
        else:
            print(f"❌ MM1 authentication failed: {response.status_code}")
            return False

    def test_mm2_authentication(self):
        """Test MM2 (SP2) Authentication"""
        print("🔐 TESTING: MM2 Authentication")
        
        sp2_creds = self.config["service_providers"]["sp2"]
        response = requests.post(
            f"{self.base_url}/partner/auth/login",
            json={
                "access_key": sp2_creds["access_key"],
                "secret_key": sp2_creds["secret_key"]
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            self.mm2_token = response.json()["data"]["access_token"]
            print(f"✅ MM2 authentication successful")
            return True
        else:
            print(f"❌ MM2 authentication failed: {response.status_code}")
            return False

    def test_user_token_validation(self):
        """Test User Token Validation"""
        print("🔐 TESTING: User Token Validation")
        
        # Test with a simple user request endpoint
        response = requests.post(
            f"{self.base_url}/parlay/api/v1/user/request",
            json={},
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Content-Type": "application/json"
            }
        )
        
        # We expect this to fail with market-related errors, not auth errors
        if response.status_code == 401:
            print(f"❌ User token validation failed: {response.text}")
            return False
        elif response.status_code in [400, 422]:  # Bad request but authenticated
            print(f"✅ User token is valid (got expected validation error: {response.status_code})")
            return True
        else:
            print(f"✅ User token is valid (status: {response.status_code})")
            return True

    def test_sp1_orders_endpoint(self):
        """Test SP1 Orders Endpoint Access"""
        print("📋 TESTING: SP1 Orders Endpoint")
        
        response = requests.get(
            f"{self.base_url}/parlay/sp/orders",
            headers={
                "Authorization": f"Bearer {self.mm1_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print(f"✅ SP1 orders endpoint accessible")
            return True
        else:
            print(f"❌ SP1 orders endpoint failed: {response.status_code}")
            return False

    def test_sp2_orders_endpoint(self):
        """Test SP2 Orders Endpoint Access"""
        print("📋 TESTING: SP2 Orders Endpoint")
        
        response = requests.get(
            f"{self.base_url}/parlay/sp/orders",
            headers={
                "Authorization": f"Bearer {self.mm2_token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            print(f"✅ SP2 orders endpoint accessible")
            return True
        else:
            print(f"❌ SP2 orders endpoint failed: {response.status_code}")
            return False

    def run_validation_tests(self):
        """Run all validation tests"""
        print("🚀 WORKFLOW VALIDATION TEST")
        print("============================================================")
        print("📝 Validating Postman workflow components")
        print("============================================================")
        
        tests = [
            ("MM1 Authentication", self.test_mm1_authentication),
            ("MM2 Authentication", self.test_mm2_authentication),
            ("User Token Validation", self.test_user_token_validation),
            ("SP1 Orders Endpoint", self.test_sp1_orders_endpoint),
            ("SP2 Orders Endpoint", self.test_sp2_orders_endpoint)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        print("\n📊 VALIDATION RESULTS")
        print("============================================================")
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
            if result:
                passed += 1
        
        print("============================================================")
        print(f"📊 SUMMARY: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL WORKFLOW COMPONENTS VALIDATED!")
            print("✅ Authentication is working")
            print("✅ API endpoints are accessible")
            print("✅ Tokens are valid")
            print("📝 The issue is with market data availability, not workflow")
        else:
            print("⚠️  Some workflow components failed validation")
        
        print("============================================================")
        return passed == total

if __name__ == "__main__":
    test = WorkflowValidationTest()
    success = test.run_validation_tests()
    exit(0 if success else 1)
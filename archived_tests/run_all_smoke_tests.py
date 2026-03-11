#!/usr/bin/env python3
"""
🧪 Smoke Test Runner for All 10 Parlay Matching Flow Scenarios

Runs all test scenarios sequentially and reports results.
Based on TEST_SCENARIOS.md specification.
"""

import subprocess
import sys
import time
from datetime import datetime

# Test scenario mapping
TEST_SCENARIOS = {
    1: ("test_scenario_01.py", "Best Odds Tier - All Accept Success"),
    2: ("test_scenario_02.py", "Best Odds Tier - One Rejects STOP"),
    3: ("test_scenario_03.py", "Second Tier Matching with STOP"),
    4: ("test_scenario_04.py", "Complete Multi-Tier Success"),
    5: ("test_scenario_05.py", "Odds Expire Before User Confirmation"),
    6: (None, "Odds Expire During Matching Process ⚠️ CRITICAL - MISSING"),
    7: ("test_scenario_07.py", "Mixed Validity Periods"),
    8: ("test_scenario_08.py", "No SP Responses"),
    9: ("test_scenario_09.py", "All SPs Reject Best Tier"),
    10: ("test_scenario_10.py", "Stake Exceeds SP Capacity"),
}

def print_header():
    """Print test suite header"""
    print("\n" + "=" * 80)
    print("🧪 PARLAY MATCHING FLOW - SMOKE TEST SUITE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Scenarios: {len(TEST_SCENARIOS)}")
    print("=" * 80 + "\n")

def print_scenario_header(scenario_num, description):
    """Print individual test scenario header"""
    print("\n" + "-" * 80)
    print(f"📋 Test Scenario {scenario_num}: {description}")
    print("-" * 80)

def run_test(scenario_num, file_path, description):
    """Run a single test scenario"""
    print_scenario_header(scenario_num, description)
    
    if file_path is None:
        print("⚠️  WARNING: Test file not found - scenario not implemented")
        return "MISSING", 0
    
    try:
        print(f"▶️  Running: python {file_path}")
        start_time = time.time()
        
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout per test
        )
        
        duration = time.time() - start_time
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Determine result
        if result.returncode == 0:
            print(f"✅ PASSED (Duration: {duration:.2f}s)")
            return "PASSED", duration
        else:
            print(f"❌ FAILED (Exit code: {result.returncode}, Duration: {duration:.2f}s)")
            return "FAILED", duration
            
    except subprocess.TimeoutExpired:
        print("⏱️  TIMEOUT: Test exceeded 120 second limit")
        return "TIMEOUT", 120
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        return "ERROR", 0

def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r["status"] == "PASSED")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    missing = sum(1 for r in results if r["status"] == "MISSING")
    errors = sum(1 for r in results if r["status"] in ["ERROR", "TIMEOUT"])
    total = len(results)
    total_duration = sum(r["duration"] for r in results)
    
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Missing: {missing}")
    print(f"💥 Errors/Timeouts: {errors}")
    print(f"⏱️  Total Duration: {total_duration:.2f}s")
    
    # Detailed results
    print("\n" + "-" * 80)
    print("DETAILED RESULTS:")
    print("-" * 80)
    for r in results:
        status_emoji = {
            "PASSED": "✅",
            "FAILED": "❌",
            "MISSING": "⚠️",
            "ERROR": "💥",
            "TIMEOUT": "⏱️"
        }.get(r["status"], "❓")
        
        print(f"{status_emoji} Scenario {r['scenario']:2d}: {r['status']:8s} - {r['description']}")
    
    print("=" * 80)
    
    # Exit code based on results
    if missing > 0:
        print("\n⚠️  WARNING: Some test scenarios are missing!")
    if failed > 0 or errors > 0:
        print("\n❌ SMOKE TEST SUITE FAILED")
        return 1
    elif missing == 0 and passed == total:
        print("\n✅ ALL SMOKE TESTS PASSED")
        return 0
    else:
        print("\n⚠️  SMOKE TEST SUITE COMPLETED WITH WARNINGS")
        return 2

def main():
    """Main test runner"""
    print_header()
    
    results = []
    
    # Run each scenario
    for scenario_num, (file_path, description) in TEST_SCENARIOS.items():
        status, duration = run_test(scenario_num, file_path, description)
        results.append({
            "scenario": scenario_num,
            "status": status,
            "duration": duration,
            "description": description
        })
        
        # Small delay between tests
        if scenario_num < len(TEST_SCENARIOS):
            time.sleep(1)
    
    # Print summary and exit
    exit_code = print_summary(results)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

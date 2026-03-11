#!/usr/bin/env python3
"""
Automation Runner for All Test Scenarios

This script runs all individual test scenarios for automated testing purposes.
Each scenario can be run independently or as part of a suite.
"""

import subprocess
import sys
import os
from datetime import datetime

class TestRunner:
    def __init__(self):
        self.base_dir = "/Users/tranlam/Documents/GitHub/python-parlay-api-integration-guide"
        self.results = {
            "passed": 0,
            "failed": 0,
            "scenarios": {}
        }
        
        # Available individual test scripts
        self.test_scenarios = {
            1: "test_scenario_01.py",
            2: "test_scenario_02.py",
            3: "test_scenario_03.py",
            4: "test_scenario_04.py",
            5: "test_scenario_05.py",
            7: "test_scenario_07.py",
            8: "test_scenario_08.py",
            9: "test_scenario_09.py",
            10: "test_scenario_10.py"
        }
        
        # Comprehensive test
        self.comprehensive_test = "test_scenarios_comprehensive.py"

    def run_individual_scenario(self, scenario_id: int) -> bool:
        """Run an individual test scenario"""
        if scenario_id not in self.test_scenarios:
            print(f"❌ Scenario {scenario_id} not available")
            return False
            
        script_name = self.test_scenarios[scenario_id]
        script_path = os.path.join(self.base_dir, script_name)
        
        if not os.path.exists(script_path):
            print(f"❌ Test script {script_name} not found")
            return False
        
        print(f"\n🧪 Running Test Scenario {scenario_id}")
        print("="*60)
        
        try:
            result = subprocess.run([
                sys.executable, script_path
            ], cwd=self.base_dir, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Scenario {scenario_id} PASSED")
                self.results["passed"] += 1
                self.results["scenarios"][f"scenario_{scenario_id}"] = "PASSED"
                return True
            else:
                print(f"❌ Scenario {scenario_id} FAILED")
                print(f"Error: {result.stderr}")
                self.results["failed"] += 1
                self.results["scenarios"][f"scenario_{scenario_id}"] = "FAILED"
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Scenario {scenario_id} TIMEOUT")
            self.results["failed"] += 1
            self.results["scenarios"][f"scenario_{scenario_id}"] = "TIMEOUT"
            return False
            
        except Exception as e:
            print(f"❌ Scenario {scenario_id} ERROR: {str(e)}")
            self.results["failed"] += 1
            self.results["scenarios"][f"scenario_{scenario_id}"] = f"ERROR: {str(e)}"
            return False

    def run_comprehensive_test(self) -> bool:
        """Run the comprehensive test suite"""
        script_path = os.path.join(self.base_dir, self.comprehensive_test)
        
        if not os.path.exists(script_path):
            print(f"❌ Comprehensive test script not found: {self.comprehensive_test}")
            return False
        
        print(f"\n🚀 Running Comprehensive Test Suite")
        print("="*60)
        
        try:
            result = subprocess.run([
                sys.executable, script_path
            ], cwd=self.base_dir, timeout=600)  # 10 minute timeout for comprehensive test
            
            if result.returncode == 0:
                print("✅ Comprehensive Test Suite COMPLETED")
                return True
            else:
                print("❌ Comprehensive Test Suite FAILED")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Comprehensive Test Suite TIMEOUT")
            return False
            
        except Exception as e:
            print(f"❌ Comprehensive Test Suite ERROR: {str(e)}")
            return False

    def run_all_individual_tests(self):
        """Run all available individual test scenarios"""
        print("🎯 RUNNING ALL INDIVIDUAL TEST SCENARIOS")
        print("="*80)
        print(f"Available scenarios: {list(self.test_scenarios.keys())}")
        
        for scenario_id in sorted(self.test_scenarios.keys()):
            self.run_individual_scenario(scenario_id)
            
        self.print_results("Individual Tests")

    def print_results(self, test_type: str = "Tests"):
        """Print test results summary"""
        total = self.results["passed"] + self.results["failed"]
        
        print(f"\n📊 {test_type} Results Summary")
        print("="*60)
        print(f"Total: {total} | Passed: {self.results['passed']} | Failed: {self.results['failed']}")
        
        if self.results["scenarios"]:
            print("\nDetailed Results:")
            for scenario, result in self.results["scenarios"].items():
                status_icon = "✅" if "PASSED" in result else "❌"
                print(f"   {status_icon} {scenario}: {result}")

def main():
    runner = TestRunner()
    
    print("🚀 PARLAY API TEST AUTOMATION RUNNER")
    print("="*80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Base Directory: {runner.base_dir}")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "comprehensive":
            runner.run_comprehensive_test()
        elif command == "individual":
            runner.run_all_individual_tests()
        elif command.startswith("scenario"):
            try:
                scenario_id = int(command.replace("scenario", ""))
                runner.run_individual_scenario(scenario_id)
                runner.print_results(f"Scenario {scenario_id}")
            except ValueError:
                print("❌ Invalid scenario format. Use: scenario1, scenario2, etc.")
        else:
            print("❌ Unknown command. Available: comprehensive, individual, scenario<N>")
    else:
        print("📋 Usage:")
        print("  python run_all_tests.py comprehensive    # Run comprehensive test suite")
        print("  python run_all_tests.py individual       # Run all individual scenarios")
        print("  python run_all_tests.py scenario1        # Run specific scenario")
        print("\n🔧 Available Individual Scenarios:")
        for scenario_id, script in runner.test_scenarios.items():
            print(f"   - Scenario {scenario_id}: {script}")

if __name__ == "__main__":
    main()
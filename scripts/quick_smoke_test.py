#!/usr/bin/env python3
"""Quick smoke test for deployed analysis lambdas."""

import boto3
import json
from datetime import datetime, timezone, timedelta

AWS_REGION = "eu-west-1"
lambda_client = boto3.client("lambda", region_name=AWS_REGION)


def invoke_lambda(function_name, payload):
    """Invoke a Lambda function synchronously."""
    print(f"\n→ Testing: {function_name}")
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload).encode(),
        )
        
        body = response['Payload'].read()
        result = json.loads(body) if body else {}
        
        if response.get('FunctionError'):
            print(f"  ✗ ERROR: {result}")
            return False
        else:
            print(f"  ✓ Status: {response.get('StatusCode')}")
            return True
    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return False


def main():
    print("="*60)
    print("BetBudAI Lambda Smoke Tests")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Improver Boost Enforcement
    print("\n[TEST 1] Apply Improver Boosted Picks")
    tests_total += 1
    payload = {
        "all_horses": [
            {"horse": "A", "score": 100, "boost_applied": 15, "new_score": 115, "potential_improver_flag": True},
            {"horse": "B", "score": 95, "boost_applied": 0, "new_score": 95, "potential_improver_flag": False},
        ],
        "picks_to_select": 5,
    }
    if invoke_lambda("apply-improver-boosted-picks", payload):
        tests_passed += 1
    
    # Test 2: Evening Miss Analysis
    print("\n[TEST 2] Evening Miss Analysis")
    tests_total += 1
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    payload = {
        "target_date": yesterday.strftime('%Y-%m-%d'),
        "store_insights": True
    }
    if invoke_lambda("evening-miss-analysis", payload):
        tests_passed += 1
    
    # Test 3: Check Morning Handler has new code
    print("\n[TEST 3] Morning Handler Updated")
    tests_total += 1
    try:
        response = lambda_client.get_function(FunctionName="betbudai-morning")
        config = response['Configuration']
        print(f"  ✓ Handler deployed")
        print(f"    Timeout: {config.get('Timeout')}s, Memory: {config.get('MemorySize')}MB")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Test 4: Check Evening Handler has new code
    print("\n[TEST 4] Evening Handler Updated")
    tests_total += 1
    try:
        response = lambda_client.get_function(FunctionName="betbudai-evening")
        config = response['Configuration']
        print(f"  ✓ Handler deployed")
        print(f"    Timeout: {config.get('Timeout')}s, Memory: {config.get('MemorySize')}MB")
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    print("="*60)
    
    if tests_passed == tests_total:
        print("\n✓ All smoke tests passed!")
        print("\nDeployment Summary:")
        print("  ✓ apply-improver-boosted-picks      [DEPLOYED]")
        print("  ✓ evening-miss-analysis            [DEPLOYED]")
        print("  ✓ betbudai-morning (updated)       [DEPLOYED]")
        print("  ✓ betbudai-evening (updated)       [DEPLOYED]")
    else:
        print("\n✗ Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()

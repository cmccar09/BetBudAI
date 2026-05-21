#!/usr/bin/env python3
"""Smoke test for deployed analysis lambdas."""

import boto3
import json
from datetime import datetime, timezone, timedelta

AWS_REGION = "eu-west-1"
lambda_client = boto3.client("lambda", region_name=AWS_REGION)


def invoke_lambda(function_name, payload):
    """Invoke a Lambda function synchronously."""
    print(f"\nInvoking: {function_name}")
    print(f"Payload: {json.dumps(payload, default=str)[:100]}...")
    
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload).encode(),
    )
    
    body = response['Payload'].read()
    result = json.loads(body) if body else {}
    
    if response.get('FunctionError'):
        print(f"❌ ERROR: {result}")
        return None
    else:
        print(f"✓ Response status: {response.get('StatusCode')}")
        if 'body' in result:
            try:
                body_data = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
                print(f"✓ Result: {json.dumps(body_data, default=str)[:200]}...")
            except:
                print(f"✓ Result: {result}")
        else:
            print(f"✓ Result: {json.dumps(result, default=str)[:200]}...")
        return result


def test_improver_boost():
    """Test improver boost enforcement."""
    print("\n" + "="*60)
    print("TEST 1: Apply Improver Boosted Picks")
    print("="*60)
    
    payload = {
        "all_horses": [
            {
                "horse": "Horse A",
                "horse_id": "1",
                "score": 100,
                "original_score": 100,
                "boost_applied": 15,
                "new_score": 115,
                "potential_improver_flag": True,
                "trip_suitability_score": 80
            },
            {
                "horse": "Horse B",
                "horse_id": "2",
                "score": 95,
                "original_score": 95,
                "boost_applied": 0,
                "new_score": 95,
                "potential_improver_flag": False,
                "trip_suitability_score": 60
            },
            {
                "horse": "Horse C",
                "horse_id": "3",
                "score": 98,
                "original_score": 98,
                "boost_applied": 20,
                "new_score": 118,
                "potential_improver_flag": True,
                "trip_suitability_score": 85
            }
        ],
        "picks_to_select": 5,
        "require_improver_boost": False
    }
    
    result = invoke_lambda("apply-improver-boosted-picks", payload)
    if result:
        try:
            body = json.loads(result.get('body', '{}')) if isinstance(result.get('body'), str) else result.get('body', {})
            picks = body.get('official_picks', [])
            print(f"\nOfficial picks selected: {len(picks)}")
            for p in picks[:3]:
                print(f"  Rank {p.get('pick_rank')}: {p.get('horse')} (score={p.get('score')}, boost={p.get('boost_applied')})")
        except:
            pass


def test_evening_miss_analysis():
    """Test evening miss analysis."""
    print("\n" + "="*60)
    print("TEST 2: Evening Miss Analysis")
    print("="*60)
    
    # Test with yesterday's date
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    target_date = yesterday.strftime('%Y-%m-%d')
    
    payload = {
        "target_date": target_date,
        "store_insights": True
    }
    
    result = invoke_lambda("evening-miss-analysis", payload)
    if result:
        try:
            body = json.loads(result.get('body', '{}')) if isinstance(result.get('body'), str) else result.get('body', {})
            print(f"\nAnalysis Summary:")
            print(f"  Target Date: {body.get('target_date')}")
            print(f"  Total Races: {body.get('total_races')}")
            print(f"  Hits: {body.get('hits')}")
            print(f"  Misses: {body.get('misses')}")
            print(f"  Hit Rate: {body.get('hit_rate')}")
            
            patterns = body.get('patterns', {})
            if patterns.get('total_misses', 0) > 0:
                print(f"\nMiss Patterns:")
                print(f"  Distribution: {patterns.get('category_distribution')}")
                print(f"  Top Reason: {patterns.get('top_miss_reason')}")
        except Exception as e:
            print(f"  (No races or parsing error: {e})")


def test_morning_pipeline():
    """Test morning pipeline orchestrator."""
    print("\n" + "="*60)
    print("TEST 3: Morning Pipeline Integration")
    print("="*60)
    
    payload = {
        "stage": "morning",
        "target_date": datetime.now(timezone.utc).strftime('%Y-%m-%d'),
        "force_analysis": False,
        "run_optimizations": True
    }
    
    print(f"\nNote: Invoking full pipeline (this may take 60+ seconds)...")
    result = invoke_lambda("betbudai-morning", payload)
    if result:
        try:
            body = json.loads(result.get('body', '{}')) if isinstance(result.get('body'), str) else result.get('body', {})
            print(f"\nPipeline Result:")
            print(f"  Message: {body.get('message')}")
            print(f"  Steps OK: {body.get('steps_ok')}")
            print(f"  Steps Failed: {body.get('steps_failed')}")
            
            opt_steps = body.get('optimization_steps', {})
            if opt_steps:
                print(f"\nOptimization Steps:")
                if 'calculate-improver-boost-scores' in opt_steps:
                    print(f"  ✓ improver-boost computed")
                if 'apply-improver-boosted-picks' in opt_steps:
                    print(f"  ✓ improver-picks enforced")
                if 'compare-race-fields' in opt_steps:
                    print(f"  ✓ field-compare analyzed")
        except Exception as e:
            print(f"  Pipeline error: {e}")


def main():
    print("BetBudAI Analysis Lambda Smoke Tests")
    print("="*60)
    
    # Test individual lambdas
    test_improver_boost()
    test_evening_miss_analysis()
    
    # Test pipeline integration (optional - may be slow)
    try_pipeline = input("\n\nRun full morning pipeline test? (y/n): ").lower() == 'y'
    if try_pipeline:
        test_morning_pipeline()
    
    print("\n" + "="*60)
    print("Smoke tests complete!")
    print("="*60)
    
    print("\nNext steps:")
    print("  1. Monitor CloudWatch logs for any errors")
    print("  2. Check DynamoDB for updated picks with improver boost")
    print("  3. Verify evening pipeline runs at 20:00 UTC")


if __name__ == "__main__":
    main()

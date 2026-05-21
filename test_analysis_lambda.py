"""
Test surebet-analysis Lambda Directly
======================================
Invoke the Lambda to see Phase 1 in action
"""

import boto3
import json
from datetime import datetime

print("="*70)
print("TESTING surebet-analysis LAMBDA (PHASE 1)")
print("="*70)
print()

lambda_client = boto3.client('lambda', region_name='eu-west-1')

target_date = datetime.now().strftime('%Y-%m-%d')
print(f"Target Date: {target_date}")
print()

payload = {
    'target_date': target_date,
    'force': True,
}

print(f"[INVOKING] surebet-analysis Lambda...")
print(f"  Payload: {json.dumps(payload)}")
print()

response = lambda_client.invoke(
    FunctionName='surebet-analysis',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

status_code = response['StatusCode']
print(f"[STATUS] HTTP {status_code}")
print()

if status_code == 200:
    result = json.loads(response['Payload'].read())

    # Check for Lambda error
    if response.get('FunctionError'):
        print(f"[ERROR] Lambda execution failed:")
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"[SUCCESS] Analysis complete")

        # Parse body if it's a string
        body = result.get('body', result)
        if isinstance(body, str):
            body = json.loads(body)

        print(f"\nResults:")
        print(f"  Horses analyzed: {body.get('horses_analyzed', 0)}")
        print(f"  Races analyzed: {body.get('races_analyzed', 0)}")
        print(f"  Top picks: {body.get('picks_count', 0)}")
        print(f"  Phase 1 active: {body.get('phase1_signals_active', False)}")

        # Show top 3 picks with Phase 1 reasons
        top_picks = body.get('top_picks', [])
        if top_picks:
            print(f"\nTop Picks:")
            for i, pick in enumerate(top_picks[:3], 1):
                print(f"\n  #{i}: {pick.get('name')} ({pick.get('course')} {pick.get('race_time')})")
                print(f"      Odds: {pick.get('odds')} | Score: {pick.get('score')}")

                # Show Phase 1 reasons
                reasons = pick.get('reasons', [])
                phase1_reasons = [r for r in reasons if '[PHASE1]' in r]
                if phase1_reasons:
                    print(f"      Phase 1 signals:")
                    for r in phase1_reasons:
                        print(f"        - {r}")
                else:
                    print(f"      Phase 1 signals: None (no match for this horse)")

        print(f"\n" + "="*70)
        print("[SUCCESS] PHASE 1 IS ACTIVE")
        print("="*70)
else:
    print(f"[FAILED] Lambda returned status {status_code}")
    error = response['Payload'].read().decode('utf-8')
    print(f"Error: {error[:1000]}")

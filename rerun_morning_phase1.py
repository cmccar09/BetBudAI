"""
Re-run Morning Pipeline with Phase 1 Signals
=============================================
Triggers morning pipeline to regenerate today's picks with Phase 1 active
"""

import boto3
import json
from datetime import datetime

print("="*70)
print("RE-RUNNING MORNING PIPELINE WITH PHASE 1 SIGNALS")
print("="*70)
print()

lambda_client = boto3.client('lambda', region_name='eu-west-1')

target_date = datetime.now().strftime('%Y-%m-%d')
print(f"Target Date: {target_date}")
print(f"Pipeline: betbudai-morning")
print()

payload = {
    'target_date': target_date,
    'force_rerun': True,  # Force re-analysis even if already run today
}

print(f"[INVOKING] betbudai-morning Lambda...")
print(f"  Payload: {json.dumps(payload)}")
print(f"  This will take 2-5 minutes...")
print()

response = lambda_client.invoke(
    FunctionName='betbudai-morning',
    InvocationType='RequestResponse',  # Wait for completion
    Payload=json.dumps(payload)
)

status_code = response['StatusCode']
print(f"[STATUS] HTTP {status_code}")

if status_code == 200:
    result = json.loads(response['Payload'].read())
    print(f"\n[SUCCESS] Morning pipeline completed")
    print(f"\nResponse:")
    print(json.dumps(result, indent=2, default=str)[:1000])

    print(f"\n" + "="*70)
    print("[COMPLETE] PHASE 1 SIGNALS APPLIED TO TODAY'S PICKS")
    print("="*70)
    print(f"\nCheck results:")
    print(f"  File: TODAYS_PICKS_2026-05-20.md")
    print(f"  Look for: [PHASE1] tags in pick reasons")
    print(f"\nExpected improvements:")
    print(f"  - Run style + pace match bonuses/penalties")
    print(f"  - Jockey upgrade detections")
    print(f"  - Score increases of +10-22pts on relevant picks")
else:
    print(f"\n[FAILED] Pipeline returned status {status_code}")
    error = response['Payload'].read().decode('utf-8')
    print(f"Error: {error[:500]}")

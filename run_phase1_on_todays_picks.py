"""
Run Phase 1 Analysis on Today's Picks NOW
==========================================
Re-analyzes today's races with Phase 1 signals and shows results
"""

import boto3
import json
from datetime import datetime, timezone

print("="*80)
print("RUNNING PHASE 1 ANALYSIS ON TODAY'S PICKS")
print("="*80)
print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
print()

lambda_client = boto3.client('lambda', region_name='eu-west-1')
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

target_date = datetime.now(timezone.utc).strftime('%Y-%m-%d')

# Step 1: Trigger complete morning pipeline with force flag
print(f"[STEP 1/2] Re-running morning pipeline with Phase 1...")
print(f"  Date: {target_date}")
print(f"  Force: True (override existing)")
print()

payload = {
    'target_date': target_date,
    'force_analysis': True,  # Force re-analysis
    'stage': 'morning'
}

print(f"[INVOKING] betbudai-morning Lambda...")

try:
    response = lambda_client.invoke(
        FunctionName='betbudai-morning',
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )

    status_code = response['StatusCode']
    result = json.loads(response['Payload'].read())

    print(f"[STATUS] HTTP {status_code}")

    if status_code == 200:
        body = result.get('body')
        if isinstance(body, str):
            body = json.loads(body)

        message = body.get('message', 'Unknown')
        steps_ok = body.get('steps_ok', 0)
        steps_failed = body.get('steps_failed', 0)
        errors = body.get('errors', [])

        print(f"[RESULT] {message}")
        print(f"  Steps OK: {steps_ok}")
        print(f"  Steps Failed: {steps_failed}")

        if errors:
            print(f"\n[ERRORS]:")
            for error in errors:
                print(f"  - {error.get('function')}: {error.get('error')[:100]}")

        if steps_failed == 0:
            print(f"\n[SUCCESS] Pipeline completed successfully!")
        else:
            print(f"\n[WARNING] Pipeline completed with {steps_failed} failures")

    else:
        print(f"[ERROR] Pipeline returned status {status_code}")
        print(json.dumps(result, indent=2, default=str)[:500])

except Exception as e:
    print(f"[ERROR] Failed to invoke pipeline: {e}")
    import sys
    sys.exit(1)

# Step 2: Retrieve and display today's picks with Phase 1 analysis
print(f"\n[STEP 2/2] Retrieving today's picks with Phase 1 analysis...")
print()

try:
    # Scan for today's picks
    response = table.scan(
        FilterExpression='#dt = :date',
        ExpressionAttributeNames={'#dt': 'date'},
        ExpressionAttributeValues={':date': target_date},
        Limit=100
    )

    items = response.get('Items', [])

    if not items:
        print(f"[WARNING] No items found for {target_date}")
        print(f"  This may take a few seconds to propagate to DynamoDB")
        print(f"  Try running this script again in 30 seconds")
    else:
        print(f"[FOUND] {len(items)} items for {target_date}")

        # Look for pick data
        picks_items = [
            item for item in items
            if 'picks' in item or 'all_horses' in item or item.get('bet_date', '').startswith('PICK')
        ]

        if picks_items:
            print(f"\n[PICKS DATA FOUND] {len(picks_items)} pick-related items")

            for item in picks_items[:3]:  # Show first 3 items
                bet_date = item.get('bet_date', 'Unknown')
                print(f"\n--- Item: bet_date={bet_date} ---")

                # Check for picks field
                picks = item.get('picks', [])
                if picks:
                    print(f"  Picks found: {len(picks)}")

                    for i, pick in enumerate(picks[:3], 1):
                        print(f"\n  Pick #{i}:")
                        print(f"    Horse: {pick.get('name', 'Unknown')}")
                        print(f"    Course: {pick.get('course', 'Unknown')}")
                        print(f"    Time: {pick.get('race_time', 'Unknown')}")
                        print(f"    Odds: {pick.get('odds', 'Unknown')}")
                        print(f"    Score: {pick.get('score', 0)}")

                        # Check for Phase 1 signals
                        breakdown = pick.get('breakdown', {})
                        if 'pace_match' in breakdown:
                            print(f"    [PHASE1] Pace Match: {breakdown['pace_match']} pts")
                        if 'jockey_upgrade' in breakdown:
                            print(f"    [PHASE1] Jockey Upgrade: {breakdown['jockey_upgrade']} pts")

                        # Check reasons for Phase 1 tags
                        reasons = pick.get('reasons', [])
                        phase1_reasons = [r for r in reasons if '[PHASE1]' in str(r)]
                        if phase1_reasons:
                            print(f"    [PHASE1] Reasons:")
                            for r in phase1_reasons[:3]:
                                print(f"      - {r}")
                        elif 'pace_match' not in breakdown and 'jockey_upgrade' not in breakdown:
                            print(f"    [PHASE1] No signals triggered (conditions not met)")

                # Check for phase1_active flag
                phase1_active = item.get('phase1_active')
                if phase1_active is not None:
                    print(f"\n  Phase 1 Status: {'ACTIVE' if phase1_active else 'INACTIVE'}")
        else:
            print(f"\n[INFO] No pick-specific items found yet")
            print(f"  Items found are of types:")
            for item in items[:5]:
                print(f"    - bet_date: {item.get('bet_date', 'Unknown')}")

except Exception as e:
    print(f"[ERROR] Failed to retrieve picks: {e}")
    import traceback
    traceback.print_exc()

print(f"\n" + "="*80)
print("[COMPLETE] Phase 1 analysis run finished")
print("="*80)
print()
print("If no Phase 1 signals showed above, it means:")
print("  1. Today's horses don't meet Phase 1 criteria (no matching run styles/jockeys)")
print("  2. Or the data is still propagating (wait 30 seconds and re-run)")
print()
print("Phase 1 signals fire selectively - only when conditions are met:")
print("  - Run Style: Needs form_runs with race comments + identifiable style")
print("  - Jockey Upgrade: Needs elite jockey booking vs lower-tier previous jockeys")
print()
print("Tomorrow's picks (May 21, 08:30 UTC) will also include Phase 1 automatically.")

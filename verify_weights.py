"""
Verify Phase 1 Weights in DynamoDB
===================================
"""

import boto3
from datetime import datetime

print("="*70)
print("VERIFYING PHASE 1 WEIGHTS IN DYNAMODB")
print("="*70)
print()

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

try:
    response = table.get_item(
        Key={
            'bet_id': 'SYSTEM_WEIGHTS',
            'bet_date': 'CONFIG'
        }
    )

    if 'Item' in response:
        item = response['Item']
        version = int(item.get('version', 0))
        phase = item.get('phase', 'Unknown')
        updated = item.get('updated_at', 'Unknown')
        weights = item.get('weights', {})

        print(f"[SUCCESS] Weights found in SureBetBets table")
        print(f"  Version: {version}")
        print(f"  Phase: {phase}")
        print(f"  Updated: {updated}")
        print(f"  Total weights: {len(weights)}")

        # Check for Phase 1 weights
        print(f"\nPhase 1 Weights Check:")
        phase1_weights = {
            'pace_match_bonus': 12,
            'pace_mismatch_penalty': 8,
            'jockey_upgrade_bonus': 10,
            'jockey_downgrade_penalty': 8,
            'first_time_blinkers': 12,
            'first_time_visor': 10,
            'high_volume_gamble_bonus': 12,
            'low_liquidity_penalty': 5,
        }

        found_count = 0
        for weight_name, expected_val in phase1_weights.items():
            if weight_name in weights:
                actual_val = int(weights[weight_name])
                status = "[OK]" if actual_val == expected_val else f"[WARN] Expected {expected_val}"
                print(f"  {status} {weight_name}: {actual_val}")
                found_count += 1
            else:
                print(f"  [MISSING] {weight_name}")

        print(f"\nPhase 1 Status: {found_count}/{len(phase1_weights)} weights present")

        if found_count == len(phase1_weights):
            print(f"\n[SUCCESS] All Phase 1 weights deployed correctly!")
        elif found_count > 0:
            print(f"\n[WARNING] Some Phase 1 weights missing ({found_count}/{len(phase1_weights)})")
        else:
            print(f"\n[ERROR] No Phase 1 weights found!")

    else:
        print("[ERROR] Weights configuration not found in database")
        print("  Key: bet_id='SYSTEM_WEIGHTS', bet_date='CONFIG'")

except Exception as e:
    print(f"[ERROR] Failed to retrieve weights: {e}")

print("\n" + "="*70)

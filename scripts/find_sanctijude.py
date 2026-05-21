"""
Find Sanctijude pick and update to winner
"""

import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("SEARCHING FOR SANCTIJUDE")
print("="*80 + "\n")

today = '2026-05-20'

# Scan for Sanctijude (horse name search)
print("Scanning all picks for 'Sanctijude'...")
response = table.scan(
    FilterExpression='contains(horse, :name) AND bet_date = :date',
    ExpressionAttributeValues={
        ':name': 'Sanctijude',
        ':date': today
    }
)

items = response['Items']
print(f"Found {len(items)} matches\n")

if items:
    for item in items:
        print(f"Found: {item.get('horse')}")
        print(f"  Bet ID: {item.get('bet_id')}")
        print(f"  Course: {item.get('course')}")
        print(f"  Race Time: {item.get('race_time')}")
        print(f"  Score: {item.get('comprehensive_score', 0)}")
        print(f"  Odds: {item.get('odds', 0)}")
        print(f"  Current Result: {item.get('actual_result', 'PENDING')}")

        # Update to WIN if not already
        current_result = item.get('actual_result', 'PENDING')
        if current_result != 'WIN':
            print(f"\n  [UPDATING] Setting to WIN at odds 3.2")

            try:
                table.update_item(
                    Key={'bet_date': today, 'bet_id': item.get('bet_id')},
                    UpdateExpression='SET actual_result = :result, outcome_value = :value, settled_date = :date',
                    ExpressionAttributeValues={
                        ':result': 'WIN',
                        ':value': Decimal('3.2'),
                        ':date': datetime.utcnow().isoformat()
                    }
                )
                print(f"  [OK] Updated successfully!")
            except Exception as e:
                print(f"  [ERROR] Update failed: {e}")
        else:
            print(f"  [OK] Already marked as WIN")
else:
    print("[NOT FOUND] Sanctijude not in database")
    print("\nSearching for all 17:45 Gowran Park races...")

    response2 = table.scan(
        FilterExpression='bet_date = :date AND course = :course AND contains(race_time, :time)',
        ExpressionAttributeValues={
            ':date': today,
            ':course': 'Gowran Park',
            ':time': '16:45'  # UTC time for 17:45 Irish time
        }
    )

    if response2['Items']:
        print(f"\nFound {len(response2['Items'])} picks at 16:45 UTC / 17:45 Irish:")
        for item in response2['Items']:
            print(f"  - {item.get('horse')} (score: {item.get('comprehensive_score', 0)})")
    else:
        print("No picks found at 17:45")

print("\n" + "="*80 + "\n")

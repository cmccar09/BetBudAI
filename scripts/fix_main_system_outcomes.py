#!/usr/bin/env python3
"""
Fix main system outcomes for Rolltight and Ballymagreehan.
These horses WON but are marked as LOSS in the main system records.
"""

import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Main system bet IDs that need updating
main_system_winners = [
    {
        'bet_date': '2026-05-20',
        'bet_id': '2026-05-20T172000+0000_Gowran_Park_Rolltight',
        'horse': 'Rolltight',
        'odds': 2.375,
        'returns': 2.375
    },
    {
        'bet_date': '2026-05-20',
        'bet_id': '2026-05-20T175000+0000_Gowran_Park_Ballymagreehan',
        'horse': 'Ballymagreehan',
        'odds': 9.0,
        'returns': 9.0
    }
]

print("Fixing main system outcomes...")
print("="*60 + "\n")

for winner in main_system_winners:
    bet_id = winner['bet_id']
    horse = winner['horse']

    print(f"Updating {horse} (main system pick)...")

    try:
        response = table.update_item(
            Key={
                'bet_date': winner['bet_date'],
                'bet_id': bet_id
            },
            UpdateExpression='SET actual_result = :win, outcome_value = :returns, #out = :outcome, #res = :result',
            ExpressionAttributeNames={
                '#out': 'outcome',
                '#res': 'result'
            },
            ExpressionAttributeValues={
                ':win': 'WIN',
                ':returns': Decimal(str(winner['returns'])),
                ':outcome': 'win',
                ':result': 'WIN'
            },
            ReturnValues='ALL_NEW'
        )

        print(f"  [OK] {horse}")
        print(f"       outcome={response['Attributes'].get('outcome', 'N/A')}")
        print(f"       actual_result={response['Attributes'].get('actual_result', 'N/A')}")
        print(f"       result={response['Attributes'].get('result', 'N/A')}\n")

    except Exception as e:
        print(f"  [ERROR] Failed to update {horse}: {e}\n")

print("="*60)
print("Verification: All Rolltight and Ballymagreehan records")
print("="*60 + "\n")

# Query all records for these horses
for horse_name in ['Rolltight', 'Ballymagreehan']:
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        FilterExpression='contains(bet_id, :horse)',
        ExpressionAttributeValues={
            ':date': '2026-05-20',
            ':horse': horse_name
        }
    )

    print(f"{horse_name}:")
    for item in response['Items']:
        bet_id = item.get('bet_id', 'Unknown')
        outcome = item.get('outcome', 'MISSING')
        actual = item.get('actual_result', 'MISSING')
        is_featured = item.get('is_featured_meeting', False)
        tag = "[FEATURED]" if is_featured else "[MAIN]"

        print(f"  {tag:12s} {outcome:7s} actual_result={actual:6s}")
    print()

print("Done! The featured meeting API should now show correct results.")
print("Test: https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/featured-meeting?date=2026-05-20&course=Gowran+Park")

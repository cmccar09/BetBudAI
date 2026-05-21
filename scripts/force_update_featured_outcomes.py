#!/usr/bin/env python3
"""
Force update featured meeting outcomes in DynamoDB.
Update the 'outcome' field that the Lambda reads.
"""

import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Winners that need to be updated
winners = [
    {
        'bet_id': '2026-05-20_FEATURED_GOWRAN_18:20_Rolltight',
        'horse': 'Rolltight',
        'odds': 2.375,
        'returns': 2.375
    },
    {
        'bet_id': '2026-05-20_FEATURED_GOWRAN_18:50_Ballymagreehan',
        'horse': 'Ballymagreehan',
        'odds': 9.0,
        'returns': 9.0
    }
]

bet_date = '2026-05-20'

print("Updating featured meeting outcomes in DynamoDB...\n")

for winner in winners:
    bet_id = winner['bet_id']
    horse = winner['horse']

    print(f"Updating {horse}...")

    try:
        response = table.update_item(
            Key={
                'bet_date': bet_date,
                'bet_id': bet_id
            },
            UpdateExpression='SET actual_result = :win, outcome_value = :returns, #out = :outcome',
            ExpressionAttributeNames={
                '#out': 'outcome'
            },
            ExpressionAttributeValues={
                ':win': 'WIN',
                ':returns': Decimal(str(winner['returns'])),
                ':outcome': 'win'
            },
            ReturnValues='ALL_NEW'
        )

        print(f"  [OK] {horse} - outcome={response['Attributes'].get('outcome', 'N/A')}, actual_result={response['Attributes'].get('actual_result', 'N/A')}")

    except Exception as e:
        print(f"  [ERROR] Failed to update {horse}: {e}")

print("\n" + "="*60)
print("Verifying featured meeting picks...")
print("="*60 + "\n")

# Query all featured picks
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='is_featured_meeting = :featured',
    ExpressionAttributeValues={
        ':date': bet_date,
        ':featured': True
    }
)

for item in sorted(response['Items'], key=lambda x: x.get('bet_id', '')):
    horse = item.get('horse', 'Unknown')
    outcome = item.get('outcome', 'MISSING')
    actual = item.get('actual_result', 'MISSING')
    race_time = item.get('bet_id', '').split('_')[3] if '_' in item.get('bet_id', '') else 'N/A'

    status = "[WIN]" if outcome == 'win' else "[LOSS]"
    print(f"{race_time} {horse:20s} outcome={outcome:6s} actual_result={actual:6s} {status}")

print("\nDone! Check the API now:")
print("https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/featured-meeting?date=2026-05-20&course=Gowran+Park")

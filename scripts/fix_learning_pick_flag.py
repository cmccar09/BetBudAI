#!/usr/bin/env python3
"""
Remove is_learning_pick=True flag from featured winners.
Learning picks are excluded from ROI calculation.
"""

import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

bet_ids = [
    '2026-05-20T161000+0000_Gowran_Park_Gloriously_Glam',
    '2026-05-20T164500+0000_Gowran_Park_Sanctijude',
    '2026-05-20T172000+0000_Gowran_Park_Rolltight',
    '2026-05-20T175000+0000_Gowran_Park_Ballymagreehan'
]

print("Removing is_learning_pick flag from featured winners...")
print("="*60 + "\n")

for bet_id in bet_ids:
    response = table.get_item(Key={'bet_date': '2026-05-20', 'bet_id': bet_id})
    item = response.get('Item', {})
    horse = item.get('horse', 'Unknown')

    print(f"{horse}:")
    print(f"  is_learning_pick BEFORE: {item.get('is_learning_pick', 'MISSING')}")

    table.update_item(
        Key={'bet_date': '2026-05-20', 'bet_id': bet_id},
        UpdateExpression='SET is_learning_pick = :false',
        ExpressionAttributeValues={':false': False}
    )

    # Verify
    response = table.get_item(Key={'bet_date': '2026-05-20', 'bet_id': bet_id})
    item = response.get('Item', {})
    print(f"  is_learning_pick AFTER: {item.get('is_learning_pick', False)}")
    print(f"  [OK] Now counts toward ROI\n")

print("="*60)
print("Done! Featured winners should now be included in ROI.")
print("\nWait 5-10 seconds for Lambda cache to clear, then check:")
print("https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/results/cumulative-roi")

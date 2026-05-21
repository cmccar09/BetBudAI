#!/usr/bin/env python3
"""Check how many picks today meet the combined confidence threshold"""

import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-01-11'
response = table.scan(
    FilterExpression='#d = :today',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={':today': today}
)

items = response.get('Items', [])
print(f"\nTotal picks today: {len(items)}")

high_conf = [i for i in items if float(i.get('combined_confidence', 0)) >= 21]
print(f"Picks with combined_confidence >= 21: {len(high_conf)}")

if items:
    print(f"\nSample combined_confidence values:")
    for i in items[:10]:
        print(f"  {i.get('horse'):20} - {float(i.get('combined_confidence', 0)):.1f}")

print(f"\n✓ Check Results button will show {len(high_conf)} picks")

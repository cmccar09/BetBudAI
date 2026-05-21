#!/usr/bin/env python3
"""Clean up DynamoDB to keep only top 5 picks per day"""

import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('SureBetBets')

# Get today's date
today = datetime.now().strftime('%Y-%m-%d')

print(f"Cleaning picks for {today}...")

# Scan for today's picks
response = table.scan(
    FilterExpression='#d = :today',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={':today': today}
)

items = response.get('Items', [])
print(f"Found {len(items)} picks")

# Sort by confidence (descending)
sorted_items = sorted(items, key=lambda x: float(x.get('confidence', 0)), reverse=True)

# Keep top 5, delete the rest
top_5 = sorted_items[:5]
to_delete = sorted_items[5:]

print(f"\nKeeping top 5:")
for idx, item in enumerate(top_5, 1):
    print(f"  {idx}. {item.get('horse')} @ {item.get('course')} - {item.get('confidence')}% confidence")

if to_delete:
    print(f"\nDeleting {len(to_delete)} lower-confidence picks:")
    for item in to_delete:
        bet_id = item.get('bet_id')
        print(f"  - {item.get('horse')} @ {item.get('course')} - {item.get('confidence')}%")
        table.delete_item(Key={'bet_id': bet_id})
    print(f"\nDeleted {len(to_delete)} picks")
else:
    print("\nNo picks to delete (already 5 or fewer)")

print(f"\nDone! {len(top_5)} picks remaining for {today}")

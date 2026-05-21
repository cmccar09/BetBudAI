#!/usr/bin/env python3
"""Find today's picks in DynamoDB"""

import boto3
from boto3.dynamodb.conditions import Attr
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('SureBetBets')

# Scan all items with today's timestamp
today = '2026-01-09'

response = table.scan()
items = response.get('Items', [])

# Filter by timestamp
today_picks = [item for item in items if today in item.get('timestamp', '')]

print(f"Total items in table: {len(items)}")
print(f"Items with today's timestamp: {len(today_picks)}")

if today_picks:
    # Sort by confidence
    sorted_picks = sorted(today_picks, key=lambda x: float(x.get('confidence', 0)), reverse=True)
    
    print(f"\nAll picks for {today}:")
    for idx, pick in enumerate(sorted_picks, 1):
        print(f"{idx}. {pick.get('horse')} @ {pick.get('course')} - Confidence: {pick.get('confidence')}% - bet_id: {pick.get('bet_id')}")
    
    # Delete picks beyond top 5
    if len(sorted_picks) > 5:
        to_delete = sorted_picks[5:]
        print(f"\nDeleting {len(to_delete)} picks to keep only top 5:")
        for pick in to_delete:
            print(f"  Deleting: {pick.get('horse')}")
            table.delete_item(Key={'bet_id': pick.get('bet_id')})
        print("\nDone!")

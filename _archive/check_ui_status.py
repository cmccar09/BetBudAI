#!/usr/bin/env python3
"""Check if today's picks are in DynamoDB and accessible via API"""
import boto3
from datetime import datetime

# Check DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
print(f'\n=== DynamoDB Check ===')
print(f'Date: {today}')
print(f'Total picks: {len(items)}')

if items:
    print(f'\nFirst 5 picks:')
    sorted_items = sorted(items, key=lambda x: x.get('race_time', ''))
    for i, item in enumerate(sorted_items[:5], 1):
        print(f'{i}. {item["horse"]} @ {item["course"]}')
        print(f'   Time: {item.get("race_time", "N/A")}')
        print(f'   Odds: {item.get("odds", "N/A")}')
else:
    print('\n❌ NO PICKS IN DATABASE FOR TODAY')
    print('The UI will be empty because there are no picks to display.')

#!/usr/bin/env python3
"""Debug DynamoDB structure"""

import boto3
import json

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.scan(
    FilterExpression='#d = :today',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={':today': '2026-01-23'}
)

items = response.get('Items', [])
print(f'Found {len(items)} items for today')

if items:
    print('\nFirst item structure:')
    print(json.dumps(dict(items[0]), indent=2, default=str))

#!/usr/bin/env python3
import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-01-11'
response = table.scan(
    FilterExpression='#d = :today AND sport = :sport',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={':today': today, ':sport': 'greyhounds'}
)

items = response.get('Items', [])
print(f'\nGreyhound picks for today: {len(items)}')

if items:
    print('\nPicks:')
    for i in items[:10]:
        print(f'  {i.get("horse"):20} @ {i.get("course"):15} - {i.get("race_time")}')
else:
    print('No greyhound picks found yet. Task may still be running.')

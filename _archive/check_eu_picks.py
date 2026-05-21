#!/usr/bin/env python3
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
print(f'\nEU-WEST-1 - Total picks today: {len(items)}')

sources = set([i.get('source', 'unknown') for i in items])
print(f'Sources: {sources}')

greyhounds = [i for i in items if i.get('sport') == 'greyhounds']
horses = [i for i in items if i.get('sport') != 'greyhounds']

print(f'Horse picks: {len(horses)}')
print(f'Greyhound picks: {len(greyhounds)}')

if greyhounds:
    print('\nGreyhound picks:')
    for g in greyhounds[:5]:
        print(f'  {g.get("horse"):20} @ {g.get("course"):15}')

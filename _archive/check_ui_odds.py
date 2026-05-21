import boto3
import json

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# Get a few UI picks
resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-20'),
    FilterExpression='show_in_ui = :ui',
    ExpressionAttributeValues={':ui': True},
    Limit=3
)

print(f'\nFound {len(resp["Items"])} UI picks\n')

for item in resp['Items']:
    print(f'\n{item.get("horse")} @ {item.get("course")}')
    print(f'  odds: {item.get("odds")}')
    print(f'  decimal_odds: {item.get("decimal_odds")}')
    print(f'  p_win: {item.get("p_win")}')
    print(f'  p_place: {item.get("p_place")}')
    print(f'  roi: {item.get("roi")}')
    
    # Check what keys contain odds/probability data
    odds_keys = [k for k in item.keys() if 'odd' in k.lower() or 'prob' in k.lower() or 'p_' in k.lower() or 'roi' in k.lower()]
    if odds_keys:
        print(f'  Available odds/prob keys: {odds_keys}')

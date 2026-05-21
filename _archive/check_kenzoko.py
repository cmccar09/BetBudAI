#!/usr/bin/env python3
import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# Get Kenzoko
resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-19'),
    FilterExpression='horse = :h',
    ExpressionAttributeValues={':h': 'Kenzoko'}
)

if resp['Items']:
    item = resp['Items'][0]
    print('\nKENZOKO (87/100) Details:')
    print('='*60)
    print(f'Course: {item.get("course")}')
    print(f'Odds: {item.get("odds")}')
    print(f'comprehensive_score: {item.get("comprehensive_score")}')
    print(f'is_learning_pick: {item.get("is_learning_pick")}')
    print(f'show_in_ui: {item.get("show_in_ui")}')
    print(f'edge_percentage: {item.get("edge_percentage")}')
    print(f'reject_reason: {item.get("reject_reason")}')
    print(f'score_reasons: {item.get("score_reasons", [])}')
    print()
    
    if not item.get('is_learning_pick'):
        print('>>> NOT MARKED AS PICK!')
        print('>>> Checking why...')
else:
    print('Kenzoko not found')

# Check all high scorers
print('\nAll horses 75+:')
print('='*60)
resp2 = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-19')
)

high_scores = [i for i in resp2['Items'] if float(i.get('comprehensive_score', 0)) >= 75]
high_scores.sort(key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)

for item in high_scores:
    horse = item.get('horse')
    score = item.get('comprehensive_score')
    is_pick = item.get('is_learning_pick')
    show_ui = item.get('show_in_ui')
    print(f'{horse:30} {score}/100  Pick: {is_pick}  UI: {show_ui}')

#!/usr/bin/env python3
import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

print('Checking dates...\n')

for date in ['2026-02-19', '2026-02-20']:
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(date)
    )
    items = resp['Items']
    
    if items:
        scores = sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)
        max_score = float(scores[0].get('comprehensive_score', 0))
        picks = [i for i in items if i.get('is_learning_pick')]
        ui_picks = [i for i in items if i.get('show_in_ui')]
        
        print(f'{date}: {len(items)} horses analyzed')
        print(f'  Max score: {max_score}/100 ({scores[0].get("horse")})')
        print(f'  is_learning_pick: {len(picks)}')
        print(f'  show_in_ui: {len(ui_picks)}')
        
        if max_score >= 75:
            print(f'  75+ scores: {len([i for i in items if float(i.get("comprehensive_score", 0)) >= 75])}')
        print()

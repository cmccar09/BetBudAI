#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import boto3
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today),
    FilterExpression='show_in_ui = :ui',
    ExpressionAttributeValues={':ui': True}
)

picks = resp['Items']
picks.sort(key=lambda x: x.get('race_time', ''))

print(f'\nTODAY\'S UI PICKS ({len(picks)} horses)\n')
print('='*80)

for pick in picks:
    horse = pick.get('horse', '?')
    course = pick.get('course', '?')
    score = pick.get('comprehensive_score', 0)
    race_time = pick.get('race_time', '')
    odds = pick.get('odds', '?')
    recommended = pick.get('recommended_bet', False)
    
    # Extract time if ISO format
    if 'T' in race_time:
        time_str = race_time.split('T')[1][:5]  # Get HH:MM
    else:
        time_str = 'TBC'
    
    tag = '[SURE BET]' if recommended or score >= 85 else '[HIGH CONF]' if score >= 75 else ''
    
    print(f'{tag:12} {time_str}  {horse:30} @ {course:15}')
    print(f'             Score: {score}/100  Odds: {odds}')
    print()

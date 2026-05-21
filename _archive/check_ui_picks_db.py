#!/usr/bin/env python3
import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-05'))
items = resp.get('Items', [])

# Check for UI picks with both string and boolean
ui_picks = []
for i in items:
    show_ui = i.get('show_in_ui')
    if show_ui == True or str(show_ui).lower() == 'true':
        ui_picks.append(i)

print(f'Total items in database: {len(items)}')
print(f'UI picks (show_in_ui=True): {len(ui_picks)}')
print(f'\nUI Picks sorted by time:')

now = datetime.utcnow()
for pick in sorted(ui_picks, key=lambda x: str(x.get('race_time', ''))):
    race_time_str = str(pick.get('race_time', ''))
    course = pick.get('course', 'Unknown')
    horse = pick.get('horse', 'Unknown')
    score = pick.get('comprehensive_score', 0)
    rec_bet = pick.get('recommended_bet')
    
    # Check if race is in the future
    if 'T19:' in race_time_str or '2026-02-06' in race_time_str:
        status = "FUTURE"
    else:
        status = "PAST"
    
    rec_str = " [REC]" if (rec_bet == True or str(rec_bet).lower() == 'true') else ""
    print(f'  [{status:6}] {race_time_str:30} {course:20} {horse:25} {score}/100{rec_str}')

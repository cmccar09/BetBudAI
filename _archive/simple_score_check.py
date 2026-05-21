#!/usr/bin/env python3
"""Simple check of today's scores"""

import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = resp.get('Items', [])
sorted_items = sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)

print(f'\n{"="*80}')
print(f'TODAY: {today} - {len(items)} horses analyzed')
print(f'{"="*80}\n')

print('TOP 20 HIGHEST SCORES:')
print(f'{"-"*80}')
for i, item in enumerate(sorted_items[:20], 1):
    horse = item.get('horse', '?')
    score = float(item.get('comprehensive_score', 0))
    course = item.get('course', '?')
    odds = item.get('odds', 0)
    print(f'{i:2}. {horse:30} {score:5.1f}/100  @{odds:6}  {course}')

scores = [float(x.get('comprehensive_score', 0)) for x in items]

print(f'\n{"="*80}')
print('SCORE DISTRIBUTION:')
print(f'{"="*80}')
print(f'85+ (SURE THINGS):     {len([s for s in scores if s >= 85])}')
print(f'75-84 (HIGH CONF):     {len([s for s in scores if 75 <= s < 85])}')
print(f'60-74 (MEDIUM CONF):   {len([s for s in scores if 60 <= s < 75])}')
print(f'45-59 (LOW CONF):      {len([s for s in scores if 45 <= s < 60])}')
print(f'<45 (TOO LOW):         {len([s for s in scores if s < 45])}')

if sorted_items and float(sorted_items[0].get('comprehensive_score', 0)) < 75:
    print(f'\n{"="*80}')
    print('WHY NO "SURE BETS" TODAY:')
    print(f'{"="*80}')
    print(f'Highest score: {float(sorted_items[0].get("comprehensive_score", 0)):.1f}/100')
    print(f'Best horse: {sorted_items[0].get("horse", "?")}')
    print()
    print('No horse reached 75+ threshold (HIGH CONFIDENCE)')
    print('No horse reached 85+ threshold (SURE THING)')
    print()
    print('This is GOOD - system being appropriately cautious!')
    print('Better no bet than a bad bet.')

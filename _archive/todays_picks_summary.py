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
picks.sort(key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)

print(f'\n{"="*100}')
print(f'TODAY\'S HIGH-CONFIDENCE PICKS - {today}')
print(f'{"="*100}\n')

print(f'Total: {len(picks)} picks\n')

# Categorize
sure_bets = [p for p in picks if float(p.get('comprehensive_score', 0)) >= 75]  # BACKTESTED: 75+ = 45.4% ROI
high_conf = [p for p in picks if 75 <= float(p.get('comprehensive_score', 0)) < 85]
good = [p for p in picks if 70 <= float(p.get('comprehensive_score', 0)) < 75]

print(f'🎯 SURE BETS (85+): {len(sure_bets)}')
for i, p in enumerate(sure_bets, 1):
    time_str = p.get('race_time', '?')[:16] if p.get('race_time') else '?'
    print(f'  {i}. {p.get("horse"):30} @ {p.get("course"):15} {float(p.get("comprehensive_score", 0)):.0f}/100  {time_str}')

print(f'\n⭐ HIGH CONFIDENCE (75-84): {len(high_conf)}')
for i, p in enumerate(high_conf, 1):
    time_str = p.get('race_time', '?')[:16] if p.get('race_time') else '?'
    print(f'  {i}. {p.get("horse"):30} @ {p.get("course"):15} {float(p.get("comprehensive_score", 0)):.0f}/100  {time_str}')

print(f'\n✓ GOOD (70-74): {len(good)}')
for i, p in enumerate(good[:10], 1):  # Top 10
    time_str = p.get('race_time', '?')[:16] if p.get('race_time') else '?'
    print(f'  {i}. {p.get("horse"):30} @ {p.get("course"):15} {float(p.get("comprehensive_score", 0)):.0f}/100  {time_str}')

if len(good) > 10:
    print(f'  ... and {len(good) - 10} more')

print(f'\n{"="*100}\n')

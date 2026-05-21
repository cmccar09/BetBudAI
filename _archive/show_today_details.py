#!/usr/bin/env python3
"""Show today's picks with full details"""

import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.utcnow().strftime('%Y-%m-%d')
response = table.scan()
picks = [p for p in response['Items'] if p.get('bet_date', '').startswith(today)]

print(f'\n{"="*80}')
print(f'TODAY\'S PICKS ({today}) - FULL DETAILS')
print(f'{"="*80}\n')

if not picks:
    print('No picks for today yet.\n')
else:
    sorted_picks = sorted(picks, key=lambda x: float(x.get('confidence_score', 0)), reverse=True)
    
    for i, p in enumerate(sorted_picks, 1):
        horse = p.get('horse_name') or p.get('horse', 'Unknown')
        course = p.get('course', 'Unknown')
        print(f'{i}. {horse} @ {course}')
        print(f'   Time: {p.get("race_time", "TBA")}')
        print(f'   Odds: {p.get("odds", "N/A")} | Bet Type: {p.get("bet_type", "N/A")}')
        print(f'   Confidence: {p.get("confidence_score", 0)}% | Expected ROI: {p.get("expected_roi", 0)}%')
        print(f'   Reasoning: {p.get("reasoning", "No reasoning available")}')
        print()

print(f'{"="*80}\n')

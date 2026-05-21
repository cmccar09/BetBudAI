#!/usr/bin/env python3
"""Check Newcastle 16:50 picks in database"""

import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='us-east-1')
table = db.Table('SureBetBets')

# Get today's date
today = datetime.now().strftime('%Y-%m-%d')

# Scan for today's picks
resp = table.scan(
    FilterExpression='begins_with(bet_date, :d)',
    ExpressionAttributeValues={':d': today}
)

# Filter for Newcastle 16:50
newcastle_picks = [
    p for p in resp['Items']
    if 'newcastle' in p.get('course', '').lower()
    and '16:50' in p.get('race_time', '')
]

print(f"Found {len(newcastle_picks)} picks for Newcastle 16:50 GMT")
print("=" * 70)

for pick in newcastle_picks:
    print(f"\nHorse: {pick.get('horse')}")
    print(f"  Bet Type: {pick.get('bet_type')}")
    print(f"  Confidence: {pick.get('confidence')}")
    print(f"  ROI: {pick.get('roi')}%")
    print(f"  Decision Score: {pick.get('decision_score')}")
    print(f"  Race Time: {pick.get('race_time')}")
    print(f"  Course: {pick.get('course')}")

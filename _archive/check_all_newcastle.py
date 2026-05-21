#!/usr/bin/env python3
"""Check all Newcastle 16:50 picks in database"""

import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Get all items
resp = table.scan()

# Filter for Newcastle 16:50
newcastle_picks = [
    p for p in resp['Items']
    if 'newcastle' in p.get('course', '').lower()
    and '16:50' in p.get('race_time', '')
]

print(f"Total Newcastle 16:50 picks in database: {len(newcastle_picks)}\n")

for pick in sorted(newcastle_picks, key=lambda x: float(x.get('decision_score', 0)), reverse=True):
    print(f"{pick.get('horse'):20} | {pick.get('bet_type'):3} | Score: {pick.get('decision_score'):5} | ROI: {pick.get('roi'):6}% | Confidence: {pick.get('confidence')}")

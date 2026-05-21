#!/usr/bin/env python3
"""Check timestamps of Newcastle 16:50 picks"""

import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='us-east-1')
table = db.Table('SureBetBets')

resp = table.scan()

newcastle_picks = [
    p for p in resp['Items']
    if 'newcastle' in p.get('course', '').lower()
    and '16:50' in p.get('race_time', '')
]

print(f"Newcastle 16:50 picks (sorted by timestamp):\n")

for pick in sorted(newcastle_picks, key=lambda x: x.get('timestamp', '')):
    print(f"Horse: {pick.get('horse')}")
    print(f"  Bet ID: {pick.get('bet_id')}")
    print(f"  Timestamp: {pick.get('timestamp')}")
    print(f"  Bet Date: {pick.get('bet_date')}")
    print(f"  Selection ID: {pick.get('selection_id')}")
    print(f"  Market ID: {pick.get('market_id')}")
    print()

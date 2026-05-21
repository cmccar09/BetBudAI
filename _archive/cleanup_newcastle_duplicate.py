#!/usr/bin/env python3
"""Clean up Newcastle duplicate picks"""

import boto3

db = boto3.resource('dynamodb', region_name='us-east-1')
table = db.Table('SureBetBets')

# Delete Pop Favorite (lower scoring EW pick)
bet_id_to_delete = '2026-01-10T165000.000Z_Newcastle_Pop_Favorite'

print(f"Deleting duplicate pick: {bet_id_to_delete}")
table.delete_item(Key={'bet_id': bet_id_to_delete})
print("✓ Deleted successfully")

# Check remaining Newcastle 16:50 picks
resp = table.scan()
newcastle_picks = [
    p for p in resp['Items']
    if 'newcastle' in p.get('course', '').lower()
    and '16:50' in p.get('race_time', '')
]

print(f"\nRemaining Newcastle 16:50 picks: {len(newcastle_picks)}")
for pick in sorted(newcastle_picks, key=lambda x: float(x.get('decision_score', 0)), reverse=True):
    print(f"  {pick.get('horse'):20} | {pick.get('bet_type'):3} | Score: {pick.get('decision_score')}")

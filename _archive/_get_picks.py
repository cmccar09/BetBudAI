import boto3
from collections import defaultdict
ddb = boto3.resource('dynamodb', region_name='eu-west-1')
all_items = ddb.Table('CheltenhamPicks').scan().get('Items', [])

# Filter to today's records only (pick_date = 2026-03-09)
items = [p for p in all_items if str(p.get('pick_date', p.get('updated_at',''))[:10]) == '2026-03-09']
print(f"Today's records: {len(items)} out of {len(all_items)} total")

by_race = {}
for p in items:
    r = str(p.get('race_name'))
    if r not in by_race or float(p.get('score',0)) > float(by_race[r].get('score',0)):
        by_race[r] = p

print('TOP PICK PER RACE (today 2026-03-09):')
for race in sorted(by_race):
    p = by_race[race]
    score  = float(p.get('score',0))
    horse  = str(p.get('horse',''))
    trainer= str(p.get('trainer',''))
    second = str(p.get('second_horse_name',''))
    s2     = float(p.get('second_score', 0))
    gap    = score - s2
    print(f"  {score:.0f}  {horse:<30}  {trainer:<25}  gap={gap:.0f}  2nd={second}({s2:.0f})  |  {race}")

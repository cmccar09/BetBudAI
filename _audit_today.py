import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Query today
resp = table.query(KeyConditionExpression='bet_date = :d', ExpressionAttributeValues={':d': '2026-03-31'})

# Collect all show_in_ui=True picks
ui_picks = [item for item in resp['Items'] if item.get('show_in_ui') == True]

print(f"Total show_in_ui=True records today: {len(ui_picks)}")
print()

# Group by normalised race_time (first 16 chars) + course
from collections import defaultdict
races = defaultdict(list)
for p in ui_picks:
    rt = str(p.get('race_time', ''))[:16]
    key = (p.get('course',''), rt)
    races[key].append(p)

# Sort by race_time
for (course, rt), picks in sorted(races.items(), key=lambda x: x[0][1]):
    best = max(picks, key=lambda p: float(p.get('comprehensive_score') or 0))
    # Check retrospective
    created = str(best.get('created_at',''))[:16]
    race_local_time = rt[11:16] if len(rt) >= 16 else '?'
    created_time = created[11:16] if len(created) >= 16 else '?'
    
    def mins(t):
        try: h,m = t.split(':'); return int(h)*60+int(m)
        except: return 0
    
    retro = mins(created_time) > mins(race_local_time) + 30
    flag = ' *** RETROSPECTIVE ***' if retro else ''
    
    outcome = best.get('outcome', 'pending')
    print(f"  {rt[11:16]}  {course:<20}  {best.get('horse'):<30}  score={best.get('comprehensive_score')}  outcome={outcome}  created={created_time}{flag}")

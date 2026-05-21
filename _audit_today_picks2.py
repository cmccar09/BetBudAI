"""Full audit of today's UI picks — check all dates for race_time starting today"""
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from datetime import datetime, timezone

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = ddb.Table('SureBetBets')

today = '2026-04-14'

# Query today's bet_date
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq(today))
items = resp['Items']
while resp.get('LastEvaluatedKey'):
    resp = tbl.query(KeyConditionExpression=Key('bet_date').eq(today), ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp['Items'])

def f(v):
    try: return float(v)
    except: return 0.0

print(f"Total records for {today}: {len(items)}")
print()

# Find all with show_in_ui
ui_true = [i for i in items if i.get('show_in_ui') == True]
print(f"show_in_ui=True: {len(ui_true)}")
for p in sorted(ui_true, key=lambda x: str(x.get('race_time',''))):
    h = p.get('horse','?')
    c = p.get('course','?')
    rt = str(p.get('race_time',''))[:16]
    created = str(p.get('created_at','?'))[:19]
    score = f(p.get('comprehensive_score',0))
    odds = p.get('odds','?')
    grade = p.get('confidence_level','?')
    rank = p.get('pick_rank','?')
    outcome = p.get('outcome','pending')
    print(f"  {rt[11:16]:5s} {c:15s} {h:28s} score={score:5.0f} odds={str(odds):8s} grade={grade:8s} rank={rank} created={created} outcome={outcome}")

print()

# Check: were any picks demoted?
demoted = [i for i in items if i.get('demoted')]
print(f"Demoted picks: {len(demoted)}")
for p in demoted:
    h = p.get('horse','?')
    c = p.get('course','?')
    rt = str(p.get('race_time',''))[:16]
    dem_reason = p.get('demotion_reason','?')
    score = f(p.get('comprehensive_score',0))
    print(f"  {rt[11:16]:5s} {c:15s} {h:28s} score={score:5.0f} reason={dem_reason}")

print()

# Check unique created_at times (to see different analysis runs)
from collections import Counter
created_hours = Counter()
for i in items:
    c = str(i.get('created_at',''))
    if len(c) >= 13:
        created_hours[c[:13]] += 1
print("Analysis runs (created_at hour counts):")
for k, v in sorted(created_hours.items()):
    print(f"  {k}: {v} records")

print()

# Find top-scoring horses per race that COULD have been picks
races = {}
for i in items:
    rt = str(i.get('race_time',''))[:16]
    c = i.get('course','')
    key = f"{rt}|{c}"
    if key not in races:
        races[key] = []
    races[key].append(i)

print("Top horse per race (potential picks):")
for key in sorted(races.keys()):
    runners = races[key]
    runners.sort(key=lambda x: f(x.get('comprehensive_score',0)), reverse=True)
    top = runners[0]
    h = top.get('horse','?')
    c = top.get('course','?')
    score = f(top.get('comprehensive_score',0))
    show = top.get('show_in_ui', False)
    grade = top.get('confidence_level','?')
    odds = top.get('odds','?')
    outcome = top.get('outcome','pending')
    rt = key.split('|')[0]
    marker = " <<< UI PICK" if show else ""
    if score >= 75:
        print(f"  {rt[11:16]:5s} {c:15s} {h:28s} score={score:5.0f} odds={str(odds):8s} grade={grade:8s} show={show} outcome={outcome}{marker}")

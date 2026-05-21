"""Audit all picks for today — check times, show_in_ui, demotions"""
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = ddb.Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-14'))
items = resp['Items']
while resp.get('LastEvaluatedKey'):
    resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-14'),
                     ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp['Items'])

def f(v):
    try: return float(v)
    except: return 0.0

# Filter to actual picks (not learning/analysis)
picks = [i for i in items if i.get('course') and i.get('horse')]

picks.sort(key=lambda x: str(x.get('race_time', '')))

print(f"Total records for 2026-04-14: {len(items)}")
print(f"Actual picks (excl learning/analysis): {len(picks)}")
print(f"show_in_ui=True: {sum(1 for p in picks if p.get('show_in_ui'))}")
print(f"show_in_ui=False/missing: {sum(1 for p in picks if not p.get('show_in_ui'))}")
print()

# Show UI picks first
ui_picks = [p for p in picks if p.get('show_in_ui')]
hidden = [p for p in picks if not p.get('show_in_ui')]

print("=" * 100)
print("SHOWN ON UI (show_in_ui=True)")
print("=" * 100)
for p in ui_picks:
    h = p.get('horse', '?')
    c = p.get('course', '?')
    rt = str(p.get('race_time', ''))
    created = str(p.get('created_at', '?'))
    score = f(p.get('comprehensive_score', 0))
    odds = p.get('odds', '?')
    grade = p.get('confidence_level', '?')
    rank = p.get('pick_rank', '?')
    outcome = p.get('outcome', 'pending')
    print(f"  {rt[11:16] if len(rt)>15 else rt:5s} {c:15s} {h:28s} score={score:6.0f}  odds={str(odds):8s}  grade={grade:8s}  rank={rank}  created={created}  outcome={outcome}")

print()
print("=" * 100)
print("NOT SHOWN (show_in_ui=False or missing)")
print("=" * 100)
for p in hidden:
    h = p.get('horse', '?')
    c = p.get('course', '?')
    rt = str(p.get('race_time', ''))
    created = str(p.get('created_at', '?'))
    score = f(p.get('comprehensive_score', 0))
    odds = p.get('odds', '?')
    grade = p.get('confidence_level', '?')
    rank = p.get('pick_rank', '?')
    outcome = p.get('outcome', 'pending')
    demoted = p.get('demoted', False)
    dem_reason = p.get('demotion_reason', '')
    retro = p.get('retrospective', False)
    print(f"  {rt[11:16] if len(rt)>15 else rt:5s} {c:15s} {h:28s} score={score:6.0f}  odds={str(odds):8s}  grade={grade:8s}  rank={rank}  created={created}  outcome={outcome}  demoted={demoted}  reason={dem_reason}  retro={retro}")

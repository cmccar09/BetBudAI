"""Check DynamoDB Day 2 picks and current code runner counts."""
import sys, os
sys.path.insert(0, r'c:\Users\charl\OneDrive\futuregenAI\Betting')

import boto3
from barrys.surebet_intel import EXTRA_RACES, RACES_2026_MAP
from cheltenham_deep_analysis_2026 import RACES_2026
from cheltenham_full_fields_2026 import extend_race_entries, ADDITIONAL_RUNNERS
from barrys.barrys_config import FESTIVAL_RACES

# ── DynamoDB current picks for Day 2 ───────────────────────────────────────
db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('CheltenhamPicks')

resp = table.scan(
    FilterExpression='#d = :d',
    ExpressionAttributeNames={'#d': 'day'},
    ExpressionAttributeValues={':d': 'Wednesday_11_March'}
)
items = {i['race_name']: i for i in resp['Items']}

print("=" * 90)
print("  DynamoDB — Wednesday 11 March picks")
print("=" * 90)
for rn in sorted(items, key=lambda x: items[x].get('race_time', '')):
    it = items[rn]
    print(f"  {it.get('race_time','')}  {rn[:40]:<42}  pick={it.get('horse','?'):<26}  score={it.get('score','?')}")

# ── Code runner counts ────────────────────────────────────────────────────
# Build all_race_data same way as surebet_intel
all_race_data = {}
for r2026_name, entries_data in RACES_2026.items():
    fkey = RACES_2026_MAP.get(r2026_name)
    if fkey:
        all_race_data[fkey] = entries_data["entries"]
from barrys.surebet_intel import EXTRA_RACES
for fkey, data in EXTRA_RACES.items():
    all_race_data[fkey] = data["entries"]

print(f"\n{'='*90}")
print("  Code runner counts — Day 2 races")
print(f"{'='*90}")
day2_keys = sorted([k for k,v in FESTIVAL_RACES.items() if v['day']==2], key=lambda x: FESTIVAL_RACES[x]['time'])
for rkey in day2_keys:
    rinfo = FESTIVAL_RACES[rkey]
    base = all_race_data.get(rkey, [])
    full = extend_race_entries(rkey, base)
    extra_count = len(ADDITIONAL_RUNNERS.get(rkey, {}).get('entries', []))
    print(f"  {rinfo['time']}  {rinfo['name'][:42]:<44}  base={len(base):<4}  extra={extra_count:<4}  total={len(full)}")

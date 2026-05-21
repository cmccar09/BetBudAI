"""Quick comprehensive analysis of all horses, historical winners, jockey conflicts"""
import boto3, json
from decimal import Decimal
from collections import defaultdict

ddb = boto3.resource('dynamodb', region_name='eu-west-1')

# ── 1. Historical Results 2021-2025 ─────────────────────────────────────────
print("=" * 70)
print("HISTORICAL CHELTENHAM WINNERS 2021-2025 — WHY DID THEY WIN?")
print("=" * 70)

hist = ddb.Table('CheltenhamHistoricalResults')
resp = hist.scan()
items = resp['Items']
while resp.get('LastEvaluatedKey'):
    resp = hist.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp['Items'])

# Build race->years->winner dict
from collections import defaultdict
race_history = defaultdict(list)
for item in items:
    if str(item.get('position','')) == '1':
        race_history[str(item.get('race_name',''))].append({
            'year': str(item.get('year','')),
            'horse': str(item.get('horse_name','')),
            'trainer': str(item.get('trainer','')),
            'jockey': str(item.get('jockey','')),
            'sp': str(item.get('sp','')),
            'going': str(item.get('going','')),
            'age': str(item.get('age','')),
        })

for race in sorted(race_history.keys()):
    winners = sorted(race_history[race], key=lambda x: x['year'])
    print(f"\n{race}:")
    for w in winners:
        print(f"  {w['year']}: {w['horse']} ({w['sp']}) | {w['trainer']} / {w['jockey']} | Going:{w['going']} | Age:{w['age']}")

# ── 2. Trends summary ────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("TRENDS — TRAINER / JOCKEY PATTERNS")
print("=" * 70)
trends = ddb.Table('CheltenhamTrends')
resp = trends.scan()
titems = resp['Items']
for t in titems:
    key = str(t.get('trend_key',''))
    if 'trainer' in key.lower() or 'jockey' in key.lower() or 'sp_bucket' in key.lower():
        print(f"  {key}: {t.get('description','')} win_rate={t.get('win_rate','')} wins={t.get('total_wins','')} runs={t.get('total_runs','')}")

# ── 3. Jockey analysis from surebet_intel data ──────────────────────────────────
print("\n" + "=" * 70)
print("JOCKEY CONFLICT ANALYSIS — Paul Townend / Jack Kennedy")
print("(Both listed on multiple horses — can only ride ONE per race)")
print("=" * 70)

import sys, os
sys.path.insert(0, r"C:\Users\charl\OneDrive\futuregenAI\Betting")
from barrys.surebet_intel import build_all_picks

picks = build_all_picks()
jockey_map = defaultdict(list)
for race_key, race_data in picks.items():
    race_name = race_data.get('race_name', race_key)
    horses = race_data.get('all_horses', [])
    for h in horses:
        jock = h.get('jockey','?')
        if jock not in ('TBD', '?', ''):
            jockey_map[jock].append((race_name, h.get('name','?'), h.get('score',0), h.get('odds','?')))

# Sort by count and show conflicts
for jockey in sorted(jockey_map, key=lambda j: -len(jockey_map[j])):
    entries = jockey_map[jockey]
    if len(entries) >= 3:
        print(f"\n{jockey} — {len(entries)} entries:")
        for race, horse, score, odds in sorted(entries, key=lambda x: -int(x[2] or 0)):
            print(f"   {race[:35]}: {horse} (score:{score}, odds:{odds})")

# ── 4. Top picks + their form/ground analysis ────────────────────────────────
print("\n" + "=" * 70)
print("TOP 5 HIGHEST SCORED HORSES — FULL PROFILE")
print("=" * 70)

all_horses = []
for race_key, race_data in picks.items():
    race_name = race_data.get('race_name', race_key)
    for h in race_data.get('all_horses', []):
        if race_data.get('tier') == 'BETTING_PICK':
            all_horses.append({
                'race': race_name,
                'horse': h.get('name',''),
                'score': int(h.get('score', 0)),
                'odds': h.get('odds','?'),
                'trainer': h.get('trainer',''),
                'jockey': h.get('jockey',''),
                'form': h.get('form',''),
                'cheltenham_record': h.get('cheltenham_record',''),
                'last_run': h.get('last_run',''),
                'rating': h.get('rating',0),
            })

# Get top pick per race (already the scored #1), then sort globally
race_top = {}
for race_key, race_data in picks.items():
    if race_data.get('tier') == 'BETTING_PICK':
        top = race_data.get('top_pick', {})
        race_top[race_data.get('race_name', race_key)] = {
            'horse': top.get('name',''),
            'score': int(top.get('score', 0)),
            'odds': top.get('odds','?'),
            'trainer': top.get('trainer',''),
            'jockey': top.get('jockey',''),
            'form': top.get('form',''),
            'cheltenham_record': top.get('cheltenham_record',''),
            'last_run': top.get('last_run',''),
            'rating': top.get('rating',0),
            'gap': int(race_data.get('score_gap',0)),
        }

top_sorted = sorted(race_top.items(), key=lambda x: -x[1]['score'])
print("\nTOP 10 BETTING_PICK races by score:")
for race, d in top_sorted[:10]:
    print(f"  {d['score']:3d} [{d['odds']:6s}] {d['horse']:<28} {race[:35]}")
    print(f"       Trainer: {d['trainer']} | Jockey: {d['jockey']} | Gap: +{d['gap']}")
    print(f"       Form: {d['form']} | Last: {d['last_run']}")
    if d['cheltenham_record']:
        print(f"       Cheltenham: {d['cheltenham_record']}")

print("\nDone.")

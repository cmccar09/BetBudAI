"""
Post-race analysis: why did we miss the winners on 1 Apr 2026?
Races:  15:20 Wincanton (Golan Loop vs Broomfields Cave)
        16:20 Wincanton (Kingcormac vs Broomfields Cave)
        17:45 Dundalk   (I'm Spartacus vs Clonmacash)
"""
import boto3, json
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamo = boto3.resource('dynamodb', region_name='eu-west-1')
table  = dynamo.Table('SureBetBets')

# ── pull all 2026-04-01 records ──────────────────────────────────────────────
resp   = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-01'))
items  = resp['Items']

def f(v):
    return float(v) if isinstance(v, Decimal) else v

# map  race_time_prefix → all runners
races = {}
for item in items:
    rt = str(item.get('race_time', ''))[:16]
    races.setdefault(rt, []).append(item)

target = {
    '2026-04-01T15:20': {'winner': 'Broomfields Cave', 'winner_sp': '3/1',   'our_pick': 'Golan Loop'},
    '2026-04-01T16:20': {'winner': 'Broomfields Cave', 'winner_sp': '9/4',   'our_pick': 'Kingcormac'},
    '2026-04-01T17:45': {'winner': 'Clonmacash',       'winner_sp': '5/1',   'our_pick': "I'm Spartacus"},
}

for rt, meta in sorted(target.items()):
    runners = races.get(rt, [])
    runners.sort(key=lambda x: float(x.get('comprehensive_score') or 0), reverse=True)
    print(f"\n{'='*70}")
    print(f"Race: {rt}  Winner: {meta['winner']} ({meta['winner_sp']})")
    print(f"Our pick: {meta['our_pick']}")
    print(f"{'Horse':<25} {'Score':>6}  {'show_ui':>7}  {'outcome':>8}")
    print('-'*55)
    for r in runners:
        horse   = r.get('horse', r.get('horse_name', '?'))
        score   = float(r.get('comprehensive_score') or r.get('analysis_score') or 0)
        show_ui = r.get('show_in_ui', False)
        outcome = r.get('outcome', 'pending')
        mark = ' ← OUR PICK' if horse == meta['our_pick'] else (' ← WINNER' if horse == meta['winner'] else '')
        print(f"  {horse:<23} {score:6.0f}  {str(show_ui):>7}  {str(outcome):>8}{mark}")

# ── also dump racecard_cache for context ──────────────────────────────────────
print("\n\n=== Checking racecard_cache.json for winner entries ===")
try:
    with open('racecard_cache.json', encoding='utf-8') as f:
        cache = json.load(f)
    races_list = cache if isinstance(cache, list) else cache.get('races', [])
    for race in races_list:
        rt_raw = race.get('start_time', race.get('time', ''))
        course = race.get('course', race.get('venue', ''))
        if not any(t in str(rt_raw) for t in ['15:20', '16:20', '17:45']):
            continue
        print(f"\n  Race: {rt_raw} @ {course}")
        runners = race.get('runners', race.get('horses', []))
        for r in runners:
            name = r.get('horse', r.get('name', '?'))
            odds = r.get('odds', r.get('decimal_odds', '?'))
            rating = r.get('official_rating', r.get('or', '?'))
            form = r.get('form', '?')
            trainer = r.get('trainer', '?')
            print(f"    {name:<25} odds={str(odds):>6}  OR={str(rating):>4}  form={form}  trainer={trainer}")
except Exception as e:
    print(f"  Could not read racecard_cache: {e}")

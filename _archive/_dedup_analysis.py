import boto3
from boto3.dynamodb.conditions import Attr
from collections import defaultdict, Counter

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

WIN = {'win','won'}
SETTLED = WIN | {'loss','lost','placed'}

items = []
kwargs = {'FilterExpression': Attr('bet_date').between('2026-03-22','2026-03-30') & Attr('show_in_ui').eq(True)}
while True:
    resp = table.scan(**kwargs)
    items += resp['Items']
    if not resp.get('LastEvaluatedKey'): break
    kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

items = [i for i in items if i.get('bet_id') != 'SYSTEM_ANALYSIS_MANIFEST']

# Group by race_key
by_race = defaultdict(list)
for i in items:
    rk = i.get('race_key')
    if not rk:
        d = i.get('bet_date','')[:10]
        c = i.get('course','')
        t = str(i.get('race_time',''))[:5]
        rk = f"{d}_{c}_{t}"
    by_race[rk].append(i)

print(f'Total records (show_in_ui=True): {len(items)}')
print(f'Unique races: {len(by_race)}')
print(f'Duplication factor: {len(items)/len(by_race):.1f}x')

settled = {k: v for k,v in by_race.items() if any(str(r.get('outcome','')).lower() in SETTLED for r in v)}
day_races = Counter(k[:10] for k in settled)
print('\nUnique settled races per day:')
total_wins = 0
for d in sorted(day_races):
    day_win = sum(1 for k,v in settled.items() if k[:10]==d and any(str(r.get('outcome','')).lower() in WIN for r in v))
    total_wins += day_win
    print(f'  {d}: {day_races[d]} races, {day_win} wins')
n = sum(day_races.values())
print(f'\n  Total settled: {n} races, {total_wins} wins ({total_wins/n*100:.1f}%)')

correct = [r for v in settled.values() for r in v if str(r.get('outcome','')).lower() in WIN and r.get('show_in_ui')]
if correct:
    odds_list = sorted(float(r.get('odds',0)) for r in correct)
    print(f'\nWinning odds: {odds_list}')
    print(f'Avg winning odds: {sum(odds_list)/len(odds_list):.1f}')

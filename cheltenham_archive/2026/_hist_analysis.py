import boto3
from collections import defaultdict
from decimal import Decimal

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
hist = ddb.Table('CheltenhamHistoricalResults')

# Scan all rows
all_items = []
resp = hist.scan()
all_items.extend(resp['Items'])
while 'LastEvaluatedKey' in resp:
    resp = hist.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
    all_items.extend(resp['Items'])

print(f'Total rows: {len(all_items)}')

# Find winners
winners = [x for x in all_items if x.get('position') == '1st']
print(f'Winners: {len(winners)}')

# Group by race
race_winners = defaultdict(list)
for w in winners:
    race_winners[w['race_name']].append(w)

# Print each race winner by year
for race in sorted(race_winners.keys()):
    print(f'\n=== {race} ===')
    for w in sorted(race_winners[race], key=lambda x: int(x['year'])):
        sp = w.get('sp','?')
        trainer = w.get('trainer','?')
        jockey = w.get('jockey','?')
        going = w.get('going','?')
        year = int(w['year'])
        horse = w['horse']
        print(f'  {year}: {horse} | SP:{sp} | T:{trainer} | J:{jockey} | G:{going}')

# Trainer dominance analysis
print('\n\n=== TRAINER WIN COUNTS (2021-2025) ===')
trainer_wins = defaultdict(int)
for w in winners:
    trainer_wins[w.get('trainer','?')] += 1
for t, cnt in sorted(trainer_wins.items(), key=lambda x: -x[1])[:15]:
    print(f'  {t}: {cnt} wins')

# Jockey dominance analysis
print('\n=== JOCKEY WIN COUNTS (2021-2025) ===')
jockey_wins = defaultdict(int)
for w in winners:
    jockey_wins[w.get('jockey','?')] += 1
for j, cnt in sorted(jockey_wins.items(), key=lambda x: -x[1])[:15]:
    print(f'  {j}: {cnt} wins')

# SP bucket analysis
print('\n=== SP BUCKET WINS ===')
buckets = defaultdict(int)
for w in winners:
    sp = float(w.get('sp_dec', 0))
    if sp <= 2: b = 'Fav <=2/1'
    elif sp <= 4: b = '2/1-4/1'
    elif sp <= 7: b = '4/1-7/1'
    elif sp <= 12: b = '7/1-12/1'
    else: b = '12/1+'
    buckets[b] += 1
order = ['Fav <=2/1','2/1-4/1','4/1-7/1','7/1-12/1','12/1+']
for b in order:
    print(f'  {b}: {buckets.get(b,0)} wins')

# Going analysis
print('\n=== GOING WINS ===')
going_wins = defaultdict(int)
for w in winners:
    going_wins[w.get('going','?')] += 1
for g, cnt in sorted(going_wins.items(), key=lambda x: -x[1]):
    print(f'  {g}: {cnt} wins')

# Irish vs British trainers
print('\n=== IRISH vs BRITISH WINS ===')
irish_trainers = ['W P Mullins', 'G Elliott', 'H De Bromhead', 'J Harrington', 'C Byrnes', 'N Meade', 'D Weld', 'Tony Martin']
irish_wins = sum(1 for w in winners if any(t in w.get('trainer','') for t in ['W P Mullins','G Elliott','H De Bromhead','J Harrington','C Byrnes']))
british_wins = len(winners) - irish_wins
print(f'  Irish: {irish_wins} | British: {british_wins}')

# Mullins specific
mullins_wins = [w for w in winners if 'Mullins' in w.get('trainer','')]
print(f'\n=== WILLIE MULLINS WINS ===')
for w in sorted(mullins_wins, key=lambda x: int(x['year'])):
    year = int(w['year'])
    print(f'  {year}: {w["horse"]} ({w["race_name"]}) SP:{w.get("sp","?")} J:{w.get("jockey","?")}')

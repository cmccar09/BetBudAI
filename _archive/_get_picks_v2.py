import boto3
from collections import defaultdict
from decimal import Decimal

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
picks = ddb.Table('CheltenhamPicks')

resp = picks.scan()
items = resp['Items']
while 'LastEvaluatedKey' in resp:
    resp = picks.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp['Items'])

# Get latest pick per race
race_latest = {}
for item in items:
    race = item.get('race_name', '')
    date = item.get('pick_date', '')
    if race not in race_latest or date > race_latest[race].get('pick_date', ''):
        race_latest[race] = item

print(f'Unique races: {len(race_latest)}')

# Sort by score
sorted_races = sorted(race_latest.values(), key=lambda x: float(x.get('score', 0)), reverse=True)

print('\nAll picks sorted by score:')
for p in sorted_races:
    score = float(p.get('score', 0))
    horse = p.get('horse', '?')
    race = p.get('race_name', '?')
    odds = p.get('odds', '?')
    gap = float(p.get('score_gap', 0))
    jockey = p.get('jockey', '?')
    trainer = p.get('trainer', '?')
    tier = p.get('bet_tier', p.get('recommendation', '?'))
    reasons = p.get('reasons', [])
    day = p.get('day', '?')
    grade = p.get('grade', '?')
    # Get cheltenham_record from all_horses
    ch_record = ''
    all_h = p.get('all_horses', [])
    for h in all_h:
        if h.get('name') == horse:
            ch_record = h.get('cheltenham_record', '')
            break
    print(f'  [{score}] {horse} | {race[:35]} | {odds} | Gap:{gap} | T:{trainer} | J:{jockey} | Tier:{tier} | Day:{day} | CH:{ch_record}')
    if reasons:
        print(f'    Reasons: {reasons[:3]}')

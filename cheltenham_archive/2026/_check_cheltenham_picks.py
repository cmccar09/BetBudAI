import json, boto3
from decimal import Decimal

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('CheltenhamPicks')
resp = table.scan()
items = resp.get('Items', [])

mullins_picks  = [i for i in items if 'Mullins'  in str(i.get('trainer','')) or 'Mullins'  in str(i.get('jockey',''))]
elliott_picks  = [i for i in items if 'Elliott'  in str(i.get('trainer',''))]
all_picks_sorted = sorted(items, key=lambda x: float(x.get('score',0)), reverse=True)

print(f"Total Cheltenham picks in DB: {len(items)}")
print(f"Mullins trainer/jockey connections: {len(mullins_picks)}")
print(f"Elliott trainer: {len(elliott_picks)}")

print()
print("TOP 30 PICKS BY SCORE:")
print(f"  {'Score':<7} {'Horse':<28} {'Trainer':<25} {'Race'}")
print("  " + "-"*90)
for p in all_picks_sorted[:30]:
    score   = str(p.get('score','?'))
    horse   = str(p.get('horse_name','?'))[:27]
    trainer = str(p.get('trainer','?'))[:24]
    race    = str(p.get('race_name','?'))[:35]
    print(f"  {score:<7} {horse:<28} {trainer:<25} {race}")

print()
mullins_picks.sort(key=lambda x: float(x.get('score',0)), reverse=True)
print("MULLINS-CONNECTED PICKS:")
print(f"  {'Score':<7} {'Horse':<28} {'Jockey':<20} {'Race'}")
print("  " + "-"*80)
for p in mullins_picks:
    score   = str(p.get('score','?'))
    horse   = str(p.get('horse_name','?'))[:27]
    jockey  = str(p.get('jockey','?'))[:19]
    race    = str(p.get('race_name','?'))[:35]
    print(f"  {score:<7} {horse:<28} {jockey:<20} {race}")

print()
if elliott_picks:
    elliott_picks.sort(key=lambda x: float(x.get('score',0)), reverse=True)
    print("ELLIOTT PICKS:")
    print(f"  {'Score':<7} {'Horse':<28} {'Race'}")
    print("  " + "-"*70)
    for p in elliott_picks:
        score = str(p.get('score','?'))
        horse = str(p.get('horse_name','?'))[:27]
        race  = str(p.get('race_name','?'))[:35]
        print(f"  {score:<7} {horse:<28} {race}")

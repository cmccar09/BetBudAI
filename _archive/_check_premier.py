import json

with open('_sl_mar24_raw.json') as f:
    data = json.load(f)

pr = data.get('premierRaces', {})
print('premierRaces type:', type(pr))
if isinstance(pr, dict):
    print('premierRaces keys:', list(pr.keys()))
    print(json.dumps(pr, indent=2)[:2000])
elif isinstance(pr, list):
    print('premierRaces len:', len(pr))
    for item in pr:
        print('  item:', type(item), str(item)[:200])

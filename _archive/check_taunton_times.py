import json

with open('response_horses.json') as f:
    data = json.load(f)

races = data.get('races', [])
taunton_races = [r for r in races if r.get('venue') == 'Taunton']

print(f'Taunton races found: {len(taunton_races)}\n')
for r in taunton_races:
    start_time = r.get('start_time', '')
    market_name = r.get('market_name', '')
    num_runners = len(r.get('runners', []))
    print(f'{start_time} - {market_name} ({num_runners} runners)')

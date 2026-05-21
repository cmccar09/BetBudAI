import json

with open('response_live.json') as f:
    data = json.load(f)

for race in data['races']:
    for runner in race['runners']:
        if runner['name'] == 'Magna':
            print(f"Magna found in race: {race['market_name']}")
            print(f"Odds: {runner.get('odds', 'N/A')}")
            print(f"Selection ID: {runner.get('selectionId')}")
            break

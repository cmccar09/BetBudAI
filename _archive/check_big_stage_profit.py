import requests
import json

r = requests.get('https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/results')
picks = r.json().get('picks', [])

big_stage = [p for p in picks if 'Big Stage' in p.get('horse', '')][0]

print("Big Stage API data:")
print(json.dumps({
    'horse': big_stage.get('horse'),
    'outcome': big_stage.get('outcome'),
    'odds': big_stage.get('odds'),
    'stake': big_stage.get('stake'),
    'profit': big_stage.get('profit'),
    'total_return': big_stage.get('total_return'),
    'starting_price': big_stage.get('starting_price')
}, indent=2))

# Calculate what profit SHOULD be
stake = float(big_stage.get('stake', 2.0))
odds = float(big_stage.get('odds', 0))
if big_stage.get('outcome') == 'win':
    expected_return = stake * odds
    expected_profit = expected_return - stake
    print(f"\nExpected calculation:")
    print(f"  Stake: €{stake}")
    print(f"  Odds: {odds}")
    print(f"  Return: €{expected_return} (stake × odds)")
    print(f"  Profit: €{expected_profit} (return - stake)")

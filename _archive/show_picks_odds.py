import pandas as pd
import json

df = pd.read_csv('today_picks.csv')
print(f'\nToday we have {len(df)} picks')

data = json.load(open('response_live.json'))
markets = data.get('races', [])
print(f'Markets loaded: {len(markets)}')

# Build odds lookup
odds_map = {}
for m in markets:
    for r in m.get('runners', []):
        odds_map[r['name']] = r.get('odds', 0)

print('\n' + '='*60)
print('PICKS WITH ODDS:')
print('='*60)
for _, row in df.iterrows():
    name = row['runner_name']
    odds = odds_map.get(name, 0)
    p_win = row['p_win']
    print(f'{name:20s} Odds: {odds:6.2f}  P(win): {p_win:.2f}')

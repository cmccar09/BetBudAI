"""Check fetched race data details"""
import json
from collections import defaultdict

with open('response_horses.json', 'r') as f:
    data = json.load(f)

races = data.get('races', [])

print(f'\n{"="*80}')
print(f'FETCHED RACES FROM BETFAIR')
print(f'{"="*80}\n')

# Group by venue
venue_races = defaultdict(list)
for race in races:
    venue = race.get('venue', 'Unknown')
    venue_races[venue].append(race)

print(f'Total: {len(races)} races across {len(venue_races)} venues\n')

print('Summary by venue:')
for venue in sorted(venue_races.keys()):
    races_list = venue_races[venue]
    total_horses = sum(len(r.get('runners', [])) for r in races_list)
    print(f'  {venue}: {len(races_list)} races, {total_horses} horses')

print(f'\n{"="*80}')
print('RACE TIMES (Next 10 races):')
print(f'{"="*80}\n')

sorted_races = sorted(races, key=lambda x: x.get('start_time', ''))
for race in sorted_races[:10]:
    venue = race.get('venue', 'Unknown')
    start_time = race.get('start_time', 'Unknown')
    runners = len(race.get('runners', []))
    market_name = race.get('marketName', 'Unknown')
    print(f'{start_time} - {venue} ({runners} runners)')
    print(f'  {market_name}')
    print()

import json
from datetime import datetime

with open('response_horses.json', 'r') as f:
    data = json.load(f)

races = data.get('races', [])
print(f"Total races fetched from Betfair: {len(races)}")
print()

print("All races for today:")
print("=" * 80)

for i, race in enumerate(races, 1):
    venue = race.get('venue', 'Unknown')
    time = race.get('start_time', 'Unknown')
    name = race.get('market_name', race.get('event_name', 'Unknown'))
    runners = len(race.get('runners', []))
    print(f"{i:2}. {time:26} | {venue:15} | {name:30} | {runners} runners")

print("=" * 80)
print(f"Total: {len(races)} races")

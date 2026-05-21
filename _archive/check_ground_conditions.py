import json

with open('response_horses.json', 'r') as f:
    data = json.load(f)

print(f"\nTotal races: {len(data['races'])}\n")

# Check first few races for ground conditions
for i, race in enumerate(data['races'][:3]):
    print(f"Race {i+1}: {race.get('venue')} - {race.get('start_time')}")
    print(f"  Going: {race.get('going', 'NOT FOUND')}")
    print(f"  Market Name: {race.get('market_name', race.get('marketName', 'Unknown'))}")
    print()

# Check all unique venues and their going
venues_going = {}
for race in data['races']:
    venue = race.get('venue', race.get('course', 'Unknown'))
    going = race.get('going', 'Unknown')
    if venue not in venues_going:
        venues_going[venue] = going

print("\nAll venues and ground conditions today:")
for venue, going in sorted(venues_going.items()):
    print(f"  {venue:20} Going: {going}")

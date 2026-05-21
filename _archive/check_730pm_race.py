import json
from datetime import datetime

# Check for upcoming races
try:
    with open('api_response.json', 'r') as f:
        data = json.load(f)
    
    races = data.get('races', [])
    
    # Look for 19:30 races (7:30pm)
    evening_races = [r for r in races if '19:30' in r.get('race_time', '') or 'T1930' in r.get('race_time', '')]
    
    print(f"\n{'='*80}")
    print(f"RACES AT 19:30 (7:30 PM)")
    print(f"{'='*80}\n")
    
    if evening_races:
        for race in evening_races:
            print(f"Venue: {race.get('venue')}")
            print(f"Time: {race.get('race_time')}")
            print(f"Race: {race.get('race_name')}")
            print(f"Runners: {len(race.get('runners', []))}")
            print()
    else:
        print("No races found at 19:30")
        print("\nSearching for any evening races after 19:00...")
        
        # Look for any races after 19:00
        all_evening = [r for r in races if 'T19' in r.get('race_time', '') or 'T20' in r.get('race_time', '')]
        
        if all_evening:
            print(f"\nFound {len(all_evening)} races after 19:00:")
            for race in all_evening[:5]:
                print(f"  {race.get('race_time', 'Unknown')[:16]} - {race.get('venue')} - {race.get('race_name', 'Unknown')}")
        else:
            print("No evening races found in api_response.json")
            print("\nThis file may be from earlier today. Racing may be finished.")
    
except FileNotFoundError:
    print("api_response.json not found")
except Exception as e:
    print(f"Error: {e}")

print(f"\n{'='*80}")

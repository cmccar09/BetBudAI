import json
from datetime import datetime, time

# Check for tonight's remaining Wolverhampton races
try:
    with open('api_response.json', 'r') as f:
        data = json.load(f)
    
    races = data.get('races', [])
    
    # Look for Wolverhampton races after 19:00
    wolverhampton_tonight = []
    
    for race in races:
        venue = race.get('venue', '').lower()
        race_time = race.get('race_time', '')
        
        if 'wolverhampton' in venue or 'wolv' in venue:
            # Parse time
            if 'T' in race_time:
                time_part = race_time.split('T')[1][:5]  # Get HH:MM
                hour = int(time_part.split(':')[0])
                
                # After 7pm (19:00)
                if hour >= 19:
                    wolverhampton_tonight.append({
                        'time': time_part,
                        'race_name': race.get('race_name', 'Unknown'),
                        'runners': race.get('runners', [])
                    })
    
    print(f"\n{'='*80}")
    print(f"WOLVERHAMPTON RACES TONIGHT (after 19:00)")
    print(f"{'='*80}\n")
    
    if wolverhampton_tonight:
        print(f"Found {len(wolverhampton_tonight)} remaining races:\n")
        for i, race in enumerate(wolverhampton_tonight, 1):
            print(f"{i}. {race['time']} - {race['race_name']}")
            print(f"   Runners: {len(race['runners'])}")
        
        # Analyze each race
        print(f"\n{'='*80}")
        print("SWEET SPOT ANALYSIS (Based on today's 80% win rate)")
        print(f"{'='*80}\n")
        
        for race in wolverhampton_tonight:
            print(f"\n{race['time']} - {race['race_name']}")
            print("-" * 80)
            
            # Find sweet spot horses (3-9 odds, prefer 4-6)
            sweet_spot = []
            optimal_zone = []
            
            for runner in race['runners']:
                odds = runner.get('odds', 0)
                if 3.0 <= odds <= 9.0:
                    sweet_spot.append({
                        'horse': runner.get('name', 'Unknown'),
                        'odds': odds,
                        'form': runner.get('form', ''),
                        'trainer': runner.get('trainer', ''),
                        'jockey': runner.get('jockey', '')
                    })
                    
                    # Optimal zone based on today's results (4-6)
                    if 4.0 <= odds <= 6.0:
                        optimal_zone.append(sweet_spot[-1])
            
            print(f"\nSweet spot horses (3-9 odds): {len(sweet_spot)}")
            print(f"Optimal zone (4-6 odds): {len(optimal_zone)}\n")
            
            if optimal_zone:
                print("RECOMMENDED PICKS (4-6 odds - today's pattern):")
                for horse in sorted(optimal_zone, key=lambda x: abs(x['odds'] - 4.75))[:3]:
                    print(f"  {horse['horse']} @ {horse['odds']}")
                    print(f"    Form: {horse['form']}")
                    print(f"    Trainer: {horse['trainer']}")
            elif sweet_spot:
                print("SWEET SPOT PICKS (3-9 odds):")
                for horse in sorted(sweet_spot, key=lambda x: abs(x['odds'] - 4.75))[:3]:
                    print(f"  {horse['horse']} @ {horse['odds']}")
                    print(f"    Form: {horse['form']}")
            else:
                print("No horses in sweet spot range")
    
    else:
        print("No more Wolverhampton races found tonight")
        print("\nNote: api_response.json may be from earlier today")
        print("Please run the workflow to fetch latest races")

except FileNotFoundError:
    print("api_response.json not found - please fetch race data")
except json.JSONDecodeError:
    print("api_response.json is empty or invalid")
except Exception as e:
    print(f"Error: {e}")

print(f"\n{'='*80}\n")

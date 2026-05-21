import json
from datetime import datetime

print("\n" + "="*80)
print("WOLVERHAMPTON RACES - BETFAIR DATA")
print("="*80)

try:
    with open('response_horses.json', 'r') as f:
        data = json.load(f)
    
    # Find Wolverhampton races
    wolverhampton_races = []
    races = data.get('races', [])
    
    for race in races:
        venue = race.get('venue', '').lower()
        race_time = race.get('start_time', '')
        
        if 'wolverhampton' in venue:
            # Parse time to check if it's tonight
            if race_time:
                time_str = race_time.split('T')[1][:5] if 'T' in race_time else ''
                hour = int(time_str.split(':')[0]) if time_str else 0
                
                # Include races at 19:00 and later
                if hour >= 19:
                    wolverhampton_races.append(race)
    
    if wolverhampton_races:
        print(f"\nFound {len(wolverhampton_races)} Wolverhampton races tonight\n")
        
        for i, race in enumerate(wolverhampton_races, 1):
            race_time = race.get('start_time', '')
            time_display = race_time.split('T')[1][:5] if 'T' in race_time else 'Unknown'
            
            print(f"\n{'='*80}")
            print(f"RACE {i}: {time_display} - {race.get('market_name', 'Unknown')}")
            print(f"{'='*80}")
            
            runners = race.get('runners', [])
            print(f"Total runners: {len(runners)}\n")
            
            # Analyze with sweet spot strategy
            sweet_spot = []
            optimal = []
            
            for runner in runners:
                odds = runner.get('odds', 0)
                if odds > 0:
                    horse = {
                        'name': runner.get('name', 'Unknown'),
                        'odds': odds,
                        'form': runner.get('form', ''),
                        'jockey': runner.get('jockey', ''),
                        'trainer': runner.get('trainer', '')
                    }
                    
                    if 3.0 <= odds <= 9.0:
                        sweet_spot.append(horse)
                        
                        if 4.0 <= odds <= 6.0:
                            optimal.append(horse)
            
            print(f"Sweet spot (3-9 odds): {len(sweet_spot)} horses")
            print(f"Optimal zone (4-6 odds): {len(optimal)} horses\n")
            
            if optimal:
                print("RECOMMENDED PICKS (4-6 odds - 80% success today):")
                # Sort by proximity to 4.75 (today's avg winner)
                sorted_optimal = sorted(optimal, key=lambda x: abs(x['odds'] - 4.75))
                
                for j, horse in enumerate(sorted_optimal[:3], 1):
                    print(f"\n  {j}. {horse['name']} @ {horse['odds']}")
                    print(f"     Form: {horse['form']}")
                    print(f"     Jockey: {horse['jockey']}")
                    print(f"     Trainer: {horse['trainer']}")
                    print(f"     Distance from optimal (4.75): {abs(horse['odds'] - 4.75):.2f}")
                
                # Show top recommendation
                top_pick = sorted_optimal[0]
                print(f"\n  TOP PICK: {top_pick['name']} @ {top_pick['odds']}")
                print(f"  Reason: Closest to today's average winner (4.75)")
                
            elif sweet_spot:
                print("SWEET SPOT PICKS (3-9 odds, none in optimal 4-6):")
                sorted_sweet = sorted(sweet_spot, key=lambda x: abs(x['odds'] - 4.75))
                
                for j, horse in enumerate(sorted_sweet[:3], 1):
                    print(f"\n  {j}. {horse['name']} @ {horse['odds']}")
                    print(f"     Form: {horse['form']}")
            else:
                print("WARNING: No horses in sweet spot range (3-9)")
            
            # Show all runners for reference
            print(f"\n\nALL RUNNERS:")
            print("-" * 80)
            for runner in sorted(runners, key=lambda x: x.get('odds', 999)):
                odds = runner.get('odds', 0)
                marker = ""
                if 4.0 <= odds <= 6.0:
                    marker = " [OPTIMAL]"
                elif 3.0 <= odds <= 9.0:
                    marker = " [SWEET SPOT]"
                
                print(f"  {runner.get('name', 'Unknown'):30s} @ {odds:6.2f}{marker}")
    
    else:
        print("\nNo Wolverhampton races found after 19:00")
        print("Racing may be finished for the day")

except FileNotFoundError:
    print("\nresponse_horses.json not found")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("STRATEGY REMINDER:")
print("="*80)
print("Today's results: 4/5 wins (80%) at Wolverhampton")
print("Winning odds: 4.0, 4.0, 5.0, 6.0 (avg: 4.75)")
print("Optimal zone: 4-6 odds")
print("Sweet spot: 3-9 odds")
print("="*80 + "\n")

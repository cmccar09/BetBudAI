"""
Quick script to find tonight's remaining Wolverhampton races
Based on today's 80% win rate at Wolverhampton (4/5 picks)
"""

import requests
import json
from datetime import datetime

print("\n" + "="*80)
print("FETCHING TONIGHT'S WOLVERHAMPTON RACES")
print("="*80)

# Try to get latest race data
try:
    # Check if there's fresh data
    print("\nSearching for race data files...")
    
    import os
    import glob
    
    # Find recent JSON files with race data
    json_files = glob.glob("*.json")
    race_files = [f for f in json_files if 'race' in f.lower() or 'horse' in f.lower() or 'odds' in f.lower()]
    
    print(f"Found {len(race_files)} potential race data files")
    
    # Try the most recent ones
    for file in sorted(race_files, key=os.path.getmtime, reverse=True)[:5]:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                
            # Check if it has race data
            if isinstance(data, dict):
                races = data.get('races', [])
                if races:
                    print(f"\n✓ Found races in {file}: {len(races)} races")
                    
                    # Find Wolverhampton races after 19:00
                    wolv_races = []
                    for race in races:
                        venue = str(race.get('venue', '')).lower()
                        race_time = race.get('race_time', '')
                        
                        if 'wolverhampton' in venue or 'wolv' in venue:
                            if 'T19' in race_time or 'T20' in race_time or 'T21' in race_time:
                                wolv_races.append(race)
                    
                    if wolv_races:
                        print(f"\n{'='*80}")
                        print(f"FOUND {len(wolv_races)} WOLVERHAMPTON RACES TONIGHT")
                        print(f"{'='*80}\n")
                        
                        for i, race in enumerate(wolv_races, 1):
                            time_str = race.get('race_time', '')[:16]
                            print(f"\nRace {i}: {time_str}")
                            print(f"Name: {race.get('race_name', 'Unknown')}")
                            print(f"Runners: {len(race.get('runners', []))}")
                            
                            # Apply sweet spot strategy
                            runners = race.get('runners', [])
                            sweet_spot = []
                            optimal = []
                            
                            for runner in runners:
                                odds = runner.get('odds', 0)
                                if 3.0 <= odds <= 9.0:
                                    horse_data = {
                                        'name': runner.get('name', 'Unknown'),
                                        'odds': odds,
                                        'form': runner.get('form', ''),
                                        'jockey': runner.get('jockey', '')
                                    }
                                    sweet_spot.append(horse_data)
                                    
                                    # Today's optimal zone (4-6)
                                    if 4.0 <= odds <= 6.0:
                                        optimal.append(horse_data)
                            
                            print(f"\nSweet spot (3-9): {len(sweet_spot)} horses")
                            print(f"Optimal zone (4-6): {len(optimal)} horses")
                            
                            if optimal:
                                print(f"\n🎯 RECOMMENDED (based on today's 80% win rate):")
                                # Sort by proximity to 4.75 (today's avg winner)
                                best = sorted(optimal, key=lambda x: abs(x['odds'] - 4.75))[:2]
                                for horse in best:
                                    print(f"   {horse['name']} @ {horse['odds']}")
                                    print(f"   Form: {horse['form']}")
                            elif sweet_spot:
                                print(f"\n⚠️ SWEET SPOT PICKS (no horses in optimal 4-6):")
                                best = sorted(sweet_spot, key=lambda x: abs(x['odds'] - 4.75))[:2]
                                for horse in best:
                                    print(f"   {horse['name']} @ {horse['odds']}")
                        
                        break  # Found what we need
        except:
            continue
    
    else:
        print("\n❌ No race data found in JSON files")
        print("\nPlease run: python analyze_all_races_comprehensive.py")

except Exception as e:
    print(f"\nError: {e}")

print(f"\n{'='*80}")
print("WOLVERHAMPTON STRATEGY (validated today):")
print("="*80)
print("✓ Sweet spot: 3-9 odds (4/5 wins = 80%)")
print("✓ Optimal zone: 4-6 odds (all 4 wins)")
print("✓ Average winner: 4.75")
print("✓ Avoid favorites (<3.0) and longshots (>9.0)")
print("="*80 + "\n")

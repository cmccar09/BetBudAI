import json

# Check response_horses.json for Ayr 14:05
with open('response_horses.json', 'r') as f:
    data = json.load(f)

races = data.get('races', [])

print("SEARCHING FOR AYR 14:05")
print("="*80)

ayr_race = None
for race in races:
    venue = race.get('venue', '')
    start_time = race.get('start_time', '')
    
    if 'Ayr' in venue and '14:05' in start_time:
        ayr_race = race
        break

if not ayr_race:
    print("❌ Ayr 14:05 not found in response_horses.json")
    print("\nAvailable Ayr races:")
    for race in races:
        if 'Ayr' in race.get('venue', ''):
            print(f"  {race.get('venue')} {race.get('start_time')}")
else:
    print(f"✓ Found: {ayr_race.get('venue')} {ayr_race.get('start_time')}")
    print(f"Runners: {len(ayr_race.get('runners', []))}")
    print()
    
    runners = ayr_race.get('runners', [])
    
    print(f"{'Horse':<30} {'Odds':<10} {'Form':<15}")
    print("-"*60)
    
    for runner in sorted(runners, key=lambda x: float(x.get('odds', 999))):
        name = runner.get('name', 'Unknown')[:28]
        odds = float(runner.get('odds', 0))
        form = runner.get('form', '')[:12]
        
        # Calculate place odds
        if odds < 3.0:
            place_odds = 1 + ((odds - 1) / 5)
        else:
            place_odds = 1 + ((odds - 1) / 4)
        
        marker = ""
        if 'Ballymackie' in name:
            marker = "  ← FAVORITE (hot)"
        elif odds >= 3.0 and odds <= 10.0:
            marker = "  ← PLACE VALUE?"
        
        print(f"{name:<30} {odds:>6.2f}     {form:<15}{marker}")
        print(f"  → Place odds ~{place_odds:.2f} (ROI {(place_odds-1)*100:+.1f}%)")
    
    # Analysis
    print("\n" + "="*80)
    print("PLACE BETTING ANALYSIS")
    print("="*80)
    
    favorite = min(runners, key=lambda x: float(x.get('odds', 999)))
    fav_odds = float(favorite.get('odds', 0))
    
    print(f"\nFavorite: {favorite.get('name')} @ {fav_odds:.2f}")
    
    if fav_odds <= 1.5:  # Very strong favorite (2/5 or better)
        print(f"  ✓ VERY strong favorite ({fav_odds:.2f} = {int((1/(fav_odds-1)))}/{int(1/(fav_odds-1))*((fav_odds-1)/(1-fav_odds+1))} fractional)")
        print(f"  ✓ Likely to win or at minimum PLACE")
        print(f"\n  STRATEGY: Favorite is so strong, look at 2nd/3rd for PLACE bets")
        
        # Find 2nd and 3rd best
        others = [r for r in runners if r != favorite]
        others_sorted = sorted(others, key=lambda x: float(x.get('odds', 999)))
        
        if len(others_sorted) >= 1:
            second = others_sorted[0]
            sec_odds = float(second.get('odds', 0))
            sec_place_odds = 1 + ((sec_odds - 1) / 4)
            
            print(f"\n  2nd FAVORITE: {second.get('name')} @ {sec_odds:.2f}")
            print(f"    Place odds: ~{sec_place_odds:.2f}")
            
            if 3.0 <= sec_odds <= 10.0:
                print(f"    ✓ PLACE VALUE: Good odds, likely to place if favorite wins")
                print(f"    ✓ Lower risk than win bet")
            elif sec_odds < 3.0:
                print(f"    ⚠️ Too short for value")
            else:
                print(f"    ⚠️ Odds too high, risky")
        
        if len(others_sorted) >= 2:
            third = others_sorted[1]
            third_odds = float(third.get('odds', 0))
            third_place_odds = 1 + ((third_odds - 1) / 4)
            
            print(f"\n  3rd FAVORITE: {third.get('name')} @ {third_odds:.2f}")
            print(f"    Place odds: ~{third_place_odds:.2f}")
            
            if 5.0 <= third_odds <= 15.0:
                print(f"    ⚠️ EACH-WAY option: Higher odds, decent place chance")

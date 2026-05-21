"""Debug race scoring to see which horses score 85+"""
from comprehensive_pick_logic import analyze_horse_comprehensive
import json

# Load races
with open('response_horses.json', 'r') as f:
    data = json.load(f)

races = data.get('races', [])

# Test Lingfield 14:33
lingfield_1433 = None
for race in races:
    if race.get('venue') == 'Lingfield' and '14:33' in race.get('start_time', ''):
        lingfield_1433 = race
        break

if lingfield_1433:
    print("=" * 80)
    print("Lingfield 14:33 - ALL HORSE SCORES:")
    print("=" * 80)
    
    runners = lingfield_1433.get('runners', [])
    course = lingfield_1433.get('venue')
    
    scored_horses = []
    for runner in runners:
        score, breakdown, reasons = analyze_horse_comprehensive(runner, course)
        if score > 0:
            scored_horses.append({
                'name': runner.get('name'),
                'score': score,
                'odds': runner.get('odds', 0)
            })
    
    # Sort by score
    scored_horses.sort(key=lambda x: x['score'], reverse=True)
    
    horses_85_plus = [h for h in scored_horses if h['score'] >= 85]
    
    print(f"\nTotal runners: {len(runners)}")
    print(f"Horses with scores > 0: {len(scored_horses)}")
    print(f"Horses scoring 85+: {len(horses_85_plus)}\n")
    
    for h in scored_horses[:10]:  # Show top 10
        marker = "⭐" if h['score'] >= 85 else "  "
        print(f"{marker} {h['name'][:30]:30} {h['score']:3.0f}/100  @ {h['odds']}")
    
    if len(horses_85_plus) >= 2:
        print(f"\n✓ This race SHOULD BE SKIPPED ({len(horses_85_plus)} horses at 85+)")
    else:
        print(f"\n✓ This race is OK to pick from (only {len(horses_85_plus)} horse at 85+)")

# Test Fairyhouse 15:15
print("\n" + "=" * 80)
print("Fairyhouse 15:15 - ALL HORSE SCORES:")
print("=" * 80)

fairyhouse_1515 = None
for race in races:
    if race.get('venue') == 'Fairyhouse' and '15:15' in race.get('start_time', ''):
        fairyhouse_1515 = race
        break

if fairyhouse_1515:
    runners = fairyhouse_1515.get('runners', [])
    course = fairyhouse_1515.get('venue')
    
    scored_horses = []
    for runner in runners:
        score, breakdown, reasons = analyze_horse_comprehensive(runner, course)
        if score > 0:
            scored_horses.append({
                'name': runner.get('name'),
                'score': score,
                'odds': runner.get('odds', 0)
            })
    
    scored_horses.sort(key=lambda x: x['score'], reverse=True)
    horses_85_plus = [h for h in scored_horses if h['score'] >= 85]
    
    print(f"\nTotal runners: {len(runners)}")
    print(f"Horses scoring 85+: {len(horses_85_plus)}\n")
    
    for h in scored_horses:
        marker = "⭐" if h['score'] >= 85 else "  "
        print(f"{marker} {h['name'][:30]:30} {h['score']:3.0f}/100  @ {h['odds']}")
    
    if len(horses_85_plus) >= 2:
        print(f"\n✓ This race SHOULD BE SKIPPED ({len(horses_85_plus)} horses at 85+)")
    else:
        print(f"\n✓ This race is OK to pick from (only {len(horses_85_plus)} horse at 85+)")

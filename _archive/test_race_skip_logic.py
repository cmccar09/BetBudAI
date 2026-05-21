"""Test that races with multiple 85+ horses are skipped"""
from comprehensive_pick_logic import get_comprehensive_pick
import json

# Load races
with open('response_horses.json', 'r') as f:
    data = json.load(f)

races = data.get('races', [])

# Test Lingfield 14:33 (had Green Sky 90 and Tortured Soul 89)
lingfield_1433 = None
for race in races:
    if race.get('venue') == 'Lingfield' and '14:33' in race.get('start_time', ''):
        lingfield_1433 = race
        break

if lingfield_1433:
    print("Testing Lingfield 14:33 (had 2 horses at 85+):")
    print(f"Runners: {len(lingfield_1433.get('runners', []))}")
    
    result = get_comprehensive_pick(lingfield_1433)
    
    if result is None:
        print("✓ RACE CORRECTLY SKIPPED (too close to call)")
    else:
        horse_name = result.get('horse', {}).get('name', 'Unknown')
        score = result.get('score', 0)
        print(f"✗ PROBLEM: Race returned pick {horse_name} @ {score}/100")
        print(f"   Should have been skipped!")
else:
    print("Lingfield 14:33 not found in data")

# Test Fairyhouse 15:15 (had 3 horses at 85+: Lecky Watson 101, Spanish Harlem 93, Three Card Brag 86)
fairyhouse_1515 = None
for race in races:
    if race.get('venue') == 'Fairyhouse' and '15:15' in race.get('start_time', ''):
        fairyhouse_1515 = race
        break

if fairyhouse_1515:
    print("\nTesting Fairyhouse 15:15 (had 3 horses at 85+):")
    print(f"Runners: {len(fairyhouse_1515.get('runners', []))}")
    
    result = get_comprehensive_pick(fairyhouse_1515)
    
    if result is None:
        print("✓ RACE CORRECTLY SKIPPED (too close to call)")
    else:
        horse_name = result.get('horse', {}).get('name', 'Unknown')
        score = result.get('score', 0)
        print(f"✗ PROBLEM: Race returned pick {horse_name} @ {score}/100")
        print(f"   Should have been skipped!")
else:
    print("Fairyhouse 15:15 not found in data")

# Test a race that should NOT be skipped (only 1 horse at 85+)
print("\nTesting Fairyhouse 15:45 (Rokathir 111 - only 1 at 85+):")
fairyhouse_1545 = None
for race in races:
    if race.get('venue') == 'Fairyhouse' and '15:45' in race.get('start_time', ''):
        fairyhouse_1545 = race
        break

if fairyhouse_1545:
    result = get_comprehensive_pick(fairyhouse_1545)
    
    if result is None:
        print("✗ PROBLEM: Race was skipped but should have returned a pick!")
    else:
        horse_name = result.get('horse', {}).get('name', 'Unknown')
        score = result.get('score', 0)
        print(f"✓ CORRECT: Race returned pick {horse_name} @ {score}/100")
else:
    print("Fairyhouse 15:45 not found in data")

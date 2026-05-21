#!/usr/bin/env python3
"""Test the race filtering logic"""

from save_selections_to_dynamodb import filter_picks_per_race

# Test case 1: 3 picks same race, 2 same type
test_bets = [
    {'horse': 'Horse A', 'course': 'Leopardstown', 'race_time': '14:00', 'bet_type': 'WIN', 'decision_score': 75},
    {'horse': 'Horse B', 'course': 'Leopardstown', 'race_time': '14:00', 'bet_type': 'WIN', 'decision_score': 80},
    {'horse': 'Horse C', 'course': 'Leopardstown', 'race_time': '14:00', 'bet_type': 'EW', 'decision_score': 70},
]

print('Test 1: 3 picks, 2 WIN + 1 EW')
print('Expected: Keep Horse B (WIN, highest) + Horse C (EW)')
filtered, removed = filter_picks_per_race(test_bets)
print(f'Kept {len(filtered)} picks, removed {removed}')
for pick in filtered:
    print(f'  - {pick["horse"]} ({pick["bet_type"]}) score={pick["decision_score"]}')

# Test case 2: 2 picks same race, both WIN
test_bets2 = [
    {'horse': 'Horse D', 'course': 'Naas', 'race_time': '15:00', 'bet_type': 'WIN', 'decision_score': 65},
    {'horse': 'Horse E', 'course': 'Naas', 'race_time': '15:00', 'bet_type': 'WIN', 'decision_score': 72},
]

print('\nTest 2: 2 picks, both WIN')
print('Expected: Keep only Horse E (higher score)')
filtered2, removed2 = filter_picks_per_race(test_bets2)
print(f'Kept {len(filtered2)} picks, removed {removed2}')
for pick in filtered2:
    print(f'  - {pick["horse"]} ({pick["bet_type"]}) score={pick["decision_score"]}')

# Test case 3: 2 picks same race, WIN and EW
test_bets3 = [
    {'horse': 'Horse F', 'course': 'Cork', 'race_time': '16:00', 'bet_type': 'WIN', 'decision_score': 68},
    {'horse': 'Horse G', 'course': 'Cork', 'race_time': '16:00', 'bet_type': 'EW', 'decision_score': 71},
]

print('\nTest 3: 2 picks, WIN and EW')
print('Expected: Keep both (different types)')
filtered3, removed3 = filter_picks_per_race(test_bets3)
print(f'Kept {len(filtered3)} picks, removed {removed3}')
for pick in filtered3:
    print(f'  - {pick["horse"]} ({pick["bet_type"]}) score={pick["decision_score"]}')

# Test case 4: Different races
test_bets4 = [
    {'horse': 'Horse H', 'course': 'Fairyhouse', 'race_time': '13:00', 'bet_type': 'WIN', 'decision_score': 80},
    {'horse': 'Horse I', 'course': 'Fairyhouse', 'race_time': '14:00', 'bet_type': 'WIN', 'decision_score': 75},
]

print('\nTest 4: 2 picks, different races')
print('Expected: Keep both (different races)')
filtered4, removed4 = filter_picks_per_race(test_bets4)
print(f'Kept {len(filtered4)} picks, removed {removed4}')
for pick in filtered4:
    print(f'  - {pick["horse"]} at {pick["race_time"]} ({pick["bet_type"]}) score={pick["decision_score"]}')

print('\n✓ All tests completed!')

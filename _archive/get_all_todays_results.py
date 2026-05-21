import requests
from datetime import datetime
from decimal import Decimal
import json

print("\n" + "="*80)
print("FETCHING ALL TODAY'S RACE RESULTS")
print("="*80)

# Today's races we tracked
todays_picks = [
    {
        'time': '13:35',
        'course': 'Kempton',
        'our_pick': 'Unknown',
        'odds': None
    },
    {
        'time': '14:35',
        'course': 'Kempton',
        'our_pick': 'Unknown',
        'odds': None
    },
    {
        'time': '14:45',
        'course': 'Southwell',
        'our_pick': 'Unknown',
        'odds': None
    },
    {
        'time': '15:07',
        'course': 'Kempton',
        'our_pick': 'Unknown',
        'odds': None
    },
    {
        'time': '15:52',
        'course': 'Southwell',
        'our_pick': 'Unknown',
        'odds': None
    },
    {
        'time': '16:27',
        'course': 'Southwell',
        'our_pick': 'Unknown',
        'odds': None
    },
    {
        'time': '17:00',
        'course': 'Wolverhampton',
        'our_pick': 'Take The Boat',
        'odds': Decimal('4.0')
    },
    {
        'time': '17:30',
        'course': 'Wolverhampton',
        'our_pick': 'Horace Wallace',
        'odds': Decimal('4.0')
    },
    {
        'time': '18:00',
        'course': 'Wolverhampton',
        'our_pick': 'My Genghis',
        'odds': Decimal('5.0')
    },
    {
        'time': '18:30',
        'course': 'Wolverhampton',
        'our_pick': 'Mr Nugget',
        'odds': Decimal('6.0')
    },
    {
        'time': '19:00',
        'course': 'Wolverhampton',
        'our_pick': 'The Dark Baron',
        'odds': Decimal('5.1')
    }
]

# Actual winners from your analysis files
actual_results = {
    '17:00_Wolverhampton': {'winner': 'Take The Boat', 'odds': Decimal('4.0')},
    '17:30_Wolverhampton': {'winner': 'Horace Wallace', 'odds': Decimal('4.0')},
    '18:00_Wolverhampton': {'winner': 'My Genghis', 'odds': Decimal('5.0')},
    '18:30_Wolverhampton': {'winner': 'Mr Nugget', 'odds': Decimal('6.0')},
    '19:00_Wolverhampton': {'winner': 'Law Supreme', 'odds': Decimal('8.8')},
}

print("\nTODAY'S RESULTS:")
print("="*80)

wins = 0
losses = 0
total_picks = 0

for pick in todays_picks:
    race_key = f"{pick['time']}_{pick['course']}"
    
    if race_key in actual_results:
        actual = actual_results[race_key]
        our_pick = pick['our_pick']
        
        if our_pick != 'Unknown':
            total_picks += 1
            if our_pick == actual['winner']:
                result = '✓ WIN'
                wins += 1
                color = 'GREEN'
            else:
                result = '✗ LOSS'
                losses += 1
                color = 'RED'
            
            print(f"\n{pick['time']} {pick['course']}")
            print(f"  Our pick: {our_pick} @ {pick['odds']}")
            print(f"  Winner: {actual['winner']} @ {actual['odds']}")
            print(f"  Result: {result}")

print("\n" + "="*80)
print(f"SUMMARY: {wins} wins, {losses} losses from {total_picks} picks")
if total_picks > 0:
    win_rate = (wins / total_picks) * 100
    print(f"Win Rate: {win_rate:.1f}%")
print("="*80)

# Sweet spot analysis
print("\nSWEET SPOT VALIDATION:")
print("="*80)

sweet_spot_wins = []
sweet_spot_losses = []

for pick in todays_picks:
    race_key = f"{pick['time']}_{pick['course']}"
    if race_key in actual_results and pick['our_pick'] != 'Unknown':
        odds = float(pick['odds'])
        if 3.0 <= odds <= 9.0:
            if pick['our_pick'] == actual_results[race_key]['winner']:
                sweet_spot_wins.append(f"{pick['our_pick']} @ {odds}")
            else:
                sweet_spot_losses.append(f"{pick['our_pick']} @ {odds} (winner: {actual_results[race_key]['winner']} @ {actual_results[race_key]['odds']})")

print(f"\nSweet Spot Picks (3-9 odds):")
print(f"  Wins: {len(sweet_spot_wins)}")
for win in sweet_spot_wins:
    print(f"    ✓ {win}")

print(f"\n  Losses: {len(sweet_spot_losses)}")
for loss in sweet_spot_losses:
    print(f"    ✗ {loss}")

sweet_spot_total = len(sweet_spot_wins) + len(sweet_spot_losses)
if sweet_spot_total > 0:
    sweet_spot_rate = (len(sweet_spot_wins) / sweet_spot_total) * 100
    print(f"\n  Sweet Spot Win Rate: {sweet_spot_rate:.1f}%")
    print(f"  Total sweet spot: {len(sweet_spot_wins)}/{sweet_spot_total}")

print("\n" + "="*80)

# Wolverhampton specific
print("\nWOLVERHAMPTON PERFORMANCE:")
print("="*80)

wolverhampton_picks = [p for p in todays_picks if p['course'] == 'Wolverhampton' and p['our_pick'] != 'Unknown']
wolverhampton_wins = sum(1 for p in wolverhampton_picks if actual_results.get(f"{p['time']}_{p['course']}", {}).get('winner') == p['our_pick'])
wolverhampton_total = len(wolverhampton_picks)

print(f"Picks: {wolverhampton_total}")
print(f"Wins: {wolverhampton_wins}")
print(f"Win Rate: {(wolverhampton_wins/wolverhampton_total*100):.1f}%")

print("\nAll Wolverhampton picks:")
for p in wolverhampton_picks:
    race_key = f"{p['time']}_Wolverhampton"
    actual = actual_results[race_key]
    result = '✓' if p['our_pick'] == actual['winner'] else '✗'
    print(f"  {result} {p['time']}: {p['our_pick']} @ {p['odds']}")

print("\n" + "="*80)

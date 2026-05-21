"""
Check all races captured today and their results
Analyze for learning opportunities
"""
import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

print("="*80)
print("ANALYZING ALL RACES CAPTURED TODAY - 2026-02-03")
print("="*80)

# Get ALL items for today
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

all_items = response['Items']
print(f"\nTotal horses analyzed today: {len(all_items)}")

# Categorize
ui_picks = [item for item in all_items if item.get('show_in_ui')]
has_outcome = [item for item in all_items if item.get('outcome') and item.get('outcome') != 'pending']
training_data = [item for item in all_items if not item.get('show_in_ui')]

print(f"UI picks: {len(ui_picks)}")
print(f"With outcomes: {len(has_outcome)}")
print(f"Training data: {len(training_data)}")

# Group by race
races = {}
for item in all_items:
    race_key = f"{item.get('course')}_{item.get('race_time')}"
    if race_key not in races:
        races[race_key] = {
            'horses': [],
            'course': item.get('course'),
            'race_time': item.get('race_time'),
            'total_count': 0,
            'analyzed_count': 0,
            'winner': None
        }
    
    races[race_key]['horses'].append(item)
    races[race_key]['total_count'] += 1
    
    if item.get('comprehensive_score') or item.get('combined_confidence'):
        races[race_key]['analyzed_count'] += 1
    
    if item.get('outcome') == 'win':
        races[race_key]['winner'] = item

print(f"\nTotal races: {len(races)}")

# Analyze each race
print(f"\n{'='*80}")
print("RACE ANALYSIS:")
print("="*80)

races_with_winners = 0
races_we_picked = 0
races_we_won = 0
races_we_lost = 0

for race_key in sorted(races.keys(), key=lambda x: races[x]['race_time'] or ''):
    race = races[race_key]
    course = race['course']
    time = race['race_time'][:16] if race['race_time'] else 'Unknown'
    
    coverage = (race['analyzed_count'] / race['total_count'] * 100) if race['total_count'] > 0 else 0
    
    print(f"\n{time} {course}")
    print(f"  Horses: {race['total_count']}, Analyzed: {race['analyzed_count']} ({coverage:.0f}%)")
    
    # Our pick
    our_pick = [h for h in race['horses'] if h.get('show_in_ui')]
    if our_pick:
        pick = our_pick[0]
        score = pick.get('comprehensive_score') or pick.get('combined_confidence', 0)
        outcome = pick.get('outcome', 'pending')
        horse = pick.get('horse', 'Unknown')
        odds = pick.get('odds', 0)
        
        print(f"  Our pick: {horse} ({score}/100 @ {odds})")
        print(f"  Outcome: {outcome.upper()}")
        races_we_picked += 1
        
        if outcome == 'win':
            races_we_won += 1
            print(f"  ✅ WON!")
        elif outcome == 'loss':
            races_we_lost += 1
            print(f"  ❌ LOST")
    
    # Winner
    if race['winner']:
        winner = race['winner']
        winner_score = winner.get('comprehensive_score') or winner.get('combined_confidence', 0)
        winner_odds = winner.get('odds', 0)
        winner_name = winner.get('horse', 'Unknown')
        
        print(f"  Actual winner: {winner_name} ({winner_score}/100 @ {winner_odds})")
        races_with_winners += 1
        
        # Did we miss it?
        if not our_pick or our_pick[0].get('horse') != winner_name:
            print(f"  ⚠️ We missed this winner!")
            
            # Analyze why
            if winner_score < 55:
                print(f"     Reason: Score too low ({winner_score}/100 < 55 threshold)")
            elif winner_score < 70:
                print(f"     Reason: Not in TOP 10 (score {winner_score}/100)")
            else:
                print(f"     Reason: Good score ({winner_score}/100) but beaten by our pick")

# Summary
print(f"\n{'='*80}")
print("LEARNING SUMMARY:")
print("="*80)
print(f"Total races: {len(races)}")
print(f"Races with known winners: {races_with_winners}")
print(f"Races we made picks: {races_we_picked}")
print(f"Our wins: {races_we_won}")
print(f"Our losses: {races_we_lost}")

if races_we_picked > 0:
    win_rate = (races_we_won / races_we_picked) * 100
    print(f"Win rate: {win_rate:.1f}%")
    
    if races_with_winners > 0:
        capture_rate = (races_we_won / races_with_winners) * 100
        print(f"Winner capture rate: {capture_rate:.1f}%")

print(f"\n{'='*80}")
print("NEXT STEPS:")
print("="*80)
print("1. Run complete_race_learning.py to learn from all winners")
print("2. Update scoring weights based on missed winners")
print("3. Analyze why high-scoring horses lost")
print("="*80)

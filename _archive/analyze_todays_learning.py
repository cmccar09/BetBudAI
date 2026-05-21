"""
Fetch results for today's races and analyze scoring logic effectiveness
Compare predictions vs actual outcomes to improve the algorithm
"""

import boto3
import subprocess
import sys
from datetime import datetime
from decimal import Decimal

print("="*70)
print("TODAY'S LEARNING ANALYSIS")
print("="*70)
print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-05'

# Step 1: Fetch results from Racing Post/Betfair
print("STEP 1: Fetching race results...")
print("-" * 70)
try:
    result = subprocess.run(
        ['python', 'betfair_results_fetcher_v2.py'],
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode == 0:
        print("✓ Results fetched")
        # Show summary
        if result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines[-10:]:
                if 'Updated' in line or 'WON' in line or 'PLACED' in line:
                    print(f"  {line}")
    else:
        print("⚠ Results fetch had issues")
        if result.stderr:
            print(f"  {result.stderr[:300]}")
except Exception as e:
    print(f"⚠ Error fetching results: {e}")

print()

# Step 2: Get all today's data with outcomes
print("STEP 2: Analyzing predictions vs actual outcomes...")
print("-" * 70)

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response.get('Items', [])

print(f"Total horses analyzed: {len(items)}")
print()

# Separate by outcome
completed_races = [item for item in items if item.get('outcome') in ['WON', 'PLACED', 'LOST']]
pending_races = [item for item in items if not item.get('outcome') or item.get('outcome') not in ['WON', 'PLACED', 'LOST']]

print(f"Completed races: {len(completed_races)} horses")
print(f"Pending races: {len(pending_races)} horses")
print()

if not completed_races:
    print("⚠ No completed races yet - results not available")
    print("  Run this script again after races have finished")
    sys.exit(0)

# Step 3: Analyze winners vs our predictions
print("STEP 3: Winners Analysis")
print("-" * 70)

winners = [item for item in completed_races if item.get('outcome') == 'WON']
placed = [item for item in completed_races if item.get('outcome') == 'PLACED']
losers = [item for item in completed_races if item.get('outcome') == 'LOST']

print(f"Winners: {len(winners)}")
print(f"Placed: {len(placed)}")
print(f"Losers: {len(losers)}")
print()

# Analyze score distribution of winners
if winners:
    print("WINNER SCORE ANALYSIS:")
    print("-" * 70)
    
    winner_scores = []
    for winner in winners:
        score = float(winner.get('combined_confidence', 0))
        horse = winner.get('horse', 'Unknown')
        course = winner.get('course', winner.get('venue', 'Unknown'))
        odds = winner.get('odds', 'N/A')
        race_time = winner.get('race_time', '')
        time_part = race_time.split('T')[1][:5] if 'T' in race_time else ''
        
        winner_scores.append(score)
        
        if score >= 85:
            status = "✓ PREDICTED"
        elif score >= 50:
            status = "~ MODERATE"
        else:
            status = "✗ MISSED"
        
        print(f"{status}  {score:5.1f}/100  {horse:<25} @{odds:<6} {course} {time_part}")
    
    avg_winner_score = sum(winner_scores) / len(winner_scores)
    high_conf_winners = sum(1 for s in winner_scores if s >= 85)
    mid_conf_winners = sum(1 for s in winner_scores if 50 <= s < 85)
    low_conf_winners = sum(1 for s in winner_scores if s < 50)
    
    print()
    print(f"Average winner score: {avg_winner_score:.1f}/100")
    print(f"  85+ score (would bet): {high_conf_winners} winners")
    print(f"  50-84 score (moderate): {mid_conf_winners} winners")
    print(f"  <50 score (missed): {low_conf_winners} winners")
    print()

# Step 4: Analyze what we WOULD have bet on
print("STEP 4: Our Betting Performance")
print("-" * 70)

our_bets = [item for item in completed_races if float(item.get('combined_confidence', 0)) >= 85]

if our_bets:
    bet_wins = sum(1 for item in our_bets if item.get('outcome') == 'WON')
    bet_places = sum(1 for item in our_bets if item.get('outcome') == 'PLACED')
    bet_losses = sum(1 for item in our_bets if item.get('outcome') == 'LOST')
    
    print(f"Would have bet on: {len(our_bets)} horses (85+ threshold)")
    print(f"  Wins: {bet_wins}")
    print(f"  Places: {bet_places}")
    print(f"  Losses: {bet_losses}")
    
    if len(our_bets) > 0:
        win_rate = (bet_wins / len(our_bets)) * 100
        place_rate = ((bet_wins + bet_places) / len(our_bets)) * 100
        print(f"  Win rate: {win_rate:.1f}%")
        print(f"  Place rate: {place_rate:.1f}%")
    
    print()
    print("Detailed breakdown:")
    for bet in sorted(our_bets, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True):
        score = float(bet.get('combined_confidence', 0))
        horse = bet.get('horse', 'Unknown')
        course = bet.get('course', bet.get('venue', 'Unknown'))
        odds = bet.get('odds', 'N/A')
        outcome = bet.get('outcome', 'PENDING')
        race_time = bet.get('race_time', '')
        time_part = race_time.split('T')[1][:5] if 'T' in race_time else ''
        
        if outcome == 'WON':
            result = "✓ WON"
        elif outcome == 'PLACED':
            result = "~ PLACED"
        else:
            result = "✗ LOST"
        
        print(f"  {result}  {score:5.1f}/100  {horse:<25} @{odds:<6} {course} {time_part}")
else:
    print("No horses scored 85+ (correct - no high confidence picks today)")

print()

# Step 5: Identify patterns for improvement
print("STEP 5: Improvement Opportunities")
print("-" * 70)

# Find high scorers that lost
high_score_losers = [item for item in losers if float(item.get('combined_confidence', 0)) >= 70]

if high_score_losers:
    print(f"⚠ HIGH SCORERS THAT LOST ({len(high_score_losers)}):")
    for loser in sorted(high_score_losers, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True):
        score = float(loser.get('combined_confidence', 0))
        horse = loser.get('horse', 'Unknown')
        odds = loser.get('odds', 'N/A')
        course = loser.get('course', loser.get('venue', 'Unknown'))
        print(f"  {score:5.1f}/100  {horse:<25} @{odds:<6} {course}")
    print()

# Find low scorers that won
low_score_winners = [item for item in winners if float(item.get('combined_confidence', 0)) < 50]

if low_score_winners:
    print(f"📈 LOW SCORERS THAT WON ({len(low_score_winners)}):")
    print("  (These are opportunities to improve the algorithm)")
    print()
    for winner in sorted(low_score_winners, key=lambda x: float(x.get('combined_confidence', 0))):
        score = float(winner.get('combined_confidence', 0))
        horse = winner.get('horse', 'Unknown')
        odds = winner.get('odds', 'N/A')
        course = winner.get('course', winner.get('venue', 'Unknown'))
        
        # Get detailed scores
        form_score = winner.get('form_score', 0)
        class_score = winner.get('class_score', 0)
        value_score = winner.get('value_score', 0)
        comprehensive = winner.get('comprehensive_score', 0)
        
        print(f"  {score:5.1f}/100  {horse:<25} @{odds:<6} {course}")
        print(f"           Form:{form_score} Class:{class_score} Value:{value_score} Comprehensive:{comprehensive}")
    print()

# Step 6: Save learning insights
print("STEP 6: Saving learning insights...")
print("-" * 70)

insights = {
    'date': today,
    'total_analyzed': len(items),
    'completed': len(completed_races),
    'winners_count': len(winners),
    'avg_winner_score': avg_winner_score if winners else 0,
    'high_conf_winners': high_conf_winners if winners else 0,
    'low_conf_winners': low_conf_winners if winners else 0,
    'would_have_bet': len(our_bets),
    'actual_wins': bet_wins if our_bets else 0,
    'actual_places': bet_places if our_bets else 0,
    'timestamp': datetime.now().isoformat()
}

# Save to file
import json
with open(f'learning_insights_{today}.json', 'w') as f:
    json.dump(insights, f, indent=2)

print(f"✓ Saved to learning_insights_{today}.json")
print()

# Summary
print("="*70)
print("SUMMARY")
print("="*70)
print(f"Analyzed: {len(items)} horses from {len(completed_races)} completed races")

if winners:
    print(f"Winners average score: {avg_winner_score:.1f}/100")
    print(f"Our 85+ threshold would catch: {high_conf_winners}/{len(winners)} winners ({high_conf_winners/len(winners)*100:.1f}%)")

if our_bets:
    print(f"Our picks performance: {bet_wins}W {bet_places}P from {len(our_bets)} bets")
    if len(our_bets) > 0:
        print(f"  Win rate: {(bet_wins/len(our_bets))*100:.1f}%")
        print(f"  Place rate: {((bet_wins+bet_places)/len(our_bets))*100:.1f}%")
else:
    print("No bets placed (no 85+ scores) - correct defensive strategy")

print()
print("✓ Learning complete - data saved for weight optimization")
print("="*70)

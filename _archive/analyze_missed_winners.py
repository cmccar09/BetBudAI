import boto3
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.scan()
items = response.get('Items', [])

# Get today's items
today_items = [item for item in items 
               if item.get('bet_date') == '2026-02-03' 
               and '2026-02-04' in item.get('race_time', '')]

# Get all winners
winners = [item for item in today_items if item.get('outcome') == 'WON']

print("="*80)
print("ANALYZING MISSED WINNERS - What Can We Learn?")
print("="*80)

# Categorize winners by score
high_scorers = [w for w in winners if float(w.get('combined_confidence', 0)) >= 85]
medium_scorers = [w for w in winners if 60 <= float(w.get('combined_confidence', 0)) < 85]
low_scorers = [w for w in winners if float(w.get('combined_confidence', 0)) < 60]

print(f"\n✅ HIGH SCORERS (85+): {len(high_scorers)} - WE PICKED THESE!")
for w in sorted(high_scorers, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True):
    print(f"  {float(w.get('combined_confidence', 0)):5.1f}/100  {w.get('horse', 'Unknown'):<25} @{w.get('odds', 'N/A')}")

print(f"\n⚠️ MEDIUM SCORERS (60-84): {len(medium_scorers)} - Close but not UI picks")
for w in sorted(medium_scorers, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True):
    print(f"  {float(w.get('combined_confidence', 0)):5.1f}/100  {w.get('horse', 'Unknown'):<25} @{w.get('odds', 'N/A')}")

print(f"\n❌ LOW SCORERS (<60): {len(low_scorers)} - THESE ARE THE LEARNING OPPORTUNITIES")
print("="*80)

for winner in sorted(low_scorers, key=lambda x: float(x.get('combined_confidence', 0))):
    horse = winner.get('horse', 'Unknown')
    score = float(winner.get('combined_confidence', 0))
    odds = winner.get('odds', 'N/A')
    course = winner.get('course', 'Unknown')
    race_time = winner.get('race_time', '')[:16]
    
    print(f"\n🔍 {horse} - Score: {score}/100 @ {odds} ({course})")
    print("-" * 80)
    
    # Get the race to see what we preferred
    race_horses = [item for item in today_items 
                   if item.get('course') == course 
                   and item.get('race_time', '').startswith(race_time)]
    
    # Sort by our score
    race_horses_sorted = sorted(race_horses, 
                                key=lambda x: float(x.get('combined_confidence', 0)), 
                                reverse=True)
    
    print(f"  Our predictions for this race (top 5):")
    for i, h in enumerate(race_horses_sorted[:5], 1):
        h_name = h.get('horse', 'Unknown')
        h_score = float(h.get('combined_confidence', 0))
        h_odds = h.get('odds', 'N/A')
        h_outcome = h.get('outcome', 'PENDING')
        marker = "👈 ACTUAL WINNER" if h_name == horse else f"({h_outcome})"
        print(f"    {i}. {h_score:5.1f}/100  {h_name:<25} @{h_odds:<6} {marker}")
    
    # Analyze what the winner had
    print(f"\n  Winner's attributes:")
    print(f"    Odds: {odds}")
    print(f"    Form: {winner.get('form_quality', 'N/A')}")
    print(f"    Recent wins: {winner.get('days_since_last_win', 'N/A')}")
    print(f"    Course history: {winner.get('course_history', 'N/A')}")
    print(f"    Database history: {winner.get('database_history', 'N/A')}")
    print(f"    Going suitability: {winner.get('going_suitability', 'N/A')}")
    print(f"    Trainer: {winner.get('trainer', 'N/A')}")
    print(f"    Jockey: {winner.get('jockey', 'N/A')}")
    
    # Scoring breakdown if available
    if winner.get('scoring_breakdown'):
        print(f"    Scoring breakdown: {winner.get('scoring_breakdown', 'N/A')}")

# Now analyze common patterns in low-scoring winners
print("\n" + "="*80)
print("PATTERN ANALYSIS - Low Scoring Winners")
print("="*80)

if low_scorers:
    # Analyze odds range
    odds_values = []
    for w in low_scorers:
        try:
            odds_values.append(float(w.get('odds', 0)))
        except:
            pass
    
    if odds_values:
        avg_odds = sum(odds_values) / len(odds_values)
        print(f"\nAverage odds of missed winners: {avg_odds:.2f}")
        favorites = sum(1 for o in odds_values if o < 2.5)
        print(f"Favorites (< 2.5): {favorites}/{len(odds_values)}")
        longshots = sum(1 for o in odds_values if o > 5.0)
        print(f"Longshots (> 5.0): {longshots}/{len(odds_values)}")
    
    # Analyze trainers
    trainers = defaultdict(int)
    for w in low_scorers:
        trainer = w.get('trainer', 'Unknown')
        if trainer and trainer != 'Unknown':
            trainers[trainer] += 1
    
    if trainers:
        print(f"\nTrainers of missed winners:")
        for trainer, count in sorted(trainers.items(), key=lambda x: x[1], reverse=True):
            print(f"  {trainer}: {count}")
    
    # Analyze form quality
    forms = defaultdict(int)
    for w in low_scorers:
        form = w.get('form_quality', 'Unknown')
        forms[form] += 1
    
    print(f"\nForm quality of missed winners:")
    for form, count in sorted(forms.items(), key=lambda x: x[1], reverse=True):
        print(f"  {form}: {count}")

print("\n" + "="*80)
print("RECOMMENDATIONS")
print("="*80)
print("\n1. Heavy favorites (< 1.5 odds) won despite low scores")
print("   → Consider boosting favorite_correction weight further")
print("\n2. Check if elite trainers appear in low-scoring winners")
print("   → May need to increase trainer_reputation weight")
print("\n3. Some longshots won despite low scores")
print("   → These may be unpredictable/noise - OK to miss")
print("\n4. Verify Im Workin On It and Dust Cover")
print("   → These SHOULD have high scores with new weights")
print("   → Their low database scores prove old weights were wrong")

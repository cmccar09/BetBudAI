import boto3
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.scan()
items = response.get('Items', [])

print("\n" + "="*80)
print("LEARNING FROM TODAY'S LOSERS - COMPREHENSIVE ANALYSIS")
print("="*80)

# Get all completed races
completed_races = defaultdict(list)

for item in items:
    outcome = item.get('outcome')
    race_time_str = item.get('race_time', '')
    
    if outcome in ['WON', 'PLACED', 'LOST'] and '2026-02-04' in race_time_str:
        course = item.get('course', 'Unknown')
        if 'T' in race_time_str:
            race_time = race_time_str.split('T')[1][:5]
        else:
            race_time = 'Unknown'
        
        race_key = f'{race_time} {course}'
        completed_races[race_key].append(item)

# Analyze each race
losing_picks = []
winning_picks = []

for race_key in sorted(completed_races.keys()):
    horses = completed_races[race_key]
    
    # Get my top pick
    my_pick = sorted(horses, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True)[0]
    my_outcome = my_pick.get('outcome', 'PENDING')
    
    # Get winner
    winners = [h for h in horses if h.get('outcome') == 'WON']
    
    if my_outcome != 'WON':
        losing_picks.append({
            'race': race_key,
            'my_pick': my_pick.get('horse'),
            'my_score': float(my_pick.get('combined_confidence', 0)),
            'my_odds': my_pick.get('odds', 'N/A'),
            'my_form': my_pick.get('form', 'N/A'),
            'my_trainer': my_pick.get('trainer', 'N/A'),
            'my_outcome': my_outcome,
            'winner': winners[0].get('horse') if winners else 'NOT IN DATABASE',
            'winner_score': float(winners[0].get('combined_confidence', 0)) if winners else 0,
            'winner_odds': winners[0].get('odds', 'N/A') if winners else 'N/A',
            'winner_trainer': winners[0].get('trainer', 'N/A') if winners else 'Unknown'
        })
    else:
        winning_picks.append({
            'race': race_key,
            'horse': my_pick.get('horse'),
            'score': float(my_pick.get('combined_confidence', 0)),
            'odds': my_pick.get('odds', 'N/A'),
            'trainer': my_pick.get('trainer', 'N/A')
        })

print(f"\nRaces analyzed: {len(completed_races)}")
print(f"My winners: {len(winning_picks)}")
print(f"My losers: {len(losing_picks)}")

print("\n" + "="*80)
print("WINNING PICKS ANALYSIS (What worked)")
print("="*80)

for win in winning_picks:
    print(f"\n✓ {win['race']}: {win['horse']}")
    print(f"  Score: {win['score']:.0f}/100")
    print(f"  Odds: {win['odds']}")
    print(f"  Trainer: {win['trainer']}")

print("\n" + "="*80)
print("LOSING PICKS ANALYSIS (What went wrong)")
print("="*80)

for loss in losing_picks:
    print(f"\n✗ {loss['race']}")
    print(f"  My pick: {loss['my_pick']} ({loss['my_score']:.0f}/100) @{loss['my_odds']} - {loss['my_outcome']}")
    print(f"  Trainer: {loss['my_trainer']}")
    print(f"  Winner: {loss['winner']} ({loss['winner_score']:.0f}/100) @{loss['winner_odds']}")
    print(f"  Winner trainer: {loss['winner_trainer']}")
    
    score_diff = loss['my_score'] - loss['winner_score']
    if score_diff > 20:
        print(f"  ⚠️ My pick scored {score_diff:.0f}pts HIGHER than winner!")

print("\n" + "="*80)
print("PATTERN ANALYSIS")
print("="*80)

# 1. Score comparison
print("\n1. SCORING EFFECTIVENESS:")
my_avg_score = sum(l['my_score'] for l in losing_picks) / len(losing_picks) if losing_picks else 0
winner_avg_score = sum(l['winner_score'] for l in losing_picks if l['winner_score'] > 0) / len([l for l in losing_picks if l['winner_score'] > 0]) if losing_picks else 0

print(f"   My losing picks avg score: {my_avg_score:.1f}/100")
print(f"   Actual winners avg score: {winner_avg_score:.1f}/100")
print(f"   Difference: {my_avg_score - winner_avg_score:.1f} pts")

if my_avg_score > winner_avg_score + 10:
    print(f"   ❌ PROBLEM: My higher-scored picks are losing to lower-scored horses")
    print(f"   → Scoring system may be over-valuing certain factors")

# 2. Odds comparison
print("\n2. ODDS PATTERNS:")
high_odds_losses = [l for l in losing_picks if isinstance(l['my_odds'], (int, float)) and float(l['my_odds']) > 5]
low_odds_winners = [l for l in losing_picks if isinstance(l['winner_odds'], (int, float)) and float(l['winner_odds']) < 4]

print(f"   My picks with odds >5: {len(high_odds_losses)}/{len(losing_picks)}")
print(f"   Winners with odds <4: {len(low_odds_winners)}/{len([l for l in losing_picks if l['winner_score'] > 0])}")

if len(low_odds_winners) > len(losing_picks) / 2:
    print(f"   ❌ PROBLEM: Favorites are winning more than my value picks")
    print(f"   → System may be over-weighting odds sweet spot")
    print(f"   → Need to increase weight on proven ability vs value")

# 3. Trainer analysis
print("\n3. TRAINER ANALYSIS:")
elite_trainers = ['W P Mullins', 'W. P. Mullins', 'Willie Mullins', 'Gordon Elliott', 
                  'Nicky Henderson', 'Paul Nicholls', 'Dan Skelton']

winners_with_elite = 0
my_picks_with_elite = 0

for loss in losing_picks:
    winner_trainer = loss.get('winner_trainer', '')
    my_trainer = loss.get('my_trainer', '')
    
    if any(elite in winner_trainer for elite in elite_trainers):
        winners_with_elite += 1
        print(f"   ✓ {loss['race']}: Winner had elite trainer ({winner_trainer})")
    
    if any(elite in my_trainer for elite in elite_trainers):
        my_picks_with_elite += 1

print(f"\n   Winners with elite trainers: {winners_with_elite}/{len([l for l in losing_picks if l['winner_score'] > 0])}")
print(f"   My picks with elite trainers: {my_picks_with_elite}/{len(losing_picks)}")

if winners_with_elite > my_picks_with_elite:
    print(f"   ❌ PROBLEM: Elite trainers winning but not weighted in my system")
    print(f"   → Need to add trainer reputation bonus (+10-15pts)")

# 4. Data coverage
print("\n4. DATA COVERAGE ISSUES:")
missing_winners = [l for l in losing_picks if l['winner'] == 'NOT IN DATABASE']

if missing_winners:
    print(f"   ⚠️ {len(missing_winners)} winners were NOT in my database:")
    for miss in missing_winners:
        print(f"      - {miss['race']}")
    print(f"   → Critical data coverage gap")
    print(f"   → Need to verify 100% runner coverage before each race")

# 5. Form analysis
print("\n5. FORM PATTERN ANALYSIS:")
print("   My losing picks form patterns:")
for loss in losing_picks:
    form = loss.get('my_form', 'N/A')
    print(f"   {loss['my_pick']}: {form}")

print("\n" + "="*80)
print("RECOMMENDED WEIGHT ADJUSTMENTS")
print("="*80)

print("\n1. REDUCE odds-based bonuses:")
print("   Current: sweet_spot (3-9 odds) likely +30pts")
print("   Recommended: Reduce to +20pts")
print("   Reason: Favorites winning despite lower scores")

print("\n2. ADD trainer reputation bonus:")
print("   Elite trainers (Mullins, Elliott, Henderson, Nicholls): +15pts")
print("   Top-tier trainers: +10pts")
print("   Reason: Willie Mullins horses winning with low scores")

print("\n3. INCREASE recent form weight:")
print("   Winners often have consistent placings vs flashy recent wins")
print("   Weight consistency (e.g., 554-P38) over volatility")

print("\n4. ADD favorite bias correction:")
print("   If odds <3.0 AND proven trainer: +10pts")
print("   Reason: Market is pricing these correctly")

print("\n5. REDUCE long-odds value weighting:")
print("   Current system may over-value 7-9 odds range")
print("   Reduce optimal_odds bonus from current level")

print("\n" + "="*80)
print("IMMEDIATE ACTIONS")
print("="*80)

print("\n1. Fix data coverage gaps:")
print("   - Verify 100% runner coverage before each race")
print("   - Add multiple data sources (Racing Post + Betfair + Timeform)")
print("   - Alert if any runner missing")

print("\n2. Test weight adjustments:")
print("   - Reduce sweet_spot from 30 to 20")
print("   - Add trainer_reputation: 15pts for elite")
print("   - Add favorite_correction: 10pts if odds <3.0")

print("\n3. Validate on next race:")
print("   - Apply new weights to 15:10 Kempton")
print("   - Check if scores change meaningfully")
print("   - Compare old vs new predictions")

print("\n" + "="*80)
print()

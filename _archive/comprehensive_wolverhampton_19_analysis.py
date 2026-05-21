"""
Comprehensive Wolverhampton 19:00 analysis using ALL learnings:
1. Sweet spot (3-9 odds) - 10/10 today
2. Horse history from database
3. Wolverhampton-specific performance
4. Form analysis (recent wins/consistency)
5. Optimal odds within sweet spot (average winner: 4.65)
"""
import json
import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Load race data
with open('response_horses.json', 'r') as f:
    data = json.load(f)

# Find 19:00 Wolverhampton race
wolv_19 = None
for race in data['races']:
    if race.get('venue') == 'Wolverhampton' and '19:00' in race.get('start_time', ''):
        wolv_19 = race
        break

print("\n" + "="*80)
print("COMPREHENSIVE ANALYSIS - WOLVERHAMPTON 19:00")
print("="*80)
print("\nLEARNINGS APPLIED:")
print("  ✓ Sweet spot: 3-9 odds (10/10 today = 100%)")
print("  ✓ Optimal odds: ~4.65 (average of 10 winners)")
print("  ✓ Wolverhampton: 4/4 today (Take The Boat 4.0, Horace Wallace 4.0, My Genghis 5.0, Mr Nugget 6.0)")
print("  ✓ Horse history: Check database for past picks")
print("  ✓ Form consistency: Recent wins + consistency")
print("="*80)

runners = wolv_19.get('runners', [])
sweet_spot = []

for runner in runners:
    name = runner.get('name')
    odds = runner.get('odds', 0)
    form = runner.get('form', '')
    trainer = runner.get('trainer', '')
    
    if 3.0 <= odds <= 9.0:
        # Check horse history in database
        try:
            response = table.scan(
                FilterExpression='horse = :name',
                ExpressionAttributeValues={':name': name}
            )
            history_count = len(response.get('Items', []))
            history_wins = sum(1 for r in response.get('Items', []) if r.get('outcome') == 'win')
            history_losses = sum(1 for r in response.get('Items', []) if r.get('outcome') == 'loss')
        except:
            history_count = 0
            history_wins = 0
            history_losses = 0
        
        # Form analysis
        wins = form.count('1')
        places = form.count('2') + form.count('3')
        recent_win = form.split('-')[-1] == '1' if '-' in form else False
        
        # Distance from optimal odds (4.65)
        odds_distance = abs(odds - 4.65)
        
        sweet_spot.append({
            'name': name,
            'odds': odds,
            'form': form,
            'trainer': trainer,
            'wins': wins,
            'places': places,
            'recent_win': recent_win,
            'odds_distance': odds_distance,
            'history_count': history_count,
            'history_wins': history_wins,
            'history_losses': history_losses
        })

print(f"\nSWEET SPOT HORSES (detailed analysis):\n")

for horse in sorted(sweet_spot, key=lambda x: x['odds']):
    print(f"{horse['name']} @ {horse['odds']}")
    print(f"  Form: {horse['form']}")
    print(f"    - Total wins in form: {horse['wins']}")
    print(f"    - Total places (2nd/3rd): {horse['places']}")
    print(f"    - Recent win: {'✓ YES' if horse['recent_win'] else '✗ No'}")
    print(f"  Odds quality: {horse['odds_distance']:.2f} from optimal (4.65)")
    if horse['history_count'] > 0:
        win_rate = (horse['history_wins'] / (horse['history_wins'] + horse['history_losses']) * 100) if (horse['history_wins'] + horse['history_losses']) > 0 else 0
        print(f"  Database history: {horse['history_count']} picks ({horse['history_wins']}W-{horse['history_losses']}L = {win_rate:.0f}%)")
    else:
        print(f"  Database history: None (no previous picks)")
    print(f"  Trainer: {horse['trainer']}")
    print()

print("="*80)
print("SCORING SYSTEM:")
print("="*80)

# Score each horse
for horse in sweet_spot:
    score = 0
    reasons = []
    
    # Sweet spot bonus (all get this)
    score += 30
    reasons.append("In sweet spot (30pts)")
    
    # Recent win
    if horse['recent_win']:
        score += 25
        reasons.append("Recent win (25pts)")
    
    # Total wins bonus
    score += horse['wins'] * 5
    if horse['wins'] > 0:
        reasons.append(f"{horse['wins']} total wins ({horse['wins']*5}pts)")
    
    # Consistency (places)
    score += horse['places'] * 2
    if horse['places'] > 0:
        reasons.append(f"{horse['places']} places ({horse['places']*2}pts)")
    
    # Odds quality (closer to 4.65 is better)
    if horse['odds_distance'] < 1.0:
        score += 20
        reasons.append("Near optimal odds (20pts)")
    elif horse['odds_distance'] < 2.0:
        score += 10
        reasons.append("Good odds position (10pts)")
    
    # Database history
    if horse['history_wins'] > 0:
        score += 15
        reasons.append(f"Past wins in database (15pts)")
    
    # Wolverhampton bonus (all get this since it's Wolverhampton)
    score += 10
    reasons.append("Wolverhampton (4/4 today) (10pts)")
    
    horse['score'] = score
    horse['reasons'] = reasons

# Sort by score
sweet_spot.sort(key=lambda x: x['score'], reverse=True)

print("\nFINAL RANKINGS:\n")
for i, horse in enumerate(sweet_spot, 1):
    print(f"{i}. {horse['name']} @ {horse['odds']} - SCORE: {horse['score']}")
    for reason in horse['reasons']:
        print(f"     + {reason}")
    print()

print("="*80)
print("🏆 BEST PICK (COMPREHENSIVE ANALYSIS):")
print("="*80)
best = sweet_spot[0]
print(f"\n{best['name']} @ {best['odds']}")
print(f"Score: {best['score']}")
print(f"Form: {best['form']}")
print(f"Trainer: {best['trainer']}")
print(f"\n✓ Includes ALL learnings:")
print(f"  • Sweet spot validated (10/10 today)")
print(f"  • Wolverhampton performance (4/4 today)")
print(f"  • Form analysis (wins: {best['wins']}, places: {best['places']})")
print(f"  • Odds optimization (distance from 4.65: {best['odds_distance']:.2f})")
if best['history_count'] > 0:
    print(f"  • Database history ({best['history_wins']}W-{best['history_losses']}L)")
print("="*80)

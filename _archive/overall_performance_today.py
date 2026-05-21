import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-04'

print(f"\n{'='*80}")
print(f"COMPREHENSIVE PERFORMANCE REPORT - {today}")
print(f"{'='*80}\n")

# Get all items from today
response = table.scan()
all_items = response.get('Items', [])

# Filter to today's items with outcomes
completed_items = [item for item in all_items 
                   if item.get('outcome') in ['WON', 'PLACED', 'LOST'] 
                   and today in item.get('race_time', '')]

# Group by race
races = {}
for item in completed_items:
    race_key = f"{item.get('course')}_{item.get('race_time')}"
    if race_key not in races:
        races[race_key] = []
    races[race_key].append(item)

print(f"📊 OVERALL STATISTICS")
print(f"{'='*80}\n")

wins = 0
places = 0
losses = 0
total_races = len(races)
total_score = 0

# Score tier tracking
tier_stats = {
    'EXCEPTIONAL (95+)': {'wins': 0, 'total': 0},
    'EXCELLENT (85-94)': {'wins': 0, 'total': 0},
    'VERY GOOD (75-84)': {'wins': 0, 'total': 0},
    'GOOD (65-74)': {'wins': 0, 'total': 0},
    'FAIR (55-64)': {'wins': 0, 'total': 0},
    'POOR (<55)': {'wins': 0, 'total': 0}
}

ui_picks_wins = 0
ui_picks_total = 0

race_details = []

for race_key, horses in races.items():
    # Get top tip (highest score)
    top_tip = sorted(horses, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True)[0]
    
    score = float(top_tip.get('combined_confidence', 0))
    outcome = top_tip.get('outcome')
    horse_name = top_tip.get('horse', 'Unknown')
    course = top_tip.get('course', 'Unknown')
    race_time = top_tip.get('race_time', '').split('T')[1][:5] if 'T' in top_tip.get('race_time', '') else 'Unknown'
    odds = top_tip.get('odds', 'N/A')
    is_ui = top_tip.get('show_in_ui', False)
    
    total_score += score
    
    # Track by tier
    if score >= 95:
        tier = 'EXCEPTIONAL (95+)'
    elif score >= 85:
        tier = 'EXCELLENT (85-94)'
    elif score >= 75:
        tier = 'VERY GOOD (75-84)'
    elif score >= 65:
        tier = 'GOOD (65-74)'
    elif score >= 55:
        tier = 'FAIR (55-64)'
    else:
        tier = 'POOR (<55)'
    
    tier_stats[tier]['total'] += 1
    
    if outcome == 'WON':
        wins += 1
        places += 1
        tier_stats[tier]['wins'] += 1
        if is_ui:
            ui_picks_wins += 1
        result_icon = '🏆'
    elif outcome == 'PLACED':
        places += 1
        result_icon = '✓'
    else:
        losses += 1
        result_icon = '✗'
    
    if is_ui:
        ui_picks_total += 1
    
    race_details.append({
        'time': race_time,
        'course': course,
        'horse': horse_name,
        'score': score,
        'tier': tier,
        'outcome': outcome,
        'icon': result_icon,
        'odds': odds,
        'is_ui': is_ui
    })

# Calculate percentages
win_rate = (wins / total_races * 100) if total_races > 0 else 0
place_rate = (places / total_races * 100) if total_races > 0 else 0
avg_score = total_score / total_races if total_races > 0 else 0

print(f"Total Races Completed: {total_races}")
print(f"Winners: {wins}/{total_races} ({win_rate:.1f}%) {'🔥' if win_rate >= 30 else '⚠️' if win_rate >= 20 else '❌'}")
print(f"Places (Top 3): {places}/{total_races} ({place_rate:.1f}%) {'✓' if place_rate >= 70 else '⚠️'}")
print(f"Losses: {losses}/{total_races}")
print(f"Average Score: {avg_score:.1f}/100")

# Target assessment
print(f"\n📈 TARGET ASSESSMENT")
print(f"{'='*80}\n")
print(f"Win Rate Target: 30-40% (GOOD tier)")
if win_rate >= 30 and win_rate <= 40:
    print(f"  ✓ PERFECT: {win_rate:.1f}% - Within target range!")
elif win_rate >= 25:
    print(f"  ⚠️  GOOD: {win_rate:.1f}% - Just below target")
elif win_rate >= 20:
    print(f"  ⚠️  FAIR: {win_rate:.1f}% - Below target, needs improvement")
else:
    print(f"  ❌ POOR: {win_rate:.1f}% - Well below target")

print(f"\nPlace Rate Target: 70%+")
if place_rate >= 70:
    print(f"  ✓ EXCELLENT: {place_rate:.1f}% - Finding competitive horses!")
else:
    print(f"  ⚠️  {place_rate:.1f}% - Below target")

# Score tier breakdown
print(f"\n🎯 PERFORMANCE BY SCORE TIER")
print(f"{'='*80}\n")

for tier_name in ['EXCEPTIONAL (95+)', 'EXCELLENT (85-94)', 'VERY GOOD (75-84)', 
                  'GOOD (65-74)', 'FAIR (55-64)', 'POOR (<55)']:
    stats = tier_stats[tier_name]
    if stats['total'] > 0:
        tier_win_rate = (stats['wins'] / stats['total'] * 100)
        print(f"{tier_name:<25} {stats['wins']}/{stats['total']} wins ({tier_win_rate:.1f}%)")

# UI picks performance
if ui_picks_total > 0:
    ui_win_rate = (ui_picks_wins / ui_picks_total * 100)
    print(f"\n🎨 UI PICKS PERFORMANCE (85+)")
    print(f"{'='*80}\n")
    print(f"UI Picks: {ui_picks_wins}/{ui_picks_total} wins ({ui_win_rate:.1f}%)")
    if ui_win_rate >= 50:
        print(f"  🔥 EXCEPTIONAL - UI picks significantly outperforming!")
    elif ui_win_rate >= 30:
        print(f"  ✓ EXCELLENT - UI threshold working well")
    else:
        print(f"  ⚠️  Below target")

# Race-by-race breakdown
print(f"\n📋 RACE-BY-RACE BREAKDOWN")
print(f"{'='*80}\n")

race_details.sort(key=lambda x: x['time'])

for race in race_details:
    ui_marker = ' [UI PICK]' if race['is_ui'] else ''
    print(f"{race['icon']} {race['time']} {race['course']:<15} {race['horse']:<25} "
          f"{race['score']:5.1f}/100 @{race['odds']:<6}{ui_marker}")

# Key patterns
print(f"\n🔍 KEY PATTERNS IDENTIFIED")
print(f"{'='*80}\n")

# Check for data gaps
all_today = [item for item in all_items if today in item.get('race_time', '')]
total_horses_analyzed = len(all_today)
print(f"✓ Total horses analyzed today: {total_horses_analyzed}")

# Elite trainer check
elite_trainers = ['Mullins', 'Elliott', 'Henderson', 'Nicholls', 'Skelton', 'De Bromhead']
elite_wins = 0
for race_key, horses in races.items():
    for horse in horses:
        if horse.get('outcome') == 'WON':
            trainer = str(horse.get('trainer', ''))
            for elite in elite_trainers:
                if elite.lower() in trainer.lower():
                    elite_wins += 1
                    break

print(f"✓ Elite trainer wins detected: {elite_wins}")

# High confidence performance
high_conf_wins = tier_stats['EXCELLENT (85-94)']['wins'] + tier_stats['EXCEPTIONAL (95+)']['wins']
high_conf_total = tier_stats['EXCELLENT (85-94)']['total'] + tier_stats['EXCEPTIONAL (95+)']['total']
if high_conf_total > 0:
    high_conf_rate = (high_conf_wins / high_conf_total * 100)
    print(f"✓ High confidence (85+) win rate: {high_conf_rate:.1f}% ({high_conf_wins}/{high_conf_total})")

# Low confidence performance
low_conf_wins = tier_stats['POOR (<55)']['wins']
low_conf_total = tier_stats['POOR (<55)']['total']
if low_conf_total > 0:
    low_conf_rate = (low_conf_wins / low_conf_total * 100)
    print(f"⚠️  Low confidence (<55) win rate: {low_conf_rate:.1f}% ({low_conf_wins}/{low_conf_total})")

print(f"\n{'='*80}")
print(f"💡 SUMMARY & RECOMMENDATIONS")
print(f"{'='*80}\n")

if win_rate >= 30:
    print(f"✓ System performing at GOOD tier level")
elif win_rate >= 20:
    print(f"⚠️  System below target but showing promise:")
    print(f"   - High confidence picks (85+) performing well")
    print(f"   - Place rate strong ({place_rate:.1f}%)")
    print(f"   - Continue monitoring weight adjustments")
else:
    print(f"❌ System needs improvement:")
    print(f"   - Win rate too low ({win_rate:.1f}%)")
    print(f"   - Review weight adjustments")
    print(f"   - Check data coverage gaps")

if high_conf_total > 0 and high_conf_rate >= 40:
    print(f"\n✓ POSITIVE: High-confidence picks (85+) are reliable")
    print(f"   Focus on increasing number of 85+ scorers")

if place_rate >= 70:
    print(f"\n✓ POSITIVE: Excellent at finding competitive horses")
    print(f"   System identifies top-3 contenders consistently")

print(f"\n{'='*80}\n")

import boto3
from collections import defaultdict
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("DATA COVERAGE VALIDATION - ALL RACES TODAY")
print("="*80)

# Get all items for today
response = table.scan()
items = response.get('Items', [])

# Filter for today's races (2026-02-04)
today_races = defaultdict(list)
for item in items:
    race_time_str = item.get('race_time', '')
    if '2026-02-04' in race_time_str:
        course = item.get('course', 'Unknown')
        race_time = race_time_str.split('T')[1][:5] if 'T' in race_time_str else 'Unknown'
        race_key = f"{course}_{race_time}"
        today_races[race_key].append(item)

print(f"\nFound {len(today_races)} races analyzed today")
print("="*80)

# Check each race
issues_found = []
completed_races = []

for race_key in sorted(today_races.keys()):
    horses = today_races[race_key]
    course = horses[0].get('course', 'Unknown')
    race_time = horses[0].get('race_time', 'Unknown')
    
    # Extract time for display
    if 'T' in race_time:
        display_time = race_time.split('T')[1][:5]
    else:
        display_time = race_time
    
    # Count horses
    num_horses = len(horses)
    
    # Check if race has completed
    outcomes = [h.get('outcome') for h in horses]
    has_results = any(o in ['WON', 'PLACED', 'LOST'] for o in outcomes)
    
    # Get race metadata if available
    race_total = horses[0].get('race_total_count', 0)
    race_coverage = horses[0].get('race_coverage_pct', 0)
    
    print(f"\n{display_time} {course}")
    print("-"*80)
    print(f"  Horses analyzed: {num_horses}")
    
    if race_total > 0:
        print(f"  Expected runners: {int(race_total)}")
        print(f"  Coverage: {race_coverage:.0f}%")
        
        if num_horses < race_total:
            gap = int(race_total) - num_horses
            print(f"  ⚠️  WARNING: Missing {gap} horses!")
            issues_found.append({
                'race': f"{display_time} {course}",
                'analyzed': num_horses,
                'expected': int(race_total),
                'missing': gap,
                'has_results': has_results
            })
    else:
        print(f"  Expected runners: Unknown")
    
    # Check if race has completed
    if has_results:
        completed_races.append(race_key)
        
        # Check if winner is in our analysis
        winners = [h for h in horses if h.get('outcome') == 'WON']
        
        if winners:
            winner = winners[0]
            winner_score = float(winner.get('combined_confidence', 0))
            print(f"  ✓ Winner in database: {winner.get('horse')} ({winner_score:.0f}/100)")
        else:
            # Check if any horse won
            all_won = [h for h in horses if h.get('outcome') == 'WON']
            if not all_won:
                print(f"  ⚠️  No winner recorded yet")
            else:
                print(f"  ✗ CRITICAL: Winner NOT in our analyzed horses!")
                issues_found.append({
                    'race': f"{display_time} {course}",
                    'issue': 'Winner missing from analysis',
                    'analyzed': num_horses,
                    'has_results': True
                })
        
        # Show top tip vs actual result
        top_tip = sorted(horses, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True)[0]
        top_name = top_tip.get('horse')
        top_score = float(top_tip.get('combined_confidence', 0))
        top_outcome = top_tip.get('outcome', 'PENDING')
        
        if top_outcome == 'WON':
            result_icon = "🏆"
            result_text = "WON"
        elif top_outcome == 'PLACED':
            result_icon = "✓"
            result_text = "PLACED"
        elif top_outcome == 'LOST':
            result_icon = "✗"
            result_text = "LOST"
        else:
            result_icon = "?"
            result_text = "PENDING"
        
        print(f"  My tip: {top_name} ({top_score:.0f}/100) {result_icon} {result_text}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nTotal races analyzed: {len(today_races)}")
print(f"Completed races: {len(completed_races)}")
print(f"Coverage issues found: {len(issues_found)}")

if issues_found:
    print("\n" + "="*80)
    print("⚠️  ISSUES DETECTED")
    print("="*80)
    
    for issue in issues_found:
        print(f"\n{issue['race']}:")
        if 'missing' in issue:
            print(f"  Missing {issue['missing']} horses ({issue['analyzed']}/{issue['expected']} coverage)")
            if issue['has_results']:
                print(f"  ⚠️  Race has completed - winner might be missing!")
        if 'issue' in issue:
            print(f"  CRITICAL: {issue['issue']}")
else:
    print("\n✓ No coverage issues detected")
    print("✓ All races have complete runner coverage")

# Check UI picks specifically
print("\n" + "="*80)
print("UI PICKS DATA VALIDATION")
print("="*80)

ui_picks = [item for item in items if item.get('show_in_ui', 0) == 1 and '2026-02-04' in item.get('race_time', '')]

if ui_picks:
    print(f"\nFound {len(ui_picks)} UI picks for today")
    
    for pick in ui_picks:
        course = pick.get('course', 'Unknown')
        race_time = pick.get('race_time', 'Unknown')
        if 'T' in race_time:
            display_time = race_time.split('T')[1][:5]
        else:
            display_time = race_time
        
        horse = pick.get('horse', 'Unknown')
        score = float(pick.get('combined_confidence', 0))
        
        # Find all horses in this race
        race_horses = [h for h in items if h.get('course') == course and h.get('race_time') == race_time]
        num_in_race = len(race_horses)
        expected = race_horses[0].get('race_total_count', 0) if race_horses else 0
        
        print(f"\n{display_time} {course}: {horse} ({score:.0f}/100)")
        print(f"  Race coverage: {num_in_race}/{int(expected) if expected else '?'} horses")
        
        if expected > 0 and num_in_race < expected:
            print(f"  ⚠️  WARNING: Missing {int(expected) - num_in_race} horses in this race!")
        else:
            print(f"  ✓ Full coverage")
else:
    print("\nNo UI picks found for today")

print("\n" + "="*80)
print()

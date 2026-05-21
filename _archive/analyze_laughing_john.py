"""
Check Wincanton results today and analyze Laughing John pick
"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

# Get all Wincanton picks/results today
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response.get('Items', [])
wincanton = [i for i in items if i.get('course', '').lower() == 'wincanton']

print('='*100)
print(f'WINCANTON ANALYSIS - {today}')
print('='*100)

# Group by race time
from collections import defaultdict
races = defaultdict(list)

for pick in wincanton:
    race_time = pick.get('race_time', 'Unknown')
    if 'T' in str(race_time):
        time_key = str(race_time).split('T')[1][:5]
    else:
        time_key = 'TBA'
    races[time_key].append(pick)

# Sort races by time
sorted_races = sorted(races.items())

print(f'\nTotal Wincanton horses analyzed: {len(wincanton)}')
print(f'Number of races: {len(races)}\n')

# Check each race
for race_time, horses in sorted_races:
    print(f'\n{"="*100}')
    print(f'Race Time: {race_time}')
    print('='*100)
    
    # Check if any have results
    with_results = [h for h in horses if h.get('outcome')]
    
    if with_results:
        print(f'✅ RACE COMPLETED - {len(with_results)} results available\n')
        
        # Show results sorted by finish
        winners = [h for h in with_results if h.get('outcome', '').lower() == 'won']
        others = [h for h in with_results if h.get('outcome', '').lower() != 'won']
        
        if winners:
            for h in winners:
                horse = h.get('horse', 'Unknown')
                score = float(h.get('comprehensive_score', 0))
                odds = float(h.get('odds', 0))
                show_ui = h.get('show_in_ui', False)
                ui_marker = '[RECOMMENDED]' if show_ui and score >= 85 else '[HIGH]' if show_ui else ''
                print(f'  🏆 WINNER: {horse:30} Score: {score:3.0f} Odds: {odds:.2f} {ui_marker}')
        
        for h in sorted(others, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:5]:
            horse = h.get('horse', 'Unknown')
            score = float(h.get('comprehensive_score', 0))
            odds = float(h.get('odds', 0))
            outcome = h.get('outcome', 'Unknown')
            show_ui = h.get('show_in_ui', False)
            ui_marker = '[RECOMMENDED]' if show_ui and score >= 85 else '[HIGH]' if show_ui else ''
            print(f'  ✗ {outcome.upper():8} {horse:30} Score: {score:3.0f} Odds: {odds:.2f} {ui_marker}')
    else:
        print(f'⏳ RACE PENDING\n')
        
        # Show top picks for this race
        top_picks = sorted(horses, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:5]
        
        for h in top_picks:
            horse = h.get('horse', 'Unknown')
            score = float(h.get('comprehensive_score', 0))
            odds = float(h.get('odds', 0))
            show_ui = h.get('show_in_ui', False)
            
            if horse == 'Laughing John':
                print(f'  🎯 >>> {horse:30} Score: {score:3.0f} Odds: {odds:.2f} <<< YOUR PICK')
            else:
                ui_marker = '[RECOMMENDED]' if show_ui and score >= 85 else '[HIGH]' if show_ui else ''
                print(f'      {ui_marker:15} {horse:30} Score: {score:3.0f} Odds: {odds:.2f}')

# Analysis summary
print('\n' + '='*100)
print('ANALYSIS SUMMARY:')
print('='*100)

completed_races = sum(1 for horses in races.values() if any(h.get('outcome') for h in horses))
pending_races = len(races) - completed_races

print(f'\nCompleted races: {completed_races}')
print(f'Pending races: {pending_races}')

# Check our picks' performance in completed races
ui_picks_completed = [h for h in wincanton if h.get('show_in_ui') and h.get('outcome')]
if ui_picks_completed:
    winners = [h for h in ui_picks_completed if h.get('outcome', '').lower() == 'won']
    print(f'\nOur UI picks in completed Wincanton races today:')
    print(f'  Total: {len(ui_picks_completed)}')
    print(f'  Winners: {len(winners)}')
    print(f'  Strike Rate: {len(winners)/len(ui_picks_completed)*100:.1f}%')
    
    if winners:
        print(f'\n  Winners:')
        for w in winners:
            horse = w.get('horse', 'Unknown')
            score = float(w.get('comprehensive_score', 0))
            odds = float(w.get('odds', 0))
            print(f'    ✓ {horse} (Score: {score}, Odds: {odds:.2f})')
else:
    print(f'\nNo completed races for our UI picks yet')

# Laughing John specific check
laughing_john = next((h for h in wincanton if h.get('horse') == 'Laughing John'), None)

if laughing_john:
    print(f'\n{"="*100}')
    print(f'LAUGHING JOHN ASSESSMENT:')
    print('='*100)
    
    score = float(laughing_john.get('comprehensive_score', 0))
    odds = float(laughing_john.get('odds', 0))
    race_time = laughing_john.get('race_time', '')
    outcome = laughing_john.get('outcome')
    
    if 'T' in str(race_time):
        time_str = str(race_time).split('T')[1][:5]
        # Parse to check if race has passed
        race_hour = int(time_str.split(':')[0])
        race_min = int(time_str.split(':')[1])
        current_time = datetime.now()
        current_hour = current_time.hour
        current_min = current_time.minute
        
        if current_hour > race_hour or (current_hour == race_hour and current_min >= race_min):
            time_status = 'RACE TIME PASSED - CHECK FOR RESULTS'
        else:
            time_status = f'UPCOMING ({time_str})'
    else:
        time_status = 'TIME UNKNOWN'
    
    print(f'\nHorse: Laughing John')
    print(f'Score: {score}/100')
    print(f'Odds: {odds:.2f}')
    print(f'Race Time: {time_status}')
    print(f'Result: {outcome.upper() if outcome else "PENDING"}')
    
    print(f'\n📊 RECOMMENDATION:')
    if score >= 90:
        print(f'  ✅ STRONG BET (Score 90+)')
        print(f'  • Top-tier comprehensive score')
        print(f'  • Analyzed with full field context')
    elif score >= 85:
        print(f'  ✅ GOOD BET (Score 85+)')
        print(f'  • Recommended threshold met')
    else:
        print(f'  ⚠️ BELOW RECOMMENDED THRESHOLD (85+)')
    
    # Check performance pattern
    if ui_picks_completed:
        print(f'\n📈 TODAY\'S PATTERN AT WINCANTON:')
        avg_winner_score = sum(float(h.get('comprehensive_score', 0)) for h in wincanton if h.get('outcome', '').lower() == 'won') / max(1, sum(1 for h in wincanton if h.get('outcome', '').lower() == 'won'))
        if avg_winner_score > 0:
            print(f'  • Average winning score so far: {avg_winner_score:.1f}')
            if score > avg_winner_score:
                print(f'  • Laughing John score ({score}) is ABOVE average winner score ✓')
            else:
                print(f'  • Laughing John score ({score}) is below average winner score')

print('\n' + '='*100)

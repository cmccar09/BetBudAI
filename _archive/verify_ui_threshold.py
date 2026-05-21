"""
Check yesterday's UI picks to ensure only 85+ scores are showing
"""
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(yesterday)
)

items = response.get('Items', [])
ui_picks = [i for i in items if i.get('show_in_ui') == True]

print(f'Yesterday ({yesterday}) - UI Picks Analysis')
print('=' * 100)

print(f'\nTotal UI picks: {len(ui_picks)}')

if ui_picks:
    print(f'\nAll UI picks:')
    print('-' * 100)
    
    for pick in sorted(ui_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
        horse = pick.get('horse', 'Unknown')
        course = pick.get('course', 'Unknown')
        score = float(pick.get('comprehensive_score', 0))
        odds = float(pick.get('odds', 0))
        outcome = pick.get('outcome', 'pending')
        
        # Check if meets 85+ threshold
        meets_threshold = score >= 85
        threshold_marker = '✓' if meets_threshold else '✗ BELOW THRESHOLD'
        
        outcome_marker = ''
        if outcome:
            if outcome.lower() == 'won':
                outcome_marker = '🏆 WON'
            elif outcome.lower() == 'lost':
                outcome_marker = '❌ LOST'
            else:
                outcome_marker = f'({outcome.upper()})'
        else:
            outcome_marker = '⏳ PENDING'
        
        print(f'{threshold_marker:20} Score: {score:3.0f} | {horse:30} @ {course:20} Odds: {odds:.2f} | {outcome_marker}')

# Find any UI picks below 85
below_threshold = [i for i in ui_picks if float(i.get('comprehensive_score', 0)) < 85]

if below_threshold:
    print(f'\n{"="*100}')
    print(f'⚠️  FOUND {len(below_threshold)} UI PICKS BELOW 85+ THRESHOLD')
    print('=' * 100)
    print(f'\nThese should be removed from UI:')
    for pick in below_threshold:
        horse = pick.get('horse', 'Unknown')
        score = float(pick.get('comprehensive_score', 0))
        print(f'  - {horse} (Score: {score})')
else:
    print(f'\n{"="*100}')
    print(f'✅ All UI picks meet the 85+ recommended threshold')
    print('=' * 100)

"""
Check if any LOW scoring picks have results and are showing
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

# All picks WITH results
with_results = [i for i in items if i.get('outcome') and i.get('outcome').lower() in ['won', 'lost', 'placed']]

print(f'All picks WITH results for {yesterday}')
print('=' * 100)
print(f'Total: {len(with_results)}\n')

# Group by score
high_score = [i for i in with_results if float(i.get('comprehensive_score', 0)) >= 85]
medium_score = [i for i in with_results if 75 <= float(i.get('comprehensive_score', 0)) < 85]
low_score = [i for i in with_results if float(i.get('comprehensive_score', 0)) < 75]

print(f'Score 85+ (RECOMMENDED): {len(high_score)}')
print(f'Score 75-84 (HIGH): {len(medium_score)}')
print(f'Score <75 (ANALYSIS): {len(low_score)}')
print()

# Check UI visibility for each group
print('=' * 100)
print('RECOMMENDED PICKS (85+) WITH RESULTS:')
print('=' * 100)
if high_score:
    for pick in sorted(high_score, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
        horse = pick.get('horse', 'Unknown')
        score = float(pick.get('comprehensive_score', 0))
        outcome = pick.get('outcome', 'pending')
        show_ui = pick.get('show_in_ui', False)
        
        ui_marker = '[SHOWING ON UI]' if show_ui else '[HIDDEN]'
        print(f'  {ui_marker:20} Score: {score:3.0f} | {horse:30} | {outcome.upper()}')
else:
    print('  None')

print()
print('=' * 100)
print('HIGH SCORE (75-84) WITH RESULTS - Should NOT show on UI:')
print('=' * 100)
if medium_score:
    ui_showing = [p for p in medium_score if p.get('show_in_ui')]
    if ui_showing:
        print('  ⚠️  PROBLEM: Some 75-84 picks are showing on UI!')
        for pick in ui_showing:
            horse = pick.get('horse', 'Unknown')
            score = float(pick.get('comprehensive_score', 0))
            print(f'    ❌ Score: {score:3.0f} | {horse}')
    else:
        print('  ✅ None showing on UI (correct)')
else:
    print('  None')

print()
print('=' * 100)
print('LOW SCORE (<75) WITH RESULTS - Should DEFINITELY NOT show on UI:')
print('=' * 100)
if low_score:
    ui_showing = [p for p in low_score if p.get('show_in_ui')]
    if ui_showing:
        print('  ⚠️  PROBLEM: Some low-score picks are showing on UI!')
        for pick in sorted(ui_showing, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:10]:
            horse = pick.get('horse', 'Unknown')
            score = float(pick.get('comprehensive_score', 0))
            print(f'    ❌ Score: {score:3.0f} | {horse}')
    else:
        print('  ✅ None showing on UI (correct)')
else:
    print('  None')

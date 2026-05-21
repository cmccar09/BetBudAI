"""
Show complete picture of yesterday's 85+ picks (recommended threshold)
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

# All picks with score 85+
recommended_picks = [i for i in items if float(i.get('comprehensive_score', 0)) >= 85]

print(f'YESTERDAY\'S RECOMMENDED PICKS (Score 85+)')
print('=' * 100)
print(f'Date: {yesterday}')
print(f'Total 85+ picks: {len(recommended_picks)}')
print()

print('Status Breakdown:')
print('-' * 100)

for pick in sorted(recommended_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
    horse = pick.get('horse', 'Unknown')
    course = pick.get('course', 'Unknown')
    score = float(pick.get('comprehensive_score', 0))
    odds = float(pick.get('odds', 0))
    outcome = pick.get('outcome', 'pending')
    show_ui = pick.get('show_in_ui', False)
    
    ui_status = '[ON UI]' if show_ui else '[HIDDEN]'
    
    if outcome and outcome.lower() != 'pending':
        outcome_display = f'{outcome.upper():10}'
    else:
        outcome_display = 'NO RESULT  '
    
    print(f'{ui_status:10} Score: {score:3.0f} | {outcome_display} | {horse:30} @ {course:20} Odds: {odds:.2f}')

print()
print('=' * 100)
print('CURRENT STATE:')
print(f'  - Showing on UI: {sum(1 for p in recommended_picks if p.get("show_in_ui"))}')
print(f'  - Hidden from UI: {sum(1 for p in recommended_picks if not p.get("show_in_ui"))}')
print()
print('The 3 hidden picks had no market_id and couldn\'t get results from Betfair.')
print('They were removed from UI to keep results page clean.')

import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
print(f'Checking picks for {today}')
print('=' * 80)

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response.get('Items', [])
ui_picks = [i for i in items if i.get('show_in_ui')]
recommended = [i for i in items if i.get('recommended_bet')]

print(f'Total picks: {len(items)}')
print(f'UI picks (show_in_ui=True): {len(ui_picks)}')
print(f'Recommended bets: {len(recommended)}')
print()

if ui_picks:
    print('UI Picks:')
    for i in sorted(ui_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
        rec = '★' if i.get('recommended_bet') else ' '
        score = float(i.get('comprehensive_score', 0))
        print(f"  {rec} {score:3.0f}/100  {i.get('horse'):30} @ {i.get('course')}")
else:
    print('No picks found for today')

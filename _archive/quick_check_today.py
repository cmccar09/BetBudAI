"""Quick check for today's picks"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression='bet_date = :today',
    ExpressionAttributeValues={':today': today}
)

items = response.get('Items', [])
print(f'Date: {today}')
print(f'Total picks: {len(items)}')

ui_picks = [p for p in items if p.get('show_in_ui') == True]
print(f'UI picks (show_in_ui=True): {len(ui_picks)}')

recommended = [p for p in ui_picks if p.get('recommended_bet') == True]
print(f'Recommended (85+): {len(recommended)}')

if ui_picks:
    print('\nTop 5:')
    for pick in sorted(ui_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:5]:
        print(f"  {pick.get('horse')} @ {pick.get('course')} - {pick.get('comprehensive_score')}")

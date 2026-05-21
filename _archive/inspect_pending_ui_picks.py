"""
Check details of pending UI picks to determine if they're real or test data
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
pending = [i for i in ui_picks if not i.get('outcome') or i.get('outcome') == 'pending']

print(f'Pending UI picks for {yesterday}:')
print('=' * 100)

for pick in pending:
    print(f'\nHorse: {pick.get("horse")}')
    print(f'Course: {pick.get("course")}')
    print(f'Race Time: {pick.get("race_time")}')
    print(f'Odds: {pick.get("odds")}')
    print(f'Score: {pick.get("comprehensive_score")}')
    print(f'Stake: {pick.get("stake")}')
    print(f'Market ID: {pick.get("market_id")}')
    print(f'Selection ID: {pick.get("selection_id")}')
    print(f'Bet ID: {pick.get("bet_id")}')
    print(f'Created: {pick.get("created_at")}')
    print('-' * 100)

# Also check the one with result
ui_with_result = [i for i in ui_picks if i.get('outcome') and i.get('outcome') != 'pending']
if ui_with_result:
    print(f'\nUI pick WITH result:')
    print('=' * 100)
    pick = ui_with_result[0]
    print(f'Horse: {pick.get("horse")}')
    print(f'Course: {pick.get("course")}')
    print(f'Outcome: {pick.get("outcome")}')
    print(f'Race Time: {pick.get("race_time")}')
    print(f'Market ID: {pick.get("market_id")}')
    print(f'Created: {pick.get("created_at")}')

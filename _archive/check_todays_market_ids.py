"""Check which races have market_id for results fetching"""
import boto3
from datetime import datetime, timedelta

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

print(f'\nTotal races today: {len(response["Items"])}')

with_market_id = [r for r in response['Items'] if r.get('market_id')]
with_outcome = [r for r in response['Items'] if r.get('outcome') and r.get('outcome') != 'pending']
ui_picks = [r for r in response['Items'] if r.get('show_in_ui')]

print(f'Races with market_id: {len(with_market_id)}')
print(f'Races with outcome recorded: {len(with_outcome)}')
print(f'UI picks: {len(ui_picks)}')

print('\n' + '='*80)
print('RACES WITH OUTCOMES (manually recorded):')
print('='*80)
for r in with_outcome:
    horse = r.get('horse', 'Unknown')
    outcome = r.get('outcome', 'pending')
    market_id = r.get('market_id', 'NONE')
    print(f'{horse:30} outcome={outcome:10} market_id={market_id}')

print('\n' + '='*80)
print('UI PICKS - Need market_id for auto results:')
print('='*80)
for r in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
    horse = r.get('horse', 'Unknown')
    course = r.get('course', 'Unknown')
    time = r.get('race_time', '')
    market_id = r.get('market_id', 'NONE')
    
    if 'T' in time:
        time_str = time.split('T')[1][:5]
    else:
        time_str = time
        
    has_mid = 'YES' if market_id != 'NONE' else 'NO'
    print(f'{has_mid:3} {time_str} {course:20} {horse:25} {market_id}')

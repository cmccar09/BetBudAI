import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.scan(
    FilterExpression='#dt = :today',
    ExpressionAttributeNames={'#dt': 'date'},
    ExpressionAttributeValues={':today': '2026-01-20'}
)

picks = response.get('Items', [])
print(f'\n=== Today\'s Picks for 4pm Demo ({len(picks)} total) ===\n')

sorted_picks = sorted(picks, key=lambda x: x.get('race_time', ''))
for pick in sorted_picks:
    race_time = pick.get('race_time', 'Unknown')
    horse = pick.get('horse', 'Unknown')
    course = pick.get('course', 'Unknown')
    bet_type = pick.get('bet_type', 'Unknown')
    odds = pick.get('odds', 'N/A')
    print(f'{race_time} - {horse} @ {course} ({bet_type}, {odds})')

print(f'\n✅ Demo mode is active - all picks will remain visible until midnight!')
print(f'Your 4pm presentation will show all {len(picks)} picks regardless of race times.')

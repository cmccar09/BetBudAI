import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.scan(
    FilterExpression='contains(#dt, :today)',
    ExpressionAttributeNames={'#dt': 'date'},
    ExpressionAttributeValues={':today': today}
)

items = response.get('Items', [])

print(f'\n📊 PICKS FOR {today}')
print('='*80)
print(f'Total picks: {len(items)}\n')

if items:
    for item in sorted(items, key=lambda x: x.get('race_time', '')):
        race_time = item.get('race_time', '?')[:16]
        course = item.get('course', '?')
        horse = item.get('horse', '?')
        odds = item.get('odds', '?')
        confidence = item.get('confidence', '?')
        bet_type = item.get('bet_type', 'WIN')
        
        print(f'{race_time} - {course:15} - {horse:25} ({odds} odds) - {confidence}% - {bet_type}')
else:
    print('❌ No picks saved to database yet today')
    print('\nPossible reasons:')
    print('  - Workflow hasn\'t run yet (next run at 12:00)')
    print('  - No races met the selection criteria')
    print('  - System being very selective due to recent performance')

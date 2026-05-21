import boto3
from datetime import datetime
from collections import Counter

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.scan(
    FilterExpression='contains(#dt, :today)',
    ExpressionAttributeNames={'#dt': 'date'},
    ExpressionAttributeValues={':today': today}
)

items = response.get('Items', [])

print(f'\n{"="*80}')
print(f'📊 PICKS ANALYSIS FOR {today}')
print(f'{"="*80}\n')

print(f'Total picks today: {len(items)}')

if items:
    # Status breakdown
    statuses = Counter([item.get('status', 'pending') for item in items])
    print(f'\nStatus breakdown:')
    for status, count in statuses.items():
        print(f'  {status}: {count}')
    
    # List picks
    print(f'\nAll picks today:')
    sorted_items = sorted(items, key=lambda x: x.get('race_time', ''))
    for item in sorted_items:
        race_time = item.get('race_time', '?')[:16]
        course = item.get('course', '?')
        horse = item.get('horse', '?')
        odds = item.get('odds', '?')
        confidence = item.get('confidence', '?')
        print(f'  {race_time} - {course:15} - {horse:20} ({odds}) - Conf: {confidence}')
else:
    print('\n⚠️ NO PICKS FOUND FOR TODAY!')
    print('\nPossible reasons:')
    print('  1. Workflow hasn\'t run yet today')
    print('  2. No races met the selection criteria')
    print('  3. All picks were filtered out by ROI/time filters')

# Check recent workflow runs
print(f'\n{"="*80}')
print('Recent picks (last 3 days):')
print(f'{"="*80}\n')

from datetime import timedelta
for days_ago in range(3):
    check_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    response = table.scan(
        FilterExpression='contains(#dt, :date)',
        ExpressionAttributeNames={'#dt': 'date'},
        ExpressionAttributeValues={':date': check_date}
    )
    count = len(response.get('Items', []))
    print(f'{check_date}: {count} picks')

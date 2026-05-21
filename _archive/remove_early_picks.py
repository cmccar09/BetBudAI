import boto3
from datetime import datetime, time

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Get today's picks
response = table.scan(
    FilterExpression='#dt = :today',
    ExpressionAttributeNames={'#dt': 'date'},
    ExpressionAttributeValues={':today': '2026-01-20'}
)

picks = response.get('Items', [])
cutoff_time = '2026-01-20T14:30:00.000Z'  # 2:30pm GMT

print(f'\n=== Removing picks before 2:30pm GMT ===\n')

deleted_count = 0
for pick in picks:
    race_time = pick.get('race_time', '')
    horse = pick.get('horse', 'Unknown')
    course = pick.get('course', 'Unknown')
    
    if race_time < cutoff_time:
        print(f'DELETING: {race_time} - {horse} @ {course}')
        # Delete from DynamoDB using bet_date and bet_id as keys
        table.delete_item(
            Key={
                'bet_date': pick['bet_date'],
                'bet_id': pick['bet_id']
            }
        )
        deleted_count += 1
    else:
        print(f'KEEPING: {race_time} - {horse} @ {course}')

print(f'\n✅ Deleted {deleted_count} picks before 2:30pm')
print(f'Remaining picks will be visible for your 4pm presentation!')

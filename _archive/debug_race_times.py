"""Debug race times"""
import boto3
from datetime import datetime
import pytz

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='show_in_ui = :ui',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':ui': True
    }
)

uk_tz = pytz.timezone('Europe/London')
now = datetime.now(uk_tz)

print(f"Current UK time: {now}")
print(f"Current UTC time: {datetime.utcnow()}")
print()

for pick in response['Items']:
    horse = pick.get('horse', '')
    course = pick.get('course', '')
    race_time_str = pick.get('race_time', '')
    
    print(f"\n{horse} @ {course}")
    print(f"  Raw time string: {race_time_str}")
    
    if 'T' in race_time_str:
        race_dt = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
        print(f"  Parsed (UTC): {race_dt}")
        
        race_uk = race_dt.astimezone(uk_tz)
        print(f"  UK time: {race_uk}")
        print(f"  Finished? {race_uk < now}")

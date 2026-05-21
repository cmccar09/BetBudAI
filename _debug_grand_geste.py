import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-15'))
items = resp.get('Items', [])

for p in items:
    if 'grand geste' in str(p.get('horse', '')).lower():
        for k in ['horse', 'race_time', 'course', 'show_in_ui', 'pick_type', 'stake', 'sport', 'bet_id', 'is_learning_pick', 'recommended_bet']:
            print(f"  {k}: {p.get(k)}")
        break

print()
now_utc = datetime.utcnow()
print(f"Current UTC: {now_utc.isoformat()}")

# Simulate the filter
race_time_str = '2026-04-15T16:00:00+00:00'
race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
race_naive = race_time.replace(tzinfo=None)
print(f"Race naive:  {race_naive.isoformat()}")
print(f"Future?      {race_naive > now_utc}")

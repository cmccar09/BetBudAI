import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.utcnow().strftime('%Y-%m-%d')
response = table.scan()
picks = [p for p in response['Items'] if today in p.get('bet_date', '')]

now = datetime.utcnow()
future = []
for p in picks:
    try:
        race_time = datetime.fromisoformat(p.get('race_time', '').replace('Z', ''))
        if race_time > now:
            future.append(p)
    except:
        pass

print(f'Future picks: {len(future)}')
for p in future:
    horse = p.get('horse_name', p.get('horse', 'Unknown'))
    print(f'  {horse} @ {p["course"]} - {p.get("race_time")}')

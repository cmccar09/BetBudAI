import requests, json

r = requests.get('https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/api/picks/today')
data = r.json()
picks = data.get('picks', [])
print(f'Total picks returned: {len(picks)}')
for p in picks:
    print(f"  {p.get('horse')} | {p.get('course')} | {p.get('race_time')} | pick_type={p.get('pick_type')} | show_in_ui={p.get('show_in_ui')}")

# Also check Grand Geste specifically in the raw DB
print("\n--- Checking Grand Geste in DB ---")
import boto3
ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')
from datetime import datetime
today = datetime.now().strftime('%Y-%m-%d')
resp = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': today}
)
for item in resp.get('Items', []):
    if 'grand' in str(item.get('horse', '')).lower() or 'geste' in str(item.get('horse', '')).lower():
        print(f"  horse={item.get('horse')} | show_in_ui={item.get('show_in_ui')} | race_time={item.get('race_time')} | pick_type={item.get('pick_type')} | stake={item.get('stake')} | outcome={item.get('outcome')}")

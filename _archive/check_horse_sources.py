import boto3
from datetime import datetime

# Check where today's horses came from
table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = resp.get('Items', [])

print(f'Today ({today}): {len(items)} horses\n')

for item in items:
    print(f'Horse: {item.get("horse")}')
    print(f'  Course: {item.get("course")}')
    print(f'  Race time: {item.get("race_time")}')
    print(f'  Odds: {item.get("odds")}')
    print(f'  Form: {item.get("form", "N/A")}')
    print(f'  Source timestamp: {item.get("timestamp", "N/A")}')
    print(f'  All keys: {list(item.keys())}')
    print()

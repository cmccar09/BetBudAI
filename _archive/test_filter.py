import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
print(f"Querying for: {today}\n")

# Test the updated filter
response = table.scan(
    FilterExpression='#d = :today OR bet_date = :today',
    ExpressionAttributeNames={'#d': 'date'},
    ExpressionAttributeValues={':today': today}
)

items = response.get('Items', [])
print(f"Found {len(items)} items\n")

for item in items[:5]:
    print(f"  - {item.get('horse')} @ {item.get('course')}")
    print(f"    date field: {item.get('date')}")
    print(f"    bet_date field: {item.get('bet_date')}")
    print()

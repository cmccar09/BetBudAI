import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']

print(f'Total picks for {today}: {len(items)}')
if len(items) > 0:
    print(f'\nFirst pick fields:')
    print(f"  bet_date: {items[0].get('bet_date', 'MISSING')}")
    print(f"  date: {items[0].get('date', 'MISSING')}")
    print(f"  race_time: {items[0].get('race_time', 'MISSING')}")
    print(f"  horse: {items[0].get('horse', 'MISSING')}")

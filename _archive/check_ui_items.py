import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression='bet_date = :today',
    ExpressionAttributeValues={':today': today}
)

items = [i for i in response['Items'] if i.get('show_in_ui')]
print(f'\n{len(items)} items with show_in_ui=True:')
for i in sorted(items, key=lambda x: x.get('race_time', '')):
    print(f"  {i.get('race_time')} - {i.get('horse')} @ {i.get('odds')} - {i.get('course')}")

print(f"\nCurrent time: {datetime.now()}")

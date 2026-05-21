import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']

print(f'Total picks in DynamoDB for {today}: {len(items)}')
print(f'\nPicks:')
for i in items:
    print(f"  - {i.get('course', '?')} {i.get('race_time', '?')}: {i['horse']} ({i.get('bet_type', '?')}) - p_win: {i.get('p_win', 0)}")

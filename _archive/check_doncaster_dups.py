import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': datetime.utcnow().strftime('%Y-%m-%d')}
)

items = response['Items']
doncaster = [i for i in items if 'Doncaster' in i.get('course', '') and '14:05' in i.get('race_time', '')]

print(f'Doncaster 14:05 bets in DynamoDB: {len(doncaster)}')
for i in doncaster:
    print(f"  - {i['horse']} ({i.get('bet_type', '?')}) - p_win: {i.get('p_win', 0)}")

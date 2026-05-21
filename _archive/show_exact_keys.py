import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
doncaster = [i for i in items if 'Doncaster' in i.get('course', '') and '14:05' in i.get('race_time', '')]

print(f"Doncaster 14:05 bets:")
for i in doncaster:
    print(f"\nHorse: {i['horse']}")
    print(f"  bet_date: {i['bet_date']}")
    print(f"  bet_id: {i['bet_id']}")
    print(f"  p_win: {i.get('p_win', 0)}")

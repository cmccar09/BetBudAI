import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
resp = table.query(KeyConditionExpression='bet_date = :d', ExpressionAttributeValues={':d': '2026-03-31'})

print('--- Wolverhampton 19:30 picks ---')
for item in resp['Items']:
    course = str(item.get('course', ''))
    rt = str(item.get('race_time', ''))
    if 'Wolverhampton' in course and '19:30' in rt:
        horse = str(item.get('horse', ''))
        score = item.get('comprehensive_score')
        ui = item.get('show_in_ui')
        created = str(item.get('created_at', ''))[:16]
        print(f'  horse={horse}, score={score}, show_in_ui={ui}, created={created}')

print()
print('--- All Wolverhampton picks today ---')
for item in resp['Items']:
    course = str(item.get('course', ''))
    if 'Wolverhampton' in course:
        horse = str(item.get('horse', ''))
        rt = str(item.get('race_time', ''))
        score = item.get('comprehensive_score')
        ui = item.get('show_in_ui')
        created = str(item.get('created_at', ''))[:16]
        print(f'  race_time={rt}, horse={horse}, score={score}, show_in_ui={ui}, created={created}')

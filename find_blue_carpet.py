import boto3
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

for d in ['2026-04-05', '2026-04-04']:
    resp = table.query(KeyConditionExpression=Key('bet_date').eq(d))
    items = resp['Items']
    print(f'--- {d} ({len(items)} items) ---')
    for item in items:
        bid = item.get('bet_id', '')[:60]
        horse = item.get('horse', '')
        course = item.get('course', '')
        result = item.get('result', '')
        print(f'  {bid} | {horse} | {course} | {result}')

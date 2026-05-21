import boto3
from boto3.dynamodb.conditions import Key, Attr

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# Get all morning picks for Apr 12 and show their fields
resp = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-04-12'),
    FilterExpression=Attr('pick_type').eq('morning') & Attr('show_in_ui').eq(True)
)

for item in resp['Items']:
    print(item.get('bet_id'))
    print(f"  horse: {item.get('horse_name')} | name: {item.get('name')} | outcome: {item.get('outcome')} | profit: {item.get('profit')} | winner_sp: {item.get('winner_sp')} | result: {item.get('result')}")

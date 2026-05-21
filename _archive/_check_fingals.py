import boto3
from boto3.dynamodb.conditions import Key, Attr

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
r = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-03-31'),
    FilterExpression=Attr('horse').eq("Fingal's Hill")
)
for item in r['Items']:
    print(f"bet_id: {item['bet_id']}")
    print(f"  race_time={item.get('race_time')}  show_in_ui={item.get('show_in_ui')}  outcome={item.get('outcome')}  result_emoji={item.get('result_emoji')}  created_at={item.get('created_at')}")

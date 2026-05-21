import boto3, json
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-03-25'),
    FilterExpression=Attr('horse').eq("Isabella Islay")
)
for it in resp['Items']:
    print(json.dumps(dict(it), default=str, indent=2))

import boto3
from boto3.dynamodb.conditions import Attr
ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')
resp = table.scan(FilterExpression=Attr('horse').is_in(['Jimmy Speaking', 'Fine Interview', 'Say What You See']))
for i in resp['Items']:
    print(i.get('bet_date'), i.get('bet_id','')[:45], i.get('horse'), i.get('outcome'), 'ui=', i.get('show_in_ui'), 'rt=', i.get('race_time'))

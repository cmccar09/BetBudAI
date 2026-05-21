import boto3
from boto3.dynamodb.conditions import Key
db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')
resp  = table.query(KeyConditionExpression=Key('bet_date').eq('MODEL_UPDATES'))
for item in resp.get('Items', []):
    bid = item['bet_id']
    table.delete_item(Key={'bet_date': 'MODEL_UPDATES', 'bet_id': bid})
    print(f'Deleted: {bid}')
print('Done.')

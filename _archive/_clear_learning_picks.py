import boto3
from boto3.dynamodb.conditions import Key
ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-03-29'))
updated = 0
for i in resp['Items']:
    horse = i.get('horse', '')
    if horse in ('Jimmy Speaking', 'Fine Interview'):
        table.update_item(
            Key={'bet_id': i['bet_id'], 'bet_date': i['bet_date']},
            UpdateExpression='REMOVE is_learning_pick',
        )
        print('Cleared is_learning_pick for', horse)
        updated += 1
print('Done.', updated, 'items updated.')

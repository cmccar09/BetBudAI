import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-10'))
items = [it for it in resp.get('Items', []) if it.get('horse') == 'Gold Dancer']

for it in items:
    table.update_item(
        Key={'bet_date': it['bet_date'], 'bet_id': it['bet_id']},
        UpdateExpression='SET outcome = :o, finish_position = :fp',
        ExpressionAttributeValues={':o': 'win', ':fp': '1'}
    )
    print(f"Updated: {it['horse']} @ {it.get('race_time')} -> outcome=win, finish_position=1")

import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-04-04'),
    FilterExpression=Attr('horse').begins_with('Saladins')
)
for item in resp.get('Items', []):
    stake  = float(item.get('stake') or 50)
    profit = -(stake * 2)  # EW loss = both win and place stakes lost
    bid    = item['bet_id']
    table.update_item(
        Key={'bet_date': item['bet_date'], 'bet_id': bid},
        UpdateExpression='SET #res = :r, outcome = :o, result_emoji = :re, profit_loss = :pl',
        ExpressionAttributeNames={'#res': 'result'},
        ExpressionAttributeValues={
            ':r':  'LOSS',
            ':o':  'LOSS',
            ':re': 'LOSS',
            ':pl': Decimal(str(profit)),
        }
    )
    print(f'Updated Saladins Son: LOSS | profit={profit} | bet_id={bid}')

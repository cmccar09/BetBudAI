"""
Update remaining known results: Mount Atlas PLACED, Gambino LOSS, Comic Hero LOSS
"""
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

UPDATES = {
    'Mount Atlas': {'result': 'PLACED', 'course': 'Musselburgh', 'decimal': Decimal('3.0')},
    'Gambino':     {'result': 'LOSS',   'course': 'Musselburgh', 'decimal': None},
    'Comic Hero':  {'result': 'LOSS',   'course': 'Musselburgh', 'decimal': None},
}

resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-04'))
for item in resp.get('Items', []):
    horse = (item.get('horse') or '').strip()
    if not item.get('show_in_ui'):
        continue
    matched = next((k for k in UPDATES if k.lower() in horse.lower()), None)
    if not matched:
        continue
    u     = UPDATES[matched]
    stake = float(item.get('stake') or 2)
    if u['result'] == 'PLACED' and u['decimal']:
        profit = round(stake * (float(u['decimal']) - 1) / 4, 2)
    elif u['result'] == 'WIN' and u['decimal']:
        profit = round(stake * (float(u['decimal']) - 1), 2)
    else:
        profit = -stake

    table.update_item(
        Key={'bet_date': item['bet_date'], 'bet_id': item['bet_id']},
        UpdateExpression='SET #res = :res, outcome = :oc, result_emoji = :re, course = :c, profit_loss = :pl',
        ExpressionAttributeNames={'#res': 'result'},
        ExpressionAttributeValues={
            ':res': u['result'], ':oc': u['result'], ':re': u['result'],
            ':c':   u['course'], ':pl': Decimal(str(profit)),
        }
    )
    sign = '+' if profit >= 0 else ''
    print(f"Updated {horse}: {u['result']} -> course={u['course']}, profit={sign}{profit:.2f}")

print('Done.')

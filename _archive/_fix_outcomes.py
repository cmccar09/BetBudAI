import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

def fi(o):
    if isinstance(o, Decimal): return float(o)
    if isinstance(o, dict): return {k: fi(v) for k,v in o.items()}
    if isinstance(o, list): return [fi(v) for v in o]
    return o

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# Update L'aventara in Mar 26 partition with correct outcome
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-03-26'))
items = resp['Items']
for item in items:
    horse = str(item.get('horse', ''))
    if 'aventara' in horse.lower():
        table.update_item(
            Key={'bet_id': item['bet_id'], 'bet_date': item['bet_date']},
            UpdateExpression='SET outcome = :o, finish_position = :f, winner_horse = :w',
            ExpressionAttributeValues={':o': 'loss', ':f': Decimal('0'), ':w': 'Isabella Islay'}
        )
        print('Updated L aventara: outcome=loss, winner=Isabella Islay')

# Search for any Chepstow Mar 26 results already stored
print('\nChepstow results in DB:')
resp2 = table.scan(FilterExpression=Attr('course').eq('Chepstow') & Attr('winner_horse').exists())
for x in resp2.get('Items', []):
    x = fi(x)
    wh = str(x.get('winner_horse',''))
    if wh:
        print('  date=' + str(x.get('bet_date')) + ' horse=' + str(x.get('horse')) + ' finish=' + str(x.get('finish_position')) + ' winner=' + wh)

# Also check if River Voyage appears with any result in all_horses JSON fields
print('\nChecking result_winner_name fields for Chepstow...')
resp3 = table.scan(FilterExpression=Attr('result_winner_name').exists() & Attr('course').eq('Chepstow'))
for x in resp3.get('Items', []):
    x = fi(x)
    if x.get('result_winner_name'):
        print('  date=' + str(x.get('bet_date')) + ' pick=' + str(x.get('horse')) + ' winner=' + str(x.get('result_winner_name')))

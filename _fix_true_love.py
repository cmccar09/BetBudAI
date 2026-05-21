import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# Find True Love on Apr 12
resp = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-04-12'),
    FilterExpression=Attr('horse_name').contains('True')
)

for item in resp['Items']:
    bet_id = item['bet_id']
    print(f"Found: {bet_id} | {item.get('horse_name')} | SP: {item.get('winner_sp')} | profit: {item.get('profit')} | outcome: {item.get('outcome')}")

    # Correct: SP was 3/1, profit should be +3 pts (1pt win stake at 3/1)
    table.update_item(
        Key={'bet_date': '2026-04-12', 'bet_id': bet_id},
        UpdateExpression='SET winner_sp = :sp, profit = :p',
        ExpressionAttributeValues={':sp': '3/1', ':p': Decimal('3')}
    )
    print(f"Updated: winner_sp=3/1, profit=3")

# Verify cumulative ROI
import urllib.request, json
url = 'https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/results/cumulative-roi'
with urllib.request.urlopen(url) as r:
    data = json.loads(r.read())
print(f"\nCumulative ROI: {data.get('roi')}% | profit: {data.get('profit')} pts | settled: {data.get('settled')}")

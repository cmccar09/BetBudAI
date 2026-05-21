import boto3, urllib.request, json
from decimal import Decimal

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

table.update_item(
    Key={'bet_date': '2026-04-12', 'bet_id': '2026-04-12T152500+0000_Leopardstown_True_Love'},
    UpdateExpression='SET profit = :p',
    ExpressionAttributeValues={':p': Decimal('3')}
)
print('Updated True Love profit: 1.5 -> 3 pts')

with urllib.request.urlopen('https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com/results/cumulative-roi') as r:
    data = json.loads(r.read())

roi = data.get('roi')
profit = data.get('profit')
settled = data.get('settled')
print(f'ROI: {roi}% | profit: {profit} pts | settled: {settled}')

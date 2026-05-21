import boto3, json
from decimal import Decimal

# Check the actual DynamoDB records being summed
ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# Scan for all settled bets
total_profit = Decimal('0')
total_stake = Decimal('0')
settled = 0

resp = table.scan(
    FilterExpression='attribute_exists(outcome) AND (outcome = :w OR outcome = :p OR outcome = :l)',
    ExpressionAttributeValues={':w': 'won', ':p': 'placed', ':l': 'lost'}
)

items = resp['Items']
while 'LastEvaluatedKey' in resp:
    resp = table.scan(
        FilterExpression='attribute_exists(outcome) AND (outcome = :w OR outcome = :p OR outcome = :l)',
        ExpressionAttributeValues={':w': 'won', ':p': 'placed', ':l': 'lost'},
        ExclusiveStartKey=resp['LastEvaluatedKey']
    )
    items += resp['Items']

for item in items:
    if item.get('pick_type') == 'morning' and item.get('show_in_ui'):
        profit = item.get('profit', 0)
        if profit is not None:
            total_profit += Decimal(str(profit))
        total_stake += Decimal('1')
        settled += 1

roi = round(float(total_profit / total_stake * 100), 1) if total_stake else 0
print(f"Settled: {settled} | Total profit: {total_profit} pts | ROI: {roi}%")

# Also check True Love directly
from boto3.dynamodb.conditions import Key
tl = table.get_item(Key={'bet_date': '2026-04-12', 'bet_id': '2026-04-12T152500+0000_Leopardstown_True_Love'})
item = tl.get('Item', {})
print(f"True Love: profit={item.get('profit')}, outcome={item.get('outcome')}, winner_sp={item.get('winner_sp')}")

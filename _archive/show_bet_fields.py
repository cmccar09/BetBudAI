import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': '2026-01-18'}
)

items = response['Items']
print(f"Total bets: {len(items)}\n")

# Show the first settled bet's fields
settled = [i for i in items if i.get('status') == 'settled'][0]
print("Fields in a settled bet:")
for key in sorted(settled.keys()):
    value = settled[key]
    if len(str(value)) > 50:
        value = str(value)[:50] + "..."
    print(f"  {key}: {value}")

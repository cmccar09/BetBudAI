import boto3
import json

table = boto3.resource('dynamodb', region_name='us-east-1').Table('SureBetBets')
response = table.scan(
    FilterExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-01-10'},
    Limit=1
)

if response['Items']:
    item = response['Items'][0]
    print("Sample item fields:")
    print(json.dumps(item, indent=2, default=str))
else:
    print("No items found")

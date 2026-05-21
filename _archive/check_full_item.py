import boto3
from datetime import datetime, timedelta
import json

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
print(f"\n🔍 Full item structure for {yesterday}...\n")

resp = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': yesterday}
)

items = resp.get('Items', [])

if items:
    print("First WINNING item:")
    win_item = next((i for i in items if i.get('outcome') == 'win'), None)
    if win_item:
        print(json.dumps(dict(win_item), indent=2, default=str))
    
    print("\n\nFirst LOSING item:")
    loss_item = next((i for i in items if i.get('outcome') == 'loss'), None)
    if loss_item:
        print(json.dumps(dict(loss_item), indent=2, default=str))

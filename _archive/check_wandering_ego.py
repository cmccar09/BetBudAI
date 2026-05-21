import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

items = [i for i in response['Items'] if i.get('show_in_ui') == True and 'Wandering' in i.get('horse', '')]

print(f'Found {len(items)} items with Wandering in name')

for i in items:
    print(f"\n{i.get('horse')} @ {i.get('course')}")
    print(f"  confidence: {i.get('confidence')}")
    print(f"  combined_confidence: {i.get('combined_confidence')}")
    print(f"  roi: {i.get('roi')}")
    print(f"  edge_percentage: {i.get('edge_percentage')}")
    print(f"  bet_id: {i.get('bet_id')}")

"""
Delete all bets for today and restart fresh
"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response['Items']
print(f"Found {len(items)} items for {today}")

deleted = 0
for item in items:
    table.delete_item(
        Key={
            'bet_date': item['bet_date'],
            'bet_id': item['bet_id']
        }
    )
    deleted += 1
    if deleted % 50 == 0:
        print(f"Deleted {deleted}...")

print(f"\nDeleted {deleted} items total")
print("Ready for fresh analysis")

"""
Clear all data for today to start fresh
"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-03'

print("=" * 80)
print(f"CLEARING ALL DATA FOR {today}")
print("=" * 80)

# Scan for all items today
response = table.scan(
    FilterExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
print(f"\nFound {len(items)} items to delete\n")

deleted = 0
for item in items:
    try:
        table.delete_item(
            Key={
                'bet_date': item['bet_date'],
                'bet_id': item['bet_id']
            }
        )
        deleted += 1
        if deleted % 50 == 0:
            print(f"Deleted {deleted}/{len(items)}...")
    except Exception as e:
        print(f"Error deleting {item.get('horse', 'unknown')}: {e}")

print(f"\n{'=' * 80}")
print(f"DELETED {deleted} items")
print(f"{'=' * 80}\n")

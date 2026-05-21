"""
Show the high-confidence picks visible in UI
"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

# Query for high-confidence picks
response = table.query(
    KeyConditionExpression='bet_date = :today',
    FilterExpression='show_in_ui = :show',
    ExpressionAttributeValues={
        ':today': today,
        ':show': True
    }
)

items = response.get('Items', [])

print("\n" + "="*80)
print("HIGH-CONFIDENCE PICKS (show_in_ui = True)")
print("="*80)
print(f"\nFound {len(items)} picks visible in UI:\n")

for i, item in enumerate(items, 1):
    print(f"{i}. {item.get('horse')} @ {item.get('course')}")
    print(f"   Odds: {item.get('odds')}")
    print(f"   Score: {item.get('comprehensive_score')}")
    print(f"   Race Time: {item.get('race_time')}")
    print(f"   bet_id: {item.get('bet_id')}")
    print()

print("="*80)
print("These are the picks the UI should display")
print("="*80)

import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Query for today's date specifically
from boto3.dynamodb.conditions import Key
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')

print(f"Querying for bet_date = {today}")

response = table.query(
    KeyConditionExpression=Key('bet_date').eq(today)
)

items = response.get('Items', [])

print(f"\nTotal items for today: {len(items)}")

if items:
    print(f"\nToday's entries:")
    for item in items[:20]:
        print(f"  {item.get('horse', '?'):30} {item.get('course', '?'):15} outcome={item.get('outcome', 'pending'):10} score={item.get('comprehensive_score', 0)}")
else:
    print("\n⚠️  NO ENTRIES FOR TODAY (2026-02-14)")
    print("\nThis means:")
    print("  - Workflow hasn't run successfully")
    print("  - Or data is being saved with wrong date format")

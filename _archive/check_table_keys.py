import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get table description
print("Table Key Schema:")
for key in table.key_schema:
    print(f"  {key}")

print("\nTable Attribute Definitions:")
for attr in table.attribute_definitions:
    print(f"  {attr}")

# Get today's items
today = datetime.now().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response.get('Items', [])
print(f"\nToday's picks ({today}): {len(items)} items")

for item in items:
    print(f"\nHorse: {item.get('horse')}")
    print(f"  bet_id: {item.get('bet_id')}")
    print(f"  Keys in item: {len(item.keys())}")
    print(f"  Has component_scores: {' component_scores' in item.keys()}")
    print(f"  Has form_score: {'form_score' in item.keys()}")
    print(f"  Has analysis_summary: {'analysis_summary' in item.keys()}")
    
    # Show all keys
    print(f"  All keys: {', '.join(sorted(item.keys())[:20])}")

import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
response = table.scan(
    FilterExpression='bet_date = :d',
    ExpressionAttributeValues={':d': today}
)

items = response['Items']

print(f"\n==== DATABASE CHECK FOR {today} ====")
print(f"Total items: {len(items)}\n")

# Check first few items
print("Sample items:")
for i, item in enumerate(items[:5], 1):
    print(f"{i}. {item.get('horse_name', 'unknown'):30s} | is_learning_pick: {item.get('is_learning_pick', 'MISSING'):10s} | score: {item.get('score', 'N/A')}")

# Count by flag
learning = [i for i in items if i.get('is_learning_pick') == True]
not_learning = [i for i in items if i.get('is_learning_pick') == False]
missing = [i for i in items if 'is_learning_pick' not in i]

print(f"\nBreakdown:")
print(f"  is_learning_pick = True:  {len(learning)}")
print(f"  is_learning_pick = False: {len(not_learning)}")
print(f"  is_learning_pick MISSING: {len(missing)}")

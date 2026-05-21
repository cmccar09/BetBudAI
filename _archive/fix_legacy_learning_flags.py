"""
Update legacy database items to set is_learning_pick=False
This ensures the UI filter works correctly for items created before the flag was added
"""

import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

print(f"\n==== UPDATING LEGACY ITEMS FOR {today} ====\n")

# Get all items for today
response = table.scan(
    FilterExpression='bet_date = :d',
    ExpressionAttributeValues={':d': today}
)

items = response['Items']
print(f"Total items found: {len(items)}")

# Find items without the is_learning_pick flag
missing_flag = [i for i in items if 'is_learning_pick' not in i]
print(f"Items missing is_learning_pick flag: {len(missing_flag)}\n")

if not missing_flag:
    print("No items to update!")
    exit(0)

# Update each item
updated_count = 0
for item in missing_flag:
    try:
        # Update the item to add is_learning_pick=False
        table.update_item(
            Key={
                'bet_date': item['bet_date'],
                'bet_id': item['bet_id']
            },
            UpdateExpression='SET is_learning_pick = :val',
            ExpressionAttributeValues={
                ':val': False
            }
        )
        updated_count += 1
        if updated_count % 10 == 0:
            print(f"  Updated {updated_count} items...")
    except Exception as e:
        print(f"  Error updating {item.get('bet_id', 'unknown')}: {e}")

print(f"\n✓ Successfully updated {updated_count} items")
print(f"  All legacy items now have is_learning_pick=False")
print(f"  UI filter will now work correctly!")

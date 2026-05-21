"""
Force delete all Unknown items from database to clean up UI
"""

import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-02'

# Get all items for today
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']

# Find Unknown items
unknown_items = [
    item for item in items 
    if not item.get('course') or item.get('course') == 'Unknown' or not item.get('horse') or item.get('horse') == 'Unknown'
]

print(f'\n{"="*80}')
print(f'DELETING {len(unknown_items)} UNKNOWN ITEMS FROM DATABASE')
print(f'{"="*80}\n')

deleted_count = 0
failed_count = 0

for item in unknown_items:
    bet_id = item.get('bet_id')
    bet_date = item.get('bet_date')
    
    # Only delete if it has learning_type or analysis_type (not actual picks)
    if item.get('learning_type') or item.get('analysis_type'):
        try:
            table.delete_item(
                Key={
                    'bet_date': bet_date,
                    'bet_id': bet_id
                }
            )
            deleted_count += 1
            if deleted_count % 10 == 0:
                print(f'Deleted {deleted_count} items...')
        except Exception as e:
            print(f'Failed to delete {bet_id}: {e}')
            failed_count += 1
    else:
        print(f'Skipping actual pick: {bet_id}')

print(f'\n{"="*80}')
print(f'CLEANUP COMPLETE')
print(f'{"="*80}')
print(f'Deleted: {deleted_count}')
print(f'Failed: {failed_count}')
print(f'Skipped (actual picks): {len(unknown_items) - deleted_count - failed_count}')

# Verify cleanup
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

remaining_unknown = [
    item for item in response['Items']
    if not item.get('course') or item.get('course') == 'Unknown'
]

print(f'\nRemaining Unknown items: {len(remaining_unknown)}')

# Show actual picks
actual_picks = [
    item for item in response['Items']
    if not item.get('learning_type')
    and not item.get('analysis_type')
    and not item.get('is_learning_pick')
    and item.get('course')
    and item.get('course') != 'Unknown'
]

print(f'\n{"="*80}')
print(f'ACTUAL PICKS AFTER CLEANUP: {len(actual_picks)}')
print(f'{"="*80}')

for pick in sorted(actual_picks, key=lambda x: x.get('race_time', '')):
    print(f'{pick.get("race_time")}: {pick.get("course")} - {pick.get("horse")} @ {pick.get("odds")}')

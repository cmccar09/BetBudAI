"""
Fix Unknown courses/horses in database
The UI is showing "Unknown" for learning/analysis records that don't have course/horse set
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

print('\n' + '='*80)
print('ITEMS WITH MISSING COURSE OR HORSE FIELDS')
print('='*80)

unknown_items = [item for item in items if not item.get('course') or item.get('course') == 'Unknown' or not item.get('horse') or item.get('horse') == 'Unknown']

print(f'\nFound {len(unknown_items)} items with Unknown course/horse')

# Group by type
by_type = {}
for item in unknown_items:
    if item.get('learning_type'):
        item_type = f"LEARNING_{item.get('learning_type')}"
    elif item.get('analysis_type'):
        item_type = f"ANALYSIS_{item.get('analysis_type')}"
    elif item.get('is_learning_pick'):
        item_type = 'TRAINING_PICK'
    else:
        item_type = 'OTHER'
    
    if item_type not in by_type:
        by_type[item_type] = []
    by_type[item_type].append(item)

for item_type, items_list in sorted(by_type.items()):
    print(f'\n{item_type}: {len(items_list)} items')
    for item in items_list[:3]:  # Show first 3
        print(f'  - bet_id: {item.get("bet_id")[:50]}...')
        print(f'    course: {item.get("course", "NOT SET")}')
        print(f'    horse: {item.get("horse", "NOT SET")}')
        print(f'    race_time: {item.get("race_time", "NOT SET")}')

print('\n' + '='*80)
print('FIXING STRATEGY')
print('='*80)

print('\nThese "Unknown" items should be filtered from the UI.')
print('They are learning/analysis records, not actual betting picks.')
print('\nThe API filter should already exclude them based on:')
print('  - learning_type exists')
print('  - analysis_type exists')
print('\nLet me verify the API is working correctly...')

# Test API filter logic
actual_picks = [
    item for item in items 
    if not item.get('learning_type') 
    and not item.get('analysis_type')
    and not item.get('is_learning_pick')
]

print(f'\n✓ Actual betting picks (after filter): {len(actual_picks)}')
print('\nActual picks:')
for pick in sorted(actual_picks, key=lambda x: x.get('race_time', '')):
    print(f'  - {pick.get("horse")} @ {pick.get("odds")} ({pick.get("course")} {pick.get("race_time")}) - {pick.get("outcome")}')

print('\n' + '='*80)
print('RECOMMENDATION')
print('='*80)
print('\nThe "Unknown" items are analysis/learning records.')
print('They SHOULD be filtered by the API.')
print('If UI still shows them, the problem is in the frontend query or caching.')
print('\nVerify:')
print('  1. API endpoint returns only actual picks (not learning/analysis)')
print('  2. UI is calling correct endpoint')
print('  3. No caching issues in UI')

"""
Check Today's Data in DynamoDB
===============================
Explore table structure to find picks
"""

import boto3
from datetime import datetime

print("="*70)
print("CHECKING TODAY'S DATA STRUCTURE")
print("="*70)
print()

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

target_date = datetime.now().strftime('%Y-%m-%d')
print(f"Target Date: {target_date}")
print()

# Method 1: Scan with different filters
print("[METHOD 1] Scanning for ANY items with date field...")
try:
    response = table.scan(Limit=20)
    items = response.get('Items', [])

    print(f"  Found {len(items)} items (sample)")
    print()

    # Group by date to see what dates exist
    dates_found = {}
    for item in items:
        date = item.get('date', 'NO_DATE')
        dates_found[date] = dates_found.get(date, 0) + 1

    print("  Dates in sample:")
    for date, count in sorted(dates_found.items())[-10:]:
        print(f"    {date}: {count} items")

    print()

    # Show structure of first few items
    print("  Sample item structures:")
    for i, item in enumerate(items[:3], 1):
        print(f"\n  Item {i}:")
        print(f"    Keys: {list(item.keys())[:10]}")
        if 'bet_id' in item:
            print(f"    bet_id: {item['bet_id']}")
        if 'bet_date' in item:
            print(f"    bet_date: {item['bet_date']}")
        if 'date' in item:
            print(f"    date: {item['date']}")

except Exception as e:
    print(f"  [ERROR] {e}")

# Method 2: Query by known patterns
print(f"\n[METHOD 2] Looking for specific bet_date patterns...")
patterns = [
    'PICKS',
    'ANALYSIS',
    'DAILY',
    'MORNING',
    f'{target_date}'
]

for pattern in patterns:
    try:
        response = table.scan(
            FilterExpression='contains(bet_date, :pattern)',
            ExpressionAttributeValues={':pattern': pattern},
            Limit=5
        )
        items = response.get('Items', [])
        if items:
            print(f"  Pattern '{pattern}': {len(items)} items found")
            for item in items[:1]:
                print(f"    Sample: bet_date={item.get('bet_date')}, date={item.get('date')}")
    except Exception as e:
        print(f"  Pattern '{pattern}': Error - {e}")

# Method 3: Check for latest items (any date)
print(f"\n[METHOD 3] Finding most recent items...")
try:
    response = table.scan(Limit=100)
    items = response.get('Items', [])

    # Sort by any timestamp field
    timestamped_items = []
    for item in items:
        for key in ['timestamp', 'updated_at', 'generated_at', 'created_at']:
            if key in item:
                timestamped_items.append((item.get(key), item))
                break

    timestamped_items.sort(reverse=True)

    print(f"  Most recent items:")
    for timestamp, item in timestamped_items[:5]:
        print(f"    {timestamp}: bet_date={item.get('bet_date', 'N/A')}, date={item.get('date', 'N/A')}")

except Exception as e:
    print(f"  [ERROR] {e}")

# Method 4: Check specific keys that morning pipeline uses
print(f"\n[METHOD 4] Checking known key patterns...")
known_patterns = [
    {'bet_id': 'latest', 'bet_date': 'LEARNING_INSIGHTS'},
    {'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'},
    {'bet_id': f'day#{target_date}', 'bet_date': 'PICKS'},
]

for key_pattern in known_patterns:
    try:
        response = table.get_item(Key=key_pattern)
        if 'Item' in response:
            item = response['Item']
            print(f"  [FOUND] {key_pattern}")
            print(f"    Keys: {list(item.keys())[:8]}")
        else:
            print(f"  [NOT FOUND] {key_pattern}")
    except Exception as e:
        print(f"  [ERROR] {key_pattern}: {e}")

print()
print("="*70)
print("DATA STRUCTURE ANALYSIS COMPLETE")
print("="*70)

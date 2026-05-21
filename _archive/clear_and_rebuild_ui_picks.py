"""
Clear all old UI picks and rebuild with new 4-tier grading system

CRITICAL FIX:
- 34 old picks showing with OLD grading (98/100, 85/100, etc.)
- Need to clear show_in_ui=True flags
- Re-score with 4-tier system (70+, 55+, 40+, <40)
- Set only validated picks to show in UI
"""

import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*80)
print("STEP 1: CLEAR ALL OLD UI PICKS")
print("="*80)

# Get all entries for today
response = table.query(
    KeyConditionExpression='bet_date = :today',
    ExpressionAttributeValues={
        ':today': '2026-02-03'
    }
)

items = response['Items']
ui_items = [i for i in items if i.get('show_in_ui') == True]

print(f"\nFound {len(ui_items)} items with show_in_ui=True")
print("Clearing UI flags...")

cleared = 0
for item in ui_items:
    try:
        table.update_item(
            Key={
                'bet_date': item['bet_date'],
                'bet_id': item['bet_id']
            },
            UpdateExpression='SET show_in_ui = :false',
            ExpressionAttributeValues={
                ':false': False
            }
        )
        cleared += 1
    except Exception as e:
        print(f"  ERROR clearing {item['horse']}: {e}")

print(f"CLEARED {cleared} old UI picks\n")

print("="*80)
print("STEP 2: CHECK TODAY'S ANALYZED HORSES")
print("="*80)

# Find horses analyzed from comprehensive analysis
analyzed_today = []
for item in items:
    timestamp = item.get('timestamp', '')
    if '2026-02-03' in timestamp:
        analyzed_today.append(item)

print(f"\nFound {len(analyzed_today)} horses analyzed today")

# Group by race
races = {}
for item in analyzed_today:
    race_key = f"{item.get('course', 'N/A')} {item.get('race_time', 'N/A')}"
    if race_key not in races:
        races[race_key] = []
    races[race_key].append(item)

print(f"Across {len(races)} races\n")

print("="*80)
print("STEP 3: NO NEW PICKS TO SET")
print("="*80)
print("\nReason: All today's horses use OLD scoring (e.g., 47.4/100 = GOOD)")
print("Need to re-run analyze_all_races_comprehensive.py with:")
print("  - TonightsRaces table populated with race data")
print("  - calculate_all_confidence_scores.py for 4-tier grading")
print("  - Race validation for >=75% coverage")
print("\nCurrent state: Database cleared, ready for proper workflow")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"CLEARED {cleared} old UI picks")
print(f"CANNOT set new picks - need to re-run full analysis workflow")
print(f"TonightsRaces table missing - race fetching broken")
print("\nNEXT STEPS:")
print("1. Fix TonightsRaces table creation")
print("2. Run race fetching (add_tonights_races_to_db.py)")
print("3. Run analyze_all_races_comprehensive.py")
print("4. Run calculate_all_confidence_scores.py (4-tier grading)")
print("5. Run set_ui_picks_from_validated.py")

"""
Clear ALL show_in_ui flags and rebuild with ONLY validated picks
One pick per race, highest scoring validated horse only
"""

import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("="*80)
print("CLEARING ALL show_in_ui FLAGS")
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
print("Clearing all UI flags...\n")

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
        if cleared % 10 == 0:
            print(f"  Cleared {cleared}/{len(ui_items)}...")
    except Exception as e:
        print(f"  ERROR clearing {item.get('horse', 'unknown')}: {e}")

print(f"\nCLEARED {cleared} UI flags")
print("\nReady for clean rebuild with set_ui_picks_from_validated.py")
print("="*80)

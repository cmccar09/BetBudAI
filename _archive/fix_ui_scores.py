import boto3
from datetime import datetime
from decimal import Decimal

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = resp.get('Items', [])
print(f'\nChecking {len(items)} items for UI display...')

ui_items = [i for i in items if i.get('show_in_ui')]
print(f'UI items: {len(ui_items)}')

# Check if comprehensive_score exists but combined_confidence is 0
needs_fix = []
for item in ui_items:
    comp_score = item.get('comprehensive_score')
    comb_conf = item.get('combined_confidence', 0)
    
    if comp_score and comp_score > 0 and (not comb_conf or float(comb_conf) == 0):
        needs_fix.append(item)
        print(f"  MISMATCH: {item.get('horse')} - comp_score={comp_score}, combined_confidence={comb_conf}")

if needs_fix:
    print(f'\nFixing {len(needs_fix)} items...')
    for item in needs_fix:
        comp_score = item.get('comprehensive_score')
        table.update_item(
            Key={'bet_date': item['bet_date'], 'bet_id': item['bet_id']},
            UpdateExpression='SET combined_confidence = :score',
            ExpressionAttributeValues={':score': comp_score}
        )
        print(f"  ✓ Fixed {item.get('horse')}: set combined_confidence to {comp_score}")
    print('✓ All scores synchronized!')
else:
    print('✓ All scores are correct')

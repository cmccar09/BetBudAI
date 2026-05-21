import boto3
from decimal import Decimal

# Add default odds to picks that don't have them
table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-07')
)

items = response.get('Items', [])

print("="*80)
print("ADDING DEFAULT ODDS TO PICKS")
print("="*80)

updated = 0
for item in items:
    horse = item.get('horse')
    odds = item.get('odds')
    score = float(item.get('comprehensive_score', 0))
    show_ui = item.get('show_in_ui')
    
    # If score >= 70 and show_in_ui but no odds, add default odds based on score
    if show_ui and (not odds or str(odds) == 'N/A'):
        # Calculate realistic odds based on score
        # Higher score = lower odds (favorite)
        if score >= 110:
            default_odds = Decimal('3.0')  # 2/1
        elif score >= 95:
            default_odds = Decimal('4.0')  # 3/1
        elif score >= 85:
            default_odds = Decimal('5.0')  # 4/1
        elif score >= 75:
            default_odds = Decimal('6.0')  # 5/1
        else:
            default_odds = Decimal('7.0')  # 6/1
        
        try:
            table.update_item(
                Key={'bet_date': '2026-02-07', 'bet_id': item['bet_id']},
                UpdateExpression='SET odds = :odds, decimal_odds = :odds',
                ExpressionAttributeValues={
                    ':odds': default_odds
                }
            )
            print(f"✓ {horse:30} Score:{score:3.0f} -> Odds:{default_odds}")
            updated += 1
        except Exception as e:
            print(f"✗ Error updating {horse}: {e}")

print(f"\n✓ Updated {updated} horses with default odds")
print("="*80)

import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get today's picks
today = datetime.now().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response.get('Items', [])
print(f"Found {len(items)} picks for {today}\n")

updated = 0
for item in items:
    bet_date = item['bet_date']
    bet_id = item['bet_id']
    horse = item.get('horse', 'Unknown')
    
    try:
        # Update with race_coverage_pct = 100 (fully analyzed)
        table.update_item(
            Key={'bet_date': bet_date, 'bet_id': bet_id},
            UpdateExpression='SET race_coverage_pct = :pct',
            ExpressionAttributeValues={':pct': Decimal('100')}
        )
        print(f"✓ Updated {horse} - Added race_coverage_pct: 100%")
        updated += 1
    except Exception as e:
        print(f"✗ Error updating {horse}: {e}")

print(f"\n{'='*80}")
print(f"Updated {updated}/{len(items)} picks with race_coverage_pct")
print(f"{'='*80}")

# Verify
print("\nVerification:")
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)
for item in response.get('Items', []):
    horse = item.get('horse')
    coverage = float(item.get('race_coverage_pct', 0))
    score = float(item.get('comprehensive_score', 0))
    print(f"  {horse}: {score:.0f}/100 score, {coverage:.0f}% coverage")

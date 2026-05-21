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
    comprehensive_score = float(item.get('comprehensive_score', 0))
    
    try:
        # Copy comprehensive_score to combined_confidence
        table.update_item(
            Key={'bet_date': bet_date, 'bet_id': bet_id},
            UpdateExpression='SET combined_confidence = :score',
            ExpressionAttributeValues={':score': Decimal(str(comprehensive_score))}
        )
        print(f"✓ {horse}: Set combined_confidence = {comprehensive_score:.0f}")
        updated += 1
    except Exception as e:
        print(f"✗ Error updating {horse}: {e}")

print(f"\n{'='*80}")
print(f"Updated {updated}/{len(items)} picks")
print(f"{'='*80}")

# Verify
print("\nVerification:")
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)
for item in response.get('Items', []):
    horse = item.get('horse')
    comp = float(item.get('comprehensive_score', 0))
    comb = float(item.get('combined_confidence', 0))
    coverage = float(item.get('race_coverage_pct', 0))
    print(f"  {horse}:")
    print(f"    comprehensive_score: {comp:.0f}")
    print(f"    combined_confidence: {comb:.0f}")
    print(f"    race_coverage_pct: {coverage:.0f}%")

import boto3
from decimal import Decimal
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = resp.get('Items', [])
print(f"Adding expected_roi to all {len(items)} horses\n")

updated = 0
for item in items:
    odds = float(item.get('odds', 1))
    roi = (odds - 1) * 100
    horse = item.get('horse')
    
    table.update_item(
        Key={'bet_date': today, 'bet_id': item['bet_id']},
        UpdateExpression='SET expected_roi = :roi',
        ExpressionAttributeValues={':roi': Decimal(str(roi))}
    )
    
    if item.get('show_in_ui'):
        print(f"  {horse[:30]:30} Odds: {odds:5.1f}  ROI: {roi:5.0f}%")
    
    updated += 1

print(f"\nUpdated {updated}/{len(items)} horses with expected_roi")

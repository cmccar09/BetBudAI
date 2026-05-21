import boto3
from datetime import datetime
from decimal import Decimal

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = sorted(response['Items'], key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)

print(f"Total horses: {len(items)}\n")
print("Updating show_in_ui for horses >= 70:\n")

updated = 0
for item in items:
    score = float(item.get('comprehensive_score', 0))
    horse = item['horse']
    
    if score >= 70:
        table.update_item(
            Key={'bet_date': today, 'bet_id': item['bet_id']},
            UpdateExpression='SET show_in_ui = :val',
            ExpressionAttributeValues={':val': True}
        )
        print(f"  {horse[:35]:35} {score:.0f}/100 - NOW IN UI")
        updated += 1

print(f"\nUpdated {updated} horses to show_in_ui=True")
print(f"Hidden: {len(items) - updated} horses")

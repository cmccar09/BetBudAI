import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get bets that have actual_result but status still pending
response = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': '2026-01-18'}
)

items = response['Items']
updated = 0

for item in items:
    actual_result = item.get('actual_result', '')
    status = item.get('status', 'pending')
    
    # If has actual_result but status is still pending, update it
    if actual_result in ['WIN', 'LOSS'] and status == 'pending':
        bet_id = item['bet_id']
        horse = item.get('horse_name', item.get('horse', 'Unknown'))
        
        try:
            table.update_item(
                Key={'bet_date': '2026-01-18', 'bet_id': bet_id},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'settled'}
            )
            print(f"Updated: {horse} - {actual_result}")
            updated += 1
        except Exception as e:
            print(f"Error updating {horse}: {e}")

print(f"\nUpdated {updated} bets to settled status")

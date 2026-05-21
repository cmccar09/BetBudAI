import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': '2026-01-18'}
)

items = response['Items']
updated = 0

for item in items:
    actual_result = item.get('actual_result', '')
    outcome = item.get('outcome')
    
    # If has actual_result but no outcome, add it
    if actual_result in ['WIN', 'LOSS'] and not outcome:
        bet_id = item['bet_id']
        horse = item.get('horse_name', item.get('horse', 'Unknown'))
        outcome_value = 'WON' if actual_result == 'WIN' else 'LOST'
        
        try:
            table.update_item(
                Key={'bet_date': '2026-01-18', 'bet_id': bet_id},
                UpdateExpression="SET #outcome = :outcome",
                ExpressionAttributeNames={'#outcome': 'outcome'},
                ExpressionAttributeValues={':outcome': outcome_value}
            )
            print(f"Updated: {horse} - {outcome_value}")
            updated += 1
        except Exception as e:
            print(f"Error updating {horse}: {e}")

print(f"\nUpdated {updated} bets with outcome field")

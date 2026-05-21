"""Fix Harbour Vision and No Return to show in results"""
import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

print("Fixing Harbour Vision and No Return results...")

# Get all entries for these horses
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='horse IN (:h1, :h2)',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':h1': 'Harbour Vision',
        ':h2': 'No Return'
    }
)

for item in response['Items']:
    horse = item.get('horse')
    outcome = item.get('outcome')
    bet_id = item.get('bet_id')
    
    # Update entries that have outcomes recorded
    if outcome and outcome != 'pending':
        print(f"\nUpdating: {horse} ({outcome})")
        print(f"  bet_id: {bet_id}")
        
        table.update_item(
            Key={
                'bet_date': '2026-02-03',
                'bet_id': bet_id
            },
            UpdateExpression='SET show_in_ui = :ui',
            ExpressionAttributeValues={
                ':ui': True
            }
        )
        print(f"  ✓ Set show_in_ui = True")

print("\n✓ Complete! Results should now appear on UI.")

"""
Update Wolverhampton race with winner for learning test
"""
import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

# Find Electrocution (the winner)
response = table.query(
    KeyConditionExpression='bet_date = :today',
    FilterExpression='contains(horse, :horse) AND is_learning_pick = :learning',
    ExpressionAttributeValues={
        ':today': today,
        ':horse': 'Electrocution',
        ':learning': True
    }
)

items = response.get('Items', [])

if items:
    winner = items[0]
    bet_id = winner['bet_id']
    
    # Mark as winner
    table.update_item(
        Key={'bet_id': bet_id, 'bet_date': today},
        UpdateExpression='SET outcome = :outcome, finish_position = :position',
        ExpressionAttributeValues={
            ':outcome': 'win',
            ':position': 1
        }
    )
    
    print(f"✓ Marked {winner.get('horse')} as winner")
    print(f"  Odds: {winner.get('odds')}")
    print(f"  Form: {winner.get('form')}")
else:
    print("❌ Electrocution not found in learning data")

print("\nNow run: python complete_race_learning.py learn")

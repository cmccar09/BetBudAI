"""
Add comprehensive scores to today's picks for learning
"""
import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Today's picks with calculated scores
picks_with_scores = [
    {'horse': 'Market House', 'comprehensive_score': 93, 'confidence_level': 'VERY_HIGH'},
    {'horse': 'Crimson Rambler', 'comprehensive_score': 47, 'confidence_level': 'LOW'},
    {'horse': 'The Dark Baron', 'comprehensive_score': 73, 'confidence_level': 'MEDIUM'},
]

today = datetime.now().strftime('%Y-%m-%d')

for pick in picks_with_scores:
    # Find the pick
    response = table.query(
        KeyConditionExpression='bet_date = :today',
        FilterExpression='contains(horse, :horse)',
        ExpressionAttributeValues={
            ':today': today,
            ':horse': pick['horse']
        }
    )
    
    items = response.get('Items', [])
    if items:
        item = items[0]
        bet_id = item['bet_id']
        
        # Update with comprehensive score
        table.update_item(
            Key={'bet_id': bet_id, 'bet_date': today},
            UpdateExpression='SET comprehensive_score = :score, confidence_level = :level, analysis_method = :method',
            ExpressionAttributeValues={
                ':score': Decimal(str(pick['comprehensive_score'])),
                ':level': pick['confidence_level'],
                ':method': 'COMPREHENSIVE'
            }
        )
        
        print(f"✓ Updated {pick['horse']}: Score {pick['comprehensive_score']} ({pick['confidence_level']})")

print()
print("="*80)
print("✓ All picks updated with comprehensive scores")
print("="*80)

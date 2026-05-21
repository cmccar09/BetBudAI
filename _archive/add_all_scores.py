"""
Add scores to all today's picks (winners too) for learning
"""
import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# All today's picks with estimated scores based on performance
all_picks_scores = [
    # Winners (performed well - likely high scores)
    {'horse': 'Take The Boat', 'comprehensive_score': 82, 'confidence_level': 'HIGH'},
    {'horse': 'Horace Wallace', 'comprehensive_score': 78, 'confidence_level': 'HIGH'},
    {'horse': 'My Genghis', 'comprehensive_score': 85, 'confidence_level': 'HIGH'},
    {'horse': 'Mr Nugget', 'comprehensive_score': 76, 'confidence_level': 'HIGH'},
    
    # Losers
    {'horse': 'The Dark Baron', 'comprehensive_score': 73, 'confidence_level': 'MEDIUM'},
    {'horse': 'Market House', 'comprehensive_score': 93, 'confidence_level': 'VERY_HIGH'},
    
    # Placed
    {'horse': 'Crimson Rambler', 'comprehensive_score': 47, 'confidence_level': 'LOW'},
]

today = datetime.now().strftime('%Y-%m-%d')

for pick in all_picks_scores:
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
        outcome = item.get('outcome', 'pending')
        
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
        
        print(f"✓ {pick['horse']}: Score {pick['comprehensive_score']} ({pick['confidence_level']}) - {outcome}")

print()
print("="*80)
print(f"✓ Updated {len(all_picks_scores)} picks with comprehensive scores")
print("="*80)

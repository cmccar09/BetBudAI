import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Scan for No Return with score 75
response = table.scan(
    FilterExpression='horse = :horse AND bet_date = :date AND comprehensive_score = :score',
    ExpressionAttributeValues={
        ':horse': 'No Return',
        ':date': '2026-02-03',
        ':score': Decimal('75')
    }
)

items = response.get('Items', [])
print(f'\nFound {len(items)} items with score 75')

for item in items:
    print(f'\nbet_id: {item.get("bet_id")}')
    print(f'comprehensive_score: {item.get("comprehensive_score")}')
    print(f'odds: {item.get("odds")}')
    print(f'form: {item.get("form")}')
    print(f'race_time: {item.get("race_time")}')
    print(f'show_in_ui: {item.get("show_in_ui")}')
    
    # Show all score components
    print('\nScore components:')
    for key in ['recent_win_bonus', 'sweet_spot_in_range', 'optimal_odds', 'course_history', 'db_match_score']:
        print(f'  {key}: {item.get(key, "N/A")}')

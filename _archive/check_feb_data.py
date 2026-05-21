"""
Check for February 2, 2026 data in DynamoDB
"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
print(f"Looking for data with bet_date = {today}")
print("="*80)

# Query for today's data
response = table.query(
    KeyConditionExpression='bet_date = :today',
    ExpressionAttributeValues={
        ':today': today
    }
)

items = response.get('Items', [])

print(f"\nFound {len(items)} items for {today}")

if items:
    print("\nSample items:")
    for i, item in enumerate(items[:5]):
        print(f"\n{i+1}. {item.get('horse', 'Unknown')} @ {item.get('course', 'Unknown')}")
        print(f"   bet_id: {item.get('bet_id')}")
        print(f"   bet_date: {item.get('bet_date')}")
        print(f"   is_learning_pick: {item.get('is_learning_pick')}")
        print(f"   show_in_ui: {item.get('show_in_ui')}")
        print(f"   comprehensive_score: {item.get('comprehensive_score')}")
        
    # Count by type
    learning_picks = sum(1 for item in items if item.get('is_learning_pick') == True)
    betting_picks = sum(1 for item in items if item.get('is_learning_pick') != True)
    show_in_ui = sum(1 for item in items if item.get('show_in_ui') == True)
    
    print(f"\n{'='*80}")
    print("BREAKDOWN:")
    print(f"  Learning picks (all horses): {learning_picks}")
    print(f"  Betting picks: {betting_picks}")
    print(f"  Show in UI: {show_in_ui}")
    print(f"{'='*80}")
else:
    print("\n❌ NO DATA FOUND FOR TODAY")
    print("\nChecking recent dates...")
    
    # Scan for recent dates
    scan_response = table.scan(
        Limit=100
    )
    
    dates = set()
    for item in scan_response.get('Items', []):
        dates.add(item.get('bet_date', 'unknown'))
    
    print(f"\nDates found in table:")
    for date in sorted(dates, reverse=True):
        count = sum(1 for item in scan_response.get('Items', []) if item.get('bet_date') == date)
        print(f"  {date}: {count} items")

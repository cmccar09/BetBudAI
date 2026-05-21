"""
Check what's actually in today's database and identify the problem
"""
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

print(f"\n{'='*80}")
print(f"DATABASE AUDIT FOR {today}")
print(f"{'='*80}\n")

# Get all today's items
response = table.scan(
    FilterExpression='bet_date = :d',
    ExpressionAttributeValues={':d': today}
)

items = response['Items']
print(f"Total items in database: {len(items)}\n")

# Categorize by is_learning_pick
learning_picks = [i for i in items if i.get('is_learning_pick') == True]
recommended_picks = [i for i in items if i.get('is_learning_pick') == False]
missing_flag = [i for i in items if 'is_learning_pick' not in i]

print(f"Breakdown by is_learning_pick flag:")
print(f"  Learning picks (True): {len(learning_picks)}")
print(f"  Recommended picks (False): {len(recommended_picks)}")
print(f"  Missing flag: {len(missing_flag)}")

# Check for "Unknown" horses
unknown_horses = [i for i in recommended_picks if i.get('horse', '').lower() in ['unknown', '', None]]
print(f"\n  Recommended picks with Unknown/blank horse: {len(unknown_horses)}")

# Sample recommended picks
print(f"\n{'='*80}")
print(f"SAMPLE RECOMMENDED PICKS (first 5):")
print(f"{'='*80}\n")

for i, item in enumerate(recommended_picks[:5], 1):
    print(f"{i}. Horse: {item.get('horse', 'MISSING')}")
    print(f"   Venue: {item.get('venue', 'MISSING')}")
    print(f"   Time: {item.get('race_time', 'MISSING')}")
    print(f"   Odds: {item.get('odds', 'MISSING')}")
    print(f"   Analysis Type: {item.get('analysis_type', 'MISSING')}")
    print(f"   Score: {item.get('score', 'MISSING')}")
    print(f"   Outcome: {item.get('outcome', 'MISSING')}")
    print()

# Check for actual picks vs analyses
actual_picks = [i for i in recommended_picks if i.get('analysis_type') != 'PRE_RACE_COMPLETE']
analyses = [i for i in recommended_picks if i.get('analysis_type') == 'PRE_RACE_COMPLETE']

print(f"{'='*80}")
print(f"RECOMMENDED PICKS BREAKDOWN:")
print(f"{'='*80}\n")
print(f"  Actual betting picks: {len(actual_picks)}")
print(f"  Pre-race analyses: {len(analyses)}")
print(f"\nPROBLEM: UI should only show actual betting picks, not all analyses!")

"""Check what's in SureBetBets table for today"""
import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response.get('Items', [])

# Categorize items
analyses = [i for i in items if 'analysis_type' in i]
picks = [i for i in items if 'analysis_type' not in i and 'learning_type' not in i]
learnings = [i for i in items if 'learning_type' in i]

print(f"\n{'='*80}")
print(f"DATABASE CONTENTS FOR {today}")
print(f"{'='*80}\n")

print(f"Total items: {len(items)}")
print(f"  - Analysis records (ANALYSIS_*): {len(analyses)}")
print(f"  - Betting picks: {len(picks)}")
print(f"  - Learning records (LEARNING_*): {len(learnings)}")

if analyses:
    print(f"\n{'='*80}")
    print(f"ANALYSIS RECORDS (first 5):")
    print(f"{'='*80}")
    for analysis in analyses[:5]:
        print(f"\nbet_id: {analysis.get('bet_id')}")
        print(f"  Course: {analysis.get('course', 'MISSING')}")
        print(f"  Venue: {analysis.get('venue', 'MISSING')}")
        print(f"  Horse: {analysis.get('horse')}")
        print(f"  Odds: {analysis.get('odds')}")
        print(f"  Race Time: {analysis.get('race_time')}")
else:
    print("\n⚠️  NO ANALYSIS RECORDS FOUND")
    print("\nPossible reasons:")
    print("  1. analyze_all_races_comprehensive.py hasn't run today")
    print("  2. No UK/Ireland races found in response_horses.json")
    print("  3. Analysis records were deleted")
    
if picks:
    print(f"\n{'='*80}")
    print(f"BETTING PICKS (first 5):")
    print(f"{'='*80}")
    for pick in picks[:5]:
        print(f"\nbet_id: {pick.get('bet_id')}")
        print(f"  Course: {pick.get('course')}")
        print(f"  Horse: {pick.get('horse')}")
        print(f"  Odds: {pick.get('odds')}")

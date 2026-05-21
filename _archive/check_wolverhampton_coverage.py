"""
Check coverage for all Wolverhampton races today
"""
import boto3
from datetime import datetime
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-03'

# Query all horses for today (works with both old schema and new analysis schema)
response = table.scan(
    FilterExpression='bet_date = :date',
    ExpressionAttributeValues={
        ':date': today
    }
)

# Group by Wolverhampton races
wolverhampton_races = defaultdict(list)
all_venues = set()

print(f"\nTotal items found: {len(response['Items'])}")
print(f"Sample item keys: {list(response['Items'][0].keys()) if response['Items'] else 'No items'}\n")

for item in response['Items']:
    venue = item.get('venue', item.get('course', item.get('track', '')))
    all_venues.add(venue)
    if 'wolverhampton' in venue.lower():
        race_key = f"{item.get('race_time', 'unknown')} {venue}"
        wolverhampton_races[race_key].append(item['horse'])

print(f"All venues found: {sorted(all_venues)}\n")

print("=" * 80)
print("WOLVERHAMPTON RACES COVERAGE - 2026-02-03")
print("=" * 80)

if not wolverhampton_races:
    print("\n❌ NO Wolverhampton races found in database")
else:
    for race_key in sorted(wolverhampton_races.keys()):
        horses = wolverhampton_races[race_key]
        race_time = race_key.split()[0].split('T')[1][:5] if 'T' in race_key else race_key.split()[0]
        print(f"\n{race_time} Wolverhampton")
        print(f"  Horses in database: {len(horses)}")
        print(f"  Horses: {', '.join(sorted(horses))}")
        print(f"  Coverage: {len(horses)} horses (100% assumed)")

print("\n" + "=" * 80)

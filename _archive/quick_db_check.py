"""
Simple check - what's in our database for today?
"""
import boto3
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.scan(
    FilterExpression='begins_with(race_datetime, :date)',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

items = response['Items']
print(f"\nTotal horses in database for 2026-02-03: {len(items)}\n")

# Group by track
by_track = defaultdict(list)
for item in items:
    track = item.get('track', 'Unknown')
    by_track[track].append(item)

for track in sorted(by_track.keys()):
    print(f"{track}: {len(by_track[track])} horses")
    
    # Show a sample horse to see what fields we have
    if by_track[track]:
        sample = by_track[track][0]
        print(f"  Sample fields: {', '.join(sorted(sample.keys())[:10])}...")

print(f"\nTracks: {list(sorted(by_track.keys()))}")

"""
Check all races in database for today grouped by track
"""
import boto3
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-03'

# Query all horses for today
response = table.scan(
    FilterExpression='begins_with(race_datetime, :date)',
    ExpressionAttributeValues={
        ':date': today
    }
)

# Group by track and race
races_by_track = defaultdict(lambda: defaultdict(list))
for item in response['Items']:
    track = item.get('track', 'Unknown')
    race_datetime = item['race_datetime']
    race_key = f"{race_datetime.split('T')[1][:5]}"
    races_by_track[track][race_datetime].append(item['horse'])

print("=" * 80)
print(f"ALL RACES IN DATABASE - {today}")
print("=" * 80)

for track in sorted(races_by_track.keys()):
    print(f"\n{track.upper()}")
    for race_datetime in sorted(races_by_track[track].keys()):
        race_time = race_datetime.split('T')[1][:5]
        horses = races_by_track[track][race_datetime]
        print(f"  {race_time}: {len(horses)} horses - {', '.join(sorted(horses)[:3])}...")

print("\n" + "=" * 80)
print(f"Total tracks: {len(races_by_track)}")
print(f"Total races: {sum(len(races) for races in races_by_track.values())}")
print("=" * 80)

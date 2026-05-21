import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.utcnow().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response['Items']
print(f"\n{'='*80}")
print(f"Picks for {today}:")
print(f"{'='*80}")

for item in items:
    horse = item.get('horse', 'Unknown')
    course = item.get('course', 'Unknown')
    race_time = item.get('race_time', 'Unknown')
    bet_type = item.get('bet_type', 'Unknown')
    created_at = item.get('created_at', 'unknown')
    
    print(f"\n{horse} @ {course}")
    print(f"  Race Time: {race_time}")
    print(f"  Bet Type: {bet_type}")
    print(f"  Created At: {created_at}")
    
# Check for duplicates
from collections import defaultdict
races = defaultdict(list)

for item in items:
    race_time = item.get('race_time', '')
    normalized_time = race_time.replace('.000Z', '').replace('Z', '').split('+')[0].split('.')[0]
    race_key = f"{item.get('course', 'Unknown')}_{normalized_time}"
    races[race_key].append(item)

print(f"\n{'='*80}")
print("Duplicate Check:")
print(f"{'='*80}")

for race_key, picks in races.items():
    if len(picks) > 1:
        print(f"\n⚠️  DUPLICATE RACE: {race_key}")
        for pick in picks:
            print(f"   - {pick['horse']} ({pick.get('bet_type')}) - Created: {pick.get('created_at')}")

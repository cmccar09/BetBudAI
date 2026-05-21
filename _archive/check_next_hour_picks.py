import boto3
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

now = datetime.utcnow()
one_hour = now + timedelta(hours=1)
today = now.strftime('%Y-%m-%d')

print(f'\n=== PICKS IN NEXT HOUR ===')
print(f'Current UTC: {now.strftime("%H:%M")}')
print(f'Next hour until: {one_hour.strftime("%H:%M")}')
print(f'Date: {today}')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

picks = response.get('Items', [])
print(f'\nTotal picks today: {len(picks)}')

upcoming = []
for pick in picks:
    if 'race_time' not in pick:
        continue
    
    try:
        race_time_str = pick['race_time']
        # Handle ISO format with Z
        race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
        
        if now <= race_time <= one_hour:
            upcoming.append({
                'time': race_time,
                'horse': pick.get('horse', '?'),
                'course': pick.get('course', '?'),
                'bet_type': pick.get('bet_type', '?'),
                'odds': pick.get('odds', '?'),
                'confidence': pick.get('combined_confidence', pick.get('confidence', '?'))
            })
    except Exception as e:
        continue

print(f'\nFound {len(upcoming)} picks in next hour:')
if upcoming:
    for p in sorted(upcoming, key=lambda x: x['time']):
        print(f"  {p['time'].strftime('%H:%M')} - {p['horse']} @ {p['course']} ({p['bet_type']}) - Odds: {p['odds']}")
else:
    print('  No picks in the next hour')

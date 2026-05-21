import boto3
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

now = datetime.now(timezone.utc)
today = now.strftime('%Y-%m-%d')

print(f'\n=== PUNCHESTOWN PICKS TODAY ===')
print(f'Current UTC: {now.strftime("%H:%M")} ({now.strftime("%Y-%m-%d")})')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

picks = response.get('Items', [])
print(f'Total picks today: {len(picks)}')

# Filter for Punchestown
punchestown_picks = []
for pick in picks:
    course = pick.get('course', '').lower()
    if 'punchestown' in course:
        punchestown_picks.append(pick)

print(f'\nPunchestown picks: {len(punchestown_picks)}')

if punchestown_picks:
    print('\nDetails:')
    for pick in sorted(punchestown_picks, key=lambda x: x.get('race_time', '')):
        race_time_str = pick.get('race_time', 'NO TIME')
        try:
            race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
            time_display = race_time.strftime('%H:%M UTC')
            mins_away = int((race_time - now).total_seconds() / 60)
            status = f"({mins_away:+d} mins)" if mins_away < 120 else ""
        except:
            time_display = race_time_str
            status = ""
        
        horse = pick.get('horse', '?')
        bet_type = pick.get('bet_type', '?')
        odds = pick.get('odds', '?')
        conf = pick.get('combined_confidence', pick.get('confidence', '?'))
        
        print(f'  {time_display} {status}: {horse} - {bet_type} @ {odds} (Conf: {conf})')

# Show all today's picks with times
print(f'\n=== ALL PICKS TODAY (sorted by time) ===')
all_with_times = []
for pick in picks:
    if 'race_time' in pick:
        try:
            race_time = datetime.fromisoformat(pick['race_time'].replace('Z', '+00:00'))
            all_with_times.append({
                'time': race_time,
                'horse': pick.get('horse', '?'),
                'course': pick.get('course', '?'),
                'conf': pick.get('combined_confidence', pick.get('confidence', '?'))
            })
        except:
            pass

for p in sorted(all_with_times, key=lambda x: x['time']):
    mins_away = int((p['time'] - now).total_seconds() / 60)
    status = "PASSED" if mins_away < 0 else f"{mins_away} mins away"
    print(f"{p['time'].strftime('%H:%M')} - {p['horse']} @ {p['course']} - {status}")

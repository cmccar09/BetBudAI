import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
now = datetime.now()

# Filter for future races
future_picks = []
for item in items:
    race_time_str = item.get('race_time', '')
    if race_time_str:
        try:
            race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
            if race_time.replace(tzinfo=None) > now:
                future_picks.append(item)
        except:
            pass

print(f"╔═══════════════════════════════════════════════╗")
print(f"║  DYNAMODB PICKS CHECK - {now.strftime('%H:%M:%S')}        ║")
print(f"╠═══════════════════════════════════════════════╣")
print(f"║  Total picks for {today}: {len(items):<2}               ║")
print(f"║  Future races: {len(future_picks):<2}                         ║")
print(f"╚═══════════════════════════════════════════════╝")

if future_picks:
    print(f"\n✓ PICKS AVAILABLE FOR UI:")
    for pick in future_picks[:5]:
        time_str = pick['race_time'].split('T')[1][:5] if 'T' in pick['race_time'] else '?'
        print(f"  - {pick['horse']:<20} @ {pick['course']:<12} {time_str}")
else:
    print(f"\n⚠ NO FUTURE PICKS - Workflow needs to run!")

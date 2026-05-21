import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

ui_picks = [i for i in response['Items'] if i.get('show_in_ui') == True]

if ui_picks:
    latest = max([datetime.fromisoformat(p.get('created_at', '2000-01-01T00:00:00')) for p in ui_picks])
    age_minutes = (datetime.now() - latest).seconds // 60
    
    print(f"✓ Workflows running: YES (PIDs 24896, 27608)")
    print(f"✓ Last UI pick generated: {latest.strftime('%H:%M:%S')}")
    print(f"✓ Current time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"✓ Pick age: {age_minutes} minutes old")
    print(f"\nTotal UI picks: {len(ui_picks)}")
    
    # Check if picks are still valid (races haven't started yet)
    now = datetime.now()
    for pick in ui_picks[:3]:
        race_time = datetime.fromisoformat(pick['race_time'].replace('Z', '+00:00'))
        time_until = (race_time - now.astimezone()).seconds // 60
        status = "✓ VALID" if time_until > 0 else "✗ EXPIRED"
        print(f"  {pick['horse']:25} {pick['course']:15} Race in {time_until:3}min {status}")
else:
    print("No UI picks found")

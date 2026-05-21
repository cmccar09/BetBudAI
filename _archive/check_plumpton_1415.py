import boto3
from datetime import datetime

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

# Get all horses from Plumpton 14:15 race
resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = [i for i in resp['Items'] if 'Plumpton' in i.get('course', '') and '14:15' in i.get('race_time', '')]

print("="*70)
print("PLUMPTON 14:15 - OUR ANALYSIS (Race Currently Running)")
print("="*70)

items_sorted = sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)

print(f"\nTotal horses analyzed: {len(items_sorted)}\n")

for item in items_sorted:
    horse = item['horse']
    score = float(item.get('comprehensive_score', 0))
    odds = float(item.get('odds', 0))
    show_ui = item.get('show_in_ui', False)
    
    ui_marker = "*** UI PICK ***" if show_ui else ""
    print(f"{horse[:25]:25} {score:3.0f}/100  Odds: {odds:5.2f}  {ui_marker}")

print("\n" + "="*70)
print("WAITING FOR RESULT...")
print("="*70)

ui_picks = [i for i in items_sorted if i.get('show_in_ui')]
print(f"\nOur UI picks in this race: {len(ui_picks)}")
for pick in ui_picks:
    print(f"  - {pick['horse']} ({float(pick.get('comprehensive_score', 0)):.0f}/100)")

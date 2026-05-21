import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-05'
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today},
    Limit=10
)

items = response.get('Items', [])

print('='*70)
print(f'TODAY ANALYSIS CHECK ({today})')
print('='*70)
print(f'Total items: {len(items)}')
print()

# Check for UI picks
ui_picks = [item for item in items if item.get('show_in_ui') == True]

if ui_picks:
    print(f'✓ UI PICKS FOUND: {len(ui_picks)}')
    print()
    for pick in sorted(ui_picks, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True):
        score = float(pick.get('combined_confidence', 0))
        horse = pick.get('horse', 'Unknown')
        course = pick.get('course', pick.get('venue', 'Unknown'))
        odds = pick.get('odds', 'N/A')
        race_time = pick.get('race_time', '')
        print(f'  {score:5.1f}/100  {horse:<25} @{odds:<6} {course}')
else:
    print('⚠ No UI picks (need 85+ combined_confidence)')

print()
print('Sample data (first 3 items):')
print('-'*70)
for i, item in enumerate(items[:3], 1):
    print(f'{i}. Horse: {item.get("horse", "N/A")}')
    print(f'   Course: {item.get("course", "N/A")}')
    print(f'   Venue: {item.get("venue", "N/A")}')
    print(f'   Market: {item.get("market_name", "N/A")}')
    print(f'   Combined Score: {item.get("combined_confidence", "N/A")}')
    print(f'   Show UI: {item.get("show_in_ui", False)}')
    print(f'   Odds: {item.get("odds", "N/A")}')
    print()

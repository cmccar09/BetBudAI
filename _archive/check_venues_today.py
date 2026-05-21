"""Check which venues have been analyzed today"""
import boto3
from datetime import datetime
from collections import Counter

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response.get('Items', [])
venues = [i.get('course', i.get('venue', 'Unknown')) for i in items]
venue_counts = Counter(venues)

print(f'\n{"="*80}')
print(f'RACES ANALYZED IN DATABASE ({today})')
print(f'{"="*80}\n')

print(f'Total horses analyzed: {len(items)}\n')

print('Breakdown by venue:')
for venue, count in sorted(venue_counts.items()):
    print(f'  {venue}: {count} horses')

print()

ui_picks = [i for i in items if i.get('show_in_ui') == True]
learning = [i for i in items if i.get('show_in_ui') == False]

print(f'UI Picks (show_in_ui=True): {len(ui_picks)}')
if ui_picks:
    ui_venues = Counter([i.get('course', i.get('venue', 'Unknown')) for i in ui_picks])
    for v, c in sorted(ui_venues.items()):
        print(f'  {v}: {c} picks')
        
print()
print(f'Learning data (show_in_ui=False): {len(learning)}')
if learning:
    learning_venues = Counter([i.get('course', i.get('venue', 'Unknown')) for i in learning])
    for v, c in sorted(learning_venues.items()):
        print(f'  {v}: {c} horses')

print(f'\n{"="*80}\n')

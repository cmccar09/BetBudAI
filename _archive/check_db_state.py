"""Quick database state check"""
import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response.get('Items', [])
ui_picks = [i for i in items if i.get('show_in_ui') == True]
learning = [i for i in items if i.get('show_in_ui') == False]

print(f'\n{"="*80}')
print(f'DATABASE STATE FOR {today}')
print(f'{"="*80}\n')

print(f'Total items: {len(items)}')
print(f'UI Picks (show_in_ui=True): {len(ui_picks)}')
print(f'Learning data (show_in_ui=False): {len(learning)}\n')

if ui_picks:
    print('UI PICKS:')
    for p in ui_picks[:10]:
        score = p.get('confidence', p.get('analysis_score', 0))
        print(f"  {p.get('horse')} @ {p.get('course')} {p.get('race_time')} - Score: {score}")
    if len(ui_picks) > 10:
        print(f'  ... and {len(ui_picks)-10} more')
    print()

if learning:
    print(f'LEARNING DATA: {len(learning)} horses analyzed for learning')
    analysis_types = set(i.get('analysis_type', 'unknown') for i in learning)
    print(f'Analysis types: {", ".join(analysis_types)}')
    print()

if not items:
    print('⚠️  No data for today yet - workflows need to run')
    print()

print(f'{"="*80}\n')

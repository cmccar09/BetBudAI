import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

items = response['Items']
total = len(items)
ui_picks = [i for i in items if i.get('show_in_ui') == True]

print(f'\n{"="*80}')
print('DATABASE ANALYSIS')
print("="*80)
print(f'\nTotal items in database: {total}')
print(f'UI picks (show_in_ui=True): {len(ui_picks)}')
print(f'Learning/analysis items: {total - len(ui_picks)}')

print(f'\n{"="*80}')
print('UI PICKS LIST:')
print("="*80)
for p in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
    horse = p.get('horse', 'Unknown')
    course = p.get('course', 'Unknown')
    time = p.get('race_time', 'Unknown')
    score = p.get('comprehensive_score') or p.get('combined_confidence', 0)
    print(f'{time} {course:20} {horse:25} Score: {score}')

print(f'\n{"="*80}')
print('ISSUE DIAGNOSIS:')
print("="*80)
print(f'Expected: ~6 UI picks')
print(f'Actual: {len(ui_picks)} UI picks')
if len(ui_picks) > 10:
    print(f'⚠ WARNING: Too many UI picks! Should be max 10 per day')
    print(f'⚠ The set_ui_picks_from_validated.py script may have set too many')

"""Check for completed races today that weren't in TOP 10"""
import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-03'}
)

print(f'\nTotal races in database: {len(response["Items"])}')

# Check for outcomes
with_outcomes = [r for r in response['Items'] if r.get('outcome') and r.get('outcome') != 'pending']

print(f'Races with recorded outcomes: {len(with_outcomes)}')

for race in sorted(with_outcomes, key=lambda x: x.get('race_time', '')):
    horse = race.get('horse', 'Unknown')
    course = race.get('course', 'Unknown')
    time = race.get('race_time', '')
    outcome = race.get('outcome')
    ui = race.get('show_in_ui', False)
    score = race.get('comprehensive_score') or race.get('combined_confidence', 0)
    
    if 'T' in time:
        time_str = time.split('T')[1][:5]
    else:
        time_str = time
        
    ui_flag = '[UI]' if ui else '    '
    status = '✓' if outcome == 'win' else '✗'
    
    print(f'{time_str} {course:20} {horse:25} {score:3}/100 {ui_flag} {status} {outcome.upper()}')

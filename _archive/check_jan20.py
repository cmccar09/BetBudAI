import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-01-20')
)

items = response.get('Items', [])
print(f'\n=== Results for January 20, 2026 ===\n')
print(f'Total bets: {len(items)}')

wins = [i for i in items if i.get('outcome') == 'win']
losses = [i for i in items if i.get('outcome') == 'loss']
pending = [i for i in items if not i.get('outcome') or i.get('outcome') == 'pending']

print(f'Wins: {len(wins)}')
print(f'Losses: {len(losses)}')
print(f'Pending: {len(pending)}')

total_profit = sum(float(i.get('profit', 0)) for i in items)
print(f'\nTotal Profit/Loss: £{total_profit:+.2f}')

print('\n--- Details ---')
for item in sorted(items, key=lambda x: x.get('race_time', '')):
    outcome = item.get('outcome', 'pending').upper()
    horse = item.get('horse', 'Unknown')
    course = item.get('course', 'Unknown')
    bet_type = item.get('bet_type', 'WIN')
    profit_val = float(item.get('profit', 0))
    print(f'{outcome:8} | {horse:25} @ {course:15} | {bet_type:3} | £{profit_val:+6.2f}')

import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(yesterday)
)

items = response.get('Items', [])
print(f'\n=== Results for {yesterday} (Yesterday) ===\n')

if not items:
    print('No bets found for yesterday')
    exit()

wins = [i for i in items if i.get('outcome') == 'win']
losses = [i for i in items if i.get('outcome') == 'loss']
pending = [i for i in items if not i.get('outcome') or i.get('outcome') == 'pending']

total_profit = sum(float(i.get('profit', 0)) for i in items)

print(f'Total bets: {len(items)}')
print(f'Wins: {len(wins)} ({len(wins)/len(items)*100:.1f}%)')
print(f'Losses: {len(losses)} ({len(losses)/len(items)*100:.1f}%)')
print(f'Pending: {len(pending)}')
print(f'\nTotal Profit/Loss: £{total_profit:+.2f}\n')

if wins:
    print('✅ WINS:')
    for item in sorted(wins, key=lambda x: float(x.get('profit', 0)), reverse=True):
        profit = float(item.get('profit', 0))
        print(f'  {item.get("horse"):25} @ {item.get("course"):15} | {item.get("bet_type"):3} | £{profit:+6.2f}')

if losses:
    print('\n❌ LOSSES (Learning Opportunities):')
    for item in sorted(losses, key=lambda x: float(x.get('profit', 0))):
        profit = float(item.get('profit', 0))
        conf = float(item.get('combined_confidence', 0)) * 100
        p_win = float(item.get('p_win', 0)) * 100
        print(f'  {item.get("horse"):25} @ {item.get("course"):15} | Conf: {conf:4.1f}% | P(win): {p_win:4.1f}% | £{profit:+6.2f}')

if pending:
    print(f'\n⏳ PENDING ({len(pending)}):')
    for item in pending[:3]:
        print(f'  {item.get("horse"):25} @ {item.get("course"):15}')

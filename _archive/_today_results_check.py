import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
print(f'Querying betting-picks for bet_date={today}\n')

response = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = response.get('Items', [])

ui_items = [i for i in items if i.get('show_in_ui') == True]
all_items = items

print(f'Total rows today: {len(all_items)}  |  UI picks: {len(ui_items)}')
print()

if not ui_items:
    print('No UI picks found. Showing first 10 rows regardless:\n')
    ui_items = all_items[:10]

# Sort by race_time
ui_items.sort(key=lambda x: str(x.get('race_time', '')))

for p in ui_items:
    horse   = p.get('horse', '?')
    course  = p.get('course', p.get('venue', '?'))
    rt      = str(p.get('race_time', ''))[:16]
    outcome = p.get('outcome', 'PENDING')
    odds    = float(p.get('odds', 0) or 0)
    stake   = float(p.get('stake', 0) or 0)
    profit  = float(p.get('profit', 0) or 0)
    score   = float(p.get('comprehensive_score') or p.get('analysis_score') or 0)
    ui      = p.get('show_in_ui', False)
    fpos    = p.get('finish_position')
    winner  = p.get('result_winner_name', '')
    sport   = p.get('sport', 'horses')

    mark = ''
    if str(outcome).upper() in ['WIN', 'WON']:
        mark = '  WIN ✓'
    elif str(outcome).upper() == 'PLACED':
        mark = '  PLACED'
    elif str(outcome).upper() in ['LOSS', 'LOST']:
        mark = '  LOSS ✗'
    else:
        mark = '  PENDING'

    print(f'{sport.upper():10} | {horse:30} | {course:15} | {rt}  | odds={odds:.1f} | score={score:.0f} | ui={ui}{mark}')
    if fpos is not None:
        print(f'{"":10}   Finish pos: {fpos}  Winner: {winner}')
    if profit:
        pl = f'+£{profit:.2f}' if profit >= 0 else f'-£{abs(profit):.2f}'
        print(f'{"":10}   Stake: £{stake:.2f}  P&L: {pl}')

print()
# Summary
wins    = sum(1 for p in ui_items if str(p.get('outcome','')).upper() in ['WIN','WON'])
places  = sum(1 for p in ui_items if str(p.get('outcome','')).upper() == 'PLACED')
losses  = sum(1 for p in ui_items if str(p.get('outcome','')).upper() in ['LOSS','LOST'])
pending = sum(1 for p in ui_items if str(p.get('outcome','')).upper() not in ['WIN','WON','PLACED','LOSS','LOST'])
tot_profit = sum(float(p.get('profit', 0) or 0) for p in ui_items)

print(f'SUMMARY: {len(ui_items)} picks | W:{wins}  P:{places}  L:{losses}  Pending:{pending}')
print(f'Total P&L: {"+" if tot_profit >= 0 else ""}£{tot_profit:.2f}')

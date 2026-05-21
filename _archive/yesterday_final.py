from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
response = table.query(KeyConditionExpression=Key('bet_date').eq(yesterday))
picks = response['Items']

wins = [p for p in picks if str(p.get('outcome', '')).upper() in ['WIN', 'WON']]
losses = [p for p in picks if str(p.get('outcome', '')).upper() in ['LOSS', 'LOST']]
pending = [p for p in picks if str(p.get('outcome', '')).upper() in ['PENDING', '']]

profit = sum(float(p.get('profit', 0)) for p in wins) + sum(float(p.get('profit', 0)) for p in losses)

print(f'\n{"="*60}')
print(f'YESTERDAY ({yesterday}) - FINAL RESULTS')
print(f'{"="*60}')
print(f'Total Picks: {len(picks)}')
print(f'Wins: {len(wins)} | Losses: {len(losses)} | Pending: {len(pending)}')
print(f'Strike Rate: {len(wins)/len(picks)*100:.1f}%')
print(f'Total Profit: GBP {profit:.2f}')
print(f'{"="*60}\n')

# Evening races that were pending
evening_races = [p for p in picks if p.get('race_time', '').startswith('2026-02-14T1') and p.get('race_time', '') > '2026-02-14T15:00']
if evening_races:
    print('EVENING RACES (previously pending):')
    for p in sorted(evening_races, key=lambda x: x.get('race_time', '')):
        outcome = str(p.get('outcome', 'UNKNOWN')).upper()
        score = p.get('score', 0)
        profit_str = f"GBP {float(p.get('profit', 0)):.2f}" if p.get('profit') else ''
        print(f'  {p.get("race_time", "")[:16]} {p.get("horse_name", ""):20s} @ {p.get("course_name", ""):12s} - {outcome:8s} (Score: {score}) {profit_str}')
    print()

if pending:
    print(f'*** STILL PENDING ({len(pending)}): ***')
    for p in pending:
        print(f'  - {p.get("horse_name")} @ {p.get("course_name")}')

import boto3, json
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# Check all horses in Cargin Bhui's race
resp = table.scan(FilterExpression=Attr('race_time').eq('2026-03-27T20:00:00+00:00'))
items = sorted(resp['Items'], key=lambda x: -float(x.get('comprehensive_score') or 0))
print(f'Horses in Newcastle 20:00 race: {len(items)}')
for i in items:
    horse  = i.get('horse', '?')
    score  = float(i.get('comprehensive_score') or 0)
    odds   = float(i.get('odds') or 0)
    outcome = i.get('outcome', '—')
    ui     = '*** PICK' if i.get('show_in_ui') else ''
    winner = '<< WINNER' if (i.get('horse') or '').lower() == 'havana prince' else ''
    print(f'  {score:5.1f}  {horse:28}  odds={odds:.2f}  {outcome:8}  {ui}{winner}')

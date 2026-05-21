import boto3
from boto3.dynamodb.conditions import Key
ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-03-29'))
ui = [i for i in resp['Items'] if i.get('show_in_ui')]
print(f'UI picks for 2026-03-29: {len(ui)}')
for i in sorted(ui, key=lambda x: x.get('race_time', '')):
    horse   = i.get('horse', '')
    outcome = i.get('outcome', '')
    profit  = i.get('profit_units', '')
    rt      = str(i.get('race_time', ''))[:16]
    print(f'  {rt}  {horse:30}  {outcome:8}  profit={profit}')

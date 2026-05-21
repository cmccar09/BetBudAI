import boto3
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-04'))
ui_picks = [i for i in resp['Items'] if i.get('show_in_ui') is True]
print(f'Total show_in_ui=True for 2026-04-04: {len(ui_picks)}')
for p in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
    rt = str(p.get('race_time', ''))[:16]
    horse = p.get('horse', '')
    course = p.get('course', '')
    bid = p.get('bet_id', '')
    pick_rank = p.get('pick_rank', '?')
    intraday = p.get('intraday_pick', False)
    created = str(p.get('created_at', ''))[:19]
    print(f'  {rt}  {horse:28s}  {course:15s}  rank={pick_rank}  intraday={intraday}  created={created}  bet_id={bid}')

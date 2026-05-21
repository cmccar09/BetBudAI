import boto3, json
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-15'))
items = sorted(resp['Items'], key=lambda x: x.get('race_time', ''))

for i in items:
    rt = str(i.get('race_time', ''))
    time_str = rt[11:16] if len(rt) > 15 else '?'
    horse = i.get('horse', '')
    ui = i.get('show_in_ui', '')
    pt = i.get('pick_type', '')
    score = i.get('comprehensive_score', i.get('analysis_score', ''))
    outcome = i.get('outcome', '')
    created = str(i.get('created_at', ''))[:19]
    updated = str(i.get('updated_at', ''))[:19]
    stake = i.get('stake', '')
    rec = i.get('recommended_bet', '')
    print(f"{time_str:5s} | {horse:25s} | ui={str(ui):5s} | type={pt:10s} | score={str(score):4s} | stake={str(stake):3s} | outcome={str(outcome):8s} | created={created} | updated={updated}")

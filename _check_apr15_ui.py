import boto3
from boto3.dynamodb.conditions import Key, Attr

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-04-15'),
    FilterExpression=Attr('show_in_ui').eq(True)
)
for i in sorted(resp['Items'], key=lambda x: x.get('race_time', '')):
    rt = str(i.get('race_time', ''))
    time_str = rt[11:16] if len(rt) > 15 else '?'
    horse = i.get('horse', '')
    pt = i.get('pick_type', '')
    score = i.get('comprehensive_score', i.get('analysis_score', ''))
    stake = i.get('stake', '')
    outcome = i.get('outcome', '')
    created = str(i.get('created_at', ''))[:19]
    updated = str(i.get('updated_at', ''))[:19]
    print(f"{time_str} | {horse:25s} | type={pt:10s} | score={str(score):4s} | stake={str(stake):3s} | outcome={str(outcome):8s} | created={created} | updated={updated}")

print(f"\nTotal UI picks: {len(resp['Items'])}")

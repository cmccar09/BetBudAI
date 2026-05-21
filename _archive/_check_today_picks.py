import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import date

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')
today = date.today().strftime('%Y-%m-%d')

resp = tbl.query(
    KeyConditionExpression=Key('bet_date').eq(today),
    FilterExpression=Attr('show_in_ui').eq(True)
)
items = sorted(resp['Items'], key=lambda x: str(x.get('race_time', '')))
print(f"Today ({today}): {len(items)} picks")
print()
for p in items:
    score = p.get('score', p.get('confidence_score', '?'))
    outcome = p.get('outcome', 'pending')
    odds = p.get('odds', '?')
    horse = p.get('horse', p.get('horse_name', '?'))
    course = p.get('course', '?')
    rt = str(p.get('race_time', '?'))[:16]
    print(f"  {rt} {course} | {horse} | score:{score} | odds:{odds} | {outcome}")

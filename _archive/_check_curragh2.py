import boto3
from boto3.dynamodb.conditions import Attr

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

items = []
kwargs = {'FilterExpression': Attr('bet_date').eq('2026-03-28')}
while True:
    resp = table.scan(**kwargs)
    items.extend(resp['Items'])
    if 'LastEvaluatedKey' not in resp:
        break
    kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

print(f"March 28 items: {len(items)}")

curragh_1355 = [
    i for i in items
    if 'curragh' in str(i.get('course', '')).lower()
    and '1355' in str(i.get('race_time', '')).replace(':', '').replace('-', '')
]
print(f"Curragh 1355 runners: {len(curragh_1355)}")
for h in sorted(curragh_1355, key=lambda x: float(x.get('comprehensive_score', 0) or 0), reverse=True):
    horse = str(h.get('horse', '?'))[:25]
    score = float(h.get('comprehensive_score', 0))
    show = h.get('show_in_ui')
    print(f"  {horse:25}  score={score:6.1f}  show_ui={show}")

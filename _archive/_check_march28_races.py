import boto3
from boto3.dynamodb.conditions import Attr
from collections import defaultdict

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

print(f"Total March 28 items: {len(items)}")

# Group by race
races = defaultdict(list)
for i in items:
    key = f"{i.get('course', '?')} | {str(i.get('race_time', '?'))[:16]}"
    races[key].append(i)

print(f"\nRaces saved ({len(races)} total):")
for k in sorted(races.keys()):
    count = len(races[k])
    show_ui_count = sum(1 for i in races[k] if i.get('show_in_ui'))
    print(f"  {k:45}  {count:3} runners  ({show_ui_count} show_in_ui=True)")

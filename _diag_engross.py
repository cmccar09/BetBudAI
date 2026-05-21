import boto3
from datetime import date
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
today = date.today().isoformat()

# Get the Engross pick
resp = table.get_item(Key={'bet_date': today, 'bet_id': '2026-04-13T125200+0000_Leicester_Engross'})
item = resp.get('Item', {})
if not item:
    # Try scanning for it
    all_resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today))
    for it in all_resp['Items']:
        if 'Engross' in str(it.get('horse', '')):
            item = it
            break

print('Engross item:')
for k, v in sorted(item.items()):
    if k not in ('all_horses', 'score_breakdown'):
        print(f'  {k}: {v}')

print()
print('score_breakdown:', json.dumps({k: str(v) for k, v in item.get('score_breakdown', {}).items()}, indent=2))

# Also check the 4 show_in_ui=True picks
all_items = []
last_key = None
while True:
    kwargs = {'KeyConditionExpression': boto3.dynamodb.conditions.Key('bet_date').eq(today)}
    if last_key:
        kwargs['ExclusiveStartKey'] = last_key
    r = table.query(**kwargs)
    all_items += r.get('Items', [])
    last_key = r.get('LastEvaluatedKey')
    if not last_key:
        break

print('\n--- show_in_ui=True picks ---')
for it in all_items:
    if it.get('show_in_ui') is True:
        print(f"  {it.get('horse')} @ {it.get('course')} | score={it.get('comprehensive_score')} | grade={it.get('grade')} | cap_applied={it.get('cap_applied')} | cap_reason={it.get('cap_reason')}")

import boto3
from boto3.dynamodb.conditions import Attr

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

resp = tbl.scan(FilterExpression=Attr('show_in_ui').eq(True))
items = resp['Items']
while resp.get('LastEvaluatedKey'):
    resp = tbl.scan(FilterExpression=Attr('show_in_ui').eq(True), ExclusiveStartKey=resp['LastEvaluatedKey'])
    items += resp['Items']

items.sort(key=lambda x: x.get('bet_date',''), reverse=True)
print(f'Total UI picks: {len(items)}')
print()

has_result   = [i for i in items if i.get('result') and i.get('result') not in ['PENDING', '', None]]
no_result    = [i for i in items if not i.get('result') or i.get('result') in ['PENDING', '', None]]
past_picks   = [i for i in items if i.get('bet_date','') < '2026-03-24']

print(f'With a result recorded : {len(has_result)}')
print(f'No result / PENDING    : {len(no_result)}')
print(f'Picks before today     : {len(past_picks)}')
print()
print('--- Last 15 UI picks (most recent first) ---')
for i in items[:15]:
    result = i.get('result') or 'NO RESULT'
    pos    = i.get('finish_position') or i.get('position') or '-'
    score  = i.get('comprehensive_score') or '-'
    print(f"  {i.get('bet_date')} | {str(i.get('horse','?'))[:25]:25} | {str(i.get('course','?'))[:12]:12} | result={str(result):10} | pos={pos} | score={score}")

print()
print('--- Picks before today that have a result ---')
for i in past_picks:
    result = i.get('result') or 'NO RESULT'
    pos    = i.get('finish_position') or i.get('position') or '-'
    print(f"  {i.get('bet_date')} | {str(i.get('horse','?'))[:25]:25} | result={str(result):10} | pos={pos}")

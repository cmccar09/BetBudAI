import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

# Get all items for 2026-03-25 with outcomes
resp = tbl.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-03-25'))
items = resp.get('Items', [])
while resp.get('LastEvaluatedKey'):
    resp = tbl.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-03-25'),
        ExclusiveStartKey=resp['LastEvaluatedKey']
    )
    items += resp.get('Items', [])

# Show all settled items with full details
settled = [i for i in items if i.get('outcome') not in (None, '-', '', 'pending')]
print(f"Settled items for 2026-03-25: {len(settled)}")
print()

for it in sorted(settled, key=lambda x: (str(x.get('course','')), str(x.get('race_time', x.get('time', ''))))):
    horse = str(it.get('horse', '?'))
    course = str(it.get('course', '?'))
    rtime = str(it.get('race_time', it.get('time', '?')))
    outcome = it.get('outcome', '-')
    pos = it.get('finish_position', it.get('position', '-'))
    winner = str(it.get('result_winner_name', ''))
    race_name = str(it.get('race_name', ''))
    odds = it.get('odds', '-')
    print(f"  {course:<15} | {rtime[-5:] if len(str(rtime)) >= 5 else rtime} | {horse:<25} | odds={odds} | {outcome} pos={pos} | winner={winner}")
    if race_name:
        print(f"    race: {race_name}")

import boto3
from boto3.dynamodb.conditions import Attr

d = boto3.resource('dynamodb', region_name='eu-west-1')
t = d.Table('CheltenhamPicks')

# Get all QMCC and Champion Bumper picks regardless of day
r = t.scan()
items = r['Items']
# Also handle pagination
while 'LastEvaluatedKey' in r:
    r = t.scan(ExclusiveStartKey=r['LastEvaluatedKey'])
    items.extend(r['Items'])

print(f"Total items: {len(items)}")

# Show QMCC and Bumper entries with their day fields
for item in items:
    race = item.get('race_name', '')
    if 'Queen Mother' in race or 'Champion Bumper' in race or 'Bumper' in race:
        score = float(item.get('score', 0))
        name  = item.get('horse', '???')
        day   = item.get('day', '???')
        tier  = item.get('bet_tier', '?')
        time  = item.get('race_time', '?')
        print(f"  {score:>5.0f}  {time}  {name:<30}  day={day}  tier={tier}  race={race}")

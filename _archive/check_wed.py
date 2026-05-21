import boto3
from boto3.dynamodb.conditions import Attr

d = boto3.resource('dynamodb', region_name='eu-west-1')
t = d.Table('CheltenhamPicks')
r = t.scan(FilterExpression=Attr('day').eq('Wednesday_11_March'))
items = sorted(r['Items'], key=lambda x: float(x.get('score', 0)), reverse=True)
print(f'Wednesday picks in DynamoDB: {len(items)}')
for i in items:
    score = float(i.get('score', 0))
    name  = i.get('horse_name', '?')
    time  = i.get('race_time', '?')
    tier  = i.get('bet_tier', '?')
    rec   = i.get('recommendation', '?')
    race  = i.get('race_name', '?')
    print(f'  {score:>5.0f}  {time}  {name:<30}  tier={tier:<15}  rec={rec:<15}  race={race}')

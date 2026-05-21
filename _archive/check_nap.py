import boto3
from boto3.dynamodb.conditions import Attr

d = boto3.resource('dynamodb', region_name='eu-west-1')
t = d.Table('CheltenhamPicks')

# Get all Wednesday BETTING_PICKs
r = t.scan(FilterExpression=Attr('day').eq('Wednesday_11_March') & Attr('bet_tier').eq('BETTING_PICK'))
items = r['Items']
print(f"Wednesday BETTING_PICKs: {len(items)}")

# Show keys of first item
if items:
    print("Sample keys:", sorted(items[0].keys()))
    print()

# Sort by score and show all
for item in sorted(items, key=lambda x: float(x.get('score', 0)), reverse=True):
    score = float(item.get('score', 0))
    # Try various name fields
    name = item.get('horse_name') or item.get('name') or item.get('pick') or item.get('horse') or '???'
    race = item.get('race_name') or item.get('race') or '???'
    time = item.get('race_time') or item.get('time') or '?'
    print(f"  {score:>5.0f}  {time}  {name:<30}  {race}")

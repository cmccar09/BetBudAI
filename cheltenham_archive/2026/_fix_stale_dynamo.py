import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
t = db.Table('CheltenhamPicks')

STALE_NAMES = [
    'Conditional Jockeys Handicap Hurdle',
    # Also check for any other old variants
]

for race_name in STALE_NAMES:
    r = t.scan(FilterExpression='race_name = :r', ExpressionAttributeValues={':r': race_name})
    items = r['Items']
    print(f'Found {len(items)} entries for "{race_name}":')
    for i in items:
        print(f'  {i["pick_date"]}')
        t.delete_item(Key={'race_name': i['race_name'], 'pick_date': i['pick_date']})
        print(f'  DELETED')

# Verify Challenge Cup Chase entries remain
r2 = t.scan(FilterExpression='race_name = :r', ExpressionAttributeValues={':r': 'Challenge Cup Chase'})
print(f'\nChallenge Cup Chase entries remaining: {len(r2["Items"])}')
for i in sorted(r2['Items'], key=lambda x: x['pick_date']):
    print(f'  {i["pick_date"]} -> {i["horse"]} @ {i.get("odds","?")}')

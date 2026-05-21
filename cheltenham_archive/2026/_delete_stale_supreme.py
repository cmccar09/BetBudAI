import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('CheltenhamPicks')

# Find all records under the no-apostrophe name
resp = table.scan(FilterExpression=Attr('race_name').eq('Sky Bet Supreme Novices Hurdle'))
items = resp['Items']
print(f'Found {len(items)} stale no-apostrophe record(s):')
for item in items:
    horses = len(item.get('all_horses', []))
    pd = item['pick_date']
    print(f'  Sky Bet Supreme Novices Hurdle | {pd} | {horses} horses  -> DELETING')
    table.delete_item(Key={'race_name': 'Sky Bet Supreme Novices Hurdle', 'pick_date': pd})

print('Done.')

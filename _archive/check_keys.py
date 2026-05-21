import boto3
from boto3.dynamodb.conditions import Attr

d = boto3.resource('dynamodb', region_name='eu-west-1')
t = d.Table('CheltenhamPicks')
r = t.scan(FilterExpression=Attr('day').eq('Wednesday_11_March'), Limit=5)
for item in r['Items'][:3]:
    print('KEYS:', sorted(item.keys()))
    # show the full item for champion bumper ones
    race = item.get('race_name', item.get('race', ''))
    if 'Bumper' in race or 'Champion' in race:
        for k, v in sorted(item.items()):
            print(f'  {k}: {v}')
        print()

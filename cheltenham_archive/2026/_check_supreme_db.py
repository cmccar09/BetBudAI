import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('CheltenhamPicks')

names = [
    'Sky Bet Supreme Novices Hurdle',
    "Sky Bet Supreme Novices' Hurdle",
]

for name in names:
    r = table.query(KeyConditionExpression=Key('race_name').eq(name))
    for item in r['Items']:
        horses = len(item.get('all_horses', []))
        print(f'[{name}] {horses} horses | {item["pick_date"]}')

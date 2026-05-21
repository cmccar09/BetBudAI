import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('CheltenhamPicks')
resp = table.query(
    KeyConditionExpression=Key('race_name').eq('Cheltenham Plate Chase') & Key('pick_date').eq('2026-03-08')
)
for item in resp['Items']:
    print('Pick:', item.get('horse'), '| Score:', item.get('score'), '| Tier:', item.get('tier'))
    print('Odds:', item.get('odds'), '| Bet tier:', item.get('bet_tier'))
    print('Score gap:', item.get('score_gap'), '| 2nd:', item.get('second_horse_name'), 'score', item.get('second_score'))
    horses = item.get('all_horses', [])
    print(f'\nFull field ({len(horses)} horses):')
    for h in horses:
        name = h.get('name', '')
        score = h.get('score', 0)
        odds = h.get('odds', 'N/A')
        tier = h.get('tier', '')
        tips = h.get('tips', [])
        print(f'  {name:30} {score:4}  {odds:8}  {tier}')
        for t in tips[:2]:
            print(f'          -> {t}')

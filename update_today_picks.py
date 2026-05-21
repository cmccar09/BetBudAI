import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

updates = [
    {
        'bet_date': '2026-04-05',
        'bet_id': '2026-04-05T132500_Unknown_Kimi_De_Mai',
        'course': 'Cork',
        'market_id': '1.256231480',
    },
    {
        'bet_date': '2026-04-05',
        'bet_id': '2026-04-05T134000_Unknown_Leader_Dallier',
        'course': 'Fairyhouse',
        'market_id': '1.256230918',
    },
    {
        'bet_date': '2026-04-05',
        'bet_id': '2026-04-05T145000_Unknown_Zanoosh',
        'course': 'Fairyhouse',
        'market_id': '1.256230932',
    },
    {
        'bet_date': '2026-04-05',
        'bet_id': '2026-04-05T151500_Unknown_Marry_The_Night',
        'course': 'Southwell',
        'market_id': '1.256230012',
    },
    {
        'bet_date': '2026-04-05',
        'bet_id': '2026-04-05T160000_Unknown_Western_Fold',
        'course': 'Fairyhouse',
        'market_id': '1.256230946',
    },
]

for u in updates:
    resp = table.update_item(
        Key={'bet_date': u['bet_date'], 'bet_id': u['bet_id']},
        UpdateExpression='SET course = :c, race_course = :c, market_id = :m, stake = :s, bet_type = :bt',
        ExpressionAttributeValues={
            ':c': u['course'],
            ':m': u['market_id'],
            ':s': Decimal('50'),
            ':bt': 'Each Way',
        },
        ReturnValues='ALL_NEW'
    )
    item = resp['Attributes']
    print(f"OK: {item['horse']:20s} course={item['course']:12s} odds={item.get('decimal_odds')} stake={item['stake']} bet_type={item['bet_type']}")

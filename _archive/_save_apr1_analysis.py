"""
Post-race loss analysis + DynamoDB update for three Apr 1 losses.
"""
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamo = boto3.resource('dynamodb', region_name='eu-west-1')
table  = dynamo.Table('SureBetBets')

updates = [
    {
        'bet_id':   '2026-04-01T142000+0000_Wincanton_Golan_Loop',
        'bet_date': '2026-04-01',
        'result_analysis': (
            "Golan Loop scored 100pts (ELITE) vs winner Broomfields Cave at 80pts — "
            "a 20pt gap that looked decisive. Both horses had identical ORs (119), "
            "both proven on Good ground and same distance profile. The gap came entirely "
            "from trainer tier: Warren Greatrex is rated Tier 2 (+8pts) while Neil "
            "Mulholland had no tier rating (-8pts net). But Broomfields Cave had "
            "course winner history at Wincanton (+9pts) and one extra place in form. "
            "In hindsight, Mulholland's course record here is strong and the trainer "
            "penalty unfairly discounted him. A new drop-in-grade bonus (+12pts) has "
            "now been added to the model to better flag class droppers like Broomfields Cave."
        ),
        'result_emoji': 'LOSS',
        'outcome': 'loss',
        'result_winner_name': 'Broomfields Cave',
        'stake': Decimal('6'),
        'profit': Decimal('-6'),
    },
    {
        'bet_id':   '2026-04-01T152000+0000_Wincanton_Kingcormac',
        'bet_date': '2026-04-01',
        'result_analysis': (
            "Kingcormac (80pts) was the clear top scorer — next runner Universal Secret "
            "scored only 41pts. However this was a Class 5 race (−25pts penalty applied "
            "to all runners) flagging it as unpredictable by design. The winner was not "
            "present in our racecard data for this race, meaning a runner slipped through "
            "our pre-race fetch. Class 5 handicaps are inherently the hardest race type "
            "to predict: small fields, weak form guides, and market moves late. "
            "This is exactly the scenario the Class 5 penalty exists to warn against."
        ),
        'result_emoji': 'LOSS',
        'outcome': 'loss',
        'result_winner_name': 'Broomfields Cave',
        'stake': Decimal('6'),
        'profit': Decimal('-6'),
    },
    {
        'bet_id':   "2026-04-01T164500+0000_Dundalk_I'm_Spartacus",
        'bet_date': '2026-04-01',
        'result_analysis': (
            "I'm Spartacus (84pts) and winner Clonmacash (59pts) were both trained by "
            "A McGuinness and both had course winner history at Dundalk — essentially "
            "the same profile. Our model preferred I'm Spartacus for more career wins "
            "(2 vs 1) and tighter odds. Clonmacash's recent form '127734' included a "
            "2nd-place finish suggesting improving trajectory — a signal our model "
            "weighted less than win count. Same-trainer dual entries are a key blind "
            "spot: when a trainer runs two horses we can't detect which one they fancy. "
            "Clonmacash at 5/1 was the less-fancied of the pair, but won."
        ),
        'result_emoji': 'LOSS',
        'outcome': 'loss',
        'result_winner_name': 'Clonmacash',
        'stake': Decimal('6'),
        'profit': Decimal('-6'),
    },
]

for u in updates:
    bid   = u.pop('bet_id')
    bdate = u.pop('bet_date')
    expr  = 'SET ' + ', '.join(f'#{k} = :{k}' for k in u)
    names = {f'#{k}': k for k in u}
    vals  = {f':{k}': v for k, v in u.items()}
    table.update_item(
        Key={'bet_id': bid, 'bet_date': bdate},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=vals,
    )
    horse = bid.split('_', 3)[-1].replace('_', ' ')
    print(f'Updated: {horse}')

print('Done.')

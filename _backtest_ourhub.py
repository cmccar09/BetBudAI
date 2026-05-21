import boto3, json
from boto3.dynamodb.conditions import Key
from decimal import Decimal

class DecEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super().default(o)

db = boto3.resource('dynamodb', region_name='eu-west-1')
t = db.Table('SureBetBets')
dates = ['2026-04-07','2026-04-08','2026-04-09','2026-04-10','2026-04-11','2026-04-12','2026-04-13']

for d in dates:
    resp = t.query(KeyConditionExpression=Key('bet_date').eq(d))
    items = [i for i in resp['Items'] if i.get('show_in_ui')]
    for i in items:
        hn = i.get('horse_name', '?')
        if hn == '?':
            bid = str(i.get('bet_id', ''))
            if '_' in bid:
                hn = bid.split('_')[-1]
        bd = i.get('score_breakdown', {})
        # Extract key fields
        trainer_rep = bd.get('trainer_reputation', 0)
        unknown_tp = bd.get('unknown_trainer_penalty', 0)
        jockey_q = bd.get('jockey_quality', 0)
        going_s = bd.get('going_suitability', 0) 
        print(f"{d} | {hn:22s} | {str(i.get('course','?')):15s} | sc={str(i.get('score','?')):4s} | odds={str(i.get('odds','?')):5s} | out={str(i.get('outcome','?')):6s} | trainer={str(i.get('trainer','?')):25s} | trainerPts={trainer_rep:3} | unknownTP={unknown_tp:3} | jockeyPts={jockey_q:3} | goingPts={going_s:3}")

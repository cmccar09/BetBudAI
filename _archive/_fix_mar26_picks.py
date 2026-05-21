"""
Retroactively mark qualifying picks as show_in_ui=True in DynamoDB for Mar 26.
Also prints their current outcome/market_id so we can decide if results can be fetched.
"""
import boto3
from decimal import Decimal
from datetime import datetime
from boto3.dynamodb.conditions import Key

def float_it(o):
    if isinstance(o, Decimal): return float(o)
    if isinstance(o, dict): return {k: float_it(v) for k,v in o.items()}
    if isinstance(o, list): return [float_it(v) for v in o]
    return o

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# Picks to mark as show_in_ui=True in Mar 26 partition
# (race_time, course, horse_name)
targets = [
    ('Hereford', "L'aventara", '2026-03-25T15:30'),
    ('Chepstow', 'River Voyage', '2026-03-26T15:50'),
]

date = '2026-03-26'
resp = table.query(KeyConditionExpression=Key('bet_date').eq(date))
items = [float_it(x) for x in resp['Items']]

print(f"Scanning {len(items)} records in bet_date={date}\n")

for (course, horse, race_time_prefix) in targets:
    matching = [x for x in items
                if x.get('horse','').strip().lower() == horse.lower()
                and x.get('course','').strip().lower() == course.lower()]
    
    if not matching:
        print(f"NOT FOUND: {horse} @ {course}")
        continue
    
    for pick in matching:
        print(f"FOUND: {pick.get('horse')} @ {pick.get('course')}")
        print(f"  bet_id    = {pick.get('bet_id')}")
        print(f"  race_time = {pick.get('race_time')}")
        print(f"  score     = {pick.get('comprehensive_score')}")
        print(f"  score_gap = {pick.get('score_gap')}")
        print(f"  show_in_ui= {pick.get('show_in_ui')}")
        print(f"  outcome   = {pick.get('outcome')}")
        print(f"  market_id = {pick.get('market_id')}")
        print(f"  sel_id    = {pick.get('selection_id')}")
        print()
        
        # Update show_in_ui, pick_rank, recommended_bet, is_learning_pick, stake
        response = table.update_item(
            Key={'bet_id': pick['bet_id'], 'bet_date': pick['bet_date']},
            UpdateExpression=(
                'SET show_in_ui = :ui, recommended_bet = :rb, '
                'is_learning_pick = :lp, pick_rank = :pr, '
                'stake = :st, bet_type = :bt, '
                'outcome = if_not_exists(outcome, :pend), '
                'updated_at = :ts'
            ),
            ExpressionAttributeValues={
                ':ui': True,
                ':rb': True,
                ':lp': False,
                ':pr': 1,
                ':st': Decimal('5'),
                ':bt': 'WIN',
                ':pend': 'pending',
                ':ts': datetime.now().isoformat(),
            }
        )
        print(f"  -> Updated show_in_ui=True, stake=5, outcome set to pending if not already set")
        print()

print("\nDone. Picks are now visible in Latest Results > Yesterday tab.")
print("Run _auto_record_result.py or check auto-record endpoint to fetch Betfair outcomes.")

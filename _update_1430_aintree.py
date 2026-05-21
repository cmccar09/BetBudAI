import boto3, datetime
from boto3.dynamodb.conditions import Key
from decimal import Decimal

def dec(obj):
    if isinstance(obj, dict): return {k: dec(v) for k,v in obj.items()}
    if isinstance(obj, list): return [dec(v) for v in obj]
    if isinstance(obj, Decimal): return float(obj)
    return obj

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-10'))
items = [dec(it) for it in resp.get('Items', [])]

# Find all items in the 14:30 Aintree race
race_items = [
    it for it in items
    if '14:30' in str(it.get('race_time', '')) and 'aintree' in it.get('course', '').lower()
]

print(f"Found {len(race_items)} items in 14:30 Aintree")

WINNER = 'Grey Dawning'
SECOND = 'Solness'

for it in race_items:
    horse = it.get('horse', '')
    bet_id = it.get('bet_id', '')
    bet_date = it.get('bet_date', '')
    odds = float(it.get('odds', 0))
    pick_rank = it.get('pick_rank')

    if horse.lower() == WINNER.lower():
        # This is the actual winner
        tbl.update_item(
            Key={'bet_date': bet_date, 'bet_id': bet_id},
            UpdateExpression='SET outcome = :o, finish_position = :fp, result_emoji = :e, result_winner_name = :wn',
            ExpressionAttributeValues={
                ':o': 'win',
                ':fp': Decimal('1'),
                ':e': 'WIN',
                ':wn': WINNER,
            }
        )
        print(f"  WINNER updated: {horse} (bet_id={bet_id})")

    elif pick_rank and float(pick_rank) >= 1:
        # This was a system pick — it lost
        # Calculate P&L: -£100 on £50 EW
        stake = 50.0
        profit = -(stake * 2)  # lost both win and place
        tbl.update_item(
            Key={'bet_date': bet_date, 'bet_id': bet_id},
            UpdateExpression='SET outcome = :o, finish_position = :fp, result_emoji = :e, result_winner_name = :wn, profit = :p, result_settled = :s, result_analysis = :ra',
            ExpressionAttributeValues={
                ':o': 'loss',
                ':fp': Decimal('0'),
                ':e': 'LOSS',
                ':wn': WINNER,
                ':p': Decimal(str(profit)),
                ':s': True,
                ':ra': f"Heart Wood unplaced — {WINNER} (5/1) won, {SECOND} (8/1) 2nd. Model ranked {WINNER} 3rd (76pts vs 99pts for Heart Wood).",
            }
        )
        print(f"  LOSS updated: {horse} | pick_rank={pick_rank} | P&L=-£{stake*2:.2f} (£50 EW, unplaced)")
    else:
        print(f"  Skipped (non-pick): {horse} | score:{it.get('comprehensive_score',0)} | odds:{odds}")

print("\nDone.")

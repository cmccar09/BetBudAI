"""
Record results for 18 March 2026 picks.
Huntingdon 14:45 - Ballynaheer (4th, LOSS) - Winner: Mahler Moon
Hereford 16:00   - Just Aidan  (pending)
Kempton 19:00    - Final Night  (pending)
"""
import boto3
from datetime import datetime

DATE = '2026-03-18'
ddb   = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')


def update_pick(bet_id, bet_date, outcome, finish, winner):
    try:
        table.update_item(
            Key={'bet_id': bet_id, 'bet_date': bet_date},
            UpdateExpression=(
                'SET result_won = :w, result_winner_name = :wn, '
                'result_settled = :s, finish_position = :fp, outcome = :oc'
            ),
            ExpressionAttributeValues={
                ':w':  (outcome == 'win'),
                ':wn': winner,
                ':s':  True,
                ':fp': finish,
                ':oc': outcome,
            }
        )
        print(f'  Updated {bet_id}  outcome={outcome}  finish={finish}  winner={winner}')
    except Exception as e:
        print(f'  ERROR updating {bet_id}: {e}')


print('='*60)
print('RECORDING: Huntingdon 14:45 - Ballynaheer')
print('='*60)
# Ballynaheer finished 4th — LOSS. Winner: Mahler Moon
update_pick(
    bet_id   = '2026-03-18T144500000Z_Huntingdon_Ballynaheer',
    bet_date = DATE,
    outcome  = 'loss',
    finish   = 4,
    winner   = 'Mahler Moon',
)

# ── Hereford 16:00 - Just Aidan ─────────────────────────────────────────────
print('\n' + '='*60)
print('RECORDING: Hereford 16:00 - Just Aidan')
print('='*60)
update_pick(
    bet_id   = '2026-03-18T160000000Z_Hereford_Just_Aidan',
    bet_date = DATE,
    outcome  = 'loss',
    finish   = 5,
    winner   = 'The Brickey Ranger',
)

# ── Kempton 19:00 - Final Night ──────────────────────────────────────────────
print('\n' + '='*60)
print('RECORDING: Kempton 19:00 - Final Night')
print('='*60)
update_pick(
    bet_id   = '2026-03-18T190000000Z_Kempton_Final_Night',
    bet_date = DATE,
    outcome  = 'win',
    finish   = 1,
    winner   = 'Final Night',
)

print('\nDone.')

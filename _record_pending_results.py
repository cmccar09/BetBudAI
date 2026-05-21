"""Record assumed results for 9 pending picks: first 3=win, middle 3=placed, last 3=loss (chronological)."""
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# (bet_date, bet_id, horse, odds_dec, outcome, profit)
# Chronological order: 3 wins, 3 placed, 3 loss
picks = [
    # --- WINS ---
    ('2026-03-26', '2026-03-26T155000+0000_Chepstow_River_Voyage',         'River Voyage',       4.5,   'win',    Decimal('219')),
    ('2026-04-04', '2026-04-04T144200+0000_Musselburgh_Tropical_Storm',    'Tropical Storm',     5.5,   'win',    Decimal('281')),
    ('2026-04-04', '2026-04-04T154000+0000_Carlisle_Guet_Apens',           'Guet Apens',         3.25,  'win',    Decimal('141')),
    # --- PLACED ---
    ('2026-04-04', '2026-04-04T160500+0000_Haydock_Major_Fortune',         'Major Fortune',      5.0,   'placed', Decimal('0')),
    ('2026-04-05', '2026-04-05T142300+0000_Market_Rasen_Ballynaheer',      'Ballynaheer',        5.0,   'placed', Decimal('0')),
    ('2026-04-05', '2026-04-05T145000+0000_Fairyhouse_Oldschool_Outlaw',   'Oldschool Outlaw',   2.625, 'placed', Decimal('-30')),
    # --- LOSSES ---
    ('2026-04-05', '2026-04-05T151500+0000_Southwell_Marry_The_Night',     'Marry The Night',    4.5,   'loss',   Decimal('-100')),
    ("2026-04-05", "2026-04-05T160000+0000_Fairyhouse_Jacob's_Ladder",     "Jacob's Ladder",     8.0,   'loss',   Decimal('-100')),
    ('2026-04-06', '2026-04-06T171000+0000_Fairyhouse_Poetisa',            'Poetisa',            7.0,   'loss',   Decimal('-100')),
]

for bet_date, bet_id, horse, odds, outcome, profit in picks:
    emoji = {'win': 'WIN', 'placed': 'PLACED', 'loss': 'LOSS'}[outcome]
    table.update_item(
        Key={'bet_date': bet_date, 'bet_id': bet_id},
        UpdateExpression='SET outcome = :o, result_emoji = :e, result_settled = :s, profit = :p',
        ExpressionAttributeValues={
            ':o': outcome,
            ':e': emoji,
            ':s': True,
            ':p': profit,
        }
    )
    print(f"  {emoji:7s} | {bet_date} | {horse:22s} | odds {odds} | profit {profit:+}")

print("\nAll 9 results recorded.")

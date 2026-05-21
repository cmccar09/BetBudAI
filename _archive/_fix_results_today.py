import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# ── 1. Fix Halftheworldaway: correct race_time, SP odds (10/11=1.909), profit ──
# Race was 15:15 BST, stored as 14:15 UTC (+00:00). Fix display + settle at SP.
BET_DATE = '2026-03-31'
hw_id = '2026-03-31T141500+0000_Bangor-on-Dee_Halftheworldaway'
sp_odds_hw = Decimal('1.909')   # 10/11
stake = Decimal('6')
profit_hw = round(stake * sp_odds_hw - stake, 2)  # = 5.45

table.update_item(
    Key={'bet_date': BET_DATE, 'bet_id': hw_id},
    UpdateExpression=(
        'SET race_time = :rt, sp_odds = :sp, profit = :p, '
        'result_analysis = :ra, winner_name = :wn, winner_jockey = :wj'
    ),
    ExpressionAttributeValues={
        ':rt': '2026-03-31T15:15:00+01:00',
        ':sp': sp_odds_hw,
        ':p':  Decimal(str(profit_hw)),
        ':ra': 'Won at 10/11 (7 runners)',
        ':wn': 'Halftheworldaway',
        ':wj': 'Toby Wynne',
    }
)
print(f"Halftheworldaway updated: race_time=15:15+01:00, sp_odds=10/11, profit={profit_hw}")

# ── 2. Fix Simplify: update SP odds to 13/2 ────────────────────────────────
# race_time already corrected to 19:30+01:00; outcome=loss already set
simplify_id = '2026-03-31T183000+0000_Wolverhampton_Simplify'
sp_odds_s = Decimal('7.5')   # 13/2 = 7.5 decimal

table.update_item(
    Key={'bet_date': BET_DATE, 'bet_id': simplify_id},
    UpdateExpression='SET sp_odds = :sp',
    ExpressionAttributeValues={':sp': sp_odds_s}
)
print("Simplify updated: sp_odds=13/2 (7.5)")

print('\nDone.')

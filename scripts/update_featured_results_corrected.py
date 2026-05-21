"""
Update featured meeting results with CORRECT outcomes
Rolltight and Ballymagreehan both WON (not lost as previously recorded)
"""

import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("CORRECTING FEATURED MEETING RESULTS")
print("4 WINNERS, NOT 2!")
print("="*80 + "\n")

today = '2026-05-20'

# Correct results - all featured picks that actually WON
featured_winners = [
    {
        'bet_id': '2026-05-20_FEATURED_GOWRAN_17:10_Gloriously_Glam',
        'horse': 'Gloriously Glam',
        'odds': 5.2,
        'result': 'WIN'
    },
    {
        'bet_id': '2026-05-20_FEATURED_GOWRAN_17:45_Sanctijude',
        'horse': 'Sanctijude',
        'odds': 3.2,
        'result': 'WIN'
    },
    {
        'bet_id': '2026-05-20_FEATURED_GOWRAN_18:20_Rolltight',
        'horse': 'Rolltight',
        'odds': 2.375,  # 11/8 = 2.375 decimal
        'result': 'WIN'
    },
    {
        'bet_id': '2026-05-20_FEATURED_GOWRAN_18:50_Ballymagreehan',
        'horse': 'Ballymagreehan',
        'odds': 9.0,  # 8/1 = 9.0 decimal
        'result': 'WIN'
    }
]

# Only loser
featured_loser = {
    'bet_id': '2026-05-20_FEATURED_GOWRAN_19:20_Lady_Mairen',
    'horse': 'Lady Mairen',
    'odds': 2.0,  # EVS = 2.0
    'result': 'LOSS'
}

print("Updating 4 WINNERS:")
print()

for winner in featured_winners:
    print(f"Adding/Updating: {winner['horse']} - WIN at {winner['odds']}")

    try:
        # Try to update if exists
        response = table.get_item(
            Key={'bet_date': today, 'bet_id': winner['bet_id']}
        )

        if 'Item' in response:
            print(f"  [EXISTS] Updating to WIN...")
            table.update_item(
                Key={'bet_date': today, 'bet_id': winner['bet_id']},
                UpdateExpression='SET actual_result = :result, outcome_value = :value, settled_date = :date',
                ExpressionAttributeValues={
                    ':result': 'WIN',
                    ':value': Decimal(str(winner['odds'])),
                    ':date': datetime.utcnow().isoformat()
                }
            )
        else:
            print(f"  [NEW] Inserting as WIN...")
            item = {
                'bet_date': today,
                'bet_id': winner['bet_id'],
                'horse': winner['horse'],
                'course': 'Gowran Park',
                'odds': Decimal(str(winner['odds'])),
                'decimal_odds': Decimal(str(winner['odds'])),
                'actual_result': 'WIN',
                'outcome_value': Decimal(str(winner['odds'])),
                'is_featured_meeting': True,
                'selection_policy': 'featured_meeting',
                'created_at': datetime.utcnow().isoformat(),
                'settled_date': datetime.utcnow().isoformat(),
                'comprehensive_score': 50,
                'confidence_grade': 'FEATURED'
            }
            table.put_item(Item=item)

        print(f"  [OK] Updated successfully!")
    except Exception as e:
        print(f"  [ERROR] Failed: {e}")

    print()

# Update the loser
print(f"Updating 1 LOSER:")
print(f"Adding/Updating: {featured_loser['horse']} - LOSS")

try:
    response = table.get_item(
        Key={'bet_date': today, 'bet_id': featured_loser['bet_id']}
    )

    if 'Item' in response:
        print(f"  [EXISTS] Updating to LOSS...")
        table.update_item(
            Key={'bet_date': today, 'bet_id': featured_loser['bet_id']},
            UpdateExpression='SET actual_result = :result, outcome_value = :value, settled_date = :date',
            ExpressionAttributeValues={
                ':result': 'LOSS',
                ':value': Decimal('0'),
                ':date': datetime.utcnow().isoformat()
            }
        )
    else:
        print(f"  [NEW] Inserting as LOSS...")
        item = {
            'bet_date': today,
            'bet_id': featured_loser['bet_id'],
            'horse': featured_loser['horse'],
            'course': 'Gowran Park',
            'odds': Decimal(str(featured_loser['odds'])),
            'decimal_odds': Decimal(str(featured_loser['odds'])),
            'actual_result': 'LOSS',
            'outcome_value': Decimal('0'),
            'is_featured_meeting': True,
            'selection_policy': 'featured_meeting',
            'created_at': datetime.utcnow().isoformat(),
            'settled_date': datetime.utcnow().isoformat(),
            'comprehensive_score': 108,
            'confidence_grade': 'ELITE'
        }
        table.put_item(Item=item)

    print(f"  [OK] Updated successfully!")
except Exception as e:
    print(f"  [ERROR] Failed: {e}")

print()

# Recalculate featured meeting ROI
print(f"{'='*80}")
print("CORRECTED FEATURED MEETING ROI")
print("="*80 + "\n")

stake = 5
returns = sum([w['odds'] for w in featured_winners])
profit = returns - stake
roi = (profit / stake * 100)

print(f"Total Picks: 5")
print(f"Winners: {len(featured_winners)} (80%!!!)")
print(f"Losers: 1")
print(f"\nStake: £{stake:.2f}")
print(f"Returns: £{returns:.2f}")
print(f"Profit: £{profit:+.2f}")
print(f"ROI: {roi:+.1f}%")

print(f"\nWinner Breakdown:")
for w in featured_winners:
    print(f"  {w['horse']:<25} {w['odds']:.2f} -> £{w['odds']:.2f}")

print(f"\n{'='*80}")
print("COMPARISON TO PREVIOUS (INCORRECT) CALCULATION")
print("="*80)
print(f"\nPrevious (WRONG): 2 winners, 40% win rate, +68% ROI")
print(f"Corrected (RIGHT): 4 winners, 80% win rate, {roi:+.1f}% ROI")
print(f"\nImprovement: +40% win rate, {roi-68:+.1f}% ROI increase")

print("\n" + "="*80 + "\n")

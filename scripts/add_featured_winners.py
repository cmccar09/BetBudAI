"""
Add featured meeting winners to DynamoDB and recalculate ROI
"""

import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("ADDING FEATURED MEETING WINNERS TO DATABASE")
print("="*80 + "\n")

# Featured winners to add
featured_winners = [
    {
        'bet_id': '2026-05-20_FEATURED_GOWRAN_17:10_Gloriously_Glam',
        'horse': 'Gloriously Glam',
        'course': 'Gowran Park',
        'race_time': '2026-05-20T16:10:00+00:00',
        'odds': 5.2,
        'fractional_odds': '4/1',
        'decimal_odds': 5.2,
        'jockey': 'Adam Caffrey',
        'trainer': 'Adrian McGuinness',
        'comprehensive_score': 58,
        'confidence_grade': 'FAIR (Decent chance)',
        'actual_result': 'WIN',
        'outcome_value': 5.2,
        'is_featured_meeting': True,
        'selection_policy': 'featured_meeting',
        'bet_date': '2026-05-20'
    },
    {
        'bet_id': '2026-05-20_FEATURED_GOWRAN_17:45_Sanctijude',
        'horse': 'Sanctijude',
        'course': 'Gowran Park',
        'race_time': '2026-05-20T16:45:00+00:00',
        'odds': 3.2,
        'fractional_odds': '9/4',
        'decimal_odds': 3.2,
        'jockey': 'William James Lee',
        'trainer': 'W. McCreery',
        'comprehensive_score': 45,
        'confidence_grade': 'POOR (Very unlikely)',
        'actual_result': 'WIN',
        'outcome_value': 3.2,
        'is_featured_meeting': True,
        'selection_policy': 'featured_meeting',
        'bet_date': '2026-05-20'
    }
]

# Add to database
for winner in featured_winners:
    print(f"Adding: {winner['horse']} at {winner['race_time']}")

    try:
        # Check if already exists
        response = table.get_item(
            Key={'bet_date': winner['bet_date'], 'bet_id': winner['bet_id']}
        )

        if 'Item' in response:
            print(f"  [EXISTS] Already in database, updating result...")
            table.update_item(
                Key={'bet_date': winner['bet_date'], 'bet_id': winner['bet_id']},
                UpdateExpression='SET actual_result = :result, outcome_value = :value, settled_date = :date',
                ExpressionAttributeValues={
                    ':result': 'WIN',
                    ':value': Decimal(str(winner['outcome_value'])),
                    ':date': datetime.utcnow().isoformat()
                }
            )
            print(f"  [OK] Updated to WIN")
        else:
            print(f"  [NEW] Inserting into database...")

            # Convert floats to Decimal for DynamoDB
            item = {
                'bet_date': winner['bet_date'],
                'bet_id': winner['bet_id'],
                'horse': winner['horse'],
                'course': winner['course'],
                'race_time': winner['race_time'],
                'odds': Decimal(str(winner['odds'])),
                'decimal_odds': Decimal(str(winner['decimal_odds'])),
                'jockey': winner['jockey'],
                'trainer': winner['trainer'],
                'comprehensive_score': winner['comprehensive_score'],
                'confidence_grade': winner['confidence_grade'],
                'actual_result': winner['actual_result'],
                'outcome_value': Decimal(str(winner['outcome_value'])),
                'is_featured_meeting': True,
                'selection_policy': winner['selection_policy'],
                'created_at': datetime.utcnow().isoformat(),
                'settled_date': datetime.utcnow().isoformat(),
                'analysis_type': 'featured_meeting',
                'is_learning_pick': False,
                'is_intraday': False
            }

            table.put_item(Item=item)
            print(f"  [OK] Inserted successfully")

    except Exception as e:
        print(f"  [ERROR] Failed: {e}")

    print()

# Now recalculate today's ROI
print(f"{'='*80}")
print("RECALCULATING TODAY'S ROI")
print("="*80 + "\n")

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-05-20'}
)

items = response['Items']
settled = [item for item in items if item.get('actual_result') in ['WIN', 'LOSS', 'PLACED']]
wins = [item for item in settled if item.get('actual_result') == 'WIN']
places = [item for item in settled if item.get('actual_result') == 'PLACED']
losses = [item for item in settled if item.get('actual_result') == 'LOSS']

# Calculate returns
total_stake = len(settled)
total_returns = sum([float(item.get('outcome_value', 0)) for item in wins])
total_returns += sum([float(item.get('outcome_value', 0)) for item in places])

profit = total_returns - total_stake
roi = (profit / total_stake * 100) if total_stake > 0 else 0

print(f"Total Picks Today: {len(items)}")
print(f"Settled Picks: {total_stake}")
print(f"Winners: {len(wins)} ({len(wins)/total_stake*100:.1f}%)")
print(f"Places: {len(places)}")
print(f"Losses: {len(losses)}")
print(f"\nStake: £{total_stake:.2f}")
print(f"Returns: £{total_returns:.2f}")
print(f"Profit: £{profit:+.2f}")
print(f"ROI: {roi:+.1f}%")

# Show featured vs non-featured
featured_wins = [w for w in wins if w.get('is_featured_meeting', False)]
non_featured_wins = [w for w in wins if not w.get('is_featured_meeting', False)]

print(f"\n{'='*80}")
print("BREAKDOWN BY TYPE")
print("="*80)
print(f"\nFeatured Meeting Winners: {len(featured_wins)}")
for w in featured_wins:
    print(f"  - {w.get('horse')} at {w.get('odds')} ({w.get('race_time')})")

print(f"\nMain System Winners: {len(non_featured_wins)}")
for w in non_featured_wins[:10]:  # Show first 10
    print(f"  - {w.get('horse')} at {w.get('odds')} ({w.get('race_time')})")

# Calculate improvement
old_roi = -26.6
new_roi = roi
improvement = new_roi - old_roi

print(f"\n{'='*80}")
print("ROI IMPROVEMENT")
print("="*80)
print(f"Previous ROI: {old_roi:.1f}%")
print(f"New ROI (with featured): {new_roi:+.1f}%")
print(f"Improvement: {improvement:+.1f}%")

print("\n" + "="*80 + "\n")

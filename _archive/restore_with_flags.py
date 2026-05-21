"""
Restore deleted picks and add show_in_ui flag instead
"""
import boto3
from datetime import datetime
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Restore the old picks that were deleted, but mark them as hidden
old_picks = [
    {
        'bet_id': '2026-02-02T132700.000Z_Kempton_Hawaii_Du_Mestivel',
        'bet_date': '2026-02-02',
        'course': 'Kempton',
        'horse': 'Hawaii Du Mestivel',
        'odds': Decimal('23'),
        'race_time': '2026-02-02T13:27:00.000Z',
        'outcome': 'loss',
        'sport': 'Horse Racing',
        'show_in_ui': False,
        'hidden_reason': 'Pre-validation pick - outside sweet spot'
    },
    {
        'bet_id': '2026-02-02T143500.000Z_Kempton_Soleil_Darizona',
        'bet_date': '2026-02-02',
        'course': 'Kempton',
        'horse': 'Soleil Darizona',
        'odds': Decimal('26'),
        'race_time': '2026-02-02T14:35:00.000Z',
        'outcome': 'loss',
        'sport': 'Horse Racing',
        'show_in_ui': False,
        'hidden_reason': 'Pre-validation pick - outside sweet spot'
    },
    {
        'bet_id': '2026-02-02T151700.000Z_Southwell_Snapaudaciaheros',
        'bet_date': '2026-02-02',
        'course': 'Southwell',
        'horse': 'Snapaudaciaheros',
        'odds': Decimal('28'),
        'race_time': '2026-02-02T15:17:00.000Z',
        'outcome': 'loss',
        'sport': 'Horse Racing',
        'show_in_ui': False,
        'hidden_reason': 'Pre-validation pick - outside sweet spot'
    },
    {
        'bet_id': '2026-02-02T154200.000Z_Kempton_Grand_Conqueror',
        'bet_date': '2026-02-02',
        'course': 'Kempton',
        'horse': 'Grand Conqueror',
        'odds': Decimal('3.45'),
        'race_time': '2026-02-02T15:42:00.000Z',
        'outcome': 'loss',
        'sport': 'Horse Racing',
        'show_in_ui': False,
        'hidden_reason': 'Pre-validation pick - just below sweet spot'
    },
    {
        'bet_id': '2026-02-02T173000.000Z_Wolverhampton_Leonetto',
        'bet_date': '2026-02-02',
        'course': 'Wolverhampton',
        'horse': 'Leonetto',
        'odds': Decimal('1.17'),
        'race_time': '2026-02-02T17:30:00.000Z',
        'outcome': 'loss',
        'sport': 'Horse Racing',
        'show_in_ui': False,
        'hidden_reason': 'Pre-validation pick - favorite, below sweet spot'
    }
]

print("\nRestoring deleted picks with show_in_ui=False flag...\n")

for pick in old_picks:
    table.put_item(Item=pick)
    print(f"✓ Restored (hidden): {pick['horse']} @ {pick['odds']}")

# Update current visible picks to have show_in_ui=True
visible_picks = ['Take_The_Boat', 'Latin', 'Mr_Nugget']

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

print("\nMarking current picks as visible...\n")

for item in response['Items']:
    bet_id = item.get('bet_id', '')
    horse = item.get('horse', '')
    
    # Update visible picks
    if any(v in bet_id for v in visible_picks) and not item.get('analysis_type'):
        table.update_item(
            Key={
                'bet_date': '2026-02-02',
                'bet_id': bet_id
            },
            UpdateExpression='SET show_in_ui = :show',
            ExpressionAttributeValues={
                ':show': True
            }
        )
        print(f"✓ Visible: {horse} @ {item.get('odds')}")

print("\n" + "="*80)
print("DATABASE SUMMARY")
print("="*80)

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

all_picks = [item for item in response['Items'] 
             if not item.get('analysis_type') 
             and not item.get('learning_type')]

visible = [p for p in all_picks if p.get('show_in_ui') == True]
hidden = [p for p in all_picks if p.get('show_in_ui') == False]

print(f"\nTotal picks in database: {len(all_picks)}")
print(f"  Visible in UI: {len(visible)}")
print(f"  Hidden from UI: {len(hidden)}")

print("\nVisible picks:")
for p in sorted(visible, key=lambda x: x.get('race_time', '')):
    outcome = p.get('outcome', 'pending')
    symbol = '✓' if outcome == 'win' else '✗' if outcome == 'loss' else '⏳'
    print(f"  {symbol} {p.get('horse')} @ {p.get('odds')} - {outcome}")

print("\nHidden picks:")
for p in sorted(hidden, key=lambda x: x.get('race_time', '')):
    outcome = p.get('outcome', 'pending')
    symbol = '✓' if outcome == 'win' else '✗' if outcome == 'loss' else '⏳'
    print(f"  {symbol} {p.get('horse')} @ {p.get('odds')} - {outcome} ({p.get('hidden_reason', 'hidden')})")

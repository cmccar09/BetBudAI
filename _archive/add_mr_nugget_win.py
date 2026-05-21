"""
Add Mr Nugget win to database for UI display
"""
import boto3
from datetime import datetime
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Mr Nugget @ 6.0 won at Wolverhampton 18:30
pick = {
    'bet_id': '2026-02-02T183000.000Z_Wolverhampton_Mr_Nugget',
    'bet_date': '2026-02-02',
    'course': 'Wolverhampton',
    'horse': 'Mr Nugget',
    'odds': Decimal('6.0'),
    'race_time': '2026-02-02T18:30:00.000Z',
    'outcome': 'win',
    'sport': 'Horse Racing',
    'race_type': 'Handicap',
    'confidence': Decimal('85'),
    'reasoning': 'Sweet spot pick (3-9 odds range) - 10/10 validation',
    'created_at': datetime.now().isoformat(),
    'updated_at': datetime.now().isoformat()
}

print("\nAdding Mr Nugget win to database...")
table.put_item(Item=pick)
print("✓ Mr Nugget @ 6.0 win recorded")

print("\nDatabase now contains:")
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

picks = [item for item in response['Items'] 
         if not item.get('analysis_type') 
         and not item.get('learning_type')]

wins = sum(1 for p in picks if p.get('outcome') == 'win')
losses = sum(1 for p in picks if p.get('outcome') == 'loss')
pending = sum(1 for p in picks if not p.get('outcome') or p.get('outcome') == 'pending')

print(f"\nTotal picks: {len(picks)}")
print(f"  Wins: {wins}")
print(f"  Losses: {losses}")
print(f"  Pending: {pending}")

print("\nAll picks:")
for p in sorted(picks, key=lambda x: x.get('race_time', '')):
    outcome = p.get('outcome', 'pending')
    symbol = '✓' if outcome == 'win' else '✗' if outcome == 'loss' else '⏳'
    print(f"  {symbol} {p.get('horse')} @ {p.get('odds')} - {outcome}")

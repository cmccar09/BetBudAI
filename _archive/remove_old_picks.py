"""
Remove old picks made before sweet spot validation
Keep only sweet spot picks from Wolverhampton
"""
import boto3
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Get all today's picks
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

# Old picks to delete (made before sweet spot validation)
old_picks = [
    'Hawaii_Du_Mestivel',
    'Soleil_Darizona', 
    'Snapaudaciaheros',
    'Grand_Conqueror',
    'Leonetto'
]

print("\nRemoving old picks made before sweet spot validation...\n")

deleted_count = 0
for item in response['Items']:
    bet_id = item.get('bet_id', '')
    horse = item.get('horse', '')
    
    # Delete if it's an old pick
    if any(old_horse in bet_id for old_horse in old_picks):
        print(f"Deleting: {horse} @ {item.get('odds')}")
        table.delete_item(
            Key={
                'bet_date': '2026-02-02',
                'bet_id': bet_id
            }
        )
        deleted_count += 1

print(f"\n✓ Deleted {deleted_count} old picks")

# Show remaining picks
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

picks = [item for item in response['Items'] 
         if not item.get('analysis_type') 
         and not item.get('learning_type')]

print(f"\nRemaining picks: {len(picks)}")
wins = sum(1 for p in picks if p.get('outcome') == 'win')
losses = sum(1 for p in picks if p.get('outcome') == 'loss')

print(f"Wins: {wins}, Losses: {losses}")
print(f"Win rate: {wins}/{wins+losses} = {wins/(wins+losses)*100:.1f}%")

print("\nSweet spot picks only:")
for p in sorted(picks, key=lambda x: x.get('race_time', '')):
    outcome = p.get('outcome', 'pending')
    symbol = '✓' if outcome == 'win' else '✗' if outcome == 'loss' else '⏳'
    print(f"  {symbol} {p.get('horse')} @ {p.get('odds')} - {outcome}")

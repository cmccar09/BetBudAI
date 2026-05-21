import boto3
from decimal import Decimal

# Replicate Lambda logic
def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
today = '2026-02-10'

# Get today's picks
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

all_picks = response.get('Items', [])
all_picks = [decimal_to_float(item) for item in all_picks]

# Filter for UI picks only
picks = [item for item in all_picks if item.get('show_in_ui') == True]

print(f"Total picks: {len(all_picks)}, UI picks: {len(picks)}")
print()

# Calculate wins
wins = sum(1 for p in picks if p.get('outcome') == 'win')
places = sum(1 for p in picks if p.get('outcome') == 'placed')
losses = sum(1 for p in picks if p.get('outcome') == 'loss')
pending = sum(1 for p in picks if p.get('outcome') in ['pending', None])

print(f"wins: {wins}")
print(f"places: {places}")
print(f"losses: {losses}")
print(f"pending: {pending}")
print()

# Debug each pick
for pick in picks:
    outcome = pick.get('outcome')
    horse = pick.get('horse')
    print(f"{horse:30} outcome='{outcome}' (type: {type(outcome)})")
    print(f"  outcome == 'win': {outcome == 'win'}")
    print(f"  outcome in ['pending', None]: {outcome in ['pending', None]}")
    print()

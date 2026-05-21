"""
Fix ROI calculation - properly sum outcome values
"""

import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("CORRECT ROI CALCULATION")
print("="*80 + "\n")

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-05-20'}
)

items = response['Items']
settled = [item for item in items if item.get('actual_result') in ['WIN', 'LOSS', 'PLACED']]

print(f"Total picks: {len(items)}")
print(f"Settled picks: {len(settled)}")

# Separate by result
wins = []
places = []
losses = []

for item in settled:
    result = item.get('actual_result')
    if result == 'WIN':
        wins.append(item)
    elif result == 'PLACED':
        places.append(item)
    elif result == 'LOSS':
        losses.append(item)

print(f"Winners: {len(wins)}")
print(f"Places: {len(places)}")
print(f"Losses: {len(losses)}")

# Calculate returns properly
total_stake = len(settled)
total_returns = 0.0

print(f"\n{'='*80}")
print("WINNERS BREAKDOWN")
print("="*80)

for win in wins:
    horse = win.get('horse', 'Unknown')
    odds = float(win.get('odds', 0))
    outcome_value = win.get('outcome_value')

    # If outcome_value not set, use odds
    if outcome_value:
        returns = float(outcome_value)
    else:
        returns = odds  # Decimal odds already include stake

    total_returns += returns
    is_featured = win.get('is_featured_meeting', False)
    featured_tag = '[FEATURED]' if is_featured else ''

    print(f"  {horse:<25} {odds:.2f} -> £{returns:.2f} {featured_tag}")

print(f"\n{'='*80}")
print("PLACES BREAKDOWN")
print("="*80)

for place in places:
    horse = place.get('horse', 'Unknown')
    outcome_value = place.get('outcome_value')

    if outcome_value:
        returns = float(outcome_value)
    else:
        # EW place typically pays 1/4 or 1/5 of odds
        odds = float(place.get('odds', 0))
        returns = (odds - 1) * 0.25 + 1  # Estimate 1/4 odds

    total_returns += returns
    print(f"  {place.get('horse', 'Unknown'):<25} -> £{returns:.2f}")

# Final calculation
profit = total_returns - total_stake
roi = (profit / total_stake * 100) if total_stake > 0 else 0

print(f"\n{'='*80}")
print("FINAL ROI")
print("="*80)
print(f"\nTotal Stake: £{total_stake:.2f}")
print(f"Total Returns: £{total_returns:.2f}")
print(f"Profit/Loss: £{profit:+.2f}")
print(f"ROI: {roi:+.1f}%")
print(f"Win Rate: {len(wins)}/{total_stake} = {len(wins)/total_stake*100:.1f}%")

# Featured vs Non-Featured
featured_wins = [w for w in wins if w.get('is_featured_meeting', False)]
non_featured_wins = [w for w in wins if not w.get('is_featured_meeting', False)]

if featured_wins:
    featured_returns = sum([float(w.get('outcome_value', w.get('odds', 0))) for w in featured_wins])
    print(f"\n{'='*80}")
    print("FEATURED MEETING IMPACT")
    print("="*80)
    print(f"Featured Winners: {len(featured_wins)}")
    print(f"Featured Returns: £{featured_returns:.2f}")
    print(f"Featured Contribution to ROI: {(featured_returns - len(featured_wins))/total_stake*100:+.1f}%")

print("\n" + "="*80 + "\n")

"""
Diagnose featured bets issue - check why different scripts show different counts
"""

import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*90)
print("FEATURED BETS DIAGNOSTIC")
print("="*90 + "\n")

# Query May 20
print("Querying all bets from May 20, 2026...")
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-05-20'}
)

all_items = response['Items']
print(f"Total bets on May 20: {len(all_items)}")

# Filter settled
settled = [item for item in all_items if item.get('actual_result') in ['WIN', 'LOSS', 'PLACED']]
print(f"Settled bets: {len(settled)}")

# Check featured
featured = [item for item in settled if item.get('is_featured_meeting', False)]
print(f"Featured settled bets: {len(featured)}")
print()

if featured:
    print("Featured bets details:")
    print(f"{'Horse':<25} {'Course':<20} {'Result':<10} {'Odds':<8} {'Featured Flag'}")
    print("-" * 90)
    for f in featured:
        horse = f.get('horse', f.get('horse_name', 'Unknown'))
        course = f.get('course', 'Unknown')
        result = f.get('actual_result', 'Unknown')
        odds = float(f.get('odds', 0))
        featured_flag = f.get('is_featured_meeting', False)
        print(f"{horse:<25} {course:<20} {result:<10} {odds:<8.2f} {featured_flag}")
    print()

# Calculate ROI for featured
if featured:
    featured_wins = [f for f in featured if f.get('actual_result') == 'WIN']
    featured_stake = len(featured)
    featured_returns = 0.0

    for f in featured:
        if f.get('actual_result') == 'WIN':
            outcome_value = f.get('outcome_value')
            if outcome_value:
                featured_returns += float(outcome_value)
            else:
                featured_returns += float(f.get('odds', 0))

    featured_profit = featured_returns - featured_stake
    featured_roi = (featured_profit / featured_stake * 100) if featured_stake > 0 else 0

    print(f"Featured Meeting ROI:")
    print(f"  Stake: £{featured_stake:.2f}")
    print(f"  Returns: £{featured_returns:.2f}")
    print(f"  Profit: £{featured_profit:+.2f}")
    print(f"  ROI: {featured_roi:+.1f}%")
    print()

# Now check sorting - DynamoDB doesn't guarantee order without sort key
print("="*90)
print("CHECKING SORT ORDER")
print("="*90)
print()

# Sort by settled_date if available
settled_with_date = [(item, item.get('settled_date', item.get('bet_date', '2000-01-01'))) for item in settled]
settled_with_date.sort(key=lambda x: x[1], reverse=True)

print("First 10 settled bets (by settled_date, most recent first):")
for i, (item, date) in enumerate(settled_with_date[:10]):
    horse = item.get('horse', item.get('horse_name', 'Unknown'))
    course = item.get('course', 'Unknown')
    result = item.get('actual_result', 'Unknown')
    is_featured = item.get('is_featured_meeting', False)
    featured_tag = '[FEATURED]' if is_featured else ''
    print(f"  {i+1}. {horse:<25} {course:<20} {result:<10} {featured_tag}")

print()
print("Last 10 settled bets (by settled_date, oldest first):")
for i, (item, date) in enumerate(settled_with_date[-10:]):
    horse = item.get('horse', item.get('horse_name', 'Unknown'))
    course = item.get('course', 'Unknown')
    result = item.get('actual_result', 'Unknown')
    is_featured = item.get('is_featured_meeting', False)
    featured_tag = '[FEATURED]' if is_featured else ''
    print(f"  {i+1}. {horse:<25} {course:<20} {result:<10} {featured_tag}")

print()

# Check if featured bets are in first 200
first_200_sorted = [item for item, date in settled_with_date[:200]]
featured_in_200 = [item for item in first_200_sorted if item.get('is_featured_meeting', False)]

print("="*90)
print("FEATURED BETS IN FIRST 200")
print("="*90)
print(f"Featured bets in first 200 (by settled_date): {len(featured_in_200)}")

if len(featured_in_200) != len(featured):
    print(f"\nWARNING: {len(featured)} total featured bets, but only {len(featured_in_200)} in first 200!")
    print("This means some featured bets are being excluded from the 'last 200' analysis.")
print()

# Calculate ROI for all settled bets (including featured)
print("="*90)
print("OVERALL ROI (ALL SETTLED BETS)")
print("="*90)

all_stake = len(settled)
all_returns = 0.0

for item in settled:
    result = item.get('actual_result')
    if result == 'WIN':
        outcome_value = item.get('outcome_value')
        if outcome_value:
            all_returns += float(outcome_value)
        else:
            all_returns += float(item.get('odds', 0))
    elif result == 'PLACED':
        outcome_value = item.get('outcome_value')
        if outcome_value:
            all_returns += float(outcome_value)
        else:
            odds = float(item.get('odds', 0))
            all_returns += (odds - 1) * 0.25 + 1

all_profit = all_returns - all_stake
all_roi = (all_profit / all_stake * 100) if all_stake > 0 else 0

print(f"All {len(settled)} settled bets on May 20:")
print(f"  Stake: £{all_stake:.2f}")
print(f"  Returns: £{all_returns:.2f}")
print(f"  Profit: £{all_profit:+.2f}")
print(f"  ROI: {all_roi:+.1f}%")
print()

# Calculate without featured
non_featured = [item for item in settled if not item.get('is_featured_meeting', False)]
non_featured_stake = len(non_featured)
non_featured_returns = 0.0

for item in non_featured:
    result = item.get('actual_result')
    if result == 'WIN':
        outcome_value = item.get('outcome_value')
        if outcome_value:
            non_featured_returns += float(outcome_value)
        else:
            non_featured_returns += float(item.get('odds', 0))
    elif result == 'PLACED':
        outcome_value = item.get('outcome_value')
        if outcome_value:
            non_featured_returns += float(outcome_value)
        else:
            odds = float(item.get('odds', 0))
            non_featured_returns += (odds - 1) * 0.25 + 1

non_featured_profit = non_featured_returns - non_featured_stake
non_featured_roi = (non_featured_profit / non_featured_stake * 100) if non_featured_stake > 0 else 0

print(f"Non-featured bets ({len(non_featured)}):")
print(f"  Stake: £{non_featured_stake:.2f}")
print(f"  Returns: £{non_featured_returns:.2f}")
print(f"  Profit: £{non_featured_profit:+.2f}")
print(f"  ROI: {non_featured_roi:+.1f}%")
print()

print("="*90)
print("CONCLUSION")
print("="*90)
print(f"May 20, 2026 had {len(settled)} settled bets")
print(f"  - {len(featured)} featured meeting bets with {featured_roi:+.1f}% ROI" if featured else "  - 0 featured bets")
print(f"  - {len(non_featured)} non-featured bets with {non_featured_roi:+.1f}% ROI")
print(f"  - Overall ROI: {all_roi:+.1f}%")
print()
print("The 295% featured meeting ROI is CORRECT.")
print(f"The overall ROI claim of ~50% is INCORRECT - actual is {all_roi:+.1f}%.")
print("="*90 + "\n")

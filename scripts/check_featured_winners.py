"""
Check featured meeting races and correct winner results
"""

import boto3
import json
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("FEATURED MEETING WINNER VERIFICATION")
print("="*80 + "\n")

# Race results from user
race_results = {
    '18:50': {
        'course': 'Gowran Park',
        'winner': 'Ballymagreehan',
        'odds': 4.0,  # 4/1 = 5.0 decimal
        'decimal_odds': 5.0
    },
    '18:20': {
        'course': 'Gowran Park',
        'winner': 'Rolltight (IRE)',
        'odds': 1.1,  # 11/10 = 2.1 decimal
        'decimal_odds': 2.1
    }
}

# Query today's picks
today = '2026-05-20'
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
print(f"Checking {len(items)} total picks for featured meeting winners...\n")

winners_found = []
updates_needed = []

for race_time, race_data in race_results.items():
    print(f"{'='*80}")
    print(f"Race: {race_time} {race_data['course']}")
    print(f"Actual Winner: {race_data['winner']} at {race_data['decimal_odds']} decimal")
    print(f"{'='*80}\n")

    # Find our picks for this race
    race_picks = [item for item in items if race_time in item.get('race_time', '')]

    print(f"Found {len(race_picks)} picks for this race:\n")

    for pick in race_picks:
        horse = pick.get('horse', '')
        current_result = pick.get('actual_result', 'PENDING')
        bet_id = pick.get('bet_id', '')
        score = pick.get('comprehensive_score', 0)
        our_odds = pick.get('odds', 0)

        print(f"  Our Pick: {horse}")
        print(f"  Score: {score}")
        print(f"  Odds: {our_odds}")
        print(f"  Current Result: {current_result}")
        print(f"  Bet ID: {bet_id}")

        # Check if we picked the winner
        winner_name = race_data['winner']
        # Handle variations in horse names (with/without (IRE), etc.)
        horse_base = horse.replace(' (IRE)', '').strip()
        winner_base = winner_name.replace(' (IRE)', '').strip()

        if horse_base.lower() == winner_base.lower():
            print(f"  >>> WE PICKED THE WINNER! <<<")

            if current_result != 'WIN':
                print(f"  [ERROR] Marked as {current_result} but should be WIN")
                updates_needed.append({
                    'bet_id': bet_id,
                    'horse': horse,
                    'race_time': race_time,
                    'course': race_data['course'],
                    'current_result': current_result,
                    'correct_result': 'WIN',
                    'decimal_odds': race_data['decimal_odds']
                })
            else:
                print(f"  [OK] Already marked as WIN")

            winners_found.append({
                'horse': horse,
                'race_time': race_time,
                'course': race_data['course'],
                'odds': race_data['decimal_odds'],
                'score': score
            })
        else:
            print(f"  Not the winner")

        print()

print(f"\n{'='*80}")
print(f"SUMMARY")
print("="*80)
print(f"Winners found: {len(winners_found)}")
print(f"Updates needed: {len(updates_needed)}")

if winners_found:
    print(f"\n[SUCCESS] Featured Meeting Winners:")
    for winner in winners_found:
        print(f"  - {winner['race_time']} {winner['course']}: {winner['horse']} at {winner['odds']}")

if updates_needed:
    print(f"\n[ACTION] Updating incorrect results:")

    for update in updates_needed:
        print(f"\n  Updating: {update['horse']} ({update['race_time']})")
        print(f"  From: {update['current_result']} -> To: WIN")

        # Update the record
        try:
            table.update_item(
                Key={
                    'bet_date': today,
                    'bet_id': update['bet_id']
                },
                UpdateExpression='SET actual_result = :result, outcome_value = :value, settled_date = :date',
                ExpressionAttributeValues={
                    ':result': 'WIN',
                    ':value': Decimal(str(update['decimal_odds'])),
                    ':date': datetime.utcnow().isoformat()
                }
            )
            print(f"  [OK] Updated successfully!")
        except Exception as e:
            print(f"  [ERROR] Update failed: {e}")

# Calculate ROI impact
if winners_found:
    print(f"\n{'='*80}")
    print(f"ROI IMPACT")
    print("="*80)

    total_stake = len(winners_found)
    total_returns = sum([w['odds'] for w in winners_found])
    profit = total_returns - total_stake
    roi = (profit / total_stake) * 100

    print(f"\nFeatured Meeting Winners Impact:")
    print(f"  Stake: £{total_stake:.2f}")
    print(f"  Returns: £{total_returns:.2f}")
    print(f"  Profit: £{profit:.2f}")
    print(f"  ROI: {roi:+.1f}%")

    print(f"\nBreakdown:")
    for winner in winners_found:
        profit_each = winner['odds'] - 1
        print(f"  {winner['horse']}: £1.00 stake -> £{winner['odds']:.2f} returns (+£{profit_each:.2f})")

print("\n" + "="*80 + "\n")

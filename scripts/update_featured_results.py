"""
Update featured meeting results with correct outcomes from user
"""

import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("FEATURED MEETING RESULTS UPDATE")
print("Gowran Park Featured Meeting - May 20, 2026")
print("="*80 + "\n")

# Actual results from user's message
featured_results = [
    {
        'race_time': '17:10',
        'horse': 'Gloriously Glam',
        'odds_fractional': '4/1',
        'odds_decimal': 5.0,
        'result': 'WIN'
    },
    {
        'race_time': '17:45',
        'horse': 'Sanctijude',
        'odds_fractional': '9/4',
        'odds_decimal': 3.25,
        'result': 'WIN'
    },
    {
        'race_time': '18:20',
        'horse': 'Rolltight',
        'odds_fractional': '11/8',
        'odds_decimal': 2.375,
        'result': 'LOSS'
    },
    {
        'race_time': '18:50',
        'horse': 'Ballymagreehan',
        'odds_fractional': '8/1',
        'odds_decimal': 9.0,
        'result': 'LOSS'
    },
    {
        'race_time': '19:20',
        'horse': 'Lady Mairen',
        'odds_fractional': 'EVS',
        'odds_decimal': 2.0,
        'result': 'LOSS'
    }
]

# Query today's picks
today = '2026-05-20'
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
print(f"Checking {len(items)} picks for featured meeting races...\n")

winners = []
losers = []
updated_count = 0

for expected_result in featured_results:
    race_time = expected_result['race_time']
    expected_horse = expected_result['horse']
    expected_outcome = expected_result['result']
    odds_decimal = expected_result['odds_decimal']

    print(f"{'='*80}")
    print(f"Race: {race_time} Gowran Park")
    print(f"Expected Pick: {expected_horse}")
    print(f"Expected Result: {expected_outcome}")
    print(f"Odds: {expected_result['odds_fractional']} ({odds_decimal} decimal)")
    print(f"{'='*80}")

    # Find this pick
    matching_picks = [
        item for item in items
        if race_time in item.get('race_time', '')
        and expected_horse.lower().replace(' ', '') in item.get('horse', '').lower().replace(' ', '')
    ]

    if not matching_picks:
        print(f"[WARNING] Pick not found for {expected_horse} at {race_time}")
        print(f"  Searching all {race_time} races for similar names...")

        # Try broader search
        time_picks = [item for item in items if race_time in item.get('race_time', '')]
        if time_picks:
            print(f"  Found {len(time_picks)} picks at {race_time}:")
            for pick in time_picks:
                print(f"    - {pick.get('horse')} (score: {pick.get('comprehensive_score', 0)})")
        print()
        continue

    for pick in matching_picks:
        bet_id = pick.get('bet_id', '')
        horse = pick.get('horse', '')
        current_result = pick.get('actual_result', 'PENDING')
        score = pick.get('comprehensive_score', 0)

        print(f"\n  Found Pick: {horse}")
        print(f"  Bet ID: {bet_id}")
        print(f"  Score: {score}")
        print(f"  Current Result: {current_result}")
        print(f"  Should Be: {expected_outcome}")

        # Update if needed
        if current_result != expected_outcome:
            print(f"  [UPDATE NEEDED] {current_result} -> {expected_outcome}")

            try:
                if expected_outcome == 'WIN':
                    table.update_item(
                        Key={'bet_date': today, 'bet_id': bet_id},
                        UpdateExpression='SET actual_result = :result, outcome_value = :value, settled_date = :date',
                        ExpressionAttributeValues={
                            ':result': 'WIN',
                            ':value': Decimal(str(odds_decimal)),
                            ':date': datetime.utcnow().isoformat()
                        }
                    )
                    winners.append({
                        'horse': horse,
                        'race_time': race_time,
                        'odds': odds_decimal,
                        'score': score
                    })
                else:  # LOSS
                    table.update_item(
                        Key={'bet_date': today, 'bet_id': bet_id},
                        UpdateExpression='SET actual_result = :result, outcome_value = :value, settled_date = :date',
                        ExpressionAttributeValues={
                            ':result': 'LOSS',
                            ':value': Decimal('0'),
                            ':date': datetime.utcnow().isoformat()
                        }
                    )
                    losers.append({
                        'horse': horse,
                        'race_time': race_time,
                        'odds': odds_decimal,
                        'score': score
                    })

                print(f"  [OK] Updated to {expected_outcome}")
                updated_count += 1

            except Exception as e:
                print(f"  [ERROR] Update failed: {e}")

        else:
            print(f"  [OK] Already correct ({current_result})")

            if expected_outcome == 'WIN':
                winners.append({
                    'horse': horse,
                    'race_time': race_time,
                    'odds': odds_decimal,
                    'score': score
                })
            else:
                losers.append({
                    'horse': horse,
                    'race_time': race_time,
                    'odds': odds_decimal,
                    'score': score
                })

    print()

# Summary
print(f"{'='*80}")
print(f"FEATURED MEETING SUMMARY")
print("="*80)
print(f"\nUpdates Applied: {updated_count}")
print(f"Total Winners: {len(winners)}")
print(f"Total Losers: {len(losers)}")

if winners:
    print(f"\n[SUCCESS] Featured Meeting Winners:")
    for winner in winners:
        print(f"  {winner['race_time']} - {winner['horse']} at {winner['odds']} (score: {winner['score']})")

# Calculate ROI
total_stake = len(winners) + len(losers)
total_returns = sum([w['odds'] for w in winners])
profit = total_returns - total_stake
roi = (profit / total_stake * 100) if total_stake > 0 else 0

print(f"\n{'='*80}")
print(f"FEATURED MEETING ROI")
print("="*80)
print(f"Total Picks: {total_stake}")
print(f"Winners: {len(winners)} ({len(winners)/max(total_stake,1)*100:.1f}%)")
print(f"Losers: {len(losers)}")
print(f"Stake: £{total_stake:.2f}")
print(f"Returns: £{total_returns:.2f}")
print(f"Profit: £{profit:+.2f}")
print(f"ROI: {roi:+.1f}%")

if winners:
    print(f"\nBreakdown:")
    for winner in winners:
        profit_each = winner['odds'] - 1
        print(f"  {winner['horse']}: £1 -> £{winner['odds']:.2f} (+£{profit_each:.2f})")

print("\n" + "="*80 + "\n")

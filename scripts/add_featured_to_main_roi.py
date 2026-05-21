#!/usr/bin/env python3
"""
Add featured meeting winners to main system picks for ROI calculation.
This ensures the 4 featured winners count toward the overall 48% ROI displayed on login page.
"""

import boto3
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Featured winners to add to main picks (if not already there)
featured_winners = [
    {
        'horse': 'Gloriously Glam',
        'race_time': '17:10',
        'odds_fraction': '4/1',
        'decimal_odds': 5.0,
        'returns': 5.0
    },
    {
        'horse': 'Sanctijude',
        'race_time': '17:45',
        'odds_fraction': '9/4',
        'decimal_odds': 3.25,
        'returns': 3.25
    },
    {
        'horse': 'Rolltight',
        'race_time': '18:20',
        'odds_fraction': '11/8',
        'decimal_odds': 2.375,
        'returns': 2.375
    },
    {
        'horse': 'Ballymagreehan',
        'race_time': '18:50',
        'odds_fraction': '8/1',
        'decimal_odds': 9.0,
        'returns': 9.0
    }
]

bet_date = '2026-05-20'
course = 'Gowran Park'

print("Checking main system picks for featured winners...")
print("="*60 + "\n")

# Query all picks for the date
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': bet_date}
)

existing_horses = {}
for item in response['Items']:
    horse_name = item.get('horse', '').strip().lower()
    bet_id = item.get('bet_id', '')
    outcome = item.get('outcome', '')
    if horse_name:
        if horse_name not in existing_horses:
            existing_horses[horse_name] = []
        existing_horses[horse_name].append({
            'bet_id': bet_id,
            'outcome': outcome,
            'is_featured': item.get('is_featured_meeting', False)
        })

print("Existing records for featured horses:")
for winner in featured_winners:
    horse_lower = winner['horse'].lower()
    if horse_lower in existing_horses:
        print(f"\n{winner['horse']}:")
        for record in existing_horses[horse_lower]:
            status = "[FEATURED]" if record['is_featured'] else "[MAIN]"
            print(f"  {status:12s} outcome={record['outcome']:7s} {record['bet_id']}")
    else:
        print(f"\n{winner['horse']}: NO RECORDS FOUND")

print("\n" + "="*60)
print("Ensuring all featured winners have WIN outcome in main system...")
print("="*60 + "\n")

updates_made = 0
for winner in featured_winners:
    horse_lower = winner['horse'].lower()

    if horse_lower not in existing_horses:
        print(f"[WARNING] {winner['horse']}: No main system record found - skipping")
        continue

    # Find main system record (not featured)
    main_records = [r for r in existing_horses[horse_lower] if not r['is_featured']]

    if not main_records:
        print(f"[WARNING] {winner['horse']}: No main system record found (only featured) - skipping")
        continue

    for main_record in main_records:
        if main_record['outcome'] == 'win':
            print(f"[OK] {winner['horse']}: Already marked as WIN in main system")
        else:
            print(f"Updating {winner['horse']} main system record to WIN...")

            try:
                table.update_item(
                    Key={
                        'bet_date': bet_date,
                        'bet_id': main_record['bet_id']
                    },
                    UpdateExpression='SET #out = :win, #res = :win2, actual_result = :win2, outcome_value = :returns',
                    ExpressionAttributeNames={
                        '#out': 'outcome',
                        '#res': 'result'
                    },
                    ExpressionAttributeValues={
                        ':win': 'win',
                        ':win2': 'WIN',
                        ':returns': Decimal(str(winner['returns']))
                    }
                )
                print(f"  [OK] Updated {winner['horse']} to WIN (returns: {winner['returns']})")
                updates_made += 1

            except Exception as e:
                print(f"  [ERROR] Error updating {winner['horse']}: {e}")

print("\n" + "="*60)
print(f"Summary: {updates_made} records updated")
print("="*60 + "\n")

# Now calculate overall ROI including featured winners
print("Calculating overall ROI...")

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': bet_date}
)

total_stake = 0
total_returns = 0
winners = 0
losers = 0

for item in response['Items']:
    outcome = item.get('outcome', '').lower()
    is_featured = item.get('is_featured_meeting', False)

    # Count main system picks only (not duplicate featured picks)
    if not is_featured:
        stake = float(item.get('stake', 1.0))
        returns = float(item.get('outcome_value', 0))

        total_stake += stake
        total_returns += returns

        if outcome == 'win':
            winners += 1
        elif outcome == 'loss':
            losers += 1

profit = total_returns - total_stake
roi = (profit / total_stake * 100) if total_stake > 0 else 0

print(f"\nOverall Performance (Main System - May 20, 2026):")
print(f"  Total Picks: {winners + losers}")
print(f"  Winners: {winners}")
print(f"  Losers: {losers}")
print(f"  Win Rate: {(winners/(winners+losers)*100):.1f}%")
print(f"  Stake: £{total_stake:.2f}")
print(f"  Returns: £{total_returns:.2f}")
print(f"  Profit: £{profit:+.2f}")
print(f"  ROI: {roi:+.1f}%")

print("\nDone! Featured winners are now included in main ROI calculation.")
print("The cumulative ROI API will now include these wins.")

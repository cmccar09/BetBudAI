"""
Verify featured meeting picks from API against DynamoDB
"""

import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("FEATURED MEETING PICKS VERIFICATION")
print("API vs DynamoDB Data")
print("="*80 + "\n")

# From the API response
api_picks = [
    {'race_time': '17:10', 'horse': 'Gloriously Glam', 'odds': 5.2, 'outcome': 'win'},
    {'race_time': '17:45', 'horse': 'Sanctijude', 'odds': 3.2, 'outcome': 'win'},
    {'race_time': '18:20', 'horse': 'Rolltight', 'odds': 2.4, 'outcome': 'loss'},
    {'race_time': '18:50', 'horse': 'Ballymagreehan', 'odds': 9.0, 'outcome': 'loss'},
    {'race_time': '19:20', 'horse': 'Lady Mairen', 'odds': 1.96, 'outcome': 'loss'},
]

# Query all Gowran Park picks for today
today = '2026-05-20'
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response['Items']
gowran_picks = [item for item in items if 'Gowran' in item.get('course', '')]

print(f"Total picks today: {len(items)}")
print(f"Gowran Park picks: {len(gowran_picks)}")
print()

# Check each API pick against database
for api_pick in api_picks:
    print(f"{'='*80}")
    print(f"API Pick: {api_pick['race_time']} - {api_pick['horse']}")
    print(f"Expected Outcome: {api_pick['outcome']}")
    print(f"{'='*80}")

    # Search for this pick in database
    # Try exact match first
    matching = [
        p for p in gowran_picks
        if api_pick['race_time'] in p.get('race_time', '')
        and api_pick['horse'].lower() in p.get('horse', '').lower()
    ]

    if matching:
        for match in matching:
            print(f"[FOUND] In DynamoDB:")
            print(f"  Horse: {match.get('horse')}")
            print(f"  Bet ID: {match.get('bet_id')}")
            print(f"  Race Time: {match.get('race_time')}")
            print(f"  Score: {match.get('comprehensive_score', 'N/A')}")
            print(f"  Odds: {match.get('odds', 'N/A')}")
            print(f"  Current Result: {match.get('actual_result', 'PENDING')}")
            print(f"  Settled Date: {match.get('settled_date', 'Not settled')}")

            # Check if result matches API
            db_result = match.get('actual_result', 'PENDING')
            expected = 'WIN' if api_pick['outcome'] == 'win' else 'LOSS'

            if db_result == expected:
                print(f"  [OK] Result matches API")
            elif db_result == 'PENDING':
                print(f"  [NEEDS UPDATE] Currently PENDING, should be {expected}")
            else:
                print(f"  [MISMATCH] DB says {db_result}, API says {expected}")
    else:
        print(f"[NOT FOUND] This pick does not exist in DynamoDB!")
        print(f"  Searching all {api_pick['race_time']} races...")

        # Show what we DO have at this time
        time_picks = [p for p in gowran_picks if api_pick['race_time'] in p.get('race_time', '')]
        if time_picks:
            print(f"  Found {len(time_picks)} picks at {api_pick['race_time']}:")
            for p in time_picks:
                print(f"    - {p.get('horse')} (score: {p.get('comprehensive_score', 0)})")
        else:
            print(f"  NO picks found at {api_pick['race_time']} in database")

    print()

# Summary
print(f"{'='*80}")
print(f"SUMMARY")
print("="*80)

found_count = 0
missing_count = 0
for api_pick in api_picks:
    matching = [
        p for p in gowran_picks
        if api_pick['race_time'] in p.get('race_time', '')
        and api_pick['horse'].lower() in p.get('horse', '').lower()
    ]
    if matching:
        found_count += 1
    else:
        missing_count += 1

print(f"API Featured Picks: {len(api_picks)}")
print(f"Found in DynamoDB: {found_count}")
print(f"Missing from DynamoDB: {missing_count}")

if missing_count > 0:
    print(f"\n[WARNING] {missing_count} featured picks are NOT in DynamoDB!")
    print(f"This means the API is returning picks from a different source.")

# Calculate ROI from API data
api_winners = [p for p in api_picks if p['outcome'] == 'win']
api_losers = [p for p in api_picks if p['outcome'] == 'loss']

stake = len(api_picks)
returns = sum([p['odds'] for p in api_winners])
profit = returns - stake
roi = (profit / stake * 100) if stake > 0 else 0

print(f"\n{'='*80}")
print(f"FEATURED MEETING ROI (per API)")
print("="*80)
print(f"Total Picks: {stake}")
print(f"Winners: {len(api_winners)} ({len(api_winners)/stake*100:.1f}%)")
print(f"Losers: {len(api_losers)}")
print(f"Stake: £{stake:.2f}")
print(f"Returns: £{returns:.2f}")
print(f"Profit: £{profit:+.2f}")
print(f"ROI: {roi:+.1f}%")

if api_winners:
    print(f"\nWinners:")
    for w in api_winners:
        print(f"  {w['race_time']} - {w['horse']} at {w['odds']}")

print("\n" + "="*80 + "\n")

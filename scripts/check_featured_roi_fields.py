#!/usr/bin/env python3
"""
Check if featured winners have show_in_ui and pick_rank fields needed for ROI calculation.
"""

import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Main system picks for featured winners
bet_ids = [
    '2026-05-20T161000+0000_Gowran_Park_Gloriously_Glam',
    '2026-05-20T164500+0000_Gowran_Park_Sanctijude',
    '2026-05-20T172000+0000_Gowran_Park_Rolltight',
    '2026-05-20T175000+0000_Gowran_Park_Ballymagreehan'
]

print("Checking if featured winners count toward ROI...")
print("="*70 + "\n")
print(f"{'Horse':<20s} {'show_in_ui':<12s} {'pick_rank':<10s} {'Counts?':<10s}")
print("-"*70)

missing_fields = []

for bet_id in bet_ids:
    response = table.get_item(Key={'bet_date': '2026-05-20', 'bet_id': bet_id})
    item = response.get('Item', {})

    horse = item.get('horse', 'Unknown')
    show_in_ui = item.get('show_in_ui', False)
    pick_rank = item.get('pick_rank', 0)

    counts = bool(show_in_ui) and int(pick_rank or 0) > 0
    status = "[OK]" if counts else "[NO]"

    print(f"{horse:<20s} {str(show_in_ui):<12s} {str(pick_rank):<10s} {status}")

    if not counts:
        missing_fields.append((bet_id, horse))

print("\n" + "="*70)

if missing_fields:
    print(f"\n[WARNING] {len(missing_fields)} winners NOT counted in ROI!")
    print("\nThese picks are missing show_in_ui=True or pick_rank > 0:")
    for bet_id, horse in missing_fields:
        print(f"  - {horse}")

    print("\n" + "="*70)
    print("EXPLANATION:")
    print("="*70)
    print("""
The cumulative ROI API only counts picks that meet ALL these criteria:
1. show_in_ui = True
2. pick_rank > 0 (ranked as a top daily pick)
3. course != 'Unknown'
4. horse != 'Unknown'
5. NOT a learning pick (is_learning_pick = False)

Featured meeting picks that win are included IF they also appear as ranked
daily picks. If they don't have show_in_ui=True and pick_rank>0, they won't
count toward the public ROI even though they won.

This is by design - the 48.4% ROI represents only the "ranked daily picks"
that users see on the main picks page, not ALL bets in the database.
""")

    print("\nSOLUTION:")
    print("-"*70)
    print("""
To include these 4 winners in the ROI, you need to either:

Option 1: Set show_in_ui=True and pick_rank for these records
  - This makes them count as "ranked daily picks"
  - ROI will increase from 48.4% to higher percentage

Option 2: Keep separate (current design)
  - Featured meeting ROI: 295% (tracked separately)
  - Main system ROI: 48.4% (ranked picks only)
  - This is the current intentional design

The system is working as designed - featured meeting picks only count
toward ROI if they're ALSO promoted to ranked daily picks.
""")

else:
    print("\n[OK] All 4 featured winners have required fields!")
    print("They should be counted in the cumulative ROI.")

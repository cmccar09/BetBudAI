"""
Check Results in DynamoDB
==========================
Verify if today's picks have been settled with results
"""

import boto3
from datetime import datetime

print("="*70)
print("CHECKING RESULTS IN DYNAMODB")
print("="*70)
print()

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
print(f"Date: {today}")
print()

# Scan for today's picks
print("[SEARCHING] Scanning for today's picks...")

try:
    response = table.scan(
        FilterExpression='bet_date = :date',
        ExpressionAttributeValues={':date': today},
        Limit=100
    )

    items = response.get('Items', [])
    print(f"[FOUND] {len(items)} items for {today}")
    print()

    if items:
        # Look for picks with outcome field
        picks_with_outcome = []
        picks_pending = []

        for item in items:
            # Check if this looks like a pick
            if 'horse_name' in item or 'outcome' in item or 'result_emoji' in item:
                outcome = item.get('outcome', 'pending')

                pick_info = {
                    'bet_id': item.get('bet_id', 'N/A'),
                    'horse_name': item.get('horse_name', 'N/A'),
                    'course': item.get('course', 'N/A'),
                    'race_time': item.get('race_time', 'N/A'),
                    'outcome': outcome,
                    'result_emoji': item.get('result_emoji', 'N/A'),
                    'finish_position': item.get('finish_position', 'N/A'),
                    'winner_name': item.get('winner_name', 'N/A'),
                    'profit': item.get('profit', 0),
                }

                if outcome in ['win', 'placed', 'loss']:
                    picks_with_outcome.append(pick_info)
                else:
                    picks_pending.append(pick_info)

        if picks_with_outcome:
            print(f"[SETTLED PICKS] Found {len(picks_with_outcome)} settled picks:")
            print()

            wins = [p for p in picks_with_outcome if p['outcome'] == 'win']
            placed = [p for p in picks_with_outcome if p['outcome'] == 'placed']
            losses = [p for p in picks_with_outcome if p['outcome'] == 'loss']

            print(f"  Wins: {len(wins)}")
            print(f"  Placed: {len(placed)}")
            print(f"  Losses: {len(losses)}")
            print()

            # Show details
            for i, pick in enumerate(picks_with_outcome[:10], 1):
                print(f"  Pick #{i}:")
                print(f"    Horse: {pick['horse_name']}")
                print(f"    Course: {pick['course']} @ {pick['race_time']}")
                print(f"    Outcome: {pick['outcome']} ({pick['result_emoji']})")

                if pick['finish_position'] != 'N/A':
                    print(f"    Position: {pick['finish_position']}")
                if pick['winner_name'] != 'N/A':
                    print(f"    Winner: {pick['winner_name']}")
                if pick['profit'] != 0:
                    print(f"    Profit: £{float(pick['profit']):.2f}")
                print()

        if picks_pending:
            print(f"[PENDING PICKS] Found {len(picks_pending)} pending picks:")
            print()

            for i, pick in enumerate(picks_pending[:10], 1):
                print(f"  Pick #{i}:")
                print(f"    Horse: {pick['horse_name']}")
                print(f"    Course: {pick['course']} @ {pick['race_time']}")
                print(f"    Status: PENDING (race not finished yet)")
                print()

        if not picks_with_outcome and not picks_pending:
            print(f"[INFO] No pick items found with outcome/result fields")
            print(f"\nSample items found:")
            for item in items[:3]:
                print(f"  bet_id: {item.get('bet_id', 'N/A')}")
                print(f"  bet_date: {item.get('bet_date', 'N/A')}")
                print(f"  Keys: {list(item.keys())[:8]}")
                print()

    else:
        print(f"[INFO] No items found for {today}")
        print(f"  This could mean:")
        print(f"    - Picks haven't been generated yet")
        print(f"    - They're stored with different date format")
        print(f"    - They're in a different table")

except Exception as e:
    print(f"[ERROR] Failed to check results: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
print("RESULTS CHECK COMPLETE")
print("="*70)
print()
print("Summary:")
print("  - If settled picks found: Results system WORKING")
print("  - If all pending: Races haven't finished yet")
print("  - If no picks found: Check date format or table structure")

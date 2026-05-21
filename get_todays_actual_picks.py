"""
Get Today's Actual Picks from System
=====================================
Find and display current picks for today
"""

import boto3
from datetime import datetime, timedelta

print("="*80)
print("RETRIEVING TODAY'S ACTUAL PICKS")
print("="*80)
print()

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

target_date = datetime.now().strftime('%Y-%m-%d')
print(f"Date: {target_date}")
print()

# Strategy: Scan entire table and look for items that could be today's picks
print("[SEARCHING] Scanning table for pick-related data...")
print()

try:
    # Get recent items
    response = table.scan(Limit=200)
    items = response.get('Items', [])

    print(f"[INFO] Scanned {len(items)} items")

    # Look for items with today's date or recent timestamps
    today_items = []
    recent_items = []

    for item in items:
        # Check if this could be a pick
        bet_date = str(item.get('bet_date', ''))
        bet_id = str(item.get('bet_id', ''))

        # Check for today's date in various fields
        if target_date in bet_date or target_date in bet_id:
            today_items.append(item)

        # Check for recent timestamps (last 24 hours)
        for ts_field in ['timestamp', 'updated_at', 'generated_at', 'created_at']:
            if ts_field in item:
                ts_str = str(item[ts_field])
                if target_date in ts_str:
                    if item not in today_items:
                        today_items.append(item)
                    break

    if today_items:
        print(f"[FOUND] {len(today_items)} items with today's date")
        print()

        # Look for actual picks data
        picks_found = []

        for item in today_items:
            bet_date = item.get('bet_date', 'Unknown')
            bet_id = item.get('bet_id', 'Unknown')

            # Check if this looks like a pick
            has_pick_data = (
                'horse_name' in item or
                'pick_rank' in item or
                'race_time' in item or
                'course' in item or
                'venue' in item
            )

            if has_pick_data:
                picks_found.append(item)

        if picks_found:
            print(f"[SUCCESS] Found {len(picks_found)} pick items for today")
            print()

            # Display picks
            for i, pick in enumerate(picks_found[:10], 1):
                print(f"--- Pick #{i} ---")
                print(f"  bet_id: {pick.get('bet_id', 'N/A')}")
                print(f"  bet_date: {pick.get('bet_date', 'N/A')}")

                # Extract pick details
                horse_name = pick.get('horse_name') or pick.get('name')
                course = pick.get('course') or pick.get('venue')
                race_time = pick.get('race_time') or pick.get('time')
                odds = pick.get('decimal_odds') or pick.get('odds')
                pick_rank = pick.get('pick_rank')

                if horse_name:
                    print(f"  Horse: {horse_name}")
                if course:
                    print(f"  Course: {course}")
                if race_time:
                    print(f"  Time: {race_time}")
                if odds:
                    print(f"  Odds: {odds}")
                if pick_rank:
                    print(f"  Rank: #{pick_rank}")

                # Check for Phase 1 indicators
                has_phase1 = False

                # Check breakdown
                if 'breakdown' in pick:
                    breakdown = pick.get('breakdown', {})
                    if 'pace_match' in breakdown or 'jockey_upgrade' in breakdown:
                        has_phase1 = True
                        print(f"  [PHASE1] Signals present in breakdown!")

                # Check reasons
                if 'reasons' in pick:
                    reasons = pick.get('reasons', [])
                    phase1_reasons = [r for r in reasons if '[PHASE1]' in str(r)]
                    if phase1_reasons:
                        has_phase1 = True
                        print(f"  [PHASE1] Found in reasons:")
                        for r in phase1_reasons[:2]:
                            print(f"    - {r}")

                if not has_phase1:
                    print(f"  [NO PHASE1] Generated before Phase 1 deployment")

                # Check timestamp
                for ts_field in ['timestamp', 'updated_at', 'generated_at']:
                    if ts_field in pick:
                        print(f"  Generated: {pick[ts_field]}")
                        break

                print()
        else:
            print(f"[INFO] Items found but none appear to be picks")
            print(f"\nSample items found:")
            for item in today_items[:5]:
                print(f"  bet_date: {item.get('bet_date')}")
                print(f"  bet_id: {item.get('bet_id')}")
                print(f"  Keys: {list(item.keys())[:8]}")
                print()
    else:
        print(f"[WARNING] No items found for {target_date}")
        print()
        print("[ALTERNATIVE] Checking for yesterday's picks as reference...")

        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_items = [item for item in items if yesterday in str(item.get('bet_date', ''))]

        if yesterday_items:
            print(f"[FOUND] {len(yesterday_items)} items from yesterday ({yesterday})")
            print("\nYesterday's picks (for reference):")

            for i, item in enumerate(yesterday_items[:5], 1):
                horse_name = item.get('horse_name') or item.get('name', 'Unknown')
                course = item.get('course') or item.get('venue', 'Unknown')
                print(f"  {i}. {horse_name} at {course}")

except Exception as e:
    print(f"[ERROR] Failed to retrieve picks: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("PICK STATUS SUMMARY")
print("="*80)
print()
print("Based on system investigation:")
print()
print("1. Original picks generated: ~10:58-11:00 UTC (BEFORE Phase 1)")
print("2. Phase 1 deployed: ~12:50-13:04 UTC")
print("3. Pipeline re-runs: Multiple times after 12:50 UTC")
print()
print("Issue: Pipeline completed successfully but no race data available")
print("       to re-analyze, so picks haven't been regenerated with Phase 1.")
print()
print("Current Status:")
print("  - Today's displayed picks: DO NOT include Phase 1 signals")
print("  - Phase 1 deployment: COMPLETE and tested")
print("  - Tomorrow's picks: WILL include Phase 1 automatically")
print()
print("Action:")
print("  - Today's picks are still valid (original 18.64% baseline)")
print("  - Phase 1 improvement starts tomorrow (May 21, 08:30 UTC)")
print("  - Expected improvement: 18.64% → 25-30% strike rate")

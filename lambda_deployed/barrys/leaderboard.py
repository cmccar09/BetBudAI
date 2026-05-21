"""
leaderboard.py
Displays full competition standings, picks list, and points breakdown
for Barry's Cheltenham 2026 competition.

Usage:
    python leaderboard.py              # Full leaderboard
    python leaderboard.py --day 1      # Day 1 picks only
    python leaderboard.py --picks      # Show all picks (not yet run)
"""
import sys
import os
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from barrys.barrys_config import (
    DYNAMODB_TABLE, DYNAMODB_REGION, ENTRIES, FESTIVAL_RACES,
    POINTS, COMPETITION_NAME, PRIZE, FESTIVAL_DAYS
)

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)


def get_all_picks():
    """Get all picks from DynamoDB for both entries"""
    all_picks = {}
    for entry_name in ENTRIES:
        response = table.query(
            KeyConditionExpression=Key('entry').eq(entry_name)
        )
        all_picks[entry_name] = sorted(
            response.get('Items', []),
            key=lambda x: (x.get('race_date', ''), x.get('race_time', ''))
        )
    return all_picks


def calculate_totals(picks_list):
    """Calculate total points and race stats"""
    total_pts = sum(int(p.get('points', 0)) for p in picks_list)
    results = [p.get('result', 'pending') for p in picks_list]
    wins = results.count('won')
    places = results.count('placed_2nd') + results.count('placed_3rd')
    pending = results.count('pending')
    ran = len(picks_list) - pending
    return {
        'total': total_pts,
        'wins': wins,
        'places': places,
        'ran': ran,
        'pending': pending
    }


def print_full_leaderboard(all_picks):
    """Print the main leaderboard"""
    print(f"\n{'='*80}")
    print(f"  {COMPETITION_NAME.upper()}")
    print(f"  Prize: GBP {PRIZE:,}  |  Festival: 10-13 March 2026")
    print(f"  Points: 1st=10 | 2nd=5 | 3rd=3 | Unplaced=0")
    print(f"  Updated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*80}\n")

    totals = {}
    for entry, picks in all_picks.items():
        totals[entry] = calculate_totals(picks)

    # Ranking
    ranked = sorted(totals.items(), key=lambda x: x[1]['total'], reverse=True)

    print(f"  {'POS':<5} {'ENTRY':<25} {'POINTS':>8} {'RACES RAN':>10} {'WINS':>6} {'PLACES':>8} {'PENDING':>9}")
    print(f"  {'-'*75}")
    for pos, (entry, stats) in enumerate(ranked, 1):
        max_pts = 28 * 10
        remaining_pts = stats['pending'] * 10
        leader = " <-- LEADING" if pos == 1 else ""
        print(f"  {pos:<5} {entry:<25} {stats['total']:>8} {stats['ran']:>10} {stats['wins']:>6} {stats['places']:>8} {stats['pending']:>9}{leader}")

    print(f"\n  Max possible remaining: {ranked[0][1]['pending']*10}pts per entry")
    if len(ranked) >= 2:
        gap = ranked[0][1]['total'] - ranked[1][1]['total']
        print(f"  Current gap: {gap}pts ({'='*min(gap, 30) if gap else 'tied'})")
    print()


def print_picks_table(all_picks, day_filter=None, pending_only=False):
    """Print side-by-side picks for all races"""
    day_names = {1: "Champion Day", 2: "Ladies Day", 3: "St Patricks Thursday", 4: "Gold Cup Day"}

    # Build race list from config
    for day_num in [1, 2, 3, 4]:
        if day_filter and day_num != day_filter:
            continue

        day_date = FESTIVAL_DAYS[day_num]
        day_races = {k: v for k, v in FESTIVAL_RACES.items() if v['day'] == day_num}

        print(f"\n  DAY {day_num} - {day_names[day_num].upper()} ({day_date})")
        print(f"  {'-'*105}")
        print(f"  {'TIME':<7} {'RACE':<42} {'SUREBET':<28} {'DOUGLAS STUNNERS':<28} {'RESULT'}")
        print(f"  {'-'*105}")

        for race_key, race_info in sorted(day_races.items(), key=lambda x: x[1]['time']):
            race_id = f"{day_date}_{race_key}"

            sb_pick = next((p for p in all_picks.get("Surebet", []) if p.get('race_id') == race_id), {})
            ds_pick = next((p for p in all_picks.get("Douglas Stunners", []) if p.get('race_id') == race_id), {})

            if pending_only and sb_pick.get('result', 'pending') != 'pending':
                continue

            def fmt_pick(pick):
                if not pick or pick.get('horse', 'TBC') == 'TBC':
                    return "TBC"
                horse = pick['horse'][:26]
                pts   = int(pick.get('points', 0))
                res   = pick.get('result', 'pending')
                if res == 'pending':
                    return horse
                elif res == 'won':
                    return f"{horse} WIN +{pts}pts"
                elif res == 'placed_2nd':
                    return f"{horse} 2nd +{pts}pts"
                elif res == 'placed_3rd':
                    return f"{horse} 3rd +{pts}pts"
                else:
                    return f"{horse} --- 0pts"

            # Result column - show winner if known
            winner = sb_pick.get('winner') or ds_pick.get('winner', '')
            result_label = f"Won by: {winner}" if winner else "Pending"
            if sb_pick.get('result') == 'won':
                result_label = f"SureBet WON!"
            elif ds_pick.get('result') == 'won':
                result_label = f"Douglas WON!"

            print(f"  {race_info['time']:<7} {race_info['name'][:40]:<42} {fmt_pick(sb_pick):<28} {fmt_pick(ds_pick):<28} {result_label}")

        print()


def print_summary_stats(all_picks):
    """Print ROI and performance summary"""
    print(f"\n  {'='*70}")
    print(f"  PERFORMANCE SUMMARY")
    print(f"  {'='*70}")

    for entry, picks in all_picks.items():
        ran_picks = [p for p in picks if p.get('result', 'pending') != 'pending']
        if not ran_picks:
            continue

        total_pts = sum(int(p.get('points', 0)) for p in ran_picks)
        winners   = [p for p in ran_picks if p.get('result') == 'won']
        placed    = [p for p in ran_picks if p.get('result') in ('placed_2nd', 'placed_3rd')]

        print(f"\n  [{entry}]")
        print(f"    Races run   : {len(ran_picks)}")
        print(f"    Winners     : {len(winners)}")
        print(f"    Placed      : {len(placed)}")
        print(f"    Total points: {total_pts}")
        print(f"    Strike rate : {len(winners)/len(ran_picks)*100:.1f}%")
        print(f"    Points/race : {total_pts/len(ran_picks):.2f}")

        if winners:
            print(f"    Winners     : {', '.join(p.get('horse','?') for p in winners)}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Barry's competition leaderboard")
    parser.add_argument('--day',    type=int, help='Show specific day (1-4)')
    parser.add_argument('--picks',  action='store_true', help='Show all picks table')
    parser.add_argument('--stats',  action='store_true', help='Show performance stats')
    parser.add_argument('--pending',action='store_true', help='Show pending picks only')
    args = parser.parse_args()

    print("\nLoading competition data...")
    all_picks = get_all_picks()

    print_full_leaderboard(all_picks)

    if args.picks or args.day or not any([args.stats]):
        print_picks_table(all_picks, day_filter=args.day, pending_only=args.pending)

    if args.stats:
        print_summary_stats(all_picks)

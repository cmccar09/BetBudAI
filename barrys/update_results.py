"""
update_results.py
Updates race results and points for both entries after each race.
Can be run after each race or at end of day.

Usage:
    python update_results.py                      # Interactive mode
    python update_results.py --race "Supreme Novices Hurdle" --winner "Horse Name" --second "Horse B" --third "Horse C"
    python update_results.py --day 1              # Fetch results for entire day via Betfair
"""
import sys
import os
import json
import argparse
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from barrys.barrys_config import DYNAMODB_TABLE, DYNAMODB_REGION, ENTRIES, POINTS

import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)


def get_all_picks_for_race(race_date, race_name_fragment):
    """Get all entry picks for a specific race"""
    results = []
    for entry_name in ENTRIES:
        response = table.query(
            KeyConditionExpression=Key('entry').eq(entry_name)
        )
        for item in response.get('Items', []):
            if (race_name_fragment.lower() in item.get('race_name', '').lower() and
                    item.get('race_date') == race_date):
                results.append(item)
    return results


def update_pick_result(entry, race_id, finish_position, winner_name):
    """Update a pick with its finishing position and points earned"""
    pts = POINTS.get(finish_position, 0)
    result_map = {1: 'won', 2: 'placed_2nd', 3: 'placed_3rd', 0: 'lost'}
    result = result_map.get(finish_position, 'lost')

    table.update_item(
        Key={'entry': entry, 'race_id': race_id},
        UpdateExpression='SET points = :pts, result = :res, finish_position = :pos, winner = :win, updated_at = :ts',
        ExpressionAttributeValues={
            ':pts': pts,
            ':res': result,
            ':pos': finish_position,
            ':win': winner_name,
            ':ts': datetime.now().isoformat()
        }
    )
    return pts


def process_race_result(race_date, race_name, winner, second, third):
    """Process a race result - score both entries"""
    print(f"\n{'='*70}")
    print(f"UPDATING RESULT: {race_name}")
    print(f"  1st: {winner}  |  2nd: {second}  |  3rd: {third}")
    print(f"{'='*70}\n")

    picks = get_all_picks_for_race(race_date, race_name)

    if not picks:
        print(f"[WARNING] No picks found for '{race_name}' on {race_date}")
        return

    total_pts_by_entry = {}

    for pick in picks:
        entry = pick['entry']
        horse = pick.get('horse', 'TBC')
        race_id = pick['race_id']

        if horse.lower() == winner.lower():
            position = 1
        elif horse.lower() == second.lower():
            position = 2
        elif horse.lower() == third.lower():
            position = 3
        else:
            position = 0

        pts = update_pick_result(entry, race_id, position, winner)

        pos_label = {1: "1st - WINNER!", 2: "2nd - placed", 3: "3rd - placed", 0: "unplaced"}.get(position)
        print(f"  [{entry:<20}] Picked: {horse:<30} -> {pos_label} => +{pts} pts")
        total_pts_by_entry[entry] = pts

    print()
    for entry, pts in total_pts_by_entry.items():
        print(f"  {entry}: earned {pts} points this race")


def interactive_mode():
    """Interactive result entry"""
    print(f"\n{'='*70}")
    print("INTERACTIVE RESULT ENTRY")
    print(f"{'='*70}\n")

    race_date = input("Race date (YYYY-MM-DD, enter for today): ").strip()
    if not race_date:
        race_date = datetime.now().strftime('%Y-%m-%d')

    race_name = input("Race name (partial OK, e.g. 'Supreme'): ").strip()
    winner = input("Winner: ").strip()
    second = input("Second: ").strip()
    third  = input("Third:  ").strip()

    process_race_result(race_date, race_name, winner, second, third)


def batch_update_day(day_num):
    """Batch update all races for a festival day"""
    day_dates = {1: "2026-03-10", 2: "2026-03-11", 3: "2026-03-12", 4: "2026-03-13"}
    race_date = day_dates.get(day_num)
    if not race_date:
        print(f"[ERROR] Invalid day: {day_num}")
        return

    print(f"\nBatch updating results for Day {day_num} ({race_date})")
    print("Enter results for each race. Press Enter to skip a race.")

    from barrys_config import FESTIVAL_RACES
    day_races = {k: v for k, v in FESTIVAL_RACES.items() if v['day'] == day_num}

    for race_key, race_info in sorted(day_races.items(), key=lambda x: x[1]['time']):
        print(f"\n  {race_info['time']} - {race_info['name']}")
        winner = input("    Winner (Enter to skip): ").strip()
        if not winner:
            continue
        second = input("    Second: ").strip()
        third  = input("    Third:  ").strip()
        process_race_result(race_date, race_info['name'], winner, second, third)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Update Barry's competition results")
    parser.add_argument('--race',   help='Race name')
    parser.add_argument('--winner', help='Winning horse')
    parser.add_argument('--second', help='Second placed horse')
    parser.add_argument('--third',  help='Third placed horse')
    parser.add_argument('--date',   help='Race date YYYY-MM-DD (default: today)')
    parser.add_argument('--day',    type=int, help='Festival day number (1-4) for batch update')
    args = parser.parse_args()

    if args.day:
        batch_update_day(args.day)
    elif args.race and args.winner:
        race_date = args.date or datetime.now().strftime('%Y-%m-%d')
        process_race_result(race_date, args.race, args.winner, args.second or '', args.third or '')
    else:
        interactive_mode()

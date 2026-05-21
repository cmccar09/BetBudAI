"""
SL Racecard → response_horses.json Adapter
===========================================
Converts the SL racecard_cache.json format to the response_horses.json format
expected by comprehensive_workflow.py, then runs the workflow.

Used when Betfair API is unavailable — uses SL racecard data directly.
"""

import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone, timedelta

TODAY = date.today().strftime('%Y-%m-%d')


def get_uk_tz_offset(d: date) -> str:
    """Return '+01:00' (BST) if date falls in British Summer Time, else '+00:00' (GMT)."""
    year = d.year
    # BST starts: last Sunday in March
    bst_start = date(year, 3, 31)
    while bst_start.weekday() != 6:  # 6 = Sunday
        bst_start = date(year, bst_start.month, bst_start.day - 1)
    # BST ends: last Sunday in October
    bst_end = date(year, 10, 31)
    while bst_end.weekday() != 6:
        bst_end = date(year, bst_end.month, bst_end.day - 1)
    return '+01:00' if bst_start <= d < bst_end else '+00:00'


def frac_to_decimal(odds_str):
    """Convert fractional odds '11/4' → 3.75 decimal. Returns 0 on failure."""
    if not odds_str:
        return 0.0
    odds_str = str(odds_str).strip()
    try:
        return float(odds_str)  # already decimal
    except ValueError:
        pass
    try:
        if '/' in odds_str:
            num, den = odds_str.split('/')
            return round(float(num) / float(den) + 1.0, 3)
    except Exception:
        pass
    return 0.0


def weight_to_lbs(weight_str):
    """Convert '11-12' → 166 lbs. Returns 0 on failure."""
    try:
        parts = str(weight_str).split('-')
        if len(parts) == 2:
            return int(parts[0]) * 14 + int(parts[1])
    except Exception:
        pass
    return 0


def convert_racecard_to_workflow_format(racecard_today: dict) -> list:
    """
    Convert racecard_cache dict for one date into a list of race dicts
    in the response_horses.json format.

    NOTE: Sporting Life returns race times in UTC.  We store them as UTC
    (+00:00) so that display code (frontend Europe/Dublin timezone) and
    filtering logic (cutoff comparisons against UTC now) both work
    correctly regardless of daylight-saving time.
    """
    races = []
    for course, course_races in racecard_today.items():
        for race in course_races:
            time_str = race.get('time', '')  # e.g. "13:45" — this is UTC from SL
            # Store as UTC so the frontend can convert to IST (Europe/Dublin = UTC+1 in summer)
            if time_str and len(time_str) == 5:
                start_time = f"{TODAY}T{time_str}:00+00:00"
            else:
                start_time = f"{TODAY}T00:00:00+00:00"

            runners = []
            raw_runners = race.get('runners', [])
            weights_lbs = [weight_to_lbs(r.get('weight', '')) for r in raw_runners]

            for runner in raw_runners:
                horse_name = runner.get('horse', '')
                if isinstance(horse_name, dict):
                    horse_name = horse_name.get('name', '')

                decimal_odds = frac_to_decimal(runner.get('odds', ''))

                r_dict = {
                    'name': horse_name,
                    'horse': horse_name,            # some callers use horse.name
                    'jockey': runner.get('jockey', ''),
                    'trainer': runner.get('trainer', ''),
                    'form': runner.get('form', ''),
                    'odds': decimal_odds,
                    'age': runner.get('age', ''),
                    'weight': runner.get('weight', ''),
                    'weight_lbs': weight_to_lbs(runner.get('weight', '')),
                    'official_rating': runner.get('official_rating', ''),
                    'headgear': runner.get('headgear', ''),
                    'timeform_stars': runner.get('timeform_stars', 0),
                    'prev_results': runner.get('prev_results', []),
                    'favourite': runner.get('favourite', False),
                    'cloth': runner.get('cloth', 0),
                    'draw': runner.get('draw', None),
                    # Extra fields that pick logic uses
                    'race_class': str(race.get('class', '')),
                    'race_name': race.get('name', ''),
                    'market_name': race.get('name', ''),
                }
                runners.append(r_dict)

            race_dict = {
                'venue': course,
                'start_time': start_time,
                'market_name': race.get('name', ''),
                'race_class': str(race.get('class', '')),
                'class': str(race.get('class', '')),
                'race_id': race.get('race_id', ''),
                'going': race.get('going', ''),
                'distance': race.get('distance', ''),
                'surface': race.get('surface', 'turf'),
                'has_handicap': race.get('has_handicap', False),
                'runners': runners,
                # Legacy keys some functions use
                'course': course,
                'race_time': time_str,
                'type': race.get('name', ''),
            }
            races.append(race_dict)

    # Sort by start_time
    races.sort(key=lambda r: r['start_time'])
    return races


def main():
    # Load racecard cache
    cache_path = os.path.join(os.path.dirname(__file__), 'racecard_cache.json')
    if not os.path.exists(cache_path):
        print(f"ERROR: racecard_cache.json not found. Run:")
        print(f"  python sl_racecard_fetcher.py")
        sys.exit(1)

    rc = json.load(open(cache_path, encoding='utf-8'))

    if TODAY not in rc:
        print(f"ERROR: No racecard data for {TODAY} in cache.")
        print(f"Available dates: {list(rc.keys())}")
        sys.exit(1)

    racecard_today = rc[TODAY]
    print(f"Converting SL racecard for {TODAY}...")
    courses = list(racecard_today.keys())
    total_races = sum(len(v) for v in racecard_today.values())
    print(f"  Courses: {', '.join(courses)}")
    print(f"  Total races: {total_races}")

    races = convert_racecard_to_workflow_format(racecard_today)

    # Only include races starting >15 minutes from now (matches betfair_odds_fetcher.py logic)
    now_utc = datetime.now(timezone.utc)
    cutoff = now_utc + timedelta(minutes=15)
    upcoming = [r for r in races if datetime.fromisoformat(r['start_time']) > cutoff]
    skipped = len(races) - len(upcoming)
    if skipped:
        print(f"  Skipping {skipped} races that have already started or are within 15 minutes")

    # Write to response_horses.json (workflow format)
    output = {'races': upcoming, 'source': 'sl_racecard', 'date': TODAY}
    out_path = os.path.join(os.path.dirname(__file__), 'response_horses.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)

    print(f"  Written {len(upcoming)} upcoming races → response_horses.json")
    print()

    # Run comprehensive_workflow.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workflow = os.path.join(script_dir, 'comprehensive_workflow.py')
    python = sys.executable
    result = subprocess.run([python, '-X', 'utf8', workflow], cwd=script_dir)
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()

"""
DAILY CHELTENHAM SUBMISSION GENERATOR
======================================
Run this EVERY MORNING of the festival before 11:30am to generate
Barry's competition submission picks for that day.

Usage:
    python generate_daily_submission.py            # Auto-detects today
    python generate_daily_submission.py --day 1    # Force Day 1
    python generate_daily_submission.py --day 2    # Force Day 2
    python generate_daily_submission.py --check    # Check all sources, no output yet
    python generate_daily_submission.py --verify   # Verify cloth numbers are all filled

DEADLINE: Submit by 11:30am on race day sharp.

Submission format: horse cloth numbers separated by commas, one per race, in time order.
Example: 3, 1, 7, 2, 9, 5, 4

Cloth numbers come from the official race card (Sporting Life / Racing Post).
Update CLOTH_NUMBERS_2026.py each morning once cards are published.

DAILY WORKFLOW:
    1. Check https://www.sportinglife.com/racing/news for withdrawals / jockey changes
    2. Update CLOTH_NUMBERS_2026.py with official cloth numbers from race cards
    3. Run: python generate_daily_submission.py
    4. Copy the submission string and submit by 11:30am
    5. Run: python save_cheltenham_picks.py to update DynamoDB with latest picks
"""

import sys
import os
from datetime import datetime, date
import argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from barrys.surebet_intel import build_all_picks, FESTIVAL_RACES
from CLOTH_NUMBERS_2026 import CLOTH_NUMBERS_2026, get_cloth_number

# ──────────────────────────────────────────────────────────────────────────────
# Festival day detection
# ──────────────────────────────────────────────────────────────────────────────

FESTIVAL_DAY_DATES = {
    1: date(2026, 3, 10),  # Champion Day — Tuesday
    2: date(2026, 3, 11),  # Ladies' Day — Wednesday
    3: date(2026, 3, 12),  # St Patrick's Thursday
    4: date(2026, 3, 13),  # Gold Cup Day — Friday
}

FESTIVAL_DAY_NAMES = {
    1: "Champion Day — Tuesday 10 March",
    2: "Ladies' Day — Wednesday 11 March",
    3: "St Patrick's Thursday — 12 March",
    4: "Gold Cup Day — Friday 13 March",
}

DYNAMO_DAY_KEYS = {
    1: "Tuesday_10_March",
    2: "Wednesday_11_March",
    3: "Thursday_12_March",
    4: "Friday_13_March",
}

# Map race_key prefix → day number
DAY_PREFIX_MAP = {
    "day1_race": 1,
    "day2_race": 2,
    "day3_race": 3,
    "day4_race": 4,
}


def detect_today_day() -> int | None:
    """Return current festival day number (1-4) or None if not a festival day."""
    today = date.today()
    for day_num, day_date in FESTIVAL_DAY_DATES.items():
        if today == day_date:
            return day_num
    return None


def get_active_day(force_day: int | None = None) -> int:
    """Return the day to generate picks for (forced, today, or next upcoming)."""
    if force_day:
        return force_day
    today_day = detect_today_day()
    if today_day:
        return today_day
    # Not a festival day — return next upcoming
    today = date.today()
    for day_num, day_date in sorted(FESTIVAL_DAY_DATES.items()):
        if day_date >= today:
            return day_num
    return 4  # fallback to Gold Cup Day


def get_race_keys_for_day(day_num: int) -> list[str]:
    """Return all race keys for a given festival day, in time order."""
    prefix = f"day{day_num}_race"
    keys_in_day = [
        (key, info)
        for key, info in FESTIVAL_RACES.items()
        if key.startswith(prefix)
    ]
    return sorted(keys_in_day, key=lambda x: x[1]["time"])


# ──────────────────────────────────────────────────────────────────────────────
# Sporting Life news check
# ──────────────────────────────────────────────────────────────────────────────

def check_sporting_life_news(verbose=True) -> list[dict]:
    """
    Fetch latest Sporting Life racing news headlines.
    Returns a list of {headline, url} dicts for any Cheltenham-related stories.
    """
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/122.0.0.0 Safari/537.36'
            )
        }
        r = requests.get(
            'https://www.sportinglife.com/racing/news',
            headers=headers, timeout=15
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        items = []
        # Try multiple selectors for article links
        for a in soup.find_all('a', href=True)[:200]:
            text = (a.get_text(strip=True) or '').strip()
            href = a['href']
            if len(text) < 20:
                continue
            cheltenham_kw = any(kw in text.lower() for kw in [
                'cheltenham', 'gold cup', 'champion hurdle', 'champion chase',
                'festival', 'ryanair', 'arkle', 'mares', 'stayers',
                'withdrawn', 'ruled out', 'scratched', 'declared', 'confirmed'
            ])
            if cheltenham_kw:
                url = href if href.startswith('http') else f"https://www.sportinglife.com{href}"
                if {'headline': text, 'url': url} not in items:
                    items.append({'headline': text, 'url': url})

        if verbose:
            print(f"\n  [SPORTING LIFE] {len(items)} Cheltenham-related headlines found")
            for item in items[:8]:
                print(f"    → {item['headline'][:90]}")

        return items[:10]

    except Exception as e:
        if verbose:
            print(f"  [SPORTING LIFE] Could not fetch news: {e}")
        return []


# ──────────────────────────────────────────────────────────────────────────────
# Main submission generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_submission(day_num: int, verbose: bool = True) -> dict:
    """
    Generate the full daily submission for a given festival day.
    Returns {
        'day':          int,
        'day_name':     str,
        'submission_string': str,   # e.g. "3, 1, 7, 2"
        'races':        list of race dicts,
        'missing_cloth': list of race names where cloth number not filled,
        'warnings':     list of warning strings,
    }
    """
    day_name = FESTIVAL_DAY_NAMES[day_num]

    if verbose:
        print(f"\n{'='*70}")
        print(f"  BARRY'S CHELTENHAM — DAILY SUBMISSION")
        print(f"  {day_name}")
        print(f"  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
        print(f"  DEADLINE: 11:30am — Submit BEFORE racing starts!")
        print(f"{'='*70}\n")
        print("  Checking sources...")

    # ── 1. Check Sporting Life for breaking news ─────────────────────────────
    if verbose:
        news = check_sporting_life_news(verbose=True)
    else:
        news = []

    # ── 2. Score all races fresh via the SureBet engine ─────────────────────
    if verbose:
        print("\n  Scoring all races via SureBet engine...")

    all_picks = build_all_picks(verbose=True)

    # ── 3. Build per-race submission data ────────────────────────────────────
    race_keys_for_day = get_race_keys_for_day(day_num)

    races = []
    submission_nums = []
    missing_cloth = []
    warnings = []

    for race_key, race_info in race_keys_for_day:
        pick_data = all_picks.get(race_key)
        if not pick_data:
            warnings.append(f"No pick data for {race_key} ({race_info['name']})")
            submission_nums.append("?")
            races.append({
                'race_key':   race_key,
                'race_name':  race_info['name'],
                'race_time':  race_info['time'],
                'grade':      race_info.get('grade', ''),
                'surebet_pick': '(no data)',
                'douglas_pick': '(no data)',
                'surebet_score': 0,
                'cloth_num':  None,
                'cloth_status': '⚠ NO DATA',
                'top3':       [],
            })
            continue

        sb_pick = pick_data['surebet']['name']
        ds_pick = pick_data['douglas']['name']
        sb_score = pick_data['surebet'].get('score', 0)
        sb_odds  = pick_data['surebet'].get('odds', '?')
        top3 = pick_data.get('scored', [])[:3]

        # Look up cloth number for the SureBet pick
        cloth = get_cloth_number(race_key, sb_pick)
        if cloth is None:
            cloth_status = "⚠ TBD — update CLOTH_NUMBERS_2026.py"
            missing_cloth.append(race_info['name'])
            submission_nums.append("??")
        else:
            cloth_status = f"✓ #{cloth}"
            submission_nums.append(str(cloth))

        # Flag if MacFitz disagrees
        split_note = ""
        if ds_pick != sb_pick:
            ds_cloth = get_cloth_number(race_key, ds_pick)
            ds_cloth_str = f"#{ds_cloth}" if ds_cloth else "??"
            split_note = f"  ⚡ SPLIT: SureBet={sb_pick} / MacFitz={ds_pick} ({ds_cloth_str})"

        race_entry = {
            'race_key':     race_key,
            'race_name':    race_info['name'],
            'race_time':    race_info['time'],
            'grade':        race_info.get('grade', ''),
            'surebet_pick': sb_pick,
            'surebet_score': sb_score,
            'surebet_odds': sb_odds,
            'douglas_pick': ds_pick,
            'cloth_num':    cloth,
            'cloth_status': cloth_status,
            'split_note':   split_note,
            'top3':         top3,
        }
        races.append(race_entry)

    submission_string = ", ".join(submission_nums)

    # ── 4. Print detailed race-by-race breakdown ─────────────────────────────
    if verbose:
        print(f"\n  {'='*68}")
        print(f"  RACE-BY-RACE PICKS")
        print(f"  {'='*68}")
        for i, r in enumerate(races, 1):
            grade_tag = f"[{r['grade']}]" if r.get('grade') else ""
            print(f"\n  Race {i}: {r['race_time']}  {r['race_name']:<34} {grade_tag}")
            print(f"    SureBet Pick : {r['surebet_pick']:<28}  Score: {r.get('surebet_score',0)}  "
                  f"Odds: {r.get('surebet_odds','?')}")
            print(f"    Cloth #       : {r['cloth_status']}")
            if r.get('split_note'):
                print(f"    {r['split_note']}")

            # Show top 3 horses for context
            top3 = r.get('top3', [])
            if top3:
                print(f"    Top 3 horses  :")
                for j, h in enumerate(top3, 1):
                    h_cloth = get_cloth_number(r['race_key'], h['name'])
                    c_str = f"#{h_cloth}" if h_cloth else "??"
                    print(f"      {j}. {h['name']:<28}  score={h['score']:3}  "
                          f"cloth={c_str}  {h.get('odds','?')}")

    # ── 5. Print the submission string ───────────────────────────────────────
    if verbose:
        print(f"\n  {'='*68}")
        print(f"  BARRY'S COMPETITION — SUBMISSION STRING")
        print(f"  Copy and paste this (cloth numbers in race-time order):")
        print(f"  {'='*68}")
        if missing_cloth:
            print(f"\n  ⚠ WARNING: {len(missing_cloth)} cloth number(s) not yet filled:")
            for n in missing_cloth:
                print(f"    • {n}")
            print(f"\n  Update CLOTH_NUMBERS_2026.py then re-run this script.\n")
        print(f"\n  ┌─ SUBMISSION ─────────────────────────────────────────────────┐")
        print(f"  │  {submission_string:<62}│")
        print(f"  └──────────────────────────────────────────────────────────────┘")
        print(f"\n  Races ({len(races)}):")
        for i, r in enumerate(races, 1):
            c = submission_nums[i-1]
            pick = r.get('surebet_pick', '?')
            print(f"    Race {i}: {r['race_time']}  {r['race_name']:<34}  {pick:<26}  cloth #{c}")

        if warnings:
            print(f"\n  ⚠ Warnings:")
            for w in warnings:
                print(f"    {w}")

        print(f"\n  {'='*68}")
        print(f"  ⏰ REMINDER: Submit by 11:30am on {FESTIVAL_DAY_NAMES[day_num].split('—')[1].strip()}")
        print(f"  {'='*68}\n")

    # ── 6. Save to log file ─────────────────────────────────────────────────
    log_path = os.path.join(ROOT, f"_submission_day{day_num}_{date.today().isoformat()}.txt")
    try:
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"BARRY'S CHELTENHAM 2026 — DAY {day_num} SUBMISSION\n")
            f.write(f"{day_name}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(f"SUBMISSION STRING:\n{submission_string}\n\n")
            f.write("RACE BREAKDOWN:\n")
            for i, r in enumerate(races, 1):
                f.write(f"  Race {i}: {r['race_time']}  {r['race_name']}\n")
                f.write(f"    Pick: {r.get('surebet_pick','?')}  "
                        f"Score: {r.get('surebet_score',0)}  "
                        f"Cloth #: {submission_nums[i-1]}\n")
            if missing_cloth:
                f.write(f"\nMISSING CLOTH NUMBERS:\n")
                for n in missing_cloth:
                    f.write(f"  • {n}\n")
        if verbose:
            print(f"  [LOG] Saved to: {log_path}")
    except Exception as e:
        if verbose:
            print(f"  [LOG] Could not save log: {e}")

    return {
        'day':               day_num,
        'day_name':          day_name,
        'submission_string': submission_string,
        'races':             races,
        'missing_cloth':     missing_cloth,
        'warnings':          warnings,
        'news_items':        news,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Generate Barry's Cheltenham daily submission card"
    )
    parser.add_argument(
        '--day', type=int, choices=[1, 2, 3, 4], default=None,
        help='Festival day (1=Tue, 2=Wed, 3=Thu, 4=Fri). Auto-detects if omitted.'
    )
    parser.add_argument(
        '--check', action='store_true',
        help='Check Sporting Life news only, no full analysis.'
    )
    parser.add_argument(
        '--verify', action='store_true',
        help='Verify all cloth numbers are filled for today\'s races.'
    )
    args = parser.parse_args()

    if args.check:
        print("\n  SPORTING LIFE NEWS CHECK")
        print("  " + "="*50)
        check_sporting_life_news(verbose=True)
        sys.exit(0)

    active_day = get_active_day(args.day)
    today_actual = detect_today_day()

    if today_actual is None:
        days_until = None
        for d, dt in sorted(FESTIVAL_DAY_DATES.items()):
            if dt > date.today():
                delta = (dt - date.today()).days
                print(f"\n  ℹ Festival not running today. Next up: Day {d} ({FESTIVAL_DAY_NAMES[d]}) in {delta} day(s)")
                break

    if args.verify:
        print(f"\n  CLOTH NUMBER VERIFICATION — Day {active_day}")
        print("  " + "="*50)
        race_keys = get_race_keys_for_day(active_day)
        all_filled = True
        for rk, ri in race_keys:
            missing = [h for h, v in CLOTH_NUMBERS_2026.get(rk, {}).items() if v is None]
            if missing:
                all_filled = False
                print(f"  ⚠ {ri['name']}: missing numbers for {', '.join(missing[:5])}")
            else:
                total = len(CLOTH_NUMBERS_2026.get(rk, {}))
                if total == 0:
                    print(f"  ⚠ {ri['name']}: no horses configured")
                else:
                    print(f"  ✓ {ri['name']}: all {total} horses numbered")
        if all_filled:
            print("\n  ✅ All cloth numbers filled — ready to submit!")
        else:
            print("\n  ⚠ Update CLOTH_NUMBERS_2026.py before generating submission.")
        sys.exit(0)

    generate_submission(active_day, verbose=True)

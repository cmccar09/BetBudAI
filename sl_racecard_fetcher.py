"""
SL Racecard Fetcher
===================
Fetches today's (or specified date's) UK racecard data from Sporting Life.

For each UK race, extracts via __NEXT_DATA__:
  • trainer, jockey, weight, official_rating
  • form figures (formsummary), age, sex, horse_id
  • current SP/odds, favourite flag
  • Timeform star rating, rating123
  • previous results (last 6 runs: course, distance, going, position, class)
  • race-level: going, distance, class, age-band, handicap, verdict text

Output: racecard_cache.json  (fast local lookup for comprehensive_workflow.py)
Also:   DynamoDB table SureBetRacecards  (PK=race_date, SK=race_id)

Usage:
    python sl_racecard_fetcher.py              # today
    python sl_racecard_fetcher.py 2026-03-22   # specific date
    python sl_racecard_fetcher.py --no-dynamo  # skip DynamoDB write
"""

import re
import sys
import json
import time
import boto3
from datetime import date
from decimal import Decimal

try:
    import requests
    def _fetch(url: str, headers: dict, timeout=20):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            return r.text if r.status_code == 200 else None
        except Exception as e:
            print(f"  [fetch] {e}: {url}")
            return None
except ImportError:
    import urllib.request
    def _fetch(url: str, headers: dict, timeout=20):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode('utf-8')
        except Exception as e:
            print(f"  [fetch] {e}: {url}")
            return None

sys.stdout.reconfigure(encoding='utf-8')

# ── Config ────────────────────────────────────────────────────────────────────
TARGET_DATE  = next((a for a in sys.argv[1:] if re.match(r'\d{4}-\d{2}-\d{2}', a)), date.today().strftime('%Y-%m-%d'))
SKIP_DYNAMO  = '--no-dynamo' in sys.argv
CACHE_FILE   = 'racecard_cache.json'
SL_BASE      = 'https://www.sportinglife.com'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': SL_BASE + '/',
}

# UK / Irish course names that we care about
UK_IRELAND_COURSES = {
    'musselburgh','lingfield','newbury','wolverhampton','cheltenham','kempton',
    'ascot','haydock','sandown','chester','goodwood','york','leicester',
    'nottingham','carlisle','catterick','newcastle','hamilton','perth','ayr',
    'wetherby','doncaster','exeter','taunton','hereford','huntingdon','ludlow',
    'market rasen','plumpton','stratford','uttoxeter','windsor','wincanton',
    'ffos las','sedgefield','southwell','bangor-on-dee','bangor on dee',
    'worcester','warwick','bath','chepstow','epsom','pontefract','ripon',
    'redcar','beverley','thirsk','brighton','kelso','naas','leopardstown',
    'curragh','fairyhouse','navan','gowran park','punchestown','bellewstown',
    'tramore','down royal','dundalk','cork',
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _next_data(html: str) -> dict | None:
    """Extract the __NEXT_DATA__ JSON from a Sporting Life page."""
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _to_slug(text: str) -> str:
    """Convert a race / venue name to a URL-safe slug."""
    s = text.lower()
    s = re.sub(r'[^a-z0-9\s-]', ' ', s)   # keep alphanumeric, spaces, hyphens
    s = re.sub(r'\s+', '-', s.strip())
    s = re.sub(r'-+', '-', s).strip('-')
    return s


def _is_decimal(val) -> bool:
    """Check whether a value can be stored as a DynamoDB Decimal."""
    try:
        Decimal(str(val))
        return True
    except Exception:
        return False


# ── Step 1: Get meetings for the date ────────────────────────────────────────
def fetch_meetings(date_str: str) -> list[dict]:
    """Return all meetings from the SL racecard index for the given date."""
    url = f'{SL_BASE}/racing/racecards/{date_str}'
    html = _fetch(url, HEADERS)
    if not html:
        print(f"  [racecard] failed to fetch index: {url}")
        return []

    data = _next_data(html)
    if not data:
        print(f"  [racecard] no __NEXT_DATA__ in index")
        return []

    meetings = data.get('props', {}).get('pageProps', {}).get('meetings', [])
    print(f"  [racecard] {len(meetings)} meeting(s) in index for {date_str}")
    return meetings


# ── Step 2: Fetch full data for a single race ─────────────────────────────────
def fetch_race_detail(date_str: str, venue_slug: str, race_id: int, race_name: str) -> dict | None:
    """
    Fetch the __NEXT_DATA__ for one race's racecard page.
    URL format: /racing/racecards/{date}/{venue}/racecard/{race_id}/{race-name-slug}
    Returns the 'race' dict from pageProps, or None on failure.
    """
    name_slug = _to_slug(race_name)
    url = (
        f'{SL_BASE}/racing/racecards/{date_str}/{venue_slug}'
        f'/racecard/{race_id}/{name_slug}'
    )
    html = _fetch(url, HEADERS, timeout=25)
    if not html:
        return None

    data = _next_data(html)
    if not data:
        return None

    return data.get('props', {}).get('pageProps', {}).get('race')


# ── Step 3: Parse ride data for a single runner ──────────────────────────────
def _parse_ride(ride: dict) -> dict:
    """Extract the useful fields from a single ride dict."""
    horse = ride.get('horse') or {}
    betting = ride.get('betting') or {}
    fav_raw = betting.get('favourite') or {}
    prev = horse.get('previous_results') or []

    # Timeform
    tf_stars = ride.get('timeform_stars')
    if isinstance(tf_stars, dict):
        tf_stars = tf_stars.get('value')
    r123 = ride.get('rating123')
    if isinstance(r123, dict):
        r123 = r123.get('value')

    # Previous results (keep up to 6)
    prev_clean = []
    for pr in prev[:6]:
        prev_clean.append({
            'date':     pr.get('date', ''),
            'course':   pr.get('course_name', ''),
            'distance': pr.get('distance', ''),
            'going':    pr.get('going', ''),
            'position': pr.get('position'),
            'runners':  pr.get('runner_count'),
            'class':    pr.get('race_class', ''),
            'odds':     pr.get('odds', ''),
            'ride_desc':pr.get('ride_description', ''),
            'bha':      pr.get('bha'),
        })

    return {
        'cloth':           ride.get('cloth_number'),
        'draw':            ride.get('draw_number'),
        'finish_position': ride.get('finish_position'),   # None pre-race
        'ride_status':     ride.get('ride_status', 'RUNNER'),  # NON_RUNNER etc.
        'horse':           horse.get('name', ''),
        'horse_id':        horse.get('horse_reference', {}).get('id') if isinstance(horse.get('horse_reference'), dict) else None,
        'age':             horse.get('age'),
        'sex':             horse.get('sex', {}).get('type', '') if isinstance(horse.get('sex'), dict) else '',
        'form':            horse.get('formsummary', {}).get('display_text', '') if isinstance(horse.get('formsummary'), dict) else '',
        'trainer':         (ride.get('trainer') or {}).get('name', ''),
        'trainer_id':      ((ride.get('trainer') or {}).get('business_reference') or {}).get('id'),
        'jockey':          (ride.get('jockey') or {}).get('name', ''),
        'jockey_id':       ((ride.get('jockey') or {}).get('person_reference') or {}).get('id'),
        'weight':          ride.get('handicap', ''),
        'official_rating': ride.get('official_rating'),
        'headgear':        (ride.get('headgear') or {}).get('code', '') if isinstance(ride.get('headgear'), dict) else '',
        'odds':            betting.get('current_odds', ''),
        'odds_history':    betting.get('historical_odds', []),
        'favourite':       bool(fav_raw) if not isinstance(fav_raw, bool) else fav_raw,
        'timeform_stars':  tf_stars,
        'rating123':       r123,
        'prev_results':    prev_clean,
    }


# ── Step 4: Build full racecard for the date ──────────────────────────────────
def build_racecard(date_str: str) -> dict:
    """
    Build the full racecard for the date.
    Returns: { course_name: [ {race dict} ] }
    """
    meetings = fetch_meetings(date_str)
    racecard: dict[str, list] = {}

    for mtg in meetings:
        ms = mtg.get('meeting_summary', {})
        course_name = ms.get('course', {}).get('name', '') if isinstance(ms.get('course'), dict) else ''

        if not course_name:
            continue

        # Filter to UK/Irish meetings
        if course_name.lower() not in UK_IRELAND_COURSES and \
           not any(c in course_name.lower() for c in ['dee', 'rasen', 'las']):
            continue

        venue_slug  = _to_slug(course_name)
        races_meta  = mtg.get('races', [])

        print(f"\n  [{course_name}] {len(races_meta)} race(s)")
        course_races = []

        for rm in races_meta:
            race_id   = (rm.get('race_summary_reference') or {}).get('id')
            race_name = rm.get('name', '')
            race_time = rm.get('time', '')

            if not race_id:
                continue

            print(f"    {race_time} {race_name} (ID:{race_id})", end='', flush=True)

            # Fetch full detail
            race_data = fetch_race_detail(date_str, venue_slug, race_id, race_name)

            if not race_data:
                # Fall back to summary-only data
                print(f" [no detail]")
                course_races.append({
                    'race_id':      race_id,
                    'time':         race_time,
                    'name':         race_name,
                    'going':        rm.get('going', ''),
                    'class':        rm.get('race_class', ''),
                    'distance':     rm.get('distance', ''),
                    'age':          rm.get('age', ''),
                    'has_handicap': rm.get('has_handicap', False),
                    'verdict':      rm.get('verdict', ''),
                    'runners':      [],
                })
                time.sleep(0.3)
                continue

            rs = race_data.get('race_summary') or {}
            rides_raw = race_data.get('rides') or []
            runners = [_parse_ride(r) for r in rides_raw]

            # Build clean verdict (strip HTML tags)
            verdict_html = rs.get('verdict') or rm.get('verdict', '')
            verdict_text = re.sub(r'<[^>]+>', '', verdict_html).strip()

            race_entry = {
                'race_id':       race_id,
                'time':          rs.get('time', race_time),
                'name':          rs.get('name', race_name),
                'course':        rs.get('course_name', course_name),
                'going':         rs.get('going', rm.get('going', '')),
                'going_short':   rs.get('going_shortcode', ''),
                'class':         rs.get('race_class', rm.get('race_class', '')),
                'distance':      rs.get('distance', rm.get('distance', '')),
                'age':           rs.get('age', rm.get('age', '')),
                'has_handicap':  rs.get('has_handicap', rm.get('has_handicap', False)),
                'surface':       (rs.get('course_surface') or {}).get('surface', '') if isinstance(rs.get('course_surface'), dict) else '',
                'verdict':       verdict_text,
                'runners':       runners,
            }
            course_races.append(race_entry)
            print(f" → {len(runners)} runners ✓")

            time.sleep(0.4)   # polite crawl

        if course_races:
            racecard[course_name] = course_races

    return racecard


# ── Step 5: Save to JSON cache ────────────────────────────────────────────────
def save_cache(racecard: dict, date_str: str):
    """Merge with existing cache file and save."""
    existing = {}
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            existing = json.load(f)
    except Exception:
        pass

    existing[date_str] = racecard

    # Keep only last 7 days
    all_dates = sorted(existing.keys(), reverse=True)
    for old in all_dates[7:]:
        del existing[old]

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2, default=str)

    total_races = sum(len(races) for races in racecard.values())
    total_runners = sum(len(r.get('runners', [])) for races in racecard.values() for r in races)
    print(f"\n  [cache] saved {len(racecard)} venues, {total_races} races, {total_runners} runners → {CACHE_FILE}")


# ── Step 6: Save to DynamoDB ──────────────────────────────────────────────────
def save_to_dynamo(racecard: dict, date_str: str):
    """Write racecard to DynamoDB SureBetRacecards table (creates if needed)."""
    if SKIP_DYNAMO:
        return

    try:
        db = boto3.resource('dynamodb', region_name='eu-west-1')
        table = db.Table('SureBetRacecards')
        table.load()
    except Exception as e:
        print(f"  [dynamo] table not accessible: {e}")
        return

    written = 0
    for course, races in racecard.items():
        for race in races:
            # Serialise to DynamoDB-safe format
            item = {
                'race_date':     date_str,
                'race_id':       str(race['race_id']),
                'course':        course,
                'time':          race['time'],
                'name':          race['name'],
                'going':         race['going'],
                'going_short':   race.get('going_short', ''),
                'race_class':    str(race.get('class', '')),
                'distance':      race['distance'],
                'age_band':      race.get('age', ''),
                'has_handicap':  race['has_handicap'],
                'surface':       race.get('surface', ''),
                'verdict':       race['verdict'][:2000],   # DynamoDB 400KB limit
                'runners_json':  json.dumps(race['runners'], default=str)[:5000],
            }
            try:
                table.put_item(Item=item)
                written += 1
            except Exception as e:
                print(f"  [dynamo] error writing race {race['race_id']}: {e}")

    print(f"  [dynamo] wrote {written} race(s) to SureBetRacecards")


# ── Public API ────────────────────────────────────────────────────────────────
def get_cached_racecard(date_str: str | None = None) -> dict:
    """
    Load racecard for the given date from cache file.
    Returns: { course_name: [ {race dict} ] }
    Returns empty dict if not cached.
    """
    if date_str is None:
        date_str = date.today().strftime('%Y-%m-%d')
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get(date_str, {})
    except Exception:
        return {}


def get_race_runners(course: str, race_time: str, date_str: str | None = None) -> list[dict]:
    """
    Convenience: get runner list for a specific race.
    Returns list of runner dicts (empty list if not found).
    """
    rc = get_cached_racecard(date_str)
    for c, races in rc.items():
        if c.lower() == course.lower():
            for race in races:
                if race.get('time', '') == race_time:
                    return race.get('runners', [])
    return []


def get_sl_verdict_horses(course: str, race_time: str, date_str: str | None = None) -> list[str]:
    """
    Extract horse names mentioned in the SL tipster verdict for a race.
    Bold names (ALL CAPS or <b> tagged) are the primary selections.
    Returns list of horse names in order of appearance.
    """
    rc = get_cached_racecard(date_str)
    for c, races in rc.items():
        if c.lower() == course.lower():
            for race in races:
                if race.get('time', '') == race_time:
                    verdict = race.get('verdict', '')
                    # Bold names appear in ALL CAPS in plain-text verdict
                    horses = re.findall(r'\b([A-Z][A-Z\s\']+[A-Z])\b', verdict)
                    return [h.strip().title() for h in horses if len(h) > 2]
    return []


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print(f"\n{'='*60}")
    print(f" SL Racecard Fetcher — {TARGET_DATE}")
    print(f"{'='*60}")

    racecard = build_racecard(TARGET_DATE)

    if racecard:
        save_cache(racecard, TARGET_DATE)
        save_to_dynamo(racecard, TARGET_DATE)

        print(f"\n{'='*60}")
        print(f"RACECARD SUMMARY — {TARGET_DATE}")
        print(f"{'='*60}")
        for course, races in sorted(racecard.items()):
            print(f"\n{course}:")
            for race in races:
                runners = race.get('runners', [])
                n_active = sum(1 for r in runners if r.get('ride_status', 'RUNNER') == 'RUNNER')
                fav = next((r['horse'] for r in runners if r.get('favourite')), '?')
                print(f"  {race['time']} {race['name'][:50]:<50} "
                      f"Cls:{race.get('class','?'):<3} "
                      f"Dist:{race.get('distance','?'):<12} "
                      f"Going:{race.get('going_short','?'):<4} "
                      f"Runners:{n_active:<3} Fav:{fav}")
    else:
        print("  No UK racecards found.")

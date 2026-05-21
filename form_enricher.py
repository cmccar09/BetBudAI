"""
FORM ENRICHER — Fetches detailed last-6-race history from Sporting Life for each runner.

Data per run:
  date            : "2026-01-17"
  course          : "Ascot"
  distance_f      : 18.5        # furlongs (e.g. 2m3f ≈ 18.5f)
  going           : "Good to Soft"
  position        : 1
  field_size      : 10
  official_rating : 124         # OR on that day (None if sourced from racecard)
  race_class      : "4"
  beaten_lengths  : 2.25        # None if sourced from racecard

Signals unlocked:
  - exact_course_win       +20pts
  - exact_distance_win     +20pts
  - going_win_match        +16pts
  - fresh_days_optimal     +10pts
  - close_2nd_last_time    +14pts  (needs beaten_lengths — profile fetch only)
  - or_trajectory_up       +10pts  (needs official_rating — profile fetch only)
  - big_field_win          +8pts

Fetch strategy:
  1. enrich_runners() pre-fetches today's SL race racecard pages (1 request/race).
     Every runner in today's races gets form data immediately.
  2. fetch_form() on a single horse: checks _today_form cache, then falls back to
     the SL profile page (/racing/profiles/horse/{id}) if the horse ID is known.
     Profile pages include official_rating and beaten_lengths.
  3. IDs are persisted in _sl_horse_ids.json (360+ known).

Usage:
  from form_enricher import enrich_runners, get_form_signals

  enriched_races = enrich_runners(races)   # adds 'form_runs' to each runner
  # analyze_horse_comprehensive picks up form_runs from horse_data automatically
"""

import json
import re
import time
import os
from datetime import datetime, timezone

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    import urllib.request
    _HAS_REQUESTS = False

# ---------------------------------------------------------------------------
# Cache file — avoids re-scraping the same horses on every refresh
# ---------------------------------------------------------------------------
CACHE_FILE = 'form_cache.json'
CACHE_TTL_HOURS = 12

_cache = {}


def _load_cache():
    global _cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                _cache = json.load(f)
        except Exception:
            _cache = {}


def _save_cache():
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(_cache, f, indent=2)
    except Exception:
        pass


_load_cache()

# ---------------------------------------------------------------------------
# SL horse ID map — persistent name → numeric id
# ---------------------------------------------------------------------------
_SL_ID_FILE = '_sl_horse_ids.json'
_sl_id_map = {}    # horse_name.lower() → int
_sl_ids_dirty = False


def _load_sl_ids():
    global _sl_id_map
    if os.path.exists(_SL_ID_FILE):
        try:
            with open(_SL_ID_FILE, 'r') as f:
                raw = json.load(f)
            _sl_id_map = {k.lower(): int(v) for k, v in raw.items()}
        except Exception:
            _sl_id_map = {}


def _save_sl_ids():
    global _sl_ids_dirty
    if not _sl_ids_dirty:
        return
    try:
        with open(_SL_ID_FILE, 'w') as f:
            json.dump(_sl_id_map, f, indent=2)
        _sl_ids_dirty = False
    except Exception:
        pass


_load_sl_ids()

# ---------------------------------------------------------------------------
# Today's pre-fetched form data (populated by enrich_runners)
# ---------------------------------------------------------------------------
_today_form = {}    # horse_name.lower() → list[run_dict]

# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------
_SL_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://www.sportinglife.com/',
    'Upgrade-Insecure-Requests': '1',
}


def _http_get(url, headers=None, timeout=15):
    """Minimal HTTP GET — works with or without `requests` package."""
    hdrs = headers or _SL_HEADERS
    if _HAS_REQUESTS:
        try:
            r = requests.get(url, headers=hdrs, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                return r.text
        except Exception:
            pass
        return None
    else:
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return resp.read().decode('utf-8', errors='replace')
        except Exception:
            pass
        return None


# ---------------------------------------------------------------------------
# Going normalisation + distance helpers
# ---------------------------------------------------------------------------

# Going abbreviation normaliser — maps SL short codes to standard terms
_GOING_NORM = {
    'HY': 'Heavy', 'Hy': 'Heavy', 'HVY': 'Heavy',
    'SF': 'Soft', 'Sft': 'Soft', 'Soft': 'Soft', 'GS': 'Good to Soft',
    'GF': 'Good to Firm', 'GD': 'Good', 'G': 'Good', 'Gd': 'Good',
    'F': 'Firm', 'Fm': 'Firm', 'Firm': 'Firm',
    'SD': 'Slow', 'STD': 'Standard', 'Standard': 'Standard', 'AW': 'Standard',
}


def _norm_going(g: str) -> str:
    return _GOING_NORM.get(g, g)


# Distance string → furlongs
def _dist_to_furlongs(dist_str: str) -> float | None:
    """
    Convert distance strings like '2m3f 63yds', '1m7f 50yds', '2m4f' → furlongs.
    1 mile = 8 furlongs, 1 furlong = 220 yards → 63yds ≈ 0.29f
    """
    if not dist_str:
        return None
    dist_str = str(dist_str).strip().lower()
    total_f = 0.0
    # miles
    m = re.search(r'(\d+)m', dist_str)
    if m:
        total_f += int(m.group(1)) * 8
    # furlongs
    f = re.search(r'(\d+)f', dist_str)
    if f:
        total_f += int(f.group(1))
    # yards
    y = re.search(r'(\d+)y(?:ds?)?', dist_str)
    if y:
        total_f += int(y.group(1)) / 220
    return round(total_f, 2) if total_f > 0 else None


# ---------------------------------------------------------------------------
# Beaten lengths parser: "4 3/4l", "nk", "hd", "sh hd" → float
# ---------------------------------------------------------------------------

def _parse_beaten_lengths(s) -> float | None:
    if not s:
        return None
    s = str(s).lower().strip()
    if 'sh hd' in s or 'short head' in s:
        return 0.1
    if s in ('hd', 'head') or (s.startswith('hd') and len(s) <= 3):
        return 0.2
    if s in ('nk', 'neck') or (s.startswith('nk') and len(s) <= 3):
        return 0.3
    # "4 3/4l" or "4 3/4"
    m = re.match(r'^(\d+)\s+(\d+)/(\d+)', s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / int(m.group(3))
    # "1/2l" or "3/4"
    m2 = re.match(r'^(\d+)/(\d+)', s)
    if m2:
        return int(m2.group(1)) / int(m2.group(2))
    # "3l" or "3.5"
    m3 = re.match(r'^(\d+\.?\d*)', s)
    if m3:
        return float(m3.group(1))
    return None


# ---------------------------------------------------------------------------
# Venue slug: "Newton Abbot" → "newton-abbot"
# ---------------------------------------------------------------------------

def _venue_slug(name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-')


# ---------------------------------------------------------------------------
# SL race URL discovery from main racecard page
# ---------------------------------------------------------------------------

_SL_RACE_URL_RE = re.compile(
    r'(/racing/racecards/(\d{4}-\d{2}-\d{2})/([^/\s"]+)/racecard/(\d+)/[^"?\s]+)'
)


_sl_race_url_cache = {}   # date_str → result dict (one fetch per process per date)


def _get_sl_race_urls(date_str: str = None) -> dict:
    """
    Fetch the SL main racecard page and extract all race URLs for date_str (default today).
    Returns { "venue-slug": ["https://...", ...], ... }
    Caches the result in-memory so the racecard page is only fetched once per date.
    """
    today = date_str or datetime.now(timezone.utc).strftime('%Y-%m-%d')
    if today in _sl_race_url_cache:
        return _sl_race_url_cache[today]

    url = 'https://www.sportinglife.com/racing/racecards'
    html = _http_get(url, timeout=20)
    if not html:
        _sl_race_url_cache[today] = {}
        return {}

    result = {}
    seen = set()
    for m in _SL_RACE_URL_RE.finditer(html):
        path, d, venue, _race_id = m.group(1), m.group(2), m.group(3), m.group(4)
        if d != today:
            continue
        if path in seen:
            continue
        seen.add(path)
        full_url = 'https://www.sportinglife.com' + path
        result.setdefault(venue, []).append(full_url)

    _sl_race_url_cache[today] = result
    return result


# ---------------------------------------------------------------------------
# SL race racecard fetch — one request covers all runners in a race
# ---------------------------------------------------------------------------

def _parse_sl_runs(prev_results: list, max_runs: int = 6) -> list[dict]:
    """Map SL previous_results list to standard run dicts."""
    runs = []
    for r in prev_results[:max_runs]:
        # Prefer full going name; fall back to shortcode
        going_raw = r.get('going') or r.get('going_shortcode', '')
        runs.append({
            'date': r.get('date', ''),
            'course': r.get('course_name', ''),
            'distance_f': _dist_to_furlongs(r.get('distance', '')),
            'going': _norm_going(going_raw),
            'position': _safe_int(r.get('position')),
            'field_size': _safe_int(r.get('runner_count')),
            'official_rating': _safe_int(r.get('or') or r.get('bha')),
            'race_class': str(r.get('race_class', '')),
            'beaten_lengths': _parse_beaten_lengths(r.get('result_between_distance', '')),
        })
    return runs


def _fetch_sl_race_form(race_url: str) -> dict:
    """
    Fetch one SL race racecard page.
    Returns { horse_name_lower: [run_dicts] } for all runners.
    Also updates _sl_id_map with any new horse IDs discovered.
    """
    global _sl_ids_dirty
    html = _http_get(race_url, timeout=15)
    if not html:
        return {}

    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html, re.DOTALL
    )
    if not m:
        return {}

    try:
        nd = json.loads(m.group(1))
        rides = nd['props']['pageProps']['race']['rides']
    except (KeyError, ValueError):
        return {}

    result = {}
    for ride in rides:
        horse = ride.get('horse', {})
        name = horse.get('name', '').strip()
        if not name:
            continue
        h_id = (horse.get('horse_reference') or {}).get('id')
        if h_id and name.lower() not in _sl_id_map:
            _sl_id_map[name.lower()] = int(h_id)
            _sl_ids_dirty = True
        prev_results = horse.get('previous_results', [])
        result[name.lower()] = _parse_sl_runs(prev_results)
    return result


# ---------------------------------------------------------------------------
# SL profile page — full data including official_rating + beaten_lengths
# ---------------------------------------------------------------------------

def _fetch_sl_profile(horse_id: int, max_runs: int = 6) -> list[dict]:
    """
    Fetch /racing/profiles/horse/{id}.
    Returns run dicts including official_rating and beaten_lengths.
    """
    url = f'https://www.sportinglife.com/racing/profiles/horse/{horse_id}'
    html = _http_get(url, timeout=15)
    if not html:
        return []

    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html, re.DOTALL
    )
    if not m:
        return []

    try:
        nd = json.loads(m.group(1))
        prev_results = nd['props']['pageProps']['profile']['previous_results']
    except (KeyError, ValueError):
        return []

    return _parse_sl_runs(prev_results, max_runs)


# ---------------------------------------------------------------------------
# Parse Paddy Power-style form text (kept for backwards compatibility)
# ---------------------------------------------------------------------------

def parse_pp_form_text(text: str) -> list[dict]:
    """
    Parse the tabular form section from Paddy Power / similar text:
        17 Jan 26  Ascot  Asc 2m3f 63yds Sft Hdl  1/10  124
    Returns list of run dicts.
    """
    runs = []
    # Match date + course + details line
    row_re = re.compile(
        r'(\d{1,2}\s+[A-Z][a-z]{2}\s+\d{2})\s+'                    # date
        r'(.+?)\s+'                                                    # full course name
        r'[A-Z][a-z]{2,4}\s+'                                         # course abbr
        r'(\d+m\d*f?\s*\d*y?d?s?)\s+'                                # distance
        r'([A-Za-z]{1,6})\s+'                                         # going
        r'(?:Hdl|Chase|Hrd|Flt|Nov|Hcp)\s*'                          # race type
        r'(\d{1,2})/(\d{1,2})\s*'                                    # pos/field
        r'(\d+|N/A)?',                                                # OR
    )
    for m in row_re.finditer(text):
        date_raw = m.group(1).strip()
        course = m.group(2).strip()
        dist_raw = m.group(3).strip()
        going_raw = m.group(4).strip()
        pos = _safe_int(m.group(5))
        field = _safe_int(m.group(6))
        or_raw = m.group(7) or ''
        try:
            date_str = datetime.strptime(date_raw, '%d %b %y').strftime('%Y-%m-%d')
        except Exception:
            date_str = date_raw
        runs.append({
            'date': date_str,
            'course': course,
            'distance_f': _dist_to_furlongs(dist_raw),
            'going': _norm_going(going_raw),
            'position': pos,
            'field_size': field,
            'official_rating': _safe_int(or_raw) if or_raw != 'N/A' else None,
            'race_class': '',
            'beaten_lengths': None,
        })
    return runs


# ---------------------------------------------------------------------------
# Main public entry points
# ---------------------------------------------------------------------------

def fetch_form(horse_name: str, max_runs: int = 6, force_refresh: bool = False) -> list[dict]:
    """
    Return last max_runs race history for a horse.

    Lookup order:
      1. form_cache.json (12h TTL) — only if it has actual runs (skips old empty entries)
      2. _today_form (pre-fetched by enrich_runners from today's race racecard pages)
      3. SL profile page (/racing/profiles/horse/{id}) if horse ID is known
      4. Return [] — no data available for this horse
    """
    cache_key = horse_name.lower().strip()
    now = datetime.now(timezone.utc)

    # 1. Cache check — skip entries with empty runs so they get re-fetched
    if not force_refresh and cache_key in _cache:
        entry = _cache[cache_key]
        if entry.get('runs'):
            cached_at_str = entry.get('cached_at', '2000-01-01')
            cached_at = datetime.fromisoformat(cached_at_str)
            # Normalise: if naive (old format), assume UTC
            if cached_at.tzinfo is None:
                from datetime import timezone as _tz_fe
                cached_at = cached_at.replace(tzinfo=_tz_fe.utc)
            age_h = (now - cached_at).total_seconds() / 3600
            if age_h < CACHE_TTL_HOURS:
                return entry['runs']

    # 2. Check today's pre-fetched race form (populated by enrich_runners)
    if cache_key in _today_form:
        runs = _today_form[cache_key]
        _cache[cache_key] = {'runs': runs, 'cached_at': now.isoformat(), 'source': 'sl_racecard'}
        _save_cache()
        return runs

    # 3. SL profile page (full data including official_rating + beaten_lengths)
    h_id = _sl_id_map.get(cache_key)
    if h_id:
        runs = _fetch_sl_profile(h_id, max_runs)
        time.sleep(0.6)
        _cache[cache_key] = {
            'runs': runs,
            'cached_at': now.isoformat(),
            'source': 'sl_profile' if runs else 'none',
        }
        _save_cache()
        return runs

    # 4. No data available — do NOT cache so it retries on next call
    return []


def enrich_runners(races: list[dict], verbose: bool = True) -> list[dict]:
    """
    Add 'form_runs' list to every runner in every race.
    Pre-fetches all SL race racecard pages for today's venues (1 request/race),
    then injects form data into each runner. Mutates races in-place and returns them.
    """
    global _today_form

    # Step 1: Get today's SL race URLs (indexed by venue slug)
    today = datetime.now().strftime('%Y-%m-%d')
    if verbose:
        print(f"  [form] Fetching SL race URLs for {today}…")
    sl_race_urls = _get_sl_race_urls(today)
    if verbose:
        n_urls = sum(len(v) for v in sl_race_urls.values())
        print(f"  [form] Found {n_urls} race URLs across {len(sl_race_urls)} venues")

    # Step 2: For each distinct venue in our races, fetch all its SL race racecard pages
    fetched_venues = set()
    for race in races:
        venue = race.get('course') or race.get('venue') or ''
        vs = _venue_slug(venue)
        if vs in fetched_venues:
            continue

        # Look up SL URLs for this venue (exact or partial match)
        sl_urls = sl_race_urls.get(vs, [])
        if not sl_urls:
            for sl_venue, urls in sl_race_urls.items():
                if vs and (vs in sl_venue or sl_venue in vs):
                    sl_urls = urls
                    break

        if not sl_urls:
            continue

        fetched_venues.add(vs)
        for race_url in sl_urls:
            race_form = _fetch_sl_race_form(race_url)
            _today_form.update(race_form)
            time.sleep(0.4)

    if verbose:
        print(f"  [form] Pre-fetched form for {len(_today_form)} horses across {len(fetched_venues)} venues")

    # Save any newly discovered horse IDs
    _save_sl_ids()

    # Step 3: Inject form_runs into each runner
    total_horses = sum(len(r.get('runners', [])) for r in races)
    done = 0
    enriched = 0
    for race in races:
        for runner in race.get('runners', []):
            name = runner.get('name') or runner.get('horse') or ''
            if name:
                # Strip country suffix like (IRE), (USA)
                name_clean = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', name).strip()
                runs = fetch_form(name_clean)
                runner['form_runs'] = runs
                done += 1
                if runs:
                    enriched += 1
                if verbose:
                    status = f"✓ {len(runs)} runs" if runs else "✗ no data"
                    print(f"  [{done}/{total_horses}] {name}: {status}")

    if verbose:
        print(f"  [form] Enriched {enriched}/{done} runners with form data")
    return races
    return races


# ---------------------------------------------------------------------------
# Scoring signals derived from form_runs
# ---------------------------------------------------------------------------

def get_form_signals(horse_data: dict, today_course: str, today_distance_f: float | None,
                      today_going: str) -> dict:
    """
    Compute new scoring signals from the horse's detailed form history.

    Returns dict of signal values:
        exact_course_win      bool
        exact_distance_win    bool
        going_win_match       bool
        going_place_match     bool
        days_since_last_run   int | None
        fresh_days_optimal    bool    — 14-35 days = optimal freshness window
        close_2nd_last_time   bool    — 2nd with beaten_lengths < 4
        or_trajectory_up      bool    — OR rising over last 3 runs
        big_field_win         bool    — won in field of 10+
        going_win_count       int     — # wins on similar going
        course_run_count      int     — # starts at this course
        course_win_count      int     — # wins at this course
        distance_win_count    int     — # wins within 0.5f of today
    """
    runs = horse_data.get('form_runs', [])
    signals = {
        'exact_course_win': False,
        'exact_distance_win': False,
        'going_win_match': False,
        'going_place_match': False,
        'days_since_last_run': None,
        'fresh_days_optimal': False,
        'close_2nd_last_time': False,
        'or_trajectory_up': False,
        'big_field_win': False,
        'going_win_count': 0,
        'course_run_count': 0,
        'course_win_count': 0,
        'distance_win_count': 0,
        'class_drop': False,   # ran in higher class (2/3) recently, drops to lower (4/5+) today
    }

    if not runs:
        return signals

    today_going_type = _going_type(today_going)

    for i, run in enumerate(runs):
        pos = run.get('position')
        course = str(run.get('course', '')).lower()
        dist_f = run.get('distance_f')
        going = run.get('going', '')
        going_type = _going_type(going)
        field = run.get('field_size') or 0
        beaten = run.get('beaten_lengths')

        # Days since last run
        if i == 0 and run.get('date'):
            try:
                last_date = datetime.strptime(run['date'], '%Y-%m-%d')
                days = (datetime.now() - last_date).days
                signals['days_since_last_run'] = days
                signals['fresh_days_optimal'] = 14 <= days <= 35
            except Exception:
                pass

        # Close 2nd last time
        if i == 0 and pos == 2 and beaten is not None and beaten < 4:
            signals['close_2nd_last_time'] = True

        # Course records
        today_course_norm = today_course.lower().strip()
        course_norm = course.strip()
        if today_course_norm and (today_course_norm in course_norm or course_norm in today_course_norm):
            signals['course_run_count'] += 1
            if pos == 1:
                signals['exact_course_win'] = True
                signals['course_win_count'] += 1

        # Distance records (±0.5 furlongs tolerance)
        if today_distance_f and dist_f:
            if abs(today_distance_f - dist_f) <= 0.5:
                signals['distance_win_count'] += (1 if pos == 1 else 0)
                if pos == 1:
                    signals['exact_distance_win'] = True

        # Going records
        if going_type == today_going_type:
            if pos == 1:
                signals['going_win_count'] += 1
                signals['going_win_match'] = True
            elif pos in (2, 3):
                signals['going_place_match'] = True

        # Big field win
        if pos == 1 and field >= 10:
            signals['big_field_win'] = True

    # OR trajectory — check last 3 runs with valid OR
    valid_ors = [(r.get('official_rating') or 0) for r in runs[:3] if r.get('official_rating')]
    if len(valid_ors) >= 2:
        signals['or_trajectory_up'] = valid_ors[0] > valid_ors[-1]   # most recent > oldest

    # Class drop detection — if today's race class is lower than horse's recent runs
    # today_class is passed via horse_data; form runs carry race_class per run
    def _norm_class(c):
        """Return numeric class (1-7) or None."""
        try:
            s = str(c).lower().replace('class', '').replace(' ', '').replace('c', '')
            n = int(s)
            return n if 1 <= n <= 7 else None
        except Exception:
            return None

    today_cls_raw = horse_data.get('race_class') or horse_data.get('class', '')
    today_cls = _norm_class(today_cls_raw)
    if today_cls and today_cls >= 4:  # only meaningful if dropping INTO class 4+
        recent_classes = [_norm_class(r.get('race_class', '')) for r in runs[:3]]
        higher_class_runs = [c for c in recent_classes if c is not None and c <= 3]
        if higher_class_runs:  # was recently in class 1/2/3, now class 4+
            signals['class_drop'] = True

    return signals


def _going_type(going: str) -> str:
    """Bucket going into broad categories for matching."""
    g = str(going).lower()
    if 'heavy' in g:
        return 'heavy'
    if 'soft' in g:
        return 'soft'
    if 'good to soft' in g or 'gs' in g:
        return 'gd_soft'
    if 'good to firm' in g or 'gf' in g:
        return 'gd_firm'
    if 'good' in g:
        return 'good'
    if 'firm' in g:
        return 'firm'
    if 'standard' in g or 'aw' in g or 'all' in g:
        return 'aw'
    return 'unknown'


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _safe_int(v) -> int | None:
    try:
        return int(str(v).strip())
    except Exception:
        return None


def _safe_float(v) -> float | None:
    try:
        return float(str(v).strip())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Quick CLI test
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    import sys
    horse = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else 'Came From Nowhere'
    print(f"\nFetching form for: {horse}")
    runs = fetch_form(horse, force_refresh=True)
    if runs:
        print(f"Found {len(runs)} runs:")
        for r in runs:
            print(f"  {r['date']} | {r['course']} | {r['distance_f']}f | {r['going']} | "
                  f"{r['position']}/{r['field_size']} | OR={r['official_rating']}")
    else:
        print("No form data retrieved (RP may have blocked — normal, still works via cache/fallback)")
    sigs = get_form_signals({'form_runs': runs}, 'Newbury', 18.5, 'Soft')
    print(f"\nSignals: {json.dumps(sigs, indent=2)}")

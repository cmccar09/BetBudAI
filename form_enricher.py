"""
FORM ENRICHER — Two-source parallel enrichment for every runner.

Sources (run in parallel, SL first, Racing API fills gaps):
  1. Sporting Life racecard scraping — parses __NEXT_DATA__ JSON to get ALL meetings
     (25 venues today vs 8 featured previously), covers UK/Irish/international field.
  2. The Racing API (theracingapi.com) — structured API, covers ~95%+ UK/Irish field
     when plan includes racecards endpoint. Set RACING_API_KEY env var as "username:password".

Data per run:
  date            : "2026-01-17"
  course          : "Ascot"
  distance_f      : 18.5        # furlongs (e.g. 2m3f ≈ 18.5f)
  going           : "Good to Soft"
  position        : 1
  field_size      : 10
  official_rating : 124
  race_class      : "4"
  beaten_lengths  : 2.25

Signals unlocked:
  - exact_course_win       +20pts
  - exact_distance_win     +20pts
  - going_win_match        +16pts
  - fresh_days_optimal     +10pts
  - close_2nd_last_time    +14pts  (needs beaten_lengths)
  - or_trajectory_up       +10pts  (needs official_rating)
  - big_field_win          +8pts

Fetch strategy:
  1. enrich_runners() fans out SL scraping + Racing API call simultaneously.
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
_today_form = {}       # horse_name.lower() → list[run_dict]
_today_tf_stars = {}   # horse_name.lower() → int (1-5 Timeform star rating)

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
    Fetch the SL main racecard page and extract all race URLs for ALL meetings today.
    Parses __NEXT_DATA__ JSON to get every meeting's race IDs (25 venues, not just 8
    featured), then constructs racecard URLs directly from race IDs.
    Returns { "venue-slug": ["https://...", ...], ... }
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

    # Primary: parse __NEXT_DATA__ — covers ALL meetings (UK, Irish, international)
    nd_match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html, re.DOTALL
    )
    if nd_match:
        try:
            nd = json.loads(nd_match.group(1))
            meetings = nd['props']['pageProps']['meetings']
            for meeting in meetings:
                ms = meeting.get('meeting_summary', {})
                course = ms.get('course', {})
                venue_name = course.get('name', '') if isinstance(course, dict) else str(course)
                if not venue_name:
                    continue
                venue_slug = _venue_slug(venue_name)
                for race in meeting.get('races', []):
                    race_ref = race.get('race_summary_reference', {})
                    race_id = race_ref.get('id') if isinstance(race_ref, dict) else None
                    if not race_id:
                        continue
                    race_url = (
                        f'https://www.sportinglife.com/racing/racecards'
                        f'/{today}/{venue_slug}/racecard/{race_id}/racecard'
                    )
                    result.setdefault(venue_slug, []).append(race_url)
        except (KeyError, ValueError, TypeError):
            pass

    # Fallback: regex HTML link extraction (featured meetings only)
    if not result:
        seen: set = set()
        for m in _SL_RACE_URL_RE.finditer(html):
            path, d, venue, _race_id = m.group(1), m.group(2), m.group(3), m.group(4)
            if d != today:
                continue
            if path in seen:
                continue
            seen.add(path)
            result.setdefault(venue, []).append('https://www.sportinglife.com' + path)

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


def _fetch_sl_race_form(race_url: str) -> tuple:
    """
    Fetch one SL race racecard page.
    Returns ({ horse_name_lower: [run_dicts] }, { horse_name_lower: tf_stars },
             { horse_name_lower: horse_id }) — thread-safe, no global mutation.
    """
    html = _http_get(race_url, timeout=15)
    if not html:
        return {}, {}, {}

    m = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html, re.DOTALL
    )
    if not m:
        return {}, {}, {}

    try:
        nd = json.loads(m.group(1))
        rides = nd['props']['pageProps']['race']['rides']
    except (KeyError, ValueError):
        return {}, {}, {}

    result = {}
    tf_stars_result = {}
    new_ids = {}
    for ride in rides:
        horse = ride.get('horse', {})
        name = horse.get('name', '').strip()
        if not name:
            continue
        h_id = (horse.get('horse_reference') or {}).get('id')
        if h_id and name.lower() not in _sl_id_map:
            new_ids[name.lower()] = int(h_id)
        prev_results = horse.get('previous_results', [])
        result[name.lower()] = _parse_sl_runs(prev_results)
        tf_stars = ride.get('timeform_stars')
        if isinstance(tf_stars, dict):
            tf_stars = tf_stars.get('value')
        if tf_stars and isinstance(tf_stars, (int, float)):
            tf_stars_result[name.lower()] = int(tf_stars)
    return result, tf_stars_result, new_ids


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
# The Racing API (theracingapi.com) — second enrichment source
# ---------------------------------------------------------------------------

def _parse_racing_api_runs(past_results: list, max_runs: int = 6) -> list[dict]:
    """Convert theracingapi.com past_results entries to our standard run_dict format."""
    runs = []
    for r in past_results[:max_runs]:
        pos = None
        pos_raw = r.get('position') or r.get('finishing_position') or r.get('pos') or ''
        try:
            pos = int(str(pos_raw).replace('st', '').replace('nd', '').replace('rd', '').replace('th', '').strip())
        except (ValueError, TypeError):
            pass

        dist_f = None
        dist_raw = r.get('distance_f') or r.get('distance') or ''
        try:
            dist_f = float(dist_raw) if isinstance(dist_raw, (int, float)) else _dist_to_furlongs(str(dist_raw))
        except Exception:
            pass

        going_raw = (r.get('going') or r.get('going_description') or r.get('ground') or '')
        field = _safe_int(r.get('runners') or r.get('field_size') or r.get('number_of_runners'))
        beaten = _parse_beaten_lengths(str(r.get('beaten_lengths') or r.get('btn') or r.get('dist') or ''))

        runs.append({
            'date':             str(r.get('date') or r.get('race_date') or ''),
            'course':           str(r.get('course') or r.get('course_name') or ''),
            'distance_f':       dist_f,
            'going':            _norm_going(str(going_raw)),
            'position':         pos,
            'field_size':       field,
            'official_rating':  _safe_int(r.get('official_rating') or r.get('or')),
            'race_class':       str(r.get('class') or r.get('race_class') or ''),
            'beaten_lengths':   beaten,
        })
    return runs


def fetch_racing_api_form(date_str: str, api_key: str) -> dict:
    """
    Fetch Pro racecard data from theracingapi.com for today's runners.
    Pro plan (£99.99/mo) — racecards/pro returns structured per-runner data including:
      past_results_flags : 'C'=course winner, 'D'=distance winner, 'CD'=both, 'BF'=beaten fav
      last_run           : days since last run (authoritative)
      rpr                : Racing Post Rating
      ts                 : Topspeed rating
      ofr                : Official Rating
      trainer_14_days    : {"runs": N, "wins": N, "percent": N} — live 14-day trainer form
      trainer_rtf        : trainer rank-to-form score

    Returns { horse_name_lower: ra_runner_dict } — injected onto runners as 'ra_data'.
    """
    if not api_key or ':' not in api_key:
        return {}

    import base64
    encoded = base64.b64encode(api_key.encode()).decode()
    headers_auth = {
        'Authorization': f'Basic {encoded}',
        'Accept': 'application/json',
    }

    # Pro endpoint — no date param needed (defaults to today); &region filters aren't needed
    try:
        resp = requests.get('https://api.theracingapi.com/v1/racecards/pro',
                            headers=headers_auth, timeout=30)
        if resp.status_code == 401:
            print(f'  [racing_api] ⛔ 401 — credentials rejected. Check RACING_API_KEY in Lambda env.')
            return {}
        if resp.status_code == 403:
            print(f'  [racing_api] ⛔ 403 — plan does not include racecards/pro. Upgrade required.')
            return {}
        if resp.status_code != 200:
            print(f'  [racing_api] HTTP {resp.status_code} from racecards/pro')
            return {}
        data = resp.json()
    except Exception as exc:
        print(f'  [racing_api] Request error: {exc}')
        return {}

    result: dict = {}
    races = data.get('racecards') or []
    for race in races:
        race_course = str(race.get('course', '')).strip()
        race_going  = str(race.get('going', '')).strip()
        for runner in (race.get('runners') or []):
            name = str(runner.get('horse') or '').strip()
            if not name:
                continue
            name_key = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', name).strip().lower()

            # trainer_14_days is {"runs": "28", "wins": "10", "percent": "36"}
            t14 = runner.get('trainer_14_days') or {}
            try:
                t14_pct = int(t14.get('percent', 0) or 0)
            except (ValueError, TypeError):
                t14_pct = 0
            try:
                t14_runs = int(t14.get('runs', 0) or 0)
            except (ValueError, TypeError):
                t14_runs = 0

            def _int_or_none(v):
                try:
                    n = int(v)
                    return n if n > 0 else None
                except (TypeError, ValueError):
                    return None

            result[name_key] = {
                'past_results_flags': str(runner.get('past_results_flags') or '').upper().strip(),
                'last_run_days':      _int_or_none(runner.get('last_run')),
                'rpr':                _int_or_none(runner.get('rpr')),
                'ts':                 _int_or_none(runner.get('ts')),
                'ofr':                _int_or_none(runner.get('ofr')),
                'trainer_14d_pct':    t14_pct,
                'trainer_14d_runs':   t14_runs,
                'trainer_rtf':        _int_or_none(runner.get('trainer_rtf')),
                'horse_id':           str(runner.get('horse_id') or ''),
                'race_course':        race_course,
                'race_going':         race_going,
                'draw':               _int_or_none(runner.get('draw')),
                'form_string':        str(runner.get('form') or ''),
            }

    print(f'  [racing_api] Pro racecard: {len(result)} runners across {len(races)} races')
    return result


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


def _sl_fan_out(all_urls: list) -> tuple:
    """Fetch all SL race pages in parallel. Returns (form_dict, tf_dict, new_ids_dict)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    merged_form: dict = {}
    merged_tf: dict = {}
    merged_ids: dict = {}
    if not all_urls:
        return merged_form, merged_tf, merged_ids
    with ThreadPoolExecutor(max_workers=min(len(all_urls), 10)) as pool:
        futures = {pool.submit(_fetch_sl_race_form, url): url for url in all_urls}
        for future in as_completed(futures):
            try:
                race_form, tf_stars_map, new_ids = future.result()
                merged_form.update(race_form)
                merged_tf.update(tf_stars_map)
                merged_ids.update(new_ids)
            except Exception as exc:
                print(f"  [sl] Warning: race page error — {exc}")
    return merged_form, merged_tf, merged_ids


def enrich_runners(races: list[dict], verbose: bool = True,
                   racing_api_key: str = '') -> list[dict]:
    """
    Parallel two-source enrichment — SL scraping + Racing API run simultaneously.
    SL data takes priority; Racing API fills every horse SL missed.
    Set racing_api_key='username:password' from theracingapi.com (free tier).
    """
    global _today_form, _today_tf_stars, _sl_ids_dirty

    from concurrent.futures import ThreadPoolExecutor, as_completed
    import os

    api_key = racing_api_key or os.environ.get('RACING_API_KEY', '')
    today = datetime.now().strftime('%Y-%m-%d')

    # ── Collect SL race URLs for today's venues ───────────────────────────────
    if verbose:
        print(f"  [form] Fetching SL race index for {today}…")
    sl_race_urls = _get_sl_race_urls(today)
    n_urls = sum(len(v) for v in sl_race_urls.values())
    if verbose:
        print(f"  [form] SL: {n_urls} race URLs | Racing API: {'enabled' if api_key else 'no key — skipping'}")

    all_sl_urls = []
    seen_urls: set = set()
    for race in races:
        venue = race.get('course') or race.get('venue') or ''
        vs = _venue_slug(venue)
        sl_urls = sl_race_urls.get(vs, [])
        if not sl_urls:
            for sl_venue, urls in sl_race_urls.items():
                if vs and (vs in sl_venue or sl_venue in vs):
                    sl_urls = urls
                    break
        for u in sl_urls:
            if u not in seen_urls:
                seen_urls.add(u)
                all_sl_urls.append(u)

    # ── Fan-out: SL pages + Racing API call run simultaneously ────────────────
    if verbose:
        sources = f"SL ({len(all_sl_urls)} pages)"
        if api_key:
            sources += " + Racing API"
        print(f"  [form] Fan-out: {sources}…")

    with ThreadPoolExecutor(max_workers=2) as outer_pool:
        sl_future  = outer_pool.submit(_sl_fan_out, all_sl_urls)
        ra_future  = outer_pool.submit(fetch_racing_api_form, today, api_key)

        sl_form, sl_tf, sl_ids = sl_future.result()
        ra_form = ra_future.result()

    # ── Merge: SL form into cache ─────────────────────────────────────────────
    _today_form.update(sl_form)
    _today_tf_stars.update(sl_tf)
    for name, h_id in sl_ids.items():
        if name not in _sl_id_map:
            _sl_id_map[name] = h_id
            _sl_ids_dirty = True
    _save_sl_ids()

    # ra_form now contains {horse_name: ra_runner_dict} (structured racecard data,
    # NOT individual run lists). It is NOT merged into _today_form (which holds run lists).
    # Instead it is injected directly onto each runner as runner['ra_data'].

    if verbose:
        print(f"  [form] SL form pool: {len(sl_form)} horses | "
              f"Racing API Pro racecard: {len(ra_form)} runners | "
              f"Total SL cache: {len(_today_form)} horses")

    # ── Inject form_runs + ra_data + timeform_stars into each runner ──────────
    total_horses = sum(len(r.get('runners', [])) for r in races)
    enriched   = 0
    tf_count   = 0
    ra_injected = 0
    for race in races:
        for runner in race.get('runners', []):
            name = runner.get('name') or runner.get('horse') or ''
            if not name:
                continue
            name_clean = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', name).strip()
            name_key = name_clean.lower()

            # SL form runs (individual race history)
            runs = fetch_form(name_clean)
            runner['form_runs'] = runs
            if runs:
                enriched += 1
                runner['form_source'] = 'sl'

            # Racing API Pro racecard data — injected for ALL runners (C/D flags,
            # live trainer form, RPR, last_run_days etc.)
            ra_data = ra_form.get(name_key)
            if ra_data:
                runner['ra_data'] = ra_data
                ra_injected += 1

            tf = _today_tf_stars.get(name_key)
            if tf:
                runner['timeform_stars'] = tf
                tf_count += 1

    if verbose:
        pct = round(100 * enriched / total_horses) if total_horses else 0
        print(f"  [form] SL form_runs: {enriched}/{total_horses} ({pct}%) | "
              f"Racing API ra_data: {ra_injected}/{total_horses} | "
              f"Timeform stars: {tf_count}")
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
        # Current form quality signals
        'won_last_2_runs': False,  # won in either of last 2 races — horse is IN form right now
        'runs_since_last_win': None,  # count of runs without a win; None = no run history
        'form_trend_improving': False,  # positions improving across last 3 runs (e.g. 6→3→1)
        'form_trend_declining': False,  # positions declining across last 3 runs (e.g. 1→3→6)
        'or_above_field': False,  # horse's current OR is highest or near-highest in recent fields
    }

    # ── Racing API Pro data — augments or substitutes form_runs signals ───────
    # Available for ALL runners (even those without SL form_runs).
    # C/D flags from theracingapi.com are authoritative — pre-computed from full history.
    ra = horse_data.get('ra_data', {})
    if ra:
        flags = ra.get('past_results_flags', '')

        # last_run_days: RA is more reliable than computed from form_runs dates
        if ra.get('last_run_days') is not None:
            ld = int(ra['last_run_days'])
            signals['days_since_last_run'] = ld
            signals['fresh_days_optimal']  = 14 <= ld <= 35

        # C/D flags — only set from RA if form_runs haven't already fired them
        # (avoids double-counting on the ~86% of horses that have SL data too)
        if 'C' in flags and not signals['exact_course_win']:
            signals['exact_course_win']  = True
            signals['course_win_count']  = max(signals['course_win_count'], 1)
        if 'D' in flags and not signals['exact_distance_win']:
            signals['exact_distance_win']  = True
            signals['distance_win_count']  = max(signals['distance_win_count'], 1)

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

    # Won in last 2 runs — horse is in winning form RIGHT NOW
    for _ri in range(min(2, len(runs))):
        if runs[_ri].get('position') == 1:
            signals['won_last_2_runs'] = True
            break

    # Runs since last win — number of runs without winning (None if no history)
    _runs_since_win = 0
    _found_win = False
    for _run in runs:
        if _run.get('position') == 1:
            _found_win = True
            break
        _runs_since_win += 1
    signals['runs_since_last_win'] = _runs_since_win if _found_win else (len(runs) if runs else None)

    # Form trend — improving or declining over last 3 runs
    _last3_pos = [r.get('position') for r in runs[:3] if isinstance(r.get('position'), int)]
    if len(_last3_pos) >= 3:
        # Improving: positions numerically DECREASING (1 is better than 6)
        # e.g. [2, 4, 7] means most recent (index 0) = 2nd, previous = 4th, oldest = 7th → improving
        signals['form_trend_improving'] = (
            _last3_pos[0] < _last3_pos[1] < _last3_pos[2]
            and _last3_pos[0] <= 4  # must be placing well in most recent
        )
        signals['form_trend_declining'] = (
            _last3_pos[0] > _last3_pos[1] > _last3_pos[2]
            and _last3_pos[0] >= 4  # must be placing poorly in most recent
        )

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

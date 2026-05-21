"""
Sporting Life Results Fetcher
=============================
Fetches race results from sportinglife.com and records WIN/LOSS for pending picks.

PRIMARY source: sportinglife.com/racing/fast-results/all
  - Single page, clean JSON (__NEXT_DATA__), updates as soon as weighed-in
  - Provides winner + placed horses instantly, no HTML scraping per race
  - Polled every 30 minutes by Windows Task Scheduler

FALLBACK: /racing/results/{date}/{course}/{id}/... per-race HTML pages
  - Used only if a race is not yet in fast-results (e.g. older dates)
  - Slower but gives full finishing order

Usage:
    python sl_results_fetcher.py              # today
    python sl_results_fetcher.py 2026-03-20   # specific date
"""

import re
import sys
import json
import requests
import boto3
from html import unescape
from datetime import date, datetime
from core.enrichment.betfair_fetcher import get_betfair_session, fetch_betfair_sp
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

# ── UK DST helper ─────────────────────────────────────────────────────────────
def _to_uk_local_hhmm(utc_hhmm: str, race_date_str: str) -> str:
    """Convert a UTC HH:MM time string to UK local time (BST = UTC+1 in summer).

    SL results pages display local (BST) times, but race_time in DynamoDB is
    stored as UTC.  This converter lets us compare them correctly.
    """
    try:
        h, mn = map(int, utc_hhmm.split(':'))
        d = datetime.strptime(race_date_str[:10], '%Y-%m-%d').date()
        year = d.year
        # BST starts last Sunday in March
        bst_start = date(year, 3, 31)
        while bst_start.weekday() != 6:   # 6 = Sunday
            bst_start = date(bst_start.year, bst_start.month, bst_start.day - 1)
        # BST ends last Sunday in October
        bst_end = date(year, 10, 31)
        while bst_end.weekday() != 6:
            bst_end = date(bst_end.year, bst_end.month, bst_end.day - 1)
        if bst_start <= d < bst_end:
            total_mins = h * 60 + mn + 60   # add 1 hour for BST
            return f'{(total_mins // 60) % 24:02d}:{total_mins % 60:02d}'
        return utc_hhmm
    except Exception:
        return utc_hhmm

try:
    from sl_racecard_fetcher import get_cached_racecard as _get_racecard
    from sl_racecard_fetcher import fetch_race_detail as _fetch_sl_race_detail
    _RACECARD_AVAILABLE = True
    _SL_RACE_DETAIL_AVAILABLE = True
except Exception:
    _RACECARD_AVAILABLE = False
    _SL_RACE_DETAIL_AVAILABLE = False

sys.stdout.reconfigure(encoding='utf-8')

# ── Config ────────────────────────────────────────────────────────────────────
TARGET_DATE = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime('%Y-%m-%d')

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.sportinglife.com/',
}

# SL URL slug  →  DB course name
COURSE_MAP = {
    'musselburgh': 'Musselburgh', 'lingfield': 'Lingfield',
    'newbury': 'Newbury', 'wolverhampton': 'Wolverhampton',
    'cheltenham': 'Cheltenham', 'kempton': 'Kempton',
    'ascot': 'Ascot', 'haydock': 'Haydock',
    'sandown': 'Sandown', 'chester': 'Chester',
    'goodwood': 'Goodwood', 'york': 'York',
    'leicester': 'Leicester', 'nottingham': 'Nottingham',
    'carlisle': 'Carlisle', 'catterick': 'Catterick',
    'newcastle': 'Newcastle', 'hamilton': 'Hamilton',
    'perth': 'Perth', 'ayr': 'Ayr',
    'wetherby': 'Wetherby', 'doncaster': 'Doncaster',
    'exeter': 'Exeter', 'taunton': 'Taunton',
    'hereford': 'Hereford', 'huntingdon': 'Huntingdon',
    'ludlow': 'Ludlow', 'market-rasen': 'Market Rasen',
    'plumpton': 'Plumpton', 'stratford': 'Stratford',
    'uttoxeter': 'Uttoxeter', 'windsor': 'Windsor',
    'wincanton': 'Wincanton', 'ffos-las': 'Ffos Las',
    'sedgefield': 'Sedgefield', 'southwell': 'Southwell',
    'bangor': 'Bangor', 'worcester': 'Worcester',
    'warwick': 'Warwick', 'bath': 'Bath',
    'chepstow': 'Chepstow', 'epsom': 'Epsom',
    'pontefract': 'Pontefract', 'ripon': 'Ripon',
    'redcar': 'Redcar', 'beverley': 'Beverley',
    'thirsk': 'Thirsk', 'brighton': 'Brighton',
}

SL_BASE = 'https://www.sportinglife.com'

# ── Helpers ───────────────────────────────────────────────────────────────────
def norm(name: str) -> str:
    """Normalise horse name for comparison: lower, strip country code."""
    n = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', name or '').strip().lower()
    return n
def norm_course(name: str) -> str:
    """Normalise course name for comparison: lower, replace hyphens/dashes with spaces."""
    return (name or '').lower().replace('-', ' ').strip()
def _to_frac(dec: float) -> str:
    """Convert decimal odds to fractional string for display."""
    if not dec or dec <= 1:
        return str(dec)
    num = round((dec - 1) * 4)
    den = 4
    from math import gcd
    g = gcd(num, den)
    return f'{num//g}/{den//g}'
def fetch(url: str) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.text
        print(f"  HTTP {r.status_code}: {url}")
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
    return None


def _to_slug(text: str) -> str:
    s = (text or '').lower().strip()
    s = re.sub(r'&', ' and ', s)
    s = re.sub(r'[^a-z0-9\s\-]', '', s)
    s = re.sub(r'\s+', '-', s)
    return re.sub(r'-{2,}', '-', s).strip('-')


def _clean_html_text(raw_html: str) -> str:
    if not raw_html:
        return ''
    txt = re.sub(r'<[^>]+>', '', raw_html)
    txt = unescape(txt)
    return re.sub(r'\s+', ' ', txt).strip()


def _extract_loss_commentary_flags(text: str) -> list[str]:
    """Derive normalized loss-reason flags from Sporting Life narrative text."""
    if not text:
        return []
    t = text.lower()
    flags = []
    rules = {
        'jumping_error': ['not fluent', 'mistake', 'blunder', 'jumped left', 'jumped right', 'pecked', 'bad jump'],
        'stamina_faded': ['weakened', 'faded', 'tired', 'no extra', 'one pace', 'outstayed'],
        'outpaced_midrace': ['outpaced', 'lost place', 'could not go pace', 'paced'],
        'ran_prominent_flattened': ['led', 'headed', 'kept on but', 'always held', 'prominent'],
        'interference_or_traffic': ['hampered', 'bumped', 'squeezed', 'blocked', 'short of room', 'checked'],
        'never_travelling': ['never dangerous', 'never involved', 'always behind', 'detached', 'struggled'],
    }
    for flag, needles in rules.items():
        if any(n in t for n in needles):
            flags.append(flag)
    # Preserve insertion order while de-duplicating
    return list(dict.fromkeys(flags))


def _loss_model_hints_from_flags(flags: list[str]) -> list[str]:
    """Map commentary flags to conservative model-adjustment hints."""
    hints = []
    if 'jumping_error' in flags:
        hints.append('increase_recent_non_completion_penalty')
    if 'outpaced_midrace' in flags:
        hints.append('increase_market_divergence_penalty')
    if 'stamina_faded' in flags or 'ran_prominent_flattened' in flags:
        hints.append('increase_score_gap_illusion_penalty')
    if 'interference_or_traffic' in flags:
        hints.append('mark_high_variance_race_shape')
    return hints

# ── Step 1: Get completed race URLs from results index ─────────────────────────
def get_race_urls(date_str):
    """Return list of (course_slug, course_name, race_id, race_url)."""
    idx_url = f'{SL_BASE}/racing/results/{date_str}/'
    print(f"Fetching results index: {idx_url}")
    html = fetch(idx_url)
    if not html:
        return []

    # Extract the FULL race links from the index - pattern:
    # href="/racing/results/2026-03-20/musselburgh/908670/race-name-slug"
    pat = r'href="(/racing/results/' + re.escape(date_str) + r'/([^/]+)/(\d+)/[^"]+)"'
    seen = set()
    races = []
    for m in re.finditer(pat, html):
        full_path, course_slug, race_id = m.group(1), m.group(2), m.group(3)
        key = (course_slug, race_id)
        if key in seen:
            continue
        seen.add(key)
        course_name = COURSE_MAP.get(course_slug, course_slug.replace('-', ' ').title())
        race_url = SL_BASE + full_path
        races.append((course_slug, course_name, race_id, race_url))

    print(f"  Found {len(races)} completed race(s)")
    return races

# ── Step 2: Parse winner + all runners in finishing order ─────────────────────
def parse_race_result(race_url):
    """Return (off_time_HHMM, winner_name, all_runners_list) or (None, None, [])."""
    html = fetch(race_url)
    if not html:
        return None, None, []

    # Off time
    off_m = re.search(r'Off time:\s*(\d{1,2}:\d{2})', html)
    off_time = off_m.group(1).zfill(5) if off_m else None   # ensure HH:MM

    # ── All runners in finishing order ────────────────────────────────────────
    # SL React component lists ResultRunner__StyledHorseName in finish order
    all_runners = [
        m.strip() for m in re.findall(
            r'ResultRunner__StyledHorseName[^"]*"[^>]*>'
            r'<a\s+href="/racing/profiles/horse/\d+"[^>]*>([^<]+)</a>',
            html
        )
    ]
    winner = all_runners[0] if all_runners else None

    # 2) Fallback: any horse profile link near a "1" position indicator
    if not winner:
        snippets = re.findall(
            r'(?:>1\s*</|position["\'][^>]*>1[^0-9<][^<]{0,100})'
            r'.{0,600}?/racing/profiles/horse/\d+"[^>]*>([^<]+)</a>',
            html, re.DOTALL
        )
        for s in snippets:
            candidate = s.strip()
            if len(candidate) > 2:
                winner = candidate
                break

    # 3) JSON-LD structured data
    if not winner:
        for block in re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL):
            try:
                data = json.loads(block)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    w = item.get('winner', {})
                    if isinstance(w, dict) and w.get('name'):
                        winner = w['name']
                        break
            except Exception:
                pass
            if winner:
                break

    # 4) og:description  "HorseName won the RaceName"
    if not winner:
        for attr in ('og:description', 'twitter:description'):
            for pattern in [
                r'<meta[^>]+(?:name|property)=["\']' + re.escape(attr) + r'["\'][^>]+content=["\']([^"\']*)["\']',
                r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+(?:name|property)=["\']' + re.escape(attr) + r'["\']',
            ]:
                m = re.search(pattern, html, re.IGNORECASE)
                if m:
                    wm = re.match(r'^([A-Z][^\.]+?)\s+won\b', m.group(1))
                    if wm:
                        winner = wm.group(1).strip()
                        break
            if winner:
                break

    return off_time, winner, all_runners

# ── Step 2b: Fast Results page — primary, rapid source ────────────────────────
FAST_RESULTS_URL = 'https://www.sportinglife.com/racing/fast-results/all'

def _strip_country(name: str) -> str:
    """Remove country code suffix: 'Khrisma (IRE)' → 'Khrisma'"""
    return re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', name or '').strip()

def fetch_fast_results():
    """
    Fetch fast-results page and return a race_results dict in the same format
    used by the per-page scraper:
        { course_lower: [(minutes_since_midnight, winner_name, off_time_str, top_horses_list)] }

    top_horses_list = [horse_name, ...] sorted by finish position (1st first).
    Only placed horses (typically 1–3) are available; unplaced finishers are absent.
    Returns an empty dict on failure.
    """
    html = fetch(FAST_RESULTS_URL)
    if not html:
        return {}

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        print("  [fast-results] __NEXT_DATA__ not found")
        return {}

    try:
        data = json.loads(m.group(1))
    except Exception as e:
        print(f"  [fast-results] JSON parse error: {e}")
        return {}

    fast = data.get('props', {}).get('pageProps', {}).get('fastResults', [])
    print(f"  [fast-results] {len(fast)} races in feed")

    race_results = {}
    race_details = {}    # (course_lower, off_time) → enriched race metadata
    for fr in fast:
        top_horses = fr.get('top_horses')
        if not top_horses:
            continue                        # result not yet available
        course = fr.get('courseName', '')
        off_time = fr.get('time', '')       # 'HH:MM' local
        if not course or not off_time:
            continue

        try:
            h, mn = map(int, off_time.split(':'))
        except ValueError:
            continue
        mins = h * 60 + mn

        # Build all_runners list sorted by position — strip country codes
        sorted_horses = sorted(top_horses, key=lambda x: x.get('position', 99))
        all_runners = [_strip_country(h2.get('horse_name', '')) for h2 in sorted_horses]
        winner = all_runners[0] if all_runners else None
        if not winner:
            continue

        key = norm_course(course)
        if key not in race_results:
            race_results[key] = []
        # Avoid duplicate entries
        if not any(abs(existing_mins - mins) < 1 for existing_mins, _, _, _ in race_results[key]):
            race_results[key].append((mins, winner, off_time, all_runners))
            print(f"    [fast] {off_time} {course} \u2192 {winner} ({len(all_runners)} placed horses listed)")

            # Build per-horse draw and SP map for analysis
            draw_map = {_strip_country(h2.get('horse_name', '')): h2.get('draw_number') for h2 in sorted_horses}
            sp_map   = {_strip_country(h2.get('horse_name', '')): h2.get('odds', '') for h2 in sorted_horses}
            fav_map  = {_strip_country(h2.get('horse_name', '')): bool(h2.get('favourite')) for h2 in sorted_horses}

            race_details[(key, off_time)] = {
                'race_name':        fr.get('name', ''),
                'race_reference_id': ((fr.get('race_reference') or {}).get('id')),
                'meeting_reference_id': ((fr.get('meeting_reference') or {}).get('id')),
                'race_slug':        fr.get('slug', ''),
                'distance':         fr.get('distance', ''),
                'race_class':       str(fr.get('race_class', '')),
                'age_band':         fr.get('age', ''),
                'has_handicap':     fr.get('has_handicap', False),
                'runners':          fr.get('runners'),
                'non_runners':      len(fr.get('non_runners', [])),
                'tote_win':         fr.get('tote_win', ''),
                'tote_place':       fr.get('place_win', ''),
                'exacta_win':       fr.get('exacta_win', ''),
                'tricast_win':      fr.get('tricast', ''),
                'trifecta_win':     fr.get('trifecta', ''),
                'swingers':         fr.get('swingers', ''),
                'straight_forecast':fr.get('straight_forecast', ''),
                'distances_margins':fr.get('distances', ''),
                'stewards':         fr.get('stewards', ''),
                'status':           fr.get('status', ''),
                'draw_map':         draw_map,
                'sp_map':           sp_map,
                'fav_map':          fav_map,
            }

    return race_results, race_details


# ── Step 3: Match race results against pending DynamoDB picks ──────────────────
def update_results(date_str):
    db = boto3.resource('dynamodb', region_name='eu-west-1')
    t = db.Table('SureBetBets')

    # Get all racing rows for the date, not just UI picks.
    resp = t.query(
        KeyConditionExpression=Key('bet_date').eq(date_str)
    )
    picks = resp.get('Items', [])
    while resp.get('LastEvaluatedKey'):
        resp = t.query(
            KeyConditionExpression=Key('bet_date').eq(date_str),
            ExclusiveStartKey=resp['LastEvaluatedKey']
        )
        picks.extend(resp.get('Items', []))

    def _is_racing_row(item):
        sport = str(item.get('sport') or 'horses').strip().lower()
        return (
            item.get('race_time')
            and str(item.get('course') or '').strip()
            and (item.get('horse') or item.get('horse_name'))
            and sport in ('horses', 'horse racing', '')
        )

    picks = [p for p in picks if _is_racing_row(p)]
    # Process picks that are unresolved: no outcome, explicitly 'pending', or old-format ('WON'/'LOST').
    # Do not re-settle already resolved picks, to avoid accidental rematching to the wrong race.
    UNRESOLVED = {'pending', 'PENDING', 'WON', 'LOST', 'LOSS'}
    pending = [p for p in picks if not p.get('outcome') or p.get('outcome') in UNRESOLVED]
    if not pending:
        print(f"\nAll picks already settled with new format for {date_str}")
        return

    print(f"\n{len(pending)} pending racing row(s) to resolve:")
    for p in pending:
        horse = p.get('horse') or p.get('horse_name', '?')
        rt = p.get('race_time', '')[:16].replace('T', ' ')
        print(f"  - {horse} @ {p.get('course','?')} {rt}")

    # Build lookup: course_name_lower → list of (off_time_minutes, winner, all_runners)
    # We match against DB pick time with ±15 min window
    race_results = {}   # course_lower → list[(minutes_since_midnight, winner, off_time, all_runners)]
    fast_race_details = {}  # (course_lower, off_time) → enriched race metadata

    # ── PRIMARY: fast-results page (single fetch, rapid) ─────────────────────
    print(f"\nFetching fast-results feed (primary)...")
    race_results, fast_race_details = fetch_fast_results()

    # ── Load racecard cache for trainer/jockey lookups ────────────────────────
    racecard_cache = {}
    if _RACECARD_AVAILABLE:
        try:
            rc_raw = _get_racecard(date_str)
            # Build flat lookup: norm(horse_name) → {trainer, jockey, draw, odds, form}
            for _course, _races in rc_raw.items():
                for _race in _races:
                    for _runner in _race.get('runners', []):
                        hn = norm(_runner.get('horse', ''))
                        if hn:
                            racecard_cache[hn] = {
                                'trainer': _runner.get('trainer', ''),
                                'jockey':  _runner.get('jockey', ''),
                                'draw':    _runner.get('draw'),
                                'form':    _runner.get('form', ''),
                                'odds':    _runner.get('odds', ''),
                                'weight':  _runner.get('weight', ''),
                                'official_rating': _runner.get('official_rating'),
                                'timeform_stars':  _runner.get('timeform_stars'),
                                'rating123':       _runner.get('rating123'),
                            }
        except Exception as _e:
            print(f"  [racecard cache] {_e}")

    # ── FALLBACK: per-race HTML pages for any race not yet in fast-results ────
    # Determine which pending picks still have no result from the fast feed
    def _find_in_results(course, hhmm, window_min=15, results_dict=None):
        if results_dict is None:
            results_dict = race_results
        try:
            h, mn = map(int, hhmm.split(':'))
        except ValueError:
            return None, None, []
        target = h * 60 + mn
        for mins, winner, off_time, all_runners in results_dict.get(norm_course(course), []):
            if abs(mins - target) <= window_min:
                return winner, off_time, all_runners
        return None, None, []

    unresolved_courses_dates = set()
    for pick in pending:
        race_time_raw = pick.get('race_time', '')
        tm_m = re.search(r'(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})', race_time_raw)
        if not tm_m:
            continue
        race_date, race_hhmm = tm_m.group(1), tm_m.group(2)
        course = pick.get('course', '').strip()
        # The SL fast-results JSON 'time' field is UTC, matching DB storage.
        # Try the raw UTC hhmm first; then try BST-converted for HTML-fallback pages.
        local_hhmm = _to_uk_local_hhmm(race_hhmm, race_date)
        w, _, _ = _find_in_results(course, race_hhmm)   # fast-results: UTC
        if not w:
            w, _, _ = _find_in_results(course, local_hhmm)  # HTML fallback: BST
        if not w:
            unresolved_courses_dates.add(race_date)

    if unresolved_courses_dates:
        print(f"\nFallback: scraping per-race pages for {sorted(unresolved_courses_dates)}...")
    for fb_date in sorted(unresolved_courses_dates):
        races = get_race_urls(fb_date)
        print(f"  Fetching individual race pages for {fb_date} ({len(races)} races)...")
        for course_slug, course_name, race_id, race_url in races:
            off_time, winner, all_runners = parse_race_result(race_url)
            if off_time and winner:
                h, mn = map(int, off_time.split(':'))
                mins = h * 60 + mn
                key = norm_course(course_name)
                if key not in race_results:
                    race_results[key] = []
                if not any(abs(m3 - mins) < 1 for m3, _, _, _ in race_results[key]):
                    race_results[key].append((mins, winner, off_time, all_runners))
                    print(f"    {course_name} {off_time}  →  {winner} ({len(all_runners)} runners)")

    def find_result(course: str, hhmm: str, window_min=15):
        """Find winner + all runners by course + approximate time."""
        return _find_in_results(course, hhmm, window_min)

    # Match and update
    print(f"\n{'='*55}")

    # Lazy cache for richer race-level/runner-level comments from SL race pages
    sl_detail_cache = {}  # (course_norm, off_time) -> {'race_verdict': str, 'horse_map': dict}

    def _get_sl_detail(course_name: str, off_time: str, race_meta: dict) -> dict:
        key = (norm_course(course_name), off_time)
        if key in sl_detail_cache:
            return sl_detail_cache[key]
        sl_detail_cache[key] = {}

        if not _SL_RACE_DETAIL_AVAILABLE or not race_meta:
            return sl_detail_cache[key]

        race_id = race_meta.get('race_reference_id')
        race_name = race_meta.get('race_name', '')
        if not race_id:
            return sl_detail_cache[key]

        try:
            race_detail = _fetch_sl_race_detail(
                date_str,
                _to_slug(course_name),
                int(race_id),
                race_name,
            )
        except Exception as _e:
            print(f"  [sl detail] {course_name} {off_time}: {_e}")
            return sl_detail_cache[key]

        if not race_detail:
            return sl_detail_cache[key]

        rs = race_detail.get('race_summary') or {}
        rides = race_detail.get('rides') or []
        horse_map = {}
        for ride in rides:
            hname = ((ride.get('horse') or {}).get('name') or '').strip()
            if not hname:
                continue
            horse_map[norm(hname)] = {
                'commentary': (ride.get('commentary') or '').strip(),
                'ride_description': (ride.get('ride_description') or '').strip(),
                'finish_position': ride.get('finish_position'),
            }

        sl_detail_cache[key] = {
            'race_verdict': _clean_html_text(rs.get('verdict', '') or ''),
            'horse_map': horse_map,
        }
        return sl_detail_cache[key]

    # ── Betfair session for SP lookups (one login for all picks) ──────────────
    _bf_app_key, _bf_session = None, None
    _bf_sp_cache = {}   # market_id → {runner_name: bsp}
    try:
        _bf_app_key, _bf_session = get_betfair_session()
        print(f"  [betfair_sp] Session ready for SP lookups")
    except Exception as _e:
        print(f"  [betfair_sp] No Betfair session — SP will come from SL only: {_e}")

    updated = 0
    for pick in pending:
        horse = pick.get('horse') or pick.get('horse_name', '')
        course = pick.get('course', '').strip()
        race_time_raw = pick.get('race_time', '')   # ISO e.g. "2026-03-20T15:22:00.000Z"
        bet_id = pick['bet_id']
        odds = float(pick.get('odds', 0))
        stake = float(pick.get('bet_amount', 6))

        # Extract date and HH:MM from race_time (ISO format)
        tm_m = re.search(r'(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})', race_time_raw)
        if not tm_m:
            print(f"  [SKIP] {horse} – can't parse time from {race_time_raw}")
            continue
        race_date, race_hhmm = tm_m.group(1), tm_m.group(2)
        # Convert UTC race time → UK local (BST/GMT) for HTML-fallback pages.
        # Fast-results feed uses UTC, so try both.
        local_hhmm = _to_uk_local_hhmm(race_hhmm, race_date)

        winner, actual_off, all_runners = find_result(course, race_hhmm)   # fast-results: UTC
        if not winner:
            winner, actual_off, all_runners = find_result(course, local_hhmm)  # HTML fallback: BST

        if not winner:
            print(f"  [SKIP] {horse} @ {course} {race_hhmm} (local:{local_hhmm}) – no result found")
            continue

        # Find our horse's finishing position (1-based)
        finish_pos = None
        for i, r in enumerate(all_runners):
            if norm(r) == norm(horse):
                finish_pos = i + 1
                break

        # If our pick not found in results, skip (results may be incomplete or horse name mismatch)
        if finish_pos is None:
            print(f"  [SKIP] {horse} @ {course} {race_hhmm} – not found in results (winner was {winner})")
            continue

        total_runners = len(all_runners)

        # ── Enrich: fetch race details from fast-results meta ─────────────────
        _rd = fast_race_details.get((norm_course(course), actual_off or race_hhmm), {})
        # Fallback: search by approximate time match
        if not _rd:
            for (c_key, t_key), v in fast_race_details.items():
                if c_key == norm_course(course):
                    try:
                        th, tm2 = map(int, t_key.split(':'))
                        rh, rm2 = map(int, race_hhmm.split(':'))
                        if abs(th * 60 + tm2 - rh * 60 - rm2) <= 15:
                            _rd = v
                            break
                    except ValueError:
                        pass

        # Winner trainer/jockey from racecard cache
        winner_rc = racecard_cache.get(norm(winner), {})
        winner_trainer = winner_rc.get('trainer', '')
        winner_jockey  = winner_rc.get('jockey', '')
        winner_draw    = _rd.get('draw_map', {}).get(winner)
        winner_sp      = _rd.get('sp_map', {}).get(winner, '')

        # Determine outcome based on position
        if finish_pos == 1:
            outcome_lc   = 'win'
            result_emoji = 'WIN'
            profit = round((odds - 1) * stake, 2)
            pos_label    = '1st'
            analysis     = f'Won at {_to_frac(odds)} ({total_runners} runners)'
        elif finish_pos in (2, 3):
            outcome_lc   = 'placed'
            result_emoji = 'PLACED'
            profit = -round(stake, 2)   # WIN bet — stake lost; each-way would differ
            pos_label    = '2nd' if finish_pos == 2 else '3rd'
            analysis     = f'{pos_label} of {total_runners}, winner: {winner}'
        else:
            outcome_lc   = 'loss'
            result_emoji = 'LOSS'
            profit = -round(stake, 2)
            pos_label    = f'{finish_pos}th' if finish_pos else 'Unplaced'
            analysis     = f'{pos_label} of {total_runners}, winner: {winner}' if finish_pos else f'Unplaced, winner: {winner}'

        icon = '✅' if outcome_lc == 'win' else ('🥈' if outcome_lc == 'placed' else '❌')
        print(f"  {icon} {result_emoji:<7} | {horse:<30} | {pos_label} | Winner: {winner:<25} | P&L: {profit:+.2f}")

        # ── Betfair SP for our horse (prefer BSP over SL scraped SP) ──────────
        pick_sp_odds = None
        pick_market_id = pick.get('market_id', '')
        if pick_market_id and _bf_session:
            if pick_market_id not in _bf_sp_cache:
                _bf_sp_cache[pick_market_id] = fetch_betfair_sp(
                    _bf_app_key, _bf_session, pick_market_id)
            bf_sp_map = _bf_sp_cache[pick_market_id]
            # Match our horse name (case-insensitive)
            for sp_name, sp_val in bf_sp_map.items():
                if sp_name.strip().lower() == horse.strip().lower():
                    pick_sp_odds = sp_val
                    break
            if pick_sp_odds:
                # Recalculate profit using actual SP
                if outcome_lc == 'win':
                    profit = round((pick_sp_odds - 1) * stake, 2)
                    analysis = f'Won at BSP {pick_sp_odds:.2f} ({total_runners} runners)'
                print(f"    → Betfair SP: {pick_sp_odds:.2f}" +
                      (f"  (profit recalc: {profit:+.2f})" if outcome_lc == 'win' else ''))

        # Our pick's own racecard data (for learning/analysis)
        our_rc = racecard_cache.get(norm(horse), {})
        if our_rc.get('trainer'):
            pass   # will add below in extra_expr

        extra_expr = ''
        extra_vals = {}
        # Our pick's trainer/jockey/form/timeform
        if our_rc.get('trainer'):
            extra_expr += ', pick_trainer = :pt'
            extra_vals[':pt'] = our_rc['trainer']
        if our_rc.get('jockey'):
            extra_expr += ', pick_jockey = :pj'
            extra_vals[':pj'] = our_rc['jockey']
        if our_rc.get('form'):
            extra_expr += ', pick_form = :pf'
            extra_vals[':pf'] = our_rc['form']
        if our_rc.get('timeform_stars') is not None:
            extra_expr += ', pick_timeform_stars = :ptf'
            extra_vals[':ptf'] = our_rc['timeform_stars']
        if our_rc.get('rating123') is not None:
            extra_expr += ', pick_rating123 = :pr123'
            extra_vals[':pr123'] = our_rc['rating123']
        if winner_trainer:
            extra_expr += ', winner_trainer = :wt'
            extra_vals[':wt'] = winner_trainer
        if winner_jockey:
            extra_expr += ', winner_jockey = :wj'
            extra_vals[':wj'] = winner_jockey
        if winner_draw is not None:
            extra_expr += ', winner_draw = :wd'
            extra_vals[':wd'] = winner_draw
        if winner_sp:
            extra_expr += ', winner_sp = :wsp'
            extra_vals[':wsp'] = winner_sp
        # Store Betfair SP for our pick + CLV
        if pick_sp_odds:
            extra_expr += ', sp_odds = :sp'
            extra_vals[':sp'] = Decimal(str(round(pick_sp_odds, 2)))
            # CLV: positive = we got better odds than SP (genuine value)
            _opening = float(pick.get('opening_price') or pick.get('odds') or 0)
            if _opening > 0 and pick_sp_odds > 0:
                _clv_delta = round(_opening - pick_sp_odds, 3)
                extra_expr += ', clv_delta = :clv, clv_positive = :clvp'
                extra_vals[':clv'] = Decimal(str(_clv_delta))
                extra_vals[':clvp'] = _clv_delta > 0
        if _rd.get('race_name'):
            extra_expr += ', race_name_result = :rn'
            extra_vals[':rn'] = _rd['race_name']
        if _rd.get('tote_win'):
            extra_expr += ', tote_win = :tw'
            extra_vals[':tw'] = _rd['tote_win']
        if _rd.get('tote_place'):
            extra_expr += ', tote_place = :tp'
            extra_vals[':tp'] = _rd['tote_place']
        if _rd.get('exacta_win'):
            extra_expr += ', exacta_win = :ex'
            extra_vals[':ex'] = _rd['exacta_win']
        if _rd.get('tricast_win'):
            extra_expr += ', tricast_win = :tc'
            extra_vals[':tc'] = _rd['tricast_win']
        if _rd.get('distances_margins'):
            extra_expr += ', winning_margins = :dm'
            extra_vals[':dm'] = _rd['distances_margins']
        if _rd.get('non_runners') is not None:
            extra_expr += ', non_runners_count = :nr'
            extra_vals[':nr'] = _rd['non_runners']
        if _rd.get('race_class'):
            extra_expr += ', race_class_result = :rc'
            extra_vals[':rc'] = str(_rd['race_class'])
        if _rd.get('distance'):
            extra_expr += ', distance_result = :dr'
            extra_vals[':dr'] = _rd['distance']

        # Enrich settled picks with race narrative text for future model analysis
        _sl_off = actual_off or race_hhmm
        _sl_detail = _get_sl_detail(course, _sl_off, _rd) if _sl_off else {}
        _horse_detail = (_sl_detail.get('horse_map') or {}).get(norm(horse), {}) if _sl_detail else {}
        _race_verdict = _sl_detail.get('race_verdict', '') if _sl_detail else ''

        if _race_verdict:
            extra_expr += ', race_verdict = :rv'
            extra_vals[':rv'] = _race_verdict[:2000]
        if _horse_detail.get('commentary'):
            extra_expr += ', horse_commentary = :hc'
            extra_vals[':hc'] = _horse_detail['commentary'][:2000]
        if _horse_detail.get('ride_description'):
            extra_expr += ', horse_ride_description = :hrd'
            extra_vals[':hrd'] = _horse_detail['ride_description'][:1000]

        # For losses, persist structured reasons from Sporting Life commentary.
        if outcome_lc == 'loss':
            _loss_text_parts = [
                _horse_detail.get('commentary', ''),
                _horse_detail.get('ride_description', ''),
                _race_verdict,
            ]
            _loss_text = ' '.join(p for p in _loss_text_parts if p).strip()
            _loss_flags = _extract_loss_commentary_flags(_loss_text)
            _loss_hints = _loss_model_hints_from_flags(_loss_flags)

            if _loss_text:
                extra_expr += ', loss_commentary_text = :lct'
                extra_vals[':lct'] = _loss_text[:2000]
            if _loss_flags:
                extra_expr += ', loss_commentary_flags = :lcf'
                extra_vals[':lcf'] = _loss_flags[:12]
            if _loss_hints:
                extra_expr += ', loss_model_hints = :lmh'
                extra_vals[':lmh'] = _loss_hints[:8]

        t.update_item(
            Key={'bet_date': date_str, 'bet_id': bet_id},
            UpdateExpression=(
                'SET outcome = :o, result_emoji = :re, profit = :p, '
                'actual_result = :r, result_winner_name = :w, winner_name = :w, '
                'finish_position = :fp, result_analysis = :ra' + extra_expr
            ),
            ExpressionAttributeValues={
                ':o':  outcome_lc,
                ':re': result_emoji,
                ':p':  Decimal(str(profit)),
                ':r':  result_emoji,
                ':w':  winner,
                ':fp': finish_pos or 0,
                ':ra': analysis,
                **extra_vals,
            }
        )
        updated += 1

    print(f"\nUpdated {updated}/{len(pending)} pending picks")

    # Final summary
    resp2 = t.query(KeyConditionExpression=Key('bet_date').eq(date_str))
    all_picks = resp2['Items']
    while resp2.get('LastEvaluatedKey'):
        resp2 = t.query(
            KeyConditionExpression=Key('bet_date').eq(date_str),
            ExclusiveStartKey=resp2['LastEvaluatedKey']
        )
        all_picks.extend(resp2.get('Items', []))
    all_picks = [p for p in all_picks if _is_racing_row(p)]
    wins = sum(1 for p in all_picks if p.get('outcome') in ('win', 'WON'))
    places = sum(1 for p in all_picks if p.get('outcome') == 'placed')
    losses = sum(1 for p in all_picks if p.get('outcome') in ('loss', 'LOST', 'LOSS'))
    pending_count = sum(1 for p in all_picks if not p.get('outcome'))
    total_pnl = sum(float(p.get('profit', 0)) for p in all_picks)

    print(f"\n{'='*55}")
    print(f"=== {date_str} RESULTS SUMMARY ===")
    print(f"W:{wins}  Placed:{places}  L:{losses}  Pending:{pending_count}  |  P&L: {total_pnl:+.2f}")
    for p in sorted(all_picks, key=lambda x: x.get('race_time', '')):
        horse = p.get('horse') or p.get('horse_name', '?')
        outcome = p.get('outcome', 'PEND')
        emoji = p.get('result_emoji', '')
        pnl = float(p.get('profit', 0))
        course = p.get('course', '?')
        rt = str(p.get('race_time', ''))[:16]
        pos = p.get('finish_position', '')
        print(f"  {emoji or outcome:<8} | {horse:<30} | pos:{pos!s:<3} | {course:<15} | {rt} | {pnl:+.2f}")


if __name__ == '__main__':
    print(f"\n{'='*55}")
    print(f" Sporting Life Results Fetcher — {TARGET_DATE}")
    print(f"{'='*55}")
    update_results(TARGET_DATE)

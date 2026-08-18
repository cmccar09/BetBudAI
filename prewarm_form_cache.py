"""
Lambda: surebet-prewarm-form
============================
Schedule : EventBridge cron(0 23 * * ? *)  — 23:00 UTC every night
Input    : {} (no payload needed)
Output   : {"horses_cached": N, "date": "YYYY-MM-DD"}

Runs the night before racing day to pre-populate the S3 form cache so that
the 11:00 UTC analysis Lambda starts with near-complete form coverage rather
than fetching everything cold.

Steps:
  1. Call Racing API racecards/pro to get tomorrow's full declared field.
  2. For each runner:
       a. Fetch SL racecard form (fan-out across all SL race URLs).
       b. For runners SL missed, call Racing API /horses/{id}/results.
  3. Write merged form dict to s3://surebet-pipeline-data/form_cache/YYYY-MM-DD.json.

The analysis Lambda's form_enricher.enrich_runners() loads this cache first,
so SL scraping at 11:00 only needs to fill last-minute declarations.
"""

import os
import json
import base64
import re
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3

BUCKET = os.environ.get('PIPELINE_BUCKET', 'surebet-pipeline-data')
REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')

try:
    import requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False


# ---------------------------------------------------------------------------
# Shared helpers (duplicated here so this Lambda has no local import deps)
# ---------------------------------------------------------------------------

def _ra_headers(api_key: str) -> dict:
    encoded = base64.b64encode(api_key.encode()).decode()
    return {'Authorization': f'Basic {encoded}', 'Accept': 'application/json'}


def _http_get_json(url: str, headers: dict, timeout: int = 20):
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


_GOING_NORM = {
    'HY': 'Heavy', 'Hy': 'Heavy', 'SF': 'Soft', 'Sft': 'Soft',
    'GS': 'Good to Soft', 'GF': 'Good to Firm', 'GD': 'Good',
    'G': 'Good', 'Gd': 'Good', 'F': 'Firm', 'Fm': 'Firm',
    'SD': 'Slow', 'STD': 'Standard', 'AW': 'Standard',
}


def _norm_going(g: str) -> str:
    return _GOING_NORM.get(g, g)


def _dist_to_furlongs(dist_str: str):
    if not dist_str:
        return None
    s = str(dist_str).strip().lower()
    total = 0.0
    m = re.search(r'(\d+)m', s)
    if m:
        total += int(m.group(1)) * 8
    f = re.search(r'(\d+)f', s)
    if f:
        total += int(f.group(1))
    y = re.search(r'(\d+)y', s)
    if y:
        total += int(y.group(1)) / 220
    return round(total, 2) if total > 0 else None


def _safe_int(v):
    try:
        n = int(v)
        return n if n >= 0 else None
    except (TypeError, ValueError):
        return None


def _parse_beaten_lengths(s) -> float | None:
    if not s:
        return None
    s = str(s).lower().strip()
    if 'sh hd' in s or 'short' in s:
        return 0.1
    if s in ('hd', 'head'):
        return 0.2
    if s in ('nk', 'neck'):
        return 0.3
    m = re.match(r'^(\d+)\s+(\d+)/(\d+)', s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / int(m.group(3))
    m2 = re.match(r'^(\d+)/(\d+)', s)
    if m2:
        return int(m2.group(1)) / int(m2.group(2))
    m3 = re.match(r'^(\d+\.?\d*)', s)
    if m3:
        return float(m3.group(1))
    return None


# ---------------------------------------------------------------------------
# Racing API: tomorrow's racecards
# ---------------------------------------------------------------------------

def _fetch_racecards(api_key: str) -> list[dict]:
    """Fetch Pro racecards from Racing API — returns all runners for tomorrow."""
    hdrs = _ra_headers(api_key)
    # Racing API /racecards/pro defaults to today; use /racecards/standard with date param
    # for tomorrow. Try pro first (today if run at 23:00 = tomorrow's declarations), then
    # fall back to standard endpoint with explicit date.
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')

    # Try standard endpoint with explicit date
    data = _http_get_json(
        f'https://api.theracingapi.com/v1/racecards/standard?date={tomorrow}',
        hdrs,
    ) or _http_get_json(
        'https://api.theracingapi.com/v1/racecards/pro',
        hdrs,
    )
    return (data or {}).get('racecards', [])


# ---------------------------------------------------------------------------
# Racing API: single horse results
# ---------------------------------------------------------------------------

def _fetch_horse_results(horse_id: str, api_key: str, max_runs: int = 6) -> list[dict]:
    if not horse_id:
        return []
    hdrs = _ra_headers(api_key)
    data = _http_get_json(
        f'https://api.theracingapi.com/v1/horses/{horse_id}/results',
        hdrs,
        timeout=15,
    )
    if not data:
        return []
    runs = []
    for r in (data.get('results') or [])[:max_runs]:
        pos_raw = str(r.get('position') or '')
        try:
            pos = int(re.sub(r'[^0-9]', '', pos_raw) or '0') or None
        except (ValueError, TypeError):
            pos = None
        dist_raw = r.get('distance_f') or r.get('distance') or ''
        dist_f = None
        try:
            dist_f = float(dist_raw) if isinstance(dist_raw, (int, float)) else _dist_to_furlongs(str(dist_raw))
        except Exception:
            pass
        runs.append({
            'date':            str(r.get('date') or ''),
            'course':          str(r.get('course') or ''),
            'distance_f':      dist_f,
            'going':           _norm_going(str(r.get('going') or '')),
            'position':        pos,
            'field_size':      _safe_int(r.get('runners') or r.get('field_size')),
            'official_rating': _safe_int(r.get('official_rating') or r.get('ofr')),
            'race_class':      str(r.get('class') or r.get('race_class') or ''),
            'beaten_lengths':  _parse_beaten_lengths(str(r.get('beaten_lengths') or r.get('btn') or '')),
        })
    return runs


# ---------------------------------------------------------------------------
# Sporting Life: racecard form for tomorrow's venues
# ---------------------------------------------------------------------------

_SL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Referer': 'https://www.sportinglife.com/',
}

_SL_RACE_URL_RE = re.compile(r'/racing/racecards/\d{4}-\d{2}-\d{2}/[^"\'>\s]+')


def _get_sl_race_urls(date_str: str) -> list[str]:
    try:
        r = requests.get('https://www.sportinglife.com/racing/racecards',
                         headers=_SL_HEADERS, timeout=20)
        if r.status_code != 200:
            return []
        urls = list(dict.fromkeys(_SL_RACE_URL_RE.findall(r.text)))
        return [f'https://www.sportinglife.com{u}' for u in urls if date_str in u]
    except Exception:
        return []


def _fetch_sl_race_form(url: str) -> dict:
    """Fetch one SL racecard page. Returns {horse_name_lower: [run_dicts]}."""
    try:
        r = requests.get(url, headers=_SL_HEADERS, timeout=15)
        if r.status_code != 200:
            return {}
        m = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
        if not m:
            return {}
        page = json.loads(m.group(1))
        runners = (
            page.get('props', {}).get('pageProps', {})
            .get('race', {}).get('runners') or []
        )
        result = {}
        for ride in runners:
            horse = ride.get('horse') or {}
            name = str(horse.get('name') or '').strip()
            if not name:
                continue
            prev = horse.get('previous_results', []) or []
            runs = []
            for rr in prev[:6]:
                going_raw = rr.get('going') or rr.get('going_shortcode', '')
                pos_raw = rr.get('position') or rr.get('finishing_position') or ''
                try:
                    pos = int(str(pos_raw).strip())
                except (ValueError, TypeError):
                    pos = None
                dist_raw = rr.get('distance_f') or rr.get('distance') or ''
                dist_f = None
                try:
                    dist_f = float(dist_raw) if isinstance(dist_raw, (int, float)) else _dist_to_furlongs(str(dist_raw))
                except Exception:
                    pass
                runs.append({
                    'date':            str(rr.get('date') or rr.get('race_date') or ''),
                    'course':          str(rr.get('course') or rr.get('course_name') or ''),
                    'distance_f':      dist_f,
                    'going':           _norm_going(str(going_raw)),
                    'position':        pos,
                    'field_size':      _safe_int(rr.get('runners') or rr.get('field_size')),
                    'official_rating': _safe_int(rr.get('official_rating') or rr.get('or')),
                    'race_class':      str(rr.get('class') or rr.get('race_class') or ''),
                    'beaten_lengths':  _parse_beaten_lengths(str(rr.get('beaten_lengths') or rr.get('btn') or '')),
                })
            if runs:
                result[name.lower()] = runs
        return result
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Lambda handler
# ---------------------------------------------------------------------------

def lambda_handler(event, context):
    api_key = os.environ.get('RACING_API_KEY', '')
    if not api_key or ':' not in api_key:
        print('[prewarm] RACING_API_KEY not set — nothing to do')
        return {'horses_cached': 0, 'date': 'unknown'}

    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
    print(f'[prewarm] Pre-warming form cache for {tomorrow}…')

    # 1. Get tomorrow's full declared field from Racing API
    racecards = _fetch_racecards(api_key)
    print(f'[prewarm] Racing API racecards: {len(racecards)} races')

    # Build {horse_name_lower: horse_id} for all runners
    all_runners: dict[str, str] = {}   # name_lower → horse_id
    for race in racecards:
        for runner in (race.get('runners') or []):
            name = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', str(runner.get('horse') or '')).strip()
            if name:
                all_runners[name.lower()] = str(runner.get('horse_id') or '')

    print(f'[prewarm] {len(all_runners)} unique runners to cache')

    # 2. Fan-out SL racecard scraping for tomorrow's venues
    form_cache: dict[str, list] = {}
    sl_urls = _get_sl_race_urls(tomorrow)
    print(f'[prewarm] SL: {len(sl_urls)} race URLs found')
    if sl_urls:
        with ThreadPoolExecutor(max_workers=min(len(sl_urls), 10)) as pool:
            futs = {pool.submit(_fetch_sl_race_form, url): url for url in sl_urls}
            for fut in as_completed(futs):
                try:
                    form_cache.update(fut.result())
                except Exception:
                    pass
        print(f'[prewarm] SL enriched {len(form_cache)} horses')

    # 3. Racing API results fallback for runners SL missed
    sl_missed = [(name, hid) for name, hid in all_runners.items()
                 if name not in form_cache and hid]
    print(f'[prewarm] Racing API results fallback: {len(sl_missed)} runners SL missed')
    if sl_missed:
        with ThreadPoolExecutor(max_workers=min(len(sl_missed), 8)) as pool:
            futs = {pool.submit(_fetch_horse_results, hid, api_key): name
                    for name, hid in sl_missed}
            ra_filled = 0
            for fut in as_completed(futs):
                name = futs[fut]
                try:
                    runs = fut.result()
                    if runs:
                        form_cache[name] = runs
                        ra_filled += 1
                except Exception:
                    pass
        print(f'[prewarm] RA results filled {ra_filled} more horses')

    total = len(form_cache)
    coverage = round(100 * total / len(all_runners)) if all_runners else 0
    print(f'[prewarm] Total cached: {total}/{len(all_runners)} ({coverage}%) for {tomorrow}')

    # 4. Write to S3
    s3 = boto3.client('s3', region_name=REGION)
    s3_key = f'form_cache/{tomorrow}.json'
    s3.put_object(
        Bucket=BUCKET,
        Key=s3_key,
        Body=json.dumps(form_cache, default=str).encode('utf-8'),
        ContentType='application/json',
    )
    print(f'[prewarm] Saved to s3://{BUCKET}/{s3_key}')

    return {'horses_cached': total, 'date': tomorrow, 'coverage_pct': coverage}

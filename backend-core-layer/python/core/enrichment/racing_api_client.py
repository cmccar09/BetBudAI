"""
The Racing API Client
=====================
Wraps The Racing API (https://api.theracingapi.com) for BetBudAI.
Free tier: basic racecards (today/tomorrow) + today's results.
Auth: HTTP Basic (username/password).

Credentials loaded from:
  - Local:  racing-api-creds.json  {"username": "...", "password": "..."}
  - Lambda: AWS Secrets Manager key "racing-api-credentials"
"""

import json
import os
import requests
import boto3
import time

BASE_URL = "https://api.theracingapi.com/v1"

# Rate limit: Free = 1 req/sec, Basic = 2 req/sec
_last_call_ts = 0.0


def _rate_limit(min_gap=1.1):
    """Enforce rate limit between API calls."""
    global _last_call_ts
    now = time.time()
    elapsed = now - _last_call_ts
    if elapsed < min_gap:
        time.sleep(min_gap - elapsed)
    _last_call_ts = time.time()


def get_racing_api_creds():
    """Load Racing API credentials (username, password)."""
    # Try local file first
    creds_file = os.path.join(os.path.dirname(__file__), 'racing-api-creds.json')
    if os.path.exists(creds_file):
        with open(creds_file, 'r') as f:
            creds = json.load(f)
        return creds['username'], creds['password']

    # Fallback: AWS Secrets Manager (for Lambda)
    try:
        client = boto3.client('secretsmanager')
        resp = client.get_secret_value(SecretId='racing-api-credentials')
        creds = json.loads(resp['SecretString'])
        return creds['username'], creds['password']
    except Exception as e:
        print(f"[racing_api] No credentials found: {e}")
        return None, None


def _get(endpoint, params=None):
    """Make authenticated GET request to The Racing API."""
    username, password = get_racing_api_creds()
    if not username:
        return None

    _rate_limit()
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, auth=(username, password), params=params, timeout=30)
        if resp.status_code == 401:
            print(f"[racing_api] Auth failed — check credentials")
            return None
        if resp.status_code == 403:
            print(f"[racing_api] Forbidden — endpoint may require higher plan")
            return None
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[racing_api] Error calling {endpoint}: {e}")
        return None


# ── Free tier endpoints ──────────────────────────────────────────────────────

def get_free_racecards(day='today', region_codes=None):
    """Get basic racecards for today or tomorrow (Free tier).

    Returns list of race dicts with: course, date, off_time, distance,
    going, race_class, runners (name, draw, form, trainer, jockey, etc.)
    """
    params = {'day': day, 'limit': 500}
    if region_codes:
        params['region_codes'] = region_codes
    data = _get('/racecards/free', params)
    if not data:
        return []
    return data.get('racecards', [])


def get_free_results_today(region=None):
    """Get today's results (Free tier).

    Returns list of result dicts with: course, off_time, winners, placed,
    distances, going, etc.
    """
    params = {'limit': 50}
    if region:
        params['region'] = region
    data = _get('/results/today/free', params)
    if not data:
        return []
    return data.get('results', [])


def get_courses(region_codes=None):
    """Get list of courses with IDs (Free tier)."""
    params = {}
    if region_codes:
        params['region_codes'] = region_codes
    data = _get('/courses', params)
    if not data:
        return []
    return data.get('courses', [])


# ── Enrichment helpers ───────────────────────────────────────────────────────

def enrich_races_from_racecards(betfair_races):
    """Cross-reference Betfair races with Racing API racecard data.

    Adds to each race dict:
      - going, distance, race_class, field_size, surface, race_type
      - verdict (tipster pick)
      - Each runner gets: racing_api_form, sire, dam, sex, colour, headgear
    """
    racecards = get_free_racecards(day='today', region_codes='gb,ire')
    if not racecards:
        print("[racing_api] No racecards available — skipping enrichment")
        return betfair_races

    # Build lookup: normalised(course) + off_time → racecard
    rc_map = {}
    for rc in racecards:
        course = (rc.get('course') or '').strip().lower().replace(' (ire)', '').replace(' (gb)', '')
        off = rc.get('off_time', '')  # e.g. "2:30"
        rc_map[(course, off)] = rc

    enriched = 0
    for race in betfair_races:
        bf_course = (race.get('course') or '').strip().lower()
        # Betfair race_time is ISO: "2026-04-20T13:30:00.000Z"
        # Convert to H:MM for matching
        try:
            from datetime import datetime, timezone, timedelta
            rt = race.get('race_time', '')
            dt = datetime.strptime(rt[:19], "%Y-%m-%dT%H:%M:%S")
            # BST offset if applicable
            month = dt.month
            if 3 <= month <= 10:  # rough BST
                dt = dt + timedelta(hours=1)
            local_time = f"{dt.hour}:{dt.minute:02d}"
        except Exception:
            continue

        rc = rc_map.get((bf_course, local_time))
        if not rc:
            # Try fuzzy match — strip common suffixes
            for (c, t), v in rc_map.items():
                if bf_course.startswith(c.split()[0]) and t == local_time:
                    rc = v
                    break

        if rc:
            race['going'] = rc.get('going', '')
            race['distance'] = rc.get('distance', '')
            race['race_class'] = rc.get('race_class', '')
            race['field_size'] = rc.get('field_size', '')
            race['surface'] = rc.get('surface', '')
            race['race_type'] = rc.get('type', '')
            race['verdict'] = rc.get('verdict', '')
            race['rating_band'] = rc.get('rating_band', '')
            race['age_band'] = rc.get('age_band', '')

            # Enrich individual runners
            rc_runners = {}
            for r in rc.get('runners', []):
                hn = (r.get('horse') or '').strip().lower()
                rc_runners[hn] = r

            for runner in race.get('runners', []):
                rn = (runner.get('name') or '').strip().lower()
                rc_r = rc_runners.get(rn)
                if rc_r:
                    runner['sire'] = rc_r.get('sire', '')
                    runner['dam'] = rc_r.get('dam', '')
                    runner['sex'] = rc_r.get('sex', '')
                    runner['colour'] = rc_r.get('colour', '')
                    runner['headgear'] = rc_r.get('headgear', '')
                    runner['lbs_carried'] = rc_r.get('lbs', '')
                    runner['racing_api_form'] = rc_r.get('form', '')

            enriched += 1

    print(f"[racing_api] Enriched {enriched}/{len(betfair_races)} races from racecards")
    return betfair_races


def get_results_with_sp():
    """Fetch today's results and return SP odds map.

    Returns dict: {(normalised_course, off_time): {horse_name: sp_decimal}}
    Useful as a fallback when Betfair SP is unavailable.
    """
    results = get_free_results_today(region='gb')
    results += get_free_results_today(region='ire')

    sp_map = {}
    for race in results:
        course = (race.get('course') or '').strip().lower().replace(' (ire)', '').replace(' (gb)', '')
        off = race.get('off', '')
        key = (course, off)
        runners_sp = {}
        for r in race.get('runners', []):
            name = r.get('horse', '')
            sp = r.get('sp', '')
            if name and sp:
                # Convert fractional to decimal: "9/2" → 5.5
                try:
                    if '/' in str(sp):
                        parts = sp.split('/')
                        dec = float(parts[0]) / float(parts[1]) + 1.0
                    else:
                        dec = float(sp)
                    runners_sp[name] = round(dec, 2)
                except (ValueError, ZeroDivisionError):
                    pass
        if runners_sp:
            sp_map[key] = runners_sp

    return sp_map


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Testing Racing API client...")
    creds = get_racing_api_creds()
    if not creds[0]:
        print("No credentials found. Create racing-api-creds.json with:")
        print('  {"username": "your_email", "password": "your_password"}')
    else:
        print(f"Credentials loaded for: {creds[0]}")
        racecards = get_free_racecards(day='today')
        print(f"\nFound {len(racecards)} races today")
        for rc in racecards[:3]:
            print(f"  {rc.get('course')} {rc.get('off_time')} - {rc.get('race_name', '')}")
            runners = rc.get('runners', [])
            print(f"    {len(runners)} runners, going: {rc.get('going')}, dist: {rc.get('distance')}")

        results = get_free_results_today()
        print(f"\n{len(results)} results today")
        for r in results[:3]:
            print(f"  {r.get('course')} {r.get('off')} - winner: {r.get('runners', [{}])[0].get('horse', '?')}")

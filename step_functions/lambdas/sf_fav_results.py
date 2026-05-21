"""
Lambda: surebet-fav-results
============================
Phase : Evening (runs after FetchSLResults, before FetchResults)
Input : {"date": "YYYY-MM-DD"}
Output: {"success": true, "date": "...", "races_processed": N, "favs_updated": N}

For every race on the given date this Lambda:
  1. Queries ALL DynamoDB runners (no show_in_ui filter) — to find each race's favourite
  2. Fetches the Sporting Life fast-results winner map (one HTTP request)
  3. Determines whether the favourite won or lost
  4. Writes  fav_outcome = 'win' | 'loss'  and  race_winner_name  back to the
     favourite's DynamoDB row so that the /api/favs-run endpoint can display it.

This is intentionally lightweight — it does not touch any pick selection logic,
weights, or learning data.
"""

import concurrent.futures
import datetime
import json
import os
import re
import urllib.request
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')
SL_BASE = 'https://www.sportinglife.com'
_SL_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/122.0.0.0 Safari/537.36'
    ),
    'Accept':          'text/html,application/xhtml+xml',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer':         'https://www.sportinglife.com/',
}

# ── Decimal helper ──────────────────────────────────────────────────────────

def _floatify(o):
    if isinstance(o, Decimal):
        return float(o)
    if isinstance(o, dict):
        return {k: _floatify(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_floatify(v) for v in o]
    return o


# ── Odds → decimal ──────────────────────────────────────────────────────────

def _odds_dec(odds):
    if odds is None:
        return None
    try:
        return float(odds)
    except (TypeError, ValueError):
        pass
    try:
        s = str(odds).strip()
        if '/' in s:
            n, d = s.split('/')
            return float(n) / float(d) + 1.0
    except Exception:
        pass
    return None


# ── UTC → UK local (BST = UTC+1, late Mar–late Oct) ─────────────────────────

def _utc_to_local_hhmm(utc_hhmm: str, date_str: str) -> str:
    try:
        from datetime import date as _d
        d = _d.fromisoformat(date_str[:10])
        bst_start = _d(d.year, 3, 31)
        while bst_start.weekday() != 6:
            bst_start = _d(bst_start.year, bst_start.month, bst_start.day - 1)
        bst_end = _d(d.year, 10, 31)
        while bst_end.weekday() != 6:
            bst_end = _d(bst_end.year, bst_end.month, bst_end.day - 1)
        if not (bst_start <= d < bst_end):
            return utc_hhmm
        h, mn = map(int, utc_hhmm.split(':'))
        total = h * 60 + mn + 60
        return f'{(total // 60) % 24:02d}:{total % 60:02d}'
    except Exception:
        return utc_hhmm


# ── Shared HTTP helper ───────────────────────────────────────────────────────

def _sl_http(url: str) -> str:
    req = urllib.request.Request(url, headers=_SL_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode('utf-8', errors='replace')


# ── Parse a single SL race-result page → (off_time_hhmm, winner_name) ───────

def _parse_sl_race_winner(race_url: str):
    try:
        html = _sl_http(race_url)
    except Exception as e:
        print(f'[fav_results] race page error: {e}')
        return None, None

    off_time = None
    off_m = re.search(r'Off time:\s*(\d{1,2}:\d{2})', html)
    if off_m:
        off_time = off_m.group(1).zfill(5)

    # SL ResultRunner CSS class — runners listed in finish order
    runners_html = re.findall(
        r'ResultRunner__StyledHorseName[^"]*"[^>]*>'
        r'<a\s+href="/racing/profiles/horse/\d+"[^>]*>([^<]+)</a>',
        html,
    )
    if runners_html:
        w = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', runners_html[0]).strip()
        return off_time, w

    # og:description fallback: "HorseName won ..."
    for pattern in [
        r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"',
        r'<meta[^>]+content="([^"]*)"[^>]+property="og:description"',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            wm = re.match(r'^([A-Z][^.]+?)\s+won\b', m.group(1))
            if wm:
                return off_time, wm.group(1).strip()

    return off_time, None


# ── Scrape per-race pages for the date (fallback for missing meeting coverage) ─

def _fetch_per_race_winners(date_str: str, limit_courses=None) -> dict:
    """
    Fetch individual SL race-result pages for the given date.
    Returns {(course_lower, off_time_hhmm): winner_name}.
    limit_courses: optional set of course_lower strings to restrict to.
    """
    idx_url = f'{SL_BASE}/racing/results/{date_str}/'
    try:
        html = _sl_http(idx_url)
    except Exception as e:
        print(f'[fav_results] per-race index error: {e}')
        return {}

    pat = re.compile(
        r'href="(/racing/results/' + re.escape(date_str) + r'/([^/]+)/(\d+)/[^"]+)"'
    )
    seen: set = set()
    jobs = []
    for m in pat.finditer(html):
        full_path, course_slug, race_id = m.group(1), m.group(2), m.group(3)
        key = (course_slug, race_id)
        if key in seen:
            continue
        seen.add(key)
        course_lower = course_slug.replace('-', ' ').strip().lower()
        if limit_courses and course_lower not in limit_courses:
            continue
        jobs.append((course_lower, f'{SL_BASE}{full_path}'))

    print(f'[fav_results] per-race: fetching {len(jobs)} race pages '
          f'({"all courses" if not limit_courses else ", ".join(sorted(limit_courses))})')

    extra: dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        fs = {pool.submit(_parse_sl_race_winner, url): (crs, url) for crs, url in jobs}
        for fut in concurrent.futures.as_completed(fs, timeout=45):
            crs, url = fs[fut]
            try:
                off_t, winner = fut.result()
                if winner:
                    extra[(crs, off_t or '??:??')] = winner
                    print(f'[fav_results] per-race: {crs} {off_t} → {winner}')
            except Exception as e:
                print(f'[fav_results] per-race parse error {url}: {e}')

    print(f'[fav_results] per-race map: {len(extra)} winners found')
    return extra


# ── Fetch SL fast-results → {(course_lower, local_hhmm): winner_name} ───────

def _fetch_sl_winner_map() -> dict:
    url = 'https://www.sportinglife.com/racing/fast-results/all'
    try:
        req = urllib.request.Request(url, headers=_SL_HEADERS)
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f'[fav_results] SL fetch error: {e}')
        return {}

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not m:
        return {}
    try:
        data = json.loads(m.group(1))
    except Exception:
        return {}

    fast = data.get('props', {}).get('pageProps', {}).get('fastResults', [])
    winner_map: dict = {}
    for fr in fast:
        top_horses = fr.get('top_horses')
        if not top_horses:
            continue
        course   = fr.get('courseName', '')
        off_time = fr.get('time', '')
        if not course or not off_time:
            continue
        sorted_h = sorted(top_horses, key=lambda h: h.get('position', 99))
        winner   = sorted_h[0].get('horse_name', '') if sorted_h else ''
        winner   = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', winner).strip()
        if winner:
            winner_map[(course.lower().replace('-', ' ').strip(), off_time)] = winner

    print(f'[fav_results] SL winner_map: {len(winner_map)} completed races')
    return winner_map


# ── Normalise horse name for comparison ──────────────────────────────────────

def _norm_horse(name: str) -> str:
    n = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', name or '').strip().lower()
    n = re.sub(r"['\-]", '', n)
    return re.sub(r'\s+', ' ', n).strip()


# ── Main Lambda handler ───────────────────────────────────────────────────────

def lambda_handler(event, context):
    date_str = event.get('date', datetime.datetime.utcnow().strftime('%Y-%m-%d'))
    print(f'[fav_results] Processing date: {date_str}')

    db  = boto3.resource('dynamodb', region_name=REGION)
    tbl = db.Table('SureBetBets')

    # ── 1. Load ALL runners for the date (paginated) ──────────────────────────
    all_items = []
    kwargs    = {'KeyConditionExpression': Key('bet_date').eq(date_str)}
    while True:
        resp = tbl.query(**kwargs)
        all_items.extend([_floatify(it) for it in resp.get('Items', [])])
        last = resp.get('LastEvaluatedKey')
        if not last:
            break
        kwargs['ExclusiveStartKey'] = last

    print(f'[fav_results] Total DynamoDB rows for {date_str}: {len(all_items)}')
    if not all_items:
        return {'success': True, 'date': date_str, 'races_processed': 0, 'favs_updated': 0}

    # ── 2. Fetch SL winner map ────────────────────────────────────────────────
    winner_map = _fetch_sl_winner_map()

    # ── 3. Group runners by race (race_time + course) ─────────────────────────
    races: dict = {}
    for it in all_items:
        rt     = str(it.get('race_time', ''))[:19]
        course = (it.get('course') or it.get('race_course') or '').strip()
        key    = f'{rt}|{course}'
        races.setdefault(key, []).append(it)

    races_processed = 0
    favs_updated    = 0
    unresolved_races = []   # (fav_name, fav_bet_id, race_hhmm, course_key)

    for race_key, runners in sorted(races.items()):
        rt, course = race_key.split('|', 1)

        # Find favourite — lowest decimal odds runner (skip odds<=0 = missing data)
        def _sort_odds(h):
            o = _odds_dec(h.get('odds') or h.get('decimal_odds'))
            return o if o is not None and o > 0 else 99.0

        runners_sorted = sorted(runners, key=_sort_odds)
        fav            = runners_sorted[0]
        fav_odds       = _sort_odds(fav)

        # Only process genuine short-price favourites
        if fav_odds > 4.0:
            continue

        races_processed += 1
        fav_name = (fav.get('horse') or fav.get('horse_name') or '').strip()
        fav_bet_id = fav.get('bet_id', '')
        if not fav_bet_id:
            print(f'  [fav_results] No bet_id for fav {fav_name} in {course} {rt} — skipping')
            continue

        # Already resolved? Only overwrite if still None / 'pending'
        existing_outcome = fav.get('fav_outcome') or fav.get('outcome')
        if existing_outcome and str(existing_outcome).lower() not in ('', 'pending', 'none'):
            # Already have a result for this item — skip unless it was written as a pick result
            # (fav_outcome specifically might still be None even if outcome is set for a winning pick)
            if fav.get('fav_outcome'):
                continue

        # ── Resolve winner from SL winner_map ────────────────────────────────
        race_hhmm  = rt[11:16] if len(rt) >= 16 else ''
        course_key = course.lower().replace('-', ' ').strip()

        winner_name  = None
        fav_outcome  = None

        try:
            lh, lm       = map(int, race_hhmm.split(':'))
            local_mins   = lh * 60 + lm
            best_diff    = 999
            best_winner  = None
            for (c_key, t_key), w_name in winner_map.items():
                if c_key != course_key:
                    continue
                wh, wm = map(int, t_key.split(':'))
                diff = abs((wh * 60 + wm) - local_mins)
                if diff < best_diff:
                    best_diff = diff
                    best_winner = w_name.strip()
            if best_winner and best_diff <= 10:
                winner_name = best_winner
                fav_outcome = (
                    'win'
                    if _norm_horse(winner_name) == _norm_horse(fav_name)
                    else 'loss'
                )
        except Exception as ex:
            print(f'  [fav_results] matching error {course} {race_hhmm}: {ex}')

        # ── Fallback: check outcome='win' OR result_winner_name written by sl_results_fetcher ─
        if fav_outcome is None:
            for h in runners:
                h_outcome = str(h.get('outcome') or '').lower()
                if h_outcome in ('win', 'won'):
                    winner_name = (h.get('horse') or h.get('horse_name') or '').strip()
                    fav_outcome = (
                        'win'
                        if _norm_horse(winner_name) == _norm_horse(fav_name)
                        else 'loss'
                    )
                    break
                # sl_results_fetcher writes result_winner_name to every settled pick in the race
                rw = (h.get('result_winner_name') or h.get('winner_name') or '').strip()
                if rw and not winner_name:
                    winner_name = rw
                    fav_outcome = (
                        'win'
                        if _norm_horse(rw) == _norm_horse(fav_name)
                        else 'loss'
                    )
                    break

        if fav_outcome is None:
            # Collect for per-race HTML scraping fallback (3rd tier)
            unresolved_races.append((fav_name, fav_bet_id, race_hhmm, course_key))
            continue

        # ── Write fav_outcome + race_winner_name to DynamoDB ────────────────
        expr_vals = {
            ':fo': fav_outcome,
        }
        update_expr = 'SET fav_outcome = :fo'
        if winner_name:
            update_expr += ', race_winner_name = :wn'
            expr_vals[':wn'] = winner_name

        try:
            tbl.update_item(
                Key={'bet_date': date_str, 'bet_id': fav_bet_id},
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_vals,
            )
            favs_updated += 1
            result_label = '✓ FAV LOST (LAY WIN)' if fav_outcome == 'loss' else '✗ FAV WON'
            print(f'  [fav_results] {result_label}: {fav_name} @ {course} {local_hhmm} (winner: {winner_name})')
        except Exception as ex:
            print(f'  [fav_results] DynamoDB write error for {fav_name}: {ex}')

    # ── 3rd tier: per-race HTML scraping for unresolved favourites ─────────────
    if unresolved_races:
        unresolved_courses = {r[3] for r in unresolved_races}
        print(f'[fav_results] per-race fallback for {len(unresolved_races)} unresolved races '
              f'at: {", ".join(sorted(unresolved_courses))}')
        extra_map = _fetch_per_race_winners(date_str, limit_courses=unresolved_courses)

        for (fav_name, fav_bet_id, race_hhmm, course_key) in unresolved_races:
            winner_name = None
            fav_outcome = None
            if extra_map and race_hhmm:
                try:
                    lh, lm = map(int, race_hhmm.split(':'))
                    local_mins = lh * 60 + lm
                    best_diff = 999
                    best_winner = None
                    for (c_key, t_key), w_name in extra_map.items():
                        if c_key != course_key:
                            continue
                        try:
                            wh, wm = map(int, t_key.split(':'))
                            diff = abs((wh * 60 + wm) - local_mins)
                            if diff < best_diff:
                                best_diff = diff
                                best_winner = w_name.strip()
                        except ValueError:
                            pass
                    if best_winner and best_diff <= 10:
                        winner_name = best_winner
                        fav_outcome = (
                            'win'
                            if _norm_horse(winner_name) == _norm_horse(fav_name)
                            else 'loss'
                        )
                except Exception as ex:
                    print(f'  [fav_results] per-race match error {fav_name}: {ex}')

            if fav_outcome is None:
                print(f'  [fav_results] Still unresolved: {fav_name} @ {course_key} {race_hhmm}')
                continue

            expr_vals = {':fo': fav_outcome}
            update_expr = 'SET fav_outcome = :fo'
            if winner_name:
                update_expr += ', race_winner_name = :wn'
                expr_vals[':wn'] = winner_name
            try:
                tbl.update_item(
                    Key={'bet_date': date_str, 'bet_id': fav_bet_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeValues=expr_vals,
                )
                favs_updated += 1
                result_label = '✓ FAV LOST (LAY WIN)' if fav_outcome == 'loss' else '✗ FAV WON'
                print(f'  [fav_results] {result_label}: {fav_name} @ {course_key} {race_hhmm} '
                      f'(winner: {winner_name}) [per-race scrape]')
            except Exception as ex:
                print(f'  [fav_results] DynamoDB write error for {fav_name}: {ex}')

    print(f'[fav_results] Done — {races_processed} races, {favs_updated} fav outcomes written')
    return {
        'success'        : True,
        'date'           : date_str,
        'races_processed': races_processed,
        'favs_updated'   : favs_updated,
    }

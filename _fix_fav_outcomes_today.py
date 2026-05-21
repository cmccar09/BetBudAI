"""
Re-process fav_outcomes for today using correct SL per-race data.
Compares current DB values with correct winners and fixes mismatches.
"""
import re
import urllib.request
import concurrent.futures
import boto3
from boto3.dynamodb.conditions import Key
from datetime import date as _d
from decimal import Decimal

REGION = 'eu-west-1'
SL_BASE = 'https://www.sportinglife.com'
_SL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.sportinglife.com/',
}
DATE_STR = '2026-04-14'

def _sl_http(url):
    req = urllib.request.Request(url, headers=_SL_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode('utf-8', errors='replace')

def _parse_sl_race_winner(race_url):
    try:
        html = _sl_http(race_url)
    except Exception:
        return None, None
    off_m = re.search(r'Off time:\s*(\d{1,2}:\d{2})', html)
    off_time = off_m.group(1).zfill(5) if off_m else None
    runners_html = re.findall(
        r'ResultRunner__StyledHorseName[^"]*"[^>]*>'
        r'<a\s+href="/racing/profiles/horse/\d+"[^>]*>([^<]+)</a>',
        html,
    )
    if runners_html:
        w = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', runners_html[0]).strip()
        return off_time, w
    return off_time, None

def _utc_to_local_hhmm(utc_hhmm, date_str):
    try:
        d = _d.fromisoformat(date_str[:10])
        bst_start = _d(d.year, 3, 31)
        while bst_start.weekday() != 6: bst_start = _d(bst_start.year, bst_start.month, bst_start.day - 1)
        bst_end = _d(d.year, 10, 31)
        while bst_end.weekday() != 6: bst_end = _d(bst_end.year, bst_end.month, bst_end.day - 1)
        if not (bst_start <= d < bst_end): return utc_hhmm
        h, mn = map(int, utc_hhmm.split(':'))
        total = h * 60 + mn + 60
        return f'{(total // 60) % 24:02d}:{total % 60:02d}'
    except Exception:
        return utc_hhmm

def _norm(name):
    n = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', name or '').strip().lower()
    n = re.sub(r"['\-]", '', n)
    return re.sub(r'\s+', ' ', n).strip()

def _odds_dec(h):
    o = h.get('odds') or h.get('decimal_odds')
    try: return float(o)
    except: pass
    try:
        s = str(o).strip()
        if '/' in s:
            n, d = s.split('/')
            return float(n)/float(d)+1.0
    except: pass
    return 99.0

# ── 1. Fetch SL per-race winner map ──────────────────────────────────────────
print("Fetching SL per-race results...")
idx_html = _sl_http(f'{SL_BASE}/racing/results/{DATE_STR}/')
pat = re.compile(r'href="(/racing/results/' + re.escape(DATE_STR) + r'/([^/]+)/(\d+)/[^"]+)"')
seen = set()
jobs = []
for m in pat.finditer(idx_html):
    full_path, course_slug, race_id = m.group(1), m.group(2), m.group(3)
    key = (course_slug, race_id)
    if key in seen: continue
    seen.add(key)
    course_lower = course_slug.replace('-', ' ').strip().lower()
    jobs.append((course_lower, f'{SL_BASE}{full_path}'))

sl_map = {}  # {(course, off_time): winner_name}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    fs = {pool.submit(_parse_sl_race_winner, url): (crs, url) for crs, url in jobs}
    for fut in concurrent.futures.as_completed(fs, timeout=60):
        crs, url = fs[fut]
        try:
            off_t, winner = fut.result()
            if winner and off_t:
                sl_map[(crs, off_t)] = winner
        except: pass

print(f"SL per-race map: {len(sl_map)} winners")

# ── 2. Load DB items ─────────────────────────────────────────────────────────
tbl = boto3.resource('dynamodb', region_name=REGION).Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq(DATE_STR))
items = [dict(it) for it in resp['Items']]

# ── 3. Group by race, find fav, match with SL, fix if wrong ──────────────────
races = {}
for it in items:
    rt = str(it.get('race_time', ''))[:19]
    course = (it.get('course') or it.get('race_course') or '').strip()
    key = f'{rt}|{course}'
    races.setdefault(key, []).append(it)

fixes = []
for race_key, runners in sorted(races.items()):
    rt, course = race_key.split('|', 1)
    runners_sorted = sorted(runners, key=_odds_dec)
    fav = runners_sorted[0]
    fav_odds = _odds_dec(fav)
    if fav_odds > 4.0: continue
    
    fav_name = (fav.get('horse') or '').strip()
    fav_bet_id = fav.get('bet_id', '')
    current_fo = fav.get('fav_outcome', '')
    current_rwn = fav.get('race_winner_name', '')
    
    utc_hhmm = rt[11:16] if len(rt) >= 16 else ''
    date_part = rt[:10] if len(rt) >= 10 else DATE_STR
    local_hhmm = _utc_to_local_hhmm(utc_hhmm, date_part)
    course_key = course.lower().replace('-', ' ').strip()
    
    # Find CLOSEST matching SL race (not ±15, use ±5 for precision)
    best_diff = 999
    best_winner = None
    try:
        lh, lm = map(int, local_hhmm.split(':'))
        local_mins = lh * 60 + lm
        for (c_key, t_key), w_name in sl_map.items():
            if c_key != course_key: continue
            wh, wm = map(int, t_key.split(':'))
            diff = abs((wh * 60 + wm) - local_mins)
            if diff < best_diff:
                best_diff = diff
                best_winner = w_name
    except: pass
    
    if best_winner is None or best_diff > 10:
        if current_fo:
            print(f"  UNRESOLVED: {local_hhmm} {course} fav={fav_name} (closest SL {best_diff}min)")
        continue
    
    correct_fo = 'win' if _norm(best_winner) == _norm(fav_name) else 'loss'
    
    if current_fo != correct_fo:
        fixes.append({
            'bet_id': fav_bet_id,
            'fav_name': fav_name,
            'course': course,
            'local_hhmm': local_hhmm,
            'old_fo': current_fo,
            'old_rwn': current_rwn,
            'new_fo': correct_fo,
            'new_rwn': best_winner,
            'sl_diff_min': best_diff,
        })
        print(f"  FIX: {local_hhmm} {course:15s} fav={fav_name:25s} | {current_fo or 'None':4s}→{correct_fo:4s} | winner: {current_rwn or 'N/A'} → {best_winner} (±{best_diff}min)")
    else:
        if current_fo:
            print(f"  OK:  {local_hhmm} {course:15s} fav={fav_name:25s} | {current_fo:4s} | winner: {best_winner}")

print(f"\n{len(fixes)} fixes needed.")
if fixes:
    print("\nApplying fixes...")
    for f in fixes:
        tbl.update_item(
            Key={'bet_date': DATE_STR, 'bet_id': f['bet_id']},
            UpdateExpression='SET fav_outcome = :fo, race_winner_name = :wn',
            ExpressionAttributeValues={':fo': f['new_fo'], ':wn': f['new_rwn']},
        )
        print(f"  ✓ {f['local_hhmm']} {f['course']} {f['fav_name']}: {f['old_fo']}→{f['new_fo']}")
    print("Done!")

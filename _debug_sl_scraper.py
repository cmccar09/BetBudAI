"""Debug: see what the SL per-race scraper actually returns for today."""
import re
import urllib.request
import concurrent.futures

SL_BASE = 'https://www.sportinglife.com'
_SL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.sportinglife.com/',
}

def _sl_http(url):
    req = urllib.request.Request(url, headers=_SL_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode('utf-8', errors='replace')

def _parse_sl_race_winner(race_url):
    try:
        html = _sl_http(race_url)
    except Exception as e:
        return None, None, str(e)

    off_time = None
    off_m = re.search(r'Off time:\s*(\d{1,2}:\d{2})', html)
    if off_m:
        off_time = off_m.group(1).zfill(5)

    runners_html = re.findall(
        r'ResultRunner__StyledHorseName[^"]*"[^>]*>'
        r'<a\s+href="/racing/profiles/horse/\d+"[^>]*>([^<]+)</a>',
        html,
    )
    if runners_html:
        w = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', runners_html[0]).strip()
        return off_time, w, None

    for pattern in [
        r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"',
        r'<meta[^>]+content="([^"]*)"[^>]+property="og:description"',
    ]:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            wm = re.match(r'^([A-Z][^.]+?)\s+won\b', m.group(1))
            if wm:
                return off_time, wm.group(1).strip(), 'og fallback'
    
    return off_time, None, 'no winner found'

date_str = '2026-04-14'
idx_url = f'{SL_BASE}/racing/results/{date_str}/'
html = _sl_http(idx_url)

pat = re.compile(
    r'href="(/racing/results/' + re.escape(date_str) + r'/([^/]+)/(\d+)/[^"]+)"'
)
seen = set()
jobs = []
for m in pat.finditer(html):
    full_path, course_slug, race_id = m.group(1), m.group(2), m.group(3)
    key = (course_slug, race_id)
    if key in seen:
        continue
    seen.add(key)
    course_lower = course_slug.replace('-', ' ').strip().lower()
    if course_lower in ('newmarket', 'market rasen', 'lingfield', 'clonmel', 'newton abbot'):
        jobs.append((course_lower, f'{SL_BASE}{full_path}'))

print(f"Fetching {len(jobs)} race pages...")
results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    fs = {pool.submit(_parse_sl_race_winner, url): (crs, url) for crs, url in jobs}
    for fut in concurrent.futures.as_completed(fs, timeout=60):
        crs, url = fs[fut]
        try:
            off_t, winner, note = fut.result()
            results.append((crs, off_t, winner, note))
        except Exception as e:
            results.append((crs, None, None, str(e)))

results.sort(key=lambda r: (r[0], r[1] or ''))
for crs, off_t, winner, note in results:
    n = f" ({note})" if note else ""
    print(f"  {crs:15s} off_time={off_t or '???':5s} winner={winner or '???':25s}{n}")

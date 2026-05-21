"""
Quick script to fetch March 25 race results from Sporting Life
for the 9 horses listed in favs-run.html
"""
import re
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.5',
}

TARGET_HORSES = {
    'Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted',
    'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan'
}

TARGET_COURSES = {'wolverhampton', 'kempton', 'southwell', 'hereford', 'taunton'}
DATE = '2026-03-25'
SL_BASE = 'https://www.sportinglife.com'

def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        if r.status_code == 200:
            return r.text
        print(f"  HTTP {r.status_code}: {url}")
    except Exception as e:
        print(f"  Error: {e}")
    return None

def get_race_urls(date_str):
    idx_url = f'{SL_BASE}/racing/results/{date_str}/'
    print(f"Fetching: {idx_url}")
    html = fetch(idx_url)
    if not html:
        return []
    pat = r'href="(/racing/results/' + re.escape(date_str) + r'/([^/]+)/(\d+)/([^"]+))"'
    seen = set()
    races = []
    for m in re.finditer(pat, html):
        full_path, course_slug, race_id, race_slug = m.group(1), m.group(2), m.group(3), m.group(4)
        if course_slug not in TARGET_COURSES:
            continue
        key = (course_slug, race_id)
        if key in seen:
            continue
        seen.add(key)
        races.append((course_slug, race_id, SL_BASE + full_path))
    print(f"  Found {len(races)} races at target courses")
    return races

def parse_race_result(race_url):
    html = fetch(race_url)
    if not html:
        return None, None, []
    # Off time
    off_m = re.search(r'Off time:\s*(\d{1,2}:\d{2})', html)
    off_time = off_m.group(1).zfill(5) if off_m else None
    # All runners in finishing order
    all_runners = [
        m.strip() for m in re.findall(
            r'ResultRunner__StyledHorseName[^"]*"[^>]*><a\s+href="/racing/profiles/horse/\d+"[^>]*>([^<]+)</a>',
            html
        )
    ]
    winner = all_runners[0] if all_runners else None
    return off_time, winner, all_runners

print(f"\n=== Fetching results for {DATE} ===\n")
races = get_race_urls(DATE)

results = []
for course_slug, race_id, race_url in sorted(races):
    off_time, winner, runners = parse_race_result(race_url)
    print(f"{course_slug.title()} {off_time or '?:??'} — Winner: {winner or '?'}")
    
    for h in TARGET_HORSES:
        h_norm = h.lower().replace("'", "'")
        runners_norm = [r.lower().replace("'", "'") for r in runners]
        if h_norm in runners_norm:
            idx = runners_norm.index(h_norm)
            won = (idx == 0)
            print(f"  ** TARGET: {h} finished {idx+1}{'st' if idx==0 else 'nd' if idx==1 else 'rd' if idx==2 else 'th'} {'<-- WON' if won else '-- lost'}")
            results.append({'horse': h, 'course': course_slug.title(), 'time': off_time, 'pos': idx+1, 'won': won, 'winner': winner})

print(f"\n=== SUMMARY ===")
for r in sorted(results, key=lambda x: str(x.get('time',''))):
    won_str = 'WON (lay lost)' if r['won'] else f"LOST — winner: {r['winner']} (lay won)"
    print(f"{r['time'] or '?:??'} {r['course']}: {r['horse']} {won_str}")

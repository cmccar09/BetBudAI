"""Check all 23 race links found in SL index"""
import re, requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
}
DATE = '2026-03-24'
SL_BASE = 'https://www.sportinglife.com'

idx_url = f'{SL_BASE}/racing/results/{DATE}/'
r = requests.get(idx_url, headers=HEADERS, timeout=20)

pat = r'href="(/racing/results/' + re.escape(DATE) + r'/([^/]+)/(\d+)/([^"]+))"'
seen = set()
races = []
for m in re.finditer(pat, r.text):
    full_path, course_slug, race_id, slug = m.group(1), m.group(2), m.group(3), m.group(4)
    key = (course_slug, race_id)
    if key in seen:
        continue
    seen.add(key)
    races.append((course_slug, race_id, SL_BASE + full_path, slug[:40]))

print(f'Total races: {len(races)}')
# Group by course
from collections import defaultdict
by_course = defaultdict(list)
for cs, rid, url, slug in races:
    by_course[cs].append((rid, slug))

for course in sorted(by_course):
    print(f'\n{course}: {len(by_course[course])} races')
    for rid, slug in by_course[course]:
        print(f'  {slug}')

# Also search raw HTML for 'kempton' and 'hereford'
if 'kempton' in r.text.lower():
    print('\n[kempton found in HTML text]')
    idx = r.text.lower().index('kempton')
    print(r.text[max(0,idx-100):idx+200])
else:
    print('\n[kempton NOT found in HTML]')
    
if 'hereford' in r.text.lower():
    print('\n[hereford found in HTML text]')
    idx = r.text.lower().index('hereford')
    print(r.text[max(0,idx-100):idx+200])
else:
    print('\n[hereford NOT found in HTML]')

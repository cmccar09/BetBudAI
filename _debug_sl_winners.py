import json, urllib.request, re

req = urllib.request.Request(
    'https://www.sportinglife.com/racing/fast-results/all',
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-GB,en;q=0.5',
        'Referer': 'https://www.sportinglife.com/',
    },
)
with urllib.request.urlopen(req, timeout=15) as resp:
    html = resp.read().decode('utf-8', errors='replace')

m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
data = json.loads(m.group(1))
fast = data.get('props', {}).get('pageProps', {}).get('fastResults', [])

print(f"Total fast results: {len(fast)}")
for fr in fast:
    course = fr.get('courseName', '')
    off_time = fr.get('time', '')
    top = fr.get('top_horses', [])
    sorted_h = sorted(top, key=lambda h: h.get('position', 99))
    winner = sorted_h[0].get('horse_name', '') if sorted_h else ''
    winner = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', winner).strip()
    if 'newmarket' in course.lower() or 'cerro' in winner.lower():
        print(f"  {off_time} {course}: winner={winner} (key: {course.lower().replace('-',' ').strip()}|{off_time})")

# Print ALL courses seen
print("\nAll courses in SL fast results:")
courses_seen = set()
for fr in fast:
    c = fr.get('courseName', '')
    t = fr.get('time', '')
    courses_seen.add(c)
print(sorted(courses_seen))

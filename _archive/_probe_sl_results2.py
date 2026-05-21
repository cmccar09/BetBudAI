"""Deep probe of SL results page NEXT_DATA meetings structure."""
import requests, re, json, time

SL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Referer': 'https://www.sportinglife.com/',
    'Upgrade-Insecure-Requests': '1',
}
NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL)

r = requests.get('https://www.sportinglife.com/racing/results/2026-03-29', headers=SL_HEADERS, timeout=15)
nd = json.loads(NEXT_DATA_RE.search(r.text).group(1))
meetings = nd['props']['pageProps'].get('meetings', [])
print(f"Meetings count: {len(meetings)}")
if meetings:
    m0 = meetings[0]
    print(f"Meeting keys: {list(m0.keys())}")
    print(f"First meeting: {json.dumps(m0, indent=2, default=str)[:500]}")
    
    # Look for races/results within a meeting
    races = m0.get('races') or m0.get('results') or m0.get('events') or []
    print(f"\nRaces/events count: {len(races)}")
    if races:
        r0 = races[0]
        print(f"Race keys: {list(r0.keys())}")
        print(f"First race: {json.dumps(r0, indent=2, default=str)[:800]}")

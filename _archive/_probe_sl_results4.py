"""Test: use race IDs from results page to fetch historical racecards."""
import requests, re, json, time

SL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Referer': 'https://www.sportinglife.com/',
    'Upgrade-Insecure-Requests': '1',
}
NEXT_DATA_RE = re.compile(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', re.DOTALL)

# Race ID 909528 = Doncaster 13:20 on 2026-03-29 (Langstone won)
race_id = 909528
date = '2026-03-29'
course = 'doncaster'

# Try various URL formats for the historical racecard
for url in [
    f'https://www.sportinglife.com/racing/racecards/{date}/{course}/racecard/{race_id}',
    f'https://www.sportinglife.com/racing/racecards/{date}/{course}/racecard/{race_id}/race',
]:
    print(f"Trying: {url}")
    r = requests.get(url, headers=SL_HEADERS, timeout=15)
    print(f"  Status: {r.status_code}")
    if r.status_code == 200:
        m = NEXT_DATA_RE.search(r.text)
        if m:
            nd = json.loads(m.group(1))
            pp = nd.get('props', {}).get('pageProps', {})
            print(f"  pageProps keys: {list(pp.keys())[:10]}")
            if 'race' in pp:
                rides = pp['race'].get('rides', [])
                print(f"  Rides count: {len(rides)}")
                if rides:
                    horse = rides[0].get('horse', {})
                    print(f"  Horse[0] keys: {list(horse.keys())}")
                    print(f"  Horse[0] name: {horse.get('name')}")
                    print(f"  Horse[0] id: {(horse.get('horse_reference') or {}).get('id')}")
                    prev = horse.get('previous_results', [])
                    print(f"  previous_results count: {len(prev)}")
        else:
            # Check for horse IDs in raw HTML
            ids = re.findall(r'/racing/profiles/horse/(\d+)', r.text)
            print(f"  Horse IDs in HTML: {ids[:5]}")
    print()
    time.sleep(0.5)

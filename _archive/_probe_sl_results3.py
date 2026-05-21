"""Find result race URLs and horse IDs from SL results."""
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
meetings = nd['props']['pageProps']['meetings']

# Find Doncaster meeting
for mtg in meetings:
    if mtg['meeting_summary']['course']['name'] == 'Doncaster':
        print(f"Doncaster meeting ID: {mtg['meeting_summary']['meeting_reference']['id']}")
        for race in mtg['races'][:2]:
            race_id = race['race_summary_reference']['id']
            race_time = race['time']
            race_name = race['name']
            race_slug = race.get('race_slug') or ''
            print(f"\nRace {race_id} at {race_time}: {race_name[:50]}")
            print(f"  race_slug: {race_slug}")
            
            # Check top_horses
            top = race.get('top_horses') or []
            print(f"  top_horses count: {len(top)}")
            if top:
                print(f"  top_horses[0] keys: {list(top[0].keys())}")
                print(f"  top_horses[0]: {json.dumps(top[0], default=str)[:300]}")
            
            # Try to construct result race URL
            course_slug = 'doncaster'
            for fmt in [
                f'https://www.sportinglife.com/racing/results/2026-03-29/{course_slug}/race/{race_id}',
                f'https://www.sportinglife.com/racing/results/2026-03-29/{course_slug}/race/{race_id}/{race_slug or "race"}',
            ]:
                resp = requests.get(fmt, headers=SL_HEADERS, timeout=10)
                print(f"  {fmt} -> {resp.status_code}")
                if resp.status_code == 200:
                    # Check for horse IDs
                    ids = re.findall(r'/racing/profiles/horse/(\d+)', resp.text)
                    print(f"    horse IDs in page: {len(ids)} -> {ids[:5]}")
                    m2 = NEXT_DATA_RE.search(resp.text)
                    if m2:
                        nd2 = json.loads(m2.group(1))
                        pp = nd2.get('props',{}).get('pageProps',{})
                        print(f"    NEXT_DATA pageProps keys: {list(pp.keys())[:10]}")
                time.sleep(0.3)
        break

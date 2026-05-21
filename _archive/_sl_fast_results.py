"""
Check Sporting Life fast-results for today's races (same-day results)
"""
import requests, json, re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.sportinglife.com/racing/',
}

TARGET_HORSES = ['Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted', 'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan']

def norm(s):
    return re.sub(r"\s+", " ", (s or '').strip().lower()).replace('\u2019', "'").replace("'", "'")

# Try fast-results page - it covers today's results
r = requests.get('https://www.sportinglife.com/racing/fast-results/all', headers=HEADERS, timeout=30)
print(f"Fast-results page: {r.status_code}, len={len(r.text)}")

if r.status_code == 200:
    # Look for target horses
    for h in TARGET_HORSES:
        if norm(h) in norm(r.text):
            print(f"  Found: {h}")
            idx = norm(r.text).find(norm(h))
            print(f"  Context: {r.text[max(0,idx-200):idx+300]}")

# Also try the SL racecards for today
r2 = requests.get('https://www.sportinglife.com/racing/results/today', headers=HEADERS, timeout=30)
print(f"\nToday's results: {r2.status_code}, len={len(r2.text)}")

if r2.status_code == 200:
    found_any = False
    for h in TARGET_HORSES:
        if norm(h) in norm(r2.text):
            print(f"  Found: {h}")
            found_any = True
    if not found_any:
        print("  None found")
        # Try __NEXT_DATA__
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r2.text, re.DOTALL)
        if m:
            d = json.loads(m.group(1))
            pp = d.get('props', {}).get('pageProps', {})
            print(f"  pageProps keys: {list(pp.keys())[:10]}")

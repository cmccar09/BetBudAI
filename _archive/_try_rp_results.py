"""
Fetch March 25 results directly from Sporting Life per-course pages
"""
import requests
import json
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.sportinglife.com/',
}

TARGET_HORSES = ['Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted', 'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan']

def norm(s):
    s = re.sub(r"\s+", " ", (s or '').strip().lower())
    return s.replace('\u2019', "'").replace("'", "'").replace('&#x27;', "'")

SL_BASE = 'https://www.sportinglife.com'
DATE = '2026-03-25'

# Try Betfair's API which might have settled orders
# Or try the Racing Post API
def try_racing_post(horse_name, date):
    """Try Racing Post results API"""
    urls = [
        f'https://www.racingpost.com/results/{date}',
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            print(f"RP {url}: {r.status_code}")
            if r.status_code == 200 and norm(horse_name) in norm(r.text):
                print(f"  Found {horse_name} in RP page")
                return r.text
        except Exception as e:
            print(f"  Error: {e}")
    return None

# Try Racing Post for March 25
print("=== Trying Racing Post ===")
r = requests.get('https://www.racingpost.com/results/2026-03-25/', headers={
    **HEADERS,
    'Referer': 'https://www.racingpost.com/',
}, timeout=30)
print(f"Racing Post: {r.status_code}, len={len(r.text)}")

found_any = False
for h in TARGET_HORSES:
    if norm(h) in norm(r.text):
        print(f"  Contains: {h}")
        found_any = True
if not found_any:
    print("  None of target horses found in RP page")
    print("  First 300 chars:", r.text[:300])

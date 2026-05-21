"""
Try Sporting Life fast-results for March 25, 2026
"""
import requests
import json
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
}

TARGET_HORSES = [
    'Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted',
    'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan'
]

def norm(s):
    return re.sub(r"\s+", " ", (s or '').strip().lower().replace('\u2019', "'"))

# Try the Sporting Life search API or racing API
# Try the racing API endpoint used by the SL site
urls_to_try = [
    'https://www.sportinglife.com/api/racing/fast-results/all',
    'https://api.sportinglife.com/racing/fast-results/all',
    'https://www.sportinglife.com/racing/results/2026-03-25',
]

for url in urls_to_try:
    print(f"\nTrying: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        print(f"  Status: {r.status_code}, Length: {len(r.text)}")
        if r.status_code == 200 and len(r.text) > 100:
            # Look for target horses
            content = r.text
            found = [h for h in TARGET_HORSES if norm(h) in norm(content)]
            if found:
                print(f"  Found target horses: {found}")
            break
    except Exception as e:
        print(f"  Error: {e}")

"""
Parse Sporting Life March 25 results page for the 9 favs-run horses
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
    s = (s or '').strip().lower()
    s = re.sub(r"\s+", " ", s)
    s = s.replace('\u2019', "'").replace('\u2018', "'").replace('&#x27;', "'")
    return s

DATE = '2026-03-25'
url = f'https://www.sportinglife.com/racing/results/{DATE}'
print(f"Fetching: {url}")
r = requests.get(url, headers=HEADERS, timeout=30)
print(f"Status: {r.status_code}, Length: {len(r.text)}")

html = r.text

# Try to parse __NEXT_DATA__ JSON
next_data_m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)
if next_data_m:
    try:
        data = json.loads(next_data_m.group(1))
        print("Found __NEXT_DATA__")
        
        # Walk the JSON to find results
        def find_races(obj, path=""):
            if isinstance(obj, dict):
                # Print keys if we see something about results/races
                keys = list(obj.keys())
                if any(k in keys for k in ['raceResults', 'races', 'results', 'runners', 'winner']):
                    print(f"  Found at {path}: keys={keys[:10]}")
                for k, v in obj.items():
                    find_races(v, f"{path}.{k}")
            elif isinstance(obj, list) and len(obj) > 0:
                find_races(obj[0], f"{path}[0]")
        
        # Just search the serialized JSON for target horse names
        data_str = next_data_m.group(1)
        for horse in TARGET_HORSES:
            h_norm = norm(horse)
            if h_norm in norm(data_str):
                print(f"  JSON contains: {horse}")
        
        # Try to find course/race structure
        props = data.get('props', {}).get('pageProps', {})
        print(f"pageProps keys: {list(props.keys())[:15]}")
        
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")

# Also try raw HTML pattern extraction  
print("\n--- Searching HTML for target horses ---")

# Quick check for each target horse context
for horse in TARGET_HORSES:
    # Find the horse name in HTML and look for nearby winner/position data
    h_norm = norm(horse)
    idx = norm(html).find(h_norm)
    if idx >= 0:
        snippet = html[max(0, idx-200):idx+300]
        # Look for position indicators
        pos_m = re.search(r'(?:position|place)[^0-9]{0,20}([0-9]{1,2})', snippet, re.I)
        won_m = re.search(r'(?:winner|won|1st)', snippet, re.I)
        print(f"\n  {horse} found at pos {idx}")
        print(f"    Context: ...{html[max(0,idx-50):idx+100].replace(chr(10),' ').strip()}...")
        if pos_m:
            print(f"    Position found: {pos_m.group(0)}")
        if won_m:
            print(f"    Winner marker: {won_m.group(0)}")

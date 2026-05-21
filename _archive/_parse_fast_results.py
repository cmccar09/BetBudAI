"""
Parse Sporting Life fast-results page for all today's races
"""
import requests, json, re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
}

TARGET_HORSES = ['Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted', 'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan']
TARGET_COURSES = {'taunton', 'southwell', 'wolverhampton', 'hereford', 'kempton'}

def norm(s):
    return re.sub(r"\s+", " ", (s or '').strip().lower()).replace('\u2019', "'").replace("'", "'")

r = requests.get('https://www.sportinglife.com/racing/fast-results/all', headers=HEADERS, timeout=30)
print(f"Fast-results: {r.status_code}, len={len(r.text)}")

html = r.text

# Parse __NEXT_DATA__
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)
if m:
    d = json.loads(m.group(1))
    pp = d.get('props', {}).get('pageProps', {})
    print(f"pageProps keys: {list(pp.keys())[:15]}")
    
    # Explore all structure keys
    def find_races(obj, path="", depth=0):
        if depth > 6:
            return
        if isinstance(obj, dict):
            if 'runners' in obj or 'winner' in obj or 'finisher' in obj or 'result' in obj.keys():
                print(f"  [RACE-LIKE at {path}]: {list(obj.keys())[:10]}")
            for k, v in obj.items():
                find_races(v, f"{path}.{k}", depth+1)
        elif isinstance(obj, list) and len(obj) > 0:
            find_races(obj[0], f"{path}[0]", depth+1)
    
    # Print the top-level structure
    for k, v in pp.items():
        if isinstance(v, list):
            print(f"  {k}: list of {len(v)} items")
            if v:
                print(f"    First item keys: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0])}")
        elif isinstance(v, dict):
            print(f"  {k}: dict keys={list(v.keys())[:10]}")
        else:
            print(f"  {k}: {type(v)}")
    
    # Look for events/meetings/races with results
    events = pp.get('events', pp.get('meetings', pp.get('races', pp.get('results', []))))
    print(f"\nEvents/races found: {len(events)}")
    
    if events and isinstance(events, list) and isinstance(events[0], dict):
        print(f"First event keys: {list(events[0].keys())[:15]}")

# Also try raw HTML scan for top_horses or position data
print("\n\n=== HTML scan for target horses ===")
all_results = {}

# Use the same pattern as _debug_sl_json2.py - top_horses: [..., position: 1, ...]
# But search within the raw JSON string
raw_str = m.group(1) if m else html

for h in TARGET_HORSES:
    h_norm = norm(h)
    idx = norm(raw_str).find(h_norm)
    if idx >= 0:
        # Get surrounding JSON context
        ctx = raw_str[max(0, idx-300):idx+500]
        # Look for position indicators
        pos_m = re.search(r'"position"\s*:\s*(\d+)', ctx)
        top_m = re.search(r'"top_horses"[^[]*\[([^\]]*)\]', ctx)
        print(f"\n  {h} found at {idx}")
        print(f"  Context snippet: {ctx[200:350].replace(chr(10),' ')}")
        if pos_m:
            print(f"  -> Position: {pos_m.group(1)}")

"""Debug: show NEXT_DATA context for Nottingham/Catterick/Gowran in SL results."""
import urllib.request, re, json

h = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36',
     'Accept':'text/html','Accept-Language':'en-GB','Referer':'https://www.sportinglife.com/'}

for date in ['2026-04-08']:
    req = urllib.request.Request(f'https://www.sportinglife.com/racing/results/{date}/', headers=h)
    html = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'replace')
    nd = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not nd:
        print('No NEXT_DATA'); continue
    raw = nd.group(1)
    # Find all occurrences of 'gowran', 'nottingham', 'catterick' in the raw JSON
    for keyword in ['gowran', 'nottingham', 'catterick']:
        idx = raw.lower().find(keyword)
        if idx >= 0:
            snippet = raw[max(0,idx-100):idx+200]
            print(f'\n=== {keyword} context (pos {idx}): ===')
            print(snippet[:300])
        else:
            print(f'\n{keyword}: NOT FOUND in NEXT_DATA')
    
    # Also try to parse and find race IDs
    data = json.loads(raw)
    # Recursively search for anything with a numeric ID that could be a race
    def find_race_like(obj, depth=0, path=''):
        if depth > 10: return
        if isinstance(obj, dict):
            for k,v in obj.items():
                p = f'{path}.{k}'
                if isinstance(v, (list, dict)):
                    find_race_like(v, depth+1, p)
                elif isinstance(v, str) and any(x in v.lower() for x in ['nottingham','gowran','catterick']):
                    print(f'  STRING match at {p}: {v[:100]}')
        elif isinstance(obj, list):
            for i,v in enumerate(obj[:50]):
                find_race_like(v, depth+1, f'{path}[{i}]')
    
    print('\n\nSearching for course names in NEXT_DATA structure:')
    find_race_like(data)

"""Fetch race winners from SL main results page for March 24"""
import requests, json, re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Referer': 'https://www.sportinglife.com/racing',
}

runners_map = {
    ('taunton', '14:15'): ['Ettore','Falls Of Acharn','Famous Shoes','Grand Harbour','Johnjay','Modern Style','Signore Enzo','Sinchi Roca'],
    ('southwell', '14:30'): ['Catchim','Classical Sting','Ferando','Known Warrior','Shadowfax Of Rohan'],
    ('southwell', '15:30'): ['Big Bert','Broderick','Honneur De Sivola','Jack The Savage','Peckforton Hills','Raby Mere','Redeeming Love'],
    ('southwell', '16:00'): ['Danger Nap','Hillberry Hill','Karlita Desbois','Sea Of Fortune','The Flier Begley','Tombereau'],
    ('hereford', '16:00'): ['Arnie Moon','Best Night','Directly','Inca','Kotgar','Madame De Labrunie','Ramaah'],
    ('wolverhampton', '16:55'): ['Angry Ant','Buckland Belle','Cape Toronada','Lexington Express','Nautical Sky','Regal And Real','Sorted','Warm Waters'],
    ('wolverhampton', '18:00'): ['Cribbins','Echo Valley','Montevetro','Royal Standard','Stepanov'],
    ('kempton', '19:30'): ['Classical Allusion','Constitution Hill','Edward Sexton','Keep It Cool','Roadlesstravelled','Serviceman','Star Artist','Victors Spirit'],
}

# Try main March 24 results page
url = 'https://www.sportinglife.com/racing/results/2026-03-24'
print(f'Fetching: {url}')
r = requests.get(url, headers=headers, timeout=20)
print(f'HTTP {r.status_code}, len={len(r.text)}')

if r.status_code == 200:
    text = r.text
    
    m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', text, re.DOTALL)
    if m:
        data = json.loads(m.group(1))
        page_props = data.get('props', {}).get('pageProps', {})
        print(f'pageProps keys: {list(page_props.keys())[:20]}')
        
        # Try to find race results
        def find_races(obj, depth=0, path=''):
            if depth > 8:
                return
            if isinstance(obj, list) and len(obj) > 0:
                first = obj[0]
                if isinstance(first, dict):
                    keys = set(first.keys())
                    if 'runners' in keys or 'result' in keys or 'winner' in keys or 'position' in keys:
                        print(f'  Races-like list at {path}: {len(obj)} items, keys={list(first.keys())[:8]}')
                        return obj
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    result = find_races(v, depth+1, f'{path}.{k}')
                    if result:
                        return result
            return None
        
        races = find_races(page_props)
        
        # Also check for specific known structure
        results_data = page_props.get('results', page_props.get('racingResults', page_props.get('data', {})))
        if isinstance(results_data, dict):
            print(f'  results_data keys: {list(results_data.keys())[:10]}')
        
        # Save raw for inspection
        with open('_sl_mar24_raw.json', 'w') as f:
            json.dump(page_props, f, indent=2)
        print(f'\nSaved page_props to _sl_mar24_raw.json ({len(json.dumps(page_props))} bytes)')
    else:
        print('No __NEXT_DATA__ found')
        # Check text for known horses
        all_runners = [h for horses in runners_map.values() for h in horses]
        found = [h for h in all_runners if h in text]
        print(f'Horses found in page text: {found}')
else:
    # Try alternative URL format
    alt_url = 'https://www.sportinglife.com/racing/results?date=2026-03-24'
    print(f'\nTrying alt: {alt_url}')
    r2 = requests.get(alt_url, headers=headers, timeout=20)
    print(f'Alt HTTP {r2.status_code}, len={len(r2.text)}')
    if r2.status_code == 200:
        with open('_sl_mar24_alt.html', 'w', encoding='utf-8') as f:
            f.write(r2.text)
        print('Saved to _sl_mar24_alt.html')

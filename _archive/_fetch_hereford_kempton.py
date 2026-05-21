"""Use SL results index page to find race URLs for March 24, then fetch individual race results"""
import re, requests, json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
    'Referer': 'https://www.sportinglife.com/',
}
SL_BASE = 'https://www.sportinglife.com'
DATE = '2026-03-24'

TARGET_RACES = {
    ('taunton', '14:15'): 'Falls Of Acharn',
    ('southwell', '14:30'): 'Shadowfax Of Rohan',
    ('southwell', '15:30'): 'Peckforton Hills',
    ('southwell', '16:00'): 'Hillberry Hill',
    ('hereford', '16:00'): 'Best Night',
    ('wolverhampton', '16:55'): 'Sorted',
    ('wolverhampton', '18:00'): 'Montevetro',
    ('kempton', '19:30'): 'Constitution Hill',
}

# From SL JSON data already loaded (we know these):
KNOWN = {
    ('taunton', '14:15'): 'Falls Of Acharn',      # WON - LAY LOST
    ('southwell', '14:30'): 'Shadowfax Of Rohan',  # WON - LAY LOST
    ('southwell', '15:30'): 'Raby Mere',            # Peckforton Hills LOST - LAY WON
    ('southwell', '16:00'): 'Hillberry Hill',       # WON - LAY LOST
    ('wolverhampton', '16:55'): 'Lexington Express', # Sorted LOST - LAY WON
    ('wolverhampton', '18:00'): 'Royal Standard',   # Montevetro LOST - LAY WON
    ('wolverhampton', '20:00'): 'Merlier',          # Time To Take Off LOST - LAY WON
}

print('Already known from SL JSON:')
for (course, time), winner in KNOWN.items():
    print(f'  {course} {time}: winner = {winner}')

# Still need: hereford 16:00 and kempton 19:30
print('\nFetching SL results index for March 24...')
idx_url = f'{SL_BASE}/racing/results/{DATE}/'
r = requests.get(idx_url, headers=HEADERS, timeout=20)
print(f'Index HTTP {r.status_code}, len={len(r.text)}')

if r.status_code != 200:
    print('Index failed!')
else:
    html = r.text
    # Find all race links
    pat = r'href="(/racing/results/' + re.escape(DATE) + r'/([^/]+)/(\d+)/([^"]+))"'
    seen = set()
    races = []
    for m in re.finditer(pat, html):
        full_path, course_slug, race_id, slug = m.group(1), m.group(2), m.group(3), m.group(4)
        key = (course_slug, race_id)
        if key in seen:
            continue
        seen.add(key)
        races.append((course_slug, race_id, SL_BASE + full_path))
    
    print(f'Found {len(races)} race links')
    
    # Show hereford and kempton ones
    for course_slug, race_id, url in races:
        if course_slug in ('hereford', 'kempton'):
            print(f'  {course_slug}: {url}')
    
    # Filter to just target courses
    for course_slug, race_id, url in races:
        if course_slug not in ('hereford', 'kempton'):
            continue
        
        print(f'\nFetching {course_slug} race {race_id}...')
        r2 = requests.get(url, headers=HEADERS, timeout=20)
        print(f'  HTTP {r2.status_code}')
        
        if r2.status_code == 200:
            html2 = r2.text
            
            # Try NEXT_DATA
            m2 = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html2, re.DOTALL)
            if m2:
                try:
                    data = json.loads(m2.group(1))
                    pp = data.get('props', {}).get('pageProps', {})
                    
                    # Look for off time
                    off_time = None
                    for k in ['offTime', 'off_time', 'time']:
                        v = pp.get(k)
                        if v:
                            off_time = v
                            break
                    
                    # Navigate to race data
                    race_data = pp.get('race', pp.get('raceData', pp.get('result', {})))
                    runners = race_data.get('runners', race_data.get('result', []))
                    
                    print(f'  off_time={off_time}')
                    print(f'  runners count={len(runners)}')
                    if runners:
                        # Get winner (pos 1)
                        for rn in runners:
                            pos = rn.get('position', rn.get('pos', ''))
                            name = rn.get('horse', {}).get('name', rn.get('name', '?'))
                            if str(pos) == '1':
                                print(f'  ** WINNER: {name} (pos={pos})')
                                break
                        print(f'  Top 3: {[(rn.get("horse",{}).get("name",rn.get("name","?")), rn.get("position","?")) for rn in runners[:3]]}')
                    else:
                        print(f'  pageProps keys: {list(pp.keys())}')
                        # Try text search
                        if 'Constitution Hill' in html2:
                            print('  Found Constitution Hill in text')
                        if 'Best Night' in html2:
                            print('  Found Best Night in text')
                except Exception as e:
                    print(f'  JSON error: {e}')
            else:
                print('  No NEXT_DATA')
                # Text search
                for horse in ['Constitution Hill', 'Best Night', 'Serviceman', 'Arnie Moon']:
                    if horse in html2:
                        print(f'  Found {horse} in text')

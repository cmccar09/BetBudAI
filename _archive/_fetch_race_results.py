"""
Fetch individual race result pages from Sporting Life for March 25, 2026
"""
import requests
import json
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
}

TARGET_HORSES = ['Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted', 'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan']

def norm(s):
    return re.sub(r"\s+", " ", (s or '').strip().lower()).replace('\u2019', "'").replace("'", "'")

DATE = '2026-03-25'
r = requests.get(f'https://www.sportinglife.com/racing/results/{DATE}', headers=HEADERS, timeout=30)
data = json.loads(re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r.text, re.DOTALL).group(1))
meetings = data['props']['pageProps']['meetings']
SL_BASE = 'https://www.sportinglife.com'

# Collect all races at target courses
TARGET_COURSES = {'hereford', 'wolverhampton', 'kempton', 'southwell', 'taunton'}

race_list = []
for meeting in meetings:
    for race in meeting['races']:
        course = (race.get('course_name') or '').lower()
        if course not in TARGET_COURSES:
            continue
        race_id = race.get('race_summary_reference', {}).get('id')
        race_time = race.get('off_time') or race.get('time', '?')
        race_name = race.get('name', '?')
        top_horses = race.get('top_horses', [])
        race_list.append({
            'course': race.get('course_name'),
            'time': race_time,
            'name': race_name,
            'id': race_id,
            'top_horses': top_horses,
        })
        print(f"{race.get('course_name')} {race_time} [{race_id}] - {race_name}")
        if top_horses:
            print(f"  Winner: {top_horses[0]}")

print(f"\nTotal target course races: {len(race_list)}")
print("\n--- Fetching individual race pages ---\n")

results_found = []

for race in race_list:
    if not race['id']:
        continue
    
    # Try to fetch the individual race result page
    # URL format: /racing/results/{date}/{course_slug}/{race_id}/{slug}
    course_slug = race['course'].lower()
    race_url = f"{SL_BASE}/racing/results/{DATE}/{course_slug}/{race['id']}/race"
    
    try:
        rr = requests.get(race_url, headers=HEADERS, timeout=20)
        if rr.status_code != 200:
            print(f"  {race['course']} {race['time']} [{race['id']}]: HTTP {rr.status_code}")
            continue
        
        html2 = rr.text
        
        # Try __NEXT_DATA__ in this page
        m2 = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html2, re.DOTALL)
        if m2:
            d2 = json.loads(m2.group(1))
            # Find runners in any structure
            raw_str = m2.group(1)
            
            # Look for horse names by searching JSON for "horse_name" or "name" near position data
            horse_chunks = re.findall(r'"name"\s*:\s*"([^"]+)"', raw_str)
            pos_chunks = re.findall(r'"position"\s*:\s*(\d+)', raw_str)
            
            # Find target horses
            for h in TARGET_HORSES:
                if norm(h) in norm(raw_str):
                    # find position context
                    idx = norm(raw_str).find(norm(h))
                    ctx = raw_str[max(0,idx-100):idx+200]
                    pos_m = re.search(r'"position"\s*:\s*(\d+)', ctx)
                    pos = int(pos_m.group(1)) if pos_m else '?'
                    print(f"  FOUND: {h} at {race['course']} {race['time']} -> pos={pos}")
                    results_found.append({'horse': h, 'course': race['course'], 'time': race['time'], 'pos': pos})
        
        # Also try HTML-level parsing
        all_runners_in_order = re.findall(
            r'StyledHorseName[^"]*"[^>]*>\s*(?:<[^>]+>)*([^<]+)</',
            html2
        )
        for h in TARGET_HORSES:
            if norm(h) in [norm(x) for x in all_runners_in_order]:
                idx = [norm(x) for x in all_runners_in_order].index(norm(h))
                print(f"  HTML found: {h} -> pos={idx+1} at {race['course']} {race['time']}")
    
    except Exception as e:
        print(f"  Error: {race['course']} {race['time']}: {e}")

print("\n=== FINAL RESULTS ===")
for res in sorted(results_found, key=lambda x: str(x.get('time',''))):
    won = res['pos'] == 1
    print(f"{res['time']} {res['course']}: {res['horse']} -> pos={res['pos']} | {'WON (lay LOST)' if won else 'LOST (lay WON)'}")

"""
Debug SL JSON - look at top_horses and race_summary_reference
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
    return re.sub(r"\s+", " ", (s or '').strip().lower()).replace('\u2019', "'")

DATE = '2026-03-25'
r = requests.get(f'https://www.sportinglife.com/racing/results/{DATE}', headers=HEADERS, timeout=30)
data = json.loads(re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r.text, re.DOTALL).group(1))
meetings = data['props']['pageProps']['meetings']

data_str = r.text

# Check ALL races for top_horses and race summaries - just show Hereford races
for meeting in meetings:
    for race in meeting['races']:
        course = race.get('course_name', '?')
        if course.lower() not in ('hereford', 'wolverhampton', 'kempton', 'southwell', 'taunton'):
            continue
        
        rtime = race.get('off_time') or race.get('time', '?')
        rname = race.get('name', '?')
        
        top_horses = race.get('top_horses', [])
        print(f"\n{course} {rtime} - {rname}")
        print(f"  top_horses: {top_horses}")
        print(f"  race_summary_reference: {race.get('race_summary_reference', '?')}")
        print(f"  verdict: {race.get('verdict', '')}")
        
        # Check if contest Hill or similar appears
        for h in TARGET_HORSES:
            if norm(h) in norm(str(race)):
                print(f"  ** CONTAINS: {h}")

# Also look at the Constitution Hill mention in the raw HTML
idx = norm(r.text).find(norm('Constitution Hill'))
if idx >= 0:
    snippet = r.text[max(0,idx-300):idx+500]
    print("\n\n=== Constitution Hill raw HTML context ===")
    print(snippet[:600])

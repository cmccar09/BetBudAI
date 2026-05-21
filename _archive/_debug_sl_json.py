"""
Debug the SL JSON structure to find the right keys
"""
import requests
import json
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
}

DATE = '2026-03-25'
url = f'https://www.sportinglife.com/racing/results/{DATE}'
r = requests.get(url, headers=HEADERS, timeout=30)
html = r.text

next_data_m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)
data = json.loads(next_data_m.group(1))
props = data['props']['pageProps']
meetings = props.get('meetings', [])

# Debug first meeting
if meetings:
    m0 = meetings[0]
    print("Meeting keys:", list(m0.keys()))
    print("Meeting name:", m0.get('name', m0.get('course_name', m0.get('meeting_name', '?'))))
    races = m0.get('races', m0.get('race', []))
    print(f"Races count: {len(races)}")
    if races:
        r0 = races[0]
        print("Race keys:", list(r0.keys()))
        runners = r0.get('runners', r0.get('horses', r0.get('horse_records', [])))
        print(f"Runners count: {len(runners)}")
        if runners:
            runner0 = runners[0]
            print("Runner keys:", list(runner0.keys()))
            print("Runner sample:", {k: v for k, v in runner0.items() if not isinstance(v, (dict, list))})

# Also show all meeting names and race names    
print("\n\n=== All meetings and races ===")
for meeting in meetings:
    m_name = meeting.get('name') or meeting.get('course_name') or str(list(meeting.keys())[:3])
    races = meeting.get('races', [])
    print(f"\nMeeting: {m_name} ({len(races)} races)")
    for race in races[:3]:
        r_name = race.get('name') or race.get('race_name') or race.get('title') or str(list(race.keys())[:3])
        off_time = race.get('off_time') or race.get('time') or race.get('start_time')
        runners = race.get('runners', [])
        print(f"  {off_time} - {r_name} ({len(runners)} runners)")
        if runners:
            runner = runners[0]
            r_name2 = runner.get('horse_name') or runner.get('name') or runner.get('horse') or str(list(runner.keys())[:5])
            print(f"    First runner keys: {list(runner.keys())[:8]}")
            print(f"    First runner: {r_name2}")

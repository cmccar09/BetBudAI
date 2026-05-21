"""
Parse Sporting Life March 25 results: full JSON extraction
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
TARGET_NORM = {h.lower(): h for h in TARGET_HORSES}

def norm(s):
    s = (s or '').strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s.replace('\u2019', "'").replace('\u2018', "'").replace('&#x27;', "'")

DATE = '2026-03-25'
url = f'https://www.sportinglife.com/racing/results/{DATE}'
r = requests.get(url, headers=HEADERS, timeout=30)
html = r.text

next_data_m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)
data = json.loads(next_data_m.group(1))
props = data['props']['pageProps']
meetings = props.get('meetings', [])

print(f"Meetings on {DATE}: {len(meetings)}")

results = {}  # horse -> {pos, winner, course, time, race_name}

for meeting in meetings:
    course_name = meeting.get('name', meeting.get('course_name', '?'))
    races = meeting.get('races', [])
    for race in races:
        race_time = race.get('off_time', race.get('time', '?'))
        race_name = race.get('name', race.get('race_name', ''))
        runners = race.get('runners', race.get('horses', []))
        
        if not runners:
            continue
        
        # Sort by finish_position
        def get_pos(r):
            pos = r.get('position', r.get('finishing_position', r.get('finish_position', 99)))
            try:
                return int(pos)
            except:
                return 99
        
        runners_sorted = sorted(runners, key=get_pos)
        winner_name = runners_sorted[0].get('horse_name', runners_sorted[0].get('name', '?')) if runners_sorted else '?'
        
        for i, runner in enumerate(runners_sorted):
            horse_name = runner.get('horse_name', runner.get('name', ''))
            h_norm = norm(horse_name)
            
            if h_norm in TARGET_NORM:
                orig_name = TARGET_NORM[h_norm]
                pos_val = get_pos(runner)
                results[orig_name] = {
                    'pos': pos_val,
                    'won': pos_val == 1,
                    'winner': winner_name,
                    'course': course_name,
                    'time': race_time,
                    'race': race_name,
                    'odds': runner.get('odds', runner.get('sp', '?')),
                }
                print(f"  FOUND: {orig_name} | {course_name} {race_time} | pos={pos_val} | winner={winner_name}")

print("\n\n=== RESULTS SUMMARY ===")
print(f"{'Horse':<25} {'Course':<15} {'Time':<6} {'Pos':>4}  {'Result':<20} {'Winner'}")
print("-" * 90)

for horse in TARGET_HORSES:
    if horse in results:
        r = results[horse]
        result_str = 'WON (lay LOST)' if r['won'] else 'LOST (lay WON)'
        print(f"{horse:<25} {r['course']:<15} {str(r['time']):<6} {r['pos']:>4}  {result_str:<20} {r['winner']}")
    else:
        print(f"{horse:<25} {'?':<15} {'?':<6} {'?':>4}  {'NOT FOUND':<20}")

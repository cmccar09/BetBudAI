"""
Parse fastResults from Sporting Life for today's races
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
html = r.text
m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)
data = json.loads(m.group(1))
fast_results = data['props']['pageProps']['fastResults']

print(f"Total fast results: {len(fast_results)}")

all_results = {}
print("\n=== Races at target courses ===")

for race in fast_results:
    course = race.get('courseName', '')
    if norm(course) not in TARGET_COURSES:
        continue
    
    race_time = race.get('time', '?')
    race_name = race.get('name', '?')
    status = race.get('status', '?')
    top_horses = race.get('top_horses', [])
    runners = race.get('runners', [])
    
    print(f"\n{course} {race_time} - {race_name} [{status}]")
    
    # top_horses has the actual results
    if top_horses:
        print(f"  Top horses: {top_horses}")
        winner = top_horses[0].get('name') if top_horses else None
        print(f"  Winner: {winner}")
    
    # Check if any target horse is in runners
    target_found = []
    for runner in runners:
        rname = runner.get('horse', {}).get('name', runner.get('name', ''))
        if any(norm(rname) == norm(h) for h in TARGET_HORSES):
            pos = runner.get('position', runner.get('finishing_position', '?'))
            print(f"  ** TARGET: {rname} pos={pos}")
            target_found.append((rname, pos))
    
    if target_found and top_horses:
        winner_name = top_horses[0].get('name', '?') if top_horses else '?'
        for (h, pos) in target_found:
            won = (pos == 1 or (pos == '1'))
            # also check if winner name matches
            if top_horses:
                won = norm(top_horses[0].get('name', '')) == norm(h)
            all_results[h] = {
                'won': won,
                'pos': pos,
                'winner': h if won else winner_name,
                'course': course,
                'time': race_time,
                'status': status,
            }

# Also check runners for target horses using a deeper scan
print("\n\n=== Deep scan of ALL runner data ===")
for race in fast_results:
    course = race.get('courseName', '')
    if norm(course) not in TARGET_COURSES:
        continue
    
    race_time = race.get('time', '?')
    runners = race.get('runners', [])
    top = race.get('top_horses', [])
    
    # Runners might be a list of dicts with different structures
    for runner in runners:
        # Try multiple possible name fields
        rname = (runner.get('horse', {}) or {}).get('name') or runner.get('name') or runner.get('horse_name') or ''
        r_norm = norm(rname)
        
        for h in TARGET_HORSES:
            if r_norm == norm(h):
                pos = runner.get('position') or runner.get('finishing_position') or runner.get('draw') or '?'
                print(f"FOUND: {h} @ {course} {race_time} | pos={pos} | runner keys={list(runner.keys())[:8]}")
                if top:
                    winner_name = top[0].get('name', '?')
                    won = norm(top[0].get('name','')) == norm(h)
                    all_results[h] = {'won': won, 'pos': pos, 'winner': h if won else winner_name, 'course': course, 'time': race_time}
                break

print("\n\n=== ALL FAVS RESULTS FOUND ===")
for h in TARGET_HORSES:
    if h in all_results:
        r = all_results[h]
        result_str = 'WON (lay LOST)' if r['won'] else f"LOST → LAY WON (winner: {r['winner']})"
        print(f"  {h}: {result_str} [{r['course']} {r['time']}]")
    else:
        print(f"  {h}: NOT YET SETTLED / PENDING")

# Save to JSON
with open('_favs_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)
print(f"\nSaved {len(all_results)} results to _favs_results.json")

# debug: show first runner structure for a target course race
print("\n\n--- First runner struct example ---")
for race in fast_results:
    if norm(race.get('courseName','')) in TARGET_COURSES and race.get('runners'):
        print(f"  Sample runner from {race.get('courseName')} {race.get('time')}:")
        r0 = race['runners'][0]
        print(f"  Keys: {list(r0.keys())}")
        print(f"  Data: {r0}")
        break

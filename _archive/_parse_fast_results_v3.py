"""
Parse Sporting Life fast-results - corrected version
top_horses[i].horse_name = horse name, position = finish position
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
    # normalize: lowercase, strip country code like (IRE), (FR), (GB)
    s = re.sub(r"\s*\([A-Z]{2,3}\)\s*$", "", (s or '').strip())
    s = re.sub(r"\s+", " ", s).lower()
    s = s.replace('\u2019', "'").replace("'", "'")
    return s.strip()

r = requests.get('https://www.sportinglife.com/racing/fast-results/all', headers=HEADERS, timeout=30)
data = json.loads(re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r.text, re.DOTALL).group(1))
fast_results = data['props']['pageProps']['fastResults']

print(f"Total fast results: {len(fast_results)}")
print(f"Target horse norms: {[norm(h) for h in TARGET_HORSES]}")

all_results = {}

print("\n=== Races at target courses ===")
for race in fast_results:
    course = race.get('courseName', '')
    if norm(course).split('(')[0].strip() not in TARGET_COURSES and course.lower() not in TARGET_COURSES:
        continue
    
    race_time = race.get('time', '?')
    race_name = race.get('name', '?')
    status = race.get('status', '?')
    top_horses = race.get('top_horses', [])
    
    print(f"\n{course} {race_time} - {race_name} [{status}]")
    
    if not top_horses:
        print("  No top_horses data (race pending or no results)")
        # Still check if a target horse is listed in top_horses search
        for h in TARGET_HORSES:
            if norm(h) in norm(json.dumps(race)):
                print(f"  ** Reference to {h} found in race data")
        continue
    
    # top_horses[0] is the winner
    winner_name = top_horses[0].get('horse_name', '?')
    winner_fav = top_horses[0].get('favourite', False)
    print(f"  WINNER: {winner_name} (fav={winner_fav}) - top positions: {[(t.get('horse_name','?')[:20], t.get('position','?')) for t in top_horses[:3]]}")
    
    # Check if any target horse is in top_horses
    for th in top_horses:
        rname = th.get('horse_name', '')
        pos = th.get('position', '?')
        for h in TARGET_HORSES:
            if norm(rname) == norm(h):
                won = (pos == 1)
                print(f"  ** TARGET FOUND: {h} pos={pos} {'<-- WON' if won else f'<-- lost (winner={winner_name})'}")
                all_results[h] = {
                    'won': won,
                    'pos': pos,
                    'winner': h if won else winner_name,
                    'course': course,
                    'time': race_time,
                    'status': status,
                    'winner_fav': winner_fav if not won else True,
                }

print("\n\n=== FINAL RESULTS ===")
total_settled = len(all_results)
if total_settled:
    lay_wins = [h for h, r in all_results.items() if not r['won']]
    lay_losses = [h for h, r in all_results.items() if r['won']]
    print(f"Settled: {total_settled} | Lay WON (fav lost): {len(lay_wins)} | Lay LOST (fav won): {len(lay_losses)}")

for h in TARGET_HORSES:
    if h in all_results:
        res = all_results[h]
        if res['won']:
            print(f"  {h:<25} WON  → LAY ❌ LOST  [{res['course']} {res['time']}]")
        else:
            print(f"  {h:<25} LOST → LAY ✓ WON   [{res['course']} {res['time']}] winner: {res['winner']}")
    else:
        print(f"  {h:<25} -- PENDING (not yet run)")

# Save to file
with open('_favs_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)
print(f"\nSaved {len(all_results)} results to _favs_results.json")

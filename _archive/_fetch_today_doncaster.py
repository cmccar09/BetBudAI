import requests, json, re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,*/*',
    'Accept-Language': 'en-GB,en;q=0.5',
}

DATE = '2026-03-29'
TARGET_HORSES = ['say what you see', 'jimmy speaking', 'fine interview']
TARGET_TIMES = ['14:55', '16:05', '17:15']

r = requests.get('https://www.sportinglife.com/racing/results/' + DATE, headers=HEADERS, timeout=30)
m = re.search('<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r.text, re.DOTALL)
if not m:
    print('ERROR: no __NEXT_DATA__'); exit(1)

data = json.loads(m.group(1))
meetings = data['props']['pageProps']['meetings']

doncaster_races = []
for mtg in meetings:
    ms = mtg.get('meeting_summary', {})
    course = ms.get('course', {}).get('name', '') or ''
    if 'doncaster' not in course.lower():
        continue
    going = ms.get('going', '')
    print(f"=== {course} ({going}) ===\n")
    for race in mtg['races']:
        t = race.get('off_time') or race.get('time', '?')
        name = race.get('name', '?')
        top = race.get('top_horses', [])
        stage = race.get('race_stage', '')
        marker = ' <<< OUR PICK' if t in TARGET_TIMES else ''
        print(f"{t}  {name}  [{stage}]{marker}")
        if top:
            for pos, h in enumerate(top[:5], 1):
                # h can be a string or dict
                if isinstance(h, dict):
                    hname = h.get('horse_name') or h.get('name') or h.get('horse') or str(h)
                    odds = h.get('starting_price') or h.get('sp') or ''
                    extra = f"  SP: {odds}" if odds else ''
                else:
                    hname = str(h)
                    extra = ''
                hn = hname.lower()
                flag = '  *** PICK' if any(th in hn for th in TARGET_HORSES) else ''
                print(f"  {pos}. {hname}{flag}{extra}")
        else:
            print(f"  [results pending]")
        print()

print('\nAll meeting courses:')
for mtg in meetings:
    ms = mtg.get('meeting_summary', {})
    print(f"  {ms.get('course', {}).get('name')} — {len(mtg.get('races', []))} races — status: {ms.get('status')}")

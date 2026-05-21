"""Fetch race winners for March 24 races from Sporting Life"""
import requests, json, re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*',
    'Accept-Language': 'en-GB,en;q=0.9'
}

# target races: course -> [(time, fav_horse)]
targets = {
    'taunton': [('14:15', 'Falls Of Acharn')],
    'southwell': [('14:30', 'Shadowfax Of Rohan'), ('15:30', 'Peckforton Hills'), ('16:00', 'Hillberry Hill')],
    'hereford': [('16:00', 'Best Night')],
    'wolverhampton': [('16:55', 'Sorted'), ('18:00', 'Montevetro')],
    'kempton': [('19:30', 'Constitution Hill')],
}

# Full runner lists per race (from DynamoDB)
runners = {
    ('taunton', '14:15'): ['Ettore','Falls Of Acharn','Famous Shoes','Grand Harbour','Johnjay','Modern Style','Signore Enzo','Sinchi Roca'],
    ('southwell', '14:30'): ['Catchim','Classical Sting','Ferando','Known Warrior','Shadowfax Of Rohan'],
    ('southwell', '15:30'): ['Big Bert','Broderick','Honneur De Sivola','Jack The Savage','Peckforton Hills','Raby Mere','Redeeming Love'],
    ('southwell', '16:00'): ['Danger Nap','Hillberry Hill','Karlita Desbois','Sea Of Fortune','The Flier Begley','Tombereau'],
    ('hereford', '16:00'): ['Arnie Moon','Best Night','Directly','Inca','Kotgar','Madame De Labrunie','Ramaah'],
    ('wolverhampton', '16:55'): ['Angry Ant','Buckland Belle','Cape Toronada','Lexington Express','Nautical Sky','Regal And Real','Sorted','Warm Waters'],
    ('wolverhampton', '18:00'): ['Cribbins','Echo Valley','Montevetro','Royal Standard','Stepanov'],
    ('kempton', '19:30'): ['Classical Allusion','Constitution Hill','Edward Sexton','Keep It Cool','Roadlesstravelled','Serviceman','Star Artist','Victors Spirit'],
}

results = {}

for course, race_list in targets.items():
    url = f'https://www.sportinglife.com/racing/results/2026-03-24/{course}'
    print(f'\nFetching {course}: {url}')
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f'  HTTP {r.status_code}, len={len(r.text)}')
        text = r.text
        
        # Try to find NEXT_DATA JSON
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', text, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group(1))
                # Navigate to results
                page_props = data.get('props', {}).get('pageProps', {})
                races_data = page_props.get('races', page_props.get('racecardData', []))
                if not races_data:
                    # Try other paths
                    for key in page_props:
                        v = page_props[key]
                        if isinstance(v, list) and len(v) > 0:
                            print(f'  pageProps key "{key}" is a list of {len(v)}')
                    print(f'  pageProps keys: {list(page_props.keys())[:10]}')
                else:
                    print(f'  Found {len(races_data)} races')
                    for race in races_data:
                        rtime = race.get('off', race.get('time', ''))
                        runners_list = race.get('runners', race.get('result', []))
                        winner = None
                        for rn in runners_list:
                            pos = rn.get('position', rn.get('pos', ''))
                            if str(pos) == '1':
                                winner = rn.get('horse', rn.get('name', '?'))
                                break
                        print(f'    Race {rtime}: winner={winner}')
                        for (time, fav) in race_list:
                            if time in str(rtime):
                                results[(course, time)] = winner
            except Exception as e:
                print(f'  JSON parse error: {e}')
        else:
            print('  No __NEXT_DATA__ found')
            # Search for known runner names in text
            for (time, fav) in race_list:
                race_runners = runners.get((course, time), [])
                found_horses = []
                for runner in race_runners:
                    if runner in text:
                        found_horses.append(runner)
                print(f'  {time} ({fav}): found in text: {found_horses}')
    except Exception as e:
        print(f'  Error: {e}')

print('\n\n=== RESULTS SUMMARY ===')
for (course, time), winner in sorted(results.items()):
    print(f'  {course} {time}: winner = {winner}')

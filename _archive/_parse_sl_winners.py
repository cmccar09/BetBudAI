import json

with open('_sl_mar24_raw.json') as f:
    data = json.load(f)

meetings = data.get('meetings', [])

target_horses = {
    'Falls Of Acharn', 'Shadowfax Of Rohan', 'Peckforton Hills',
    'Hillberry Hill', 'Best Night', 'Sorted', 'Montevetro',
    'Constitution Hill', 'Time To Take Off'
}

print(f'Total meetings: {len(meetings)}\n')

for mtg in meetings:
    races = mtg.get('races', [])
    for race in races:
        course = race.get('course_name', '?')
        time = race.get('time', '?')
        top_horses = race.get('top_horses', [])
        
        # Check if any target horse is in this race
        horse_names = [h.get('horse', {}).get('name', '') if isinstance(h, dict) else '' for h in top_horses]
        
        # Show race info
        if len(top_horses) > 0:
            first = top_horses[0]
            if isinstance(first, dict):
                # Get winner (position 1)
                winner = None
                for h in top_horses:
                    pos = h.get('position', h.get('pos', ''))
                    hname = h.get('horse', {}).get('name', h.get('name', '?')) if isinstance(h, dict) else '?'
                    if str(pos) == '1':
                        winner = hname
                        break
                
                # Check if any fav is in this race
                runner_names = [h.get('horse', {}).get('name', h.get('name', '')) for h in top_horses]
                fav_in_race = [f for f in target_horses if f in runner_names]
                
                if fav_in_race or course in ['Taunton', 'Southwell', 'Wolverhampton', 'Hereford', 'Kempton']:
                    print(f'{course} {time}: winner={winner} | top_horses={runner_names[:4]}', end='')
                    if fav_in_race:
                        print(f' ** FAV: {fav_in_race}', end='')
                    print()
        else:
            # No top_horses - show what info exists
            if race.get('course_name') in ['Taunton', 'Southwell', 'Wolverhampton', 'Hereford', 'Kempton']:
                print(f'{course} {time}: NO top_horses | race_stage={race.get("race_stage")}')

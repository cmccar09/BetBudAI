import json

with open('_sl_mar24_raw.json') as f:
    data = json.load(f)

meetings = data.get('meetings', [])
print(f'Total meetings: {len(meetings)}\n')

for i, mtg in enumerate(meetings):
    summary = mtg.get('meeting_summary', {})
    races = mtg.get('races', [])
    
    # Get course from first race
    course = '?'
    if races:
        course = races[0].get('course_name', '?')
    
    print(f'Meeting {i}: course={course}, {len(races)} races')
    for race in races:
        rtime = race.get('time', '?')
        top = race.get('top_horses', [])
        winner = None
        if top:
            first = top[0]
            if isinstance(first, dict):
                winner = first.get('horse', {}).get('name', first.get('name', '?'))
        print(f'  {rtime}: winner={winner}, top_count={len(top)}')
    print()

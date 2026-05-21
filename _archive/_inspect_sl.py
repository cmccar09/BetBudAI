import json

with open('_sl_mar24_raw.json') as f:
    data = json.load(f)

meetings = data.get('meetings', [])
print(f'Total meetings: {len(meetings)}')

for m in meetings[:2]:
    keys = list(m.keys())
    print(f'  Meeting keys: {keys}')
    course = m.get('course', m.get('name', m.get('courseName', '?')))
    print(f'  Course: {course}')
    races = m.get('races', m.get('results', []))
    print(f'  Races count: {len(races)}')
    if races:
        r0 = races[0]
        print(f'  First race keys: {list(r0.keys())}')
        print(f'  First race sample: {json.dumps(r0, indent=2)[:500]}')
    print()

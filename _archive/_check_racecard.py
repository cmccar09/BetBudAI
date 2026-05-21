import json, datetime

with open('racecard_cache.json', encoding='utf-8') as f:
    d = json.load(f)

print('Dates in cache:', list(d.keys()))
today = str(datetime.date.today())
if today in d:
    courses = d[today]
    total = sum(len(v) for v in courses.values())
    print(f'Today: {total} races across {len(courses)} courses')
    for c, races in courses.items():
        runners_per_race = [len(r.get('runners', [])) for r in races]
        print(f'  {c}: {len(races)} races -> runners: {runners_per_race}')

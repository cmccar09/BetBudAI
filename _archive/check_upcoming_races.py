import json
from datetime import datetime

with open('response_horses.json') as f:
    data = json.load(f)

races = data.get('races', [])
now = datetime.now()

print(f"Current time: {now.strftime('%H:%M')}")
print(f"Total races in snapshot: {len(races)}\n")

upcoming = []
for race in races:
    start_time_str = race.get('start_time', '')
    if start_time_str:
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            if start_time.replace(tzinfo=None) > now:
                upcoming.append(race)
        except:
            pass

print(f"Upcoming races: {len(upcoming)}\n")
for race in upcoming[:10]:
    course = race.get('course', '?')
    start = race.get('start_time', '?')
    print(f"  - {course} @ {start}")

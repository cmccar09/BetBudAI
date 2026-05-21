import json

data = json.load(open('response_horses.json'))
print('Source:', data.get('source'))
print('Total races:', len(data.get('races', [])))
print()

for r in data.get('races', []):
    course = r.get('course', '')
    rt = r.get('race_time', '')
    if 'Wolverhampton' in course:
        print(f'{rt} {course}:')
        for runner in r.get('runners', []):
            print(f'  - {runner.get("name")} {runner.get("odds")}')
        print()

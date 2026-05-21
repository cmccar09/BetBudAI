import csv

# Read the CSV
with open('today_picks.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    picks = list(reader)

doncaster_picks = [p for p in picks if p['venue'] == 'Doncaster' and '14:05' in p['start_time_dublin']]

print(f"Total Doncaster 14:05 picks in CSV: {len(doncaster_picks)}\n")

for pick in doncaster_picks:
    # Simulate the race_key logic
    race_time = pick.get('start_time_dublin', '')
    normalized_time = race_time.replace('.000Z', '').replace('Z', '').split('+')[0].split('.')[0]
    race_key = f"{pick.get('venue', 'Unknown')}_{normalized_time}"
    
    print(f"{pick['runner_name']}:")
    print(f"  race_time: {race_time}")
    print(f"  normalized: {normalized_time}")
    print(f"  race_key: {race_key}")
    print()

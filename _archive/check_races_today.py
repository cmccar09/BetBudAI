import json
from datetime import datetime

# Load the response file
with open('response_horses.json', 'r') as f:
    data = json.load(f)

races = data.get('races', [])

print(f'\nTotal races available: {len(races)}')
print(f'Current time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('\nFirst 10 races:')

for i, race in enumerate(races[:10], 1):
    venue = race.get('venue', 'Unknown')
    start_time = race.get('marketStartTime', '')[:16]
    market_name = race.get('marketName', 'Unknown')
    print(f'{i}. {start_time} - {venue:20} - {market_name}')

# Check today's picks
print('\n' + '='*80)
print('Today picks file content:')
with open('today_picks.csv', 'r') as f:
    lines = f.readlines()
    print(f'Total lines: {len(lines)}')
    if len(lines) > 1:
        print('\nFirst few picks:')
        for line in lines[:5]:
            if 'runner_name' not in line:
                parts = line.split(',')
                if len(parts) >= 6:
                    print(f'  {parts[0]} @ {parts[4]} - {parts[5][:16]}')

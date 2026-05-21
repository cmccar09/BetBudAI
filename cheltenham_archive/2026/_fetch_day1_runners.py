"""
Fetch all Cheltenham Day 1 (10 Mar 2026) runners from Betfair
and print in a format usable for updating cheltenham_full_fields_2026.py
"""
import json, requests, sys

with open('betfair-creds.json') as f:
    creds = json.load(f)

headers = {
    'X-Application': creds['app_key'],
    'X-Authentication': creds['session_token'],
    'Content-Type': 'application/json'
}

# ── Step 1: Get all Day 1 markets ─────────────────────────────────────────
r = requests.post(
    'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/',
    headers=headers,
    json={
        'filter': {
            'eventTypeIds': ['7'],
            'marketCountries': ['GB', 'IE'],
            'textQuery': 'Cheltenham',
            'marketStartTime': {
                'from': '2026-03-10T00:00:00Z',
                'to':   '2026-03-10T23:59:59Z'
            }
        },
        'marketProjection': ['MARKET_START_TIME', 'RUNNER_DESCRIPTION', 'EVENT', 'RUNNER_METADATA'],
        'maxResults': '30',
        'sort': 'FIRST_TO_START'
    },
    timeout=15
)

if r.status_code != 200:
    print(f'ERROR {r.status_code}: {r.text[:300]}')
    sys.exit(1)

markets = r.json()

# Filter to WIN markets only (skip each-way, forecast etc.)
win_markets = [m for m in markets if m.get('marketName', '').lower() not in ('each way', 'place only', 'forecast')]

# ── Step 2: Print runners per race ────────────────────────────────────────
day1_races = {}

for m in win_markets:
    time_str = m['marketStartTime'][:16]  # "2026-03-10T13:20"
    time_hm  = time_str[11:]              # "13:20"
    race_name = m.get('marketName', '?')
    runners = sorted(
        m.get('runners', []),
        key=lambda x: x.get('sortPriority', 99)
    )
    names = [ru['runnerName'] for ru in runners]

    print(f"\n{time_hm}  {race_name}  ({len(names)} runners)")
    for i, n in enumerate(names, 1):
        sel_id = runners[i-1].get('selectionId', '')
        print(f"  {i:2}. {n:<35} (id={sel_id})")

    day1_races[time_hm] = {
        'market_name': race_name,
        'market_id': m['marketId'],
        'runners': names
    }

# ── Step 3: Save as JSON for use by update script ─────────────────────────
with open('_day1_runners_betfair.json', 'w') as f:
    json.dump(day1_races, f, indent=2)

print(f"\n\nSaved {len(day1_races)} races to _day1_runners_betfair.json")

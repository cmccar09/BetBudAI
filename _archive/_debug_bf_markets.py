"""
Debug: show all Betfair markets for March 25 to find missing courses
"""
import requests
import json

with open('betfair-creds.json') as f:
    creds = json.load(f)

APP_KEY = creds['app_key']
TOKEN = creds['session_token']

def bf(method, params):
    r = requests.post(
        f'https://api.betfair.com/exchange/betting/rest/v1.0/{method}/',
        json=params,
        headers={'X-Application': APP_KEY, 'X-Authentication': TOKEN, 'Content-Type': 'application/json'},
        timeout=30
    )
    return r.json() if r.status_code == 200 else print(f"Err {r.status_code}: {r.text[:200]}")

markets = bf('listMarketCatalogue', {
    "filter": {
        "eventTypeIds": ["7"],
        "marketCountries": ["GB"],
        "marketTypeCodes": ["WIN"],
        "marketStartTime": {
            "from": "2026-03-25T00:00:00Z",
            "to": "2026-03-26T00:00:00Z"
        }
    },
    "sort": "FIRST_TO_START",
    "maxResults": 200,
    "marketProjection": ["RUNNER_METADATA", "RUNNER_DESCRIPTION", "EVENT", "MARKET_START_TIME", "COMPETITION"]
})

print(f"Total markets: {len(markets or [])}")
print("\nAll markets:")
for m in (markets or []):
    venue = m.get('event', {}).get('venue', m.get('event', {}).get('name', '?'))
    start = m.get('marketStartTime', '')
    mname = m.get('marketName', '')
    mid = m.get('marketId', '')
    runners = m.get('runners', [])
    print(f"  {venue:20} {start[11:16]} | {mname:30} | {mid} | {len(runners)} runners")
    # Check if any of our target horses are here
    for r in runners:
        rname = r.get('runnerName','')
        targets = ['Montevetro', 'Time To Take Off', 'Constitution Hill','Peckforton Hills', 'Hillberry Hill', 'Sorted', 'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan']
        if any(t.lower() == rname.lower() for t in targets):
            print(f"    ** {rname}")

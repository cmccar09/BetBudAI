"""Fetch 18 March 2026 race results from Betfair for our 3 pending picks."""
import json, requests

with open('betfair-creds.json') as f:
    creds = json.load(f)

BETFAIR_API = 'https://api.betfair.com/exchange/betting/rest/v1.0'
headers = {
    'X-Application': creds['app_key'],
    'X-Authentication': creds['session_token'],
    'Content-Type': 'application/json',
}

OUR_HORSES = ['Ballynaheer', 'Just Aidan', 'Final Night']

# Step 1: Find markets for these races
print('Searching for GB WIN markets on 18 March 2026...')
r = requests.post(f'{BETFAIR_API}/listMarketCatalogue/', headers=headers, json={
    'filter': {
        'eventTypeIds': ['7'],
        'marketCountries': ['GB'],
        'marketTypeCodes': ['WIN'],
        'marketStartTime': {'from': '2026-03-18T13:00:00Z', 'to': '2026-03-18T22:00:00Z'}
    },
    'marketProjection': ['MARKET_NAME', 'RUNNER_DESCRIPTION', 'MARKET_START_TIME', 'EVENT'],
    'sort': 'FIRST_TO_START',
    'maxResults': 40
})
print('Status:', r.status_code)
data = r.json()

if not isinstance(data, list):
    print('Error:', data)
    exit(1)

print(f'Got {len(data)} markets')
found_markets = {}
for m in data:
    mn = m.get('marketName', '')
    st = m.get('marketStartTime', '')
    mid = m.get('marketId', '')
    ev = m.get('event', {}).get('name', '')
    runners = {rn.get('selectionId'): rn.get('runnerName', '') for rn in m.get('runners', [])}
    runner_names = list(runners.values())
    for h in OUR_HORSES:
        if h in runner_names:
            print(f'\nFOUND: {h} in market {mid} - {ev} - {mn} @ {st}')
            print(f'  Runners: {runner_names}')
            found_markets[mid] = {'name': mn, 'event': ev, 'time': st, 'runners': runners}

if not found_markets:
    print('\nNo matching markets found. Checked events:')
    for m in data[:5]:
        print(f"  {m.get('event',{}).get('name','')} - {m.get('marketName','')} @ {m.get('marketStartTime','')}")
    exit(1)

# Step 2: Get market book to find winners
print('\n\nGetting market books for settled results...')
market_ids = list(found_markets.keys())
r2 = requests.post(f'{BETFAIR_API}/listMarketBook/', headers=headers, json={
    'marketIds': market_ids,
    'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
    'orderProjection': 'EXECUTABLE',
    'matchProjection': 'NO_ROLLUP'
})
books = r2.json()
print(f'Got {len(books)} market books')

for book in books:
    mid = book.get('marketId')
    status = book.get('status')
    info = found_markets.get(mid, {})
    print(f'\nMarket {mid} - {info.get("name")} - Status: {status}')
    runners_info = info.get('runners', {})
    for runner in book.get('runners', []):
        sel_id = runner.get('selectionId')
        r_status = runner.get('status')
        sp = runner.get('lastPriceTraded')
        name = runners_info.get(sel_id, f'sel_{sel_id}')
        print(f'  {name:30} status={r_status}  sp={sp}')

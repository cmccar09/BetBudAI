import json, requests

with open('betfair-creds.json') as f:
    creds = json.load(f)

url = 'https://identitysso-cert.betfair.com/api/certlogin'
headers = {'X-Application': creds['app_key'], 'Content-Type': 'application/x-www-form-urlencoded'}
data = {'username': creds['username'], 'password': creds['password']}
r = requests.post(url, headers=headers, data=data, cert=('betfair-client.crt', 'betfair-client.key'), timeout=10)
token = r.json()['sessionToken']
print('Logged in')

sel_ids = {67637275, 80332611, 68799508, 8581909, 96512233}
api_url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/'
api_headers = {
    'X-Application': creds['app_key'],
    'X-Authentication': token,
    'content-type': 'application/json'
}
payload = {
    'filter': {
        'eventTypeIds': ['7'],
        'marketCountries': ['GB', 'IE'],
        'marketStartTime': {'from': '2026-04-05T12:00:00Z', 'to': '2026-04-05T18:00:00Z'},
        'marketTypeCodes': ['WIN']
    },
    'marketProjection': ['EVENT', 'RUNNER_DESCRIPTION', 'MARKET_START_TIME'],
    'maxResults': '200'
}
resp = requests.post(api_url, headers=api_headers, json=payload, timeout=10)
markets = resp.json()
print(f'Got {len(markets)} markets')

found = {}
for mkt in markets:
    for runner in mkt.get('runners', []):
        sid = runner['selectionId']
        if sid in sel_ids:
            event = mkt.get('event', {})
            venue = event.get('venue') or event.get('name', 'Unknown')
            mkt_time = mkt.get('marketStartTime', '')
            found[sid] = {
                'horse': runner['runnerName'],
                'venue': venue,
                'market_id': mkt['marketId'],
                'time': mkt_time
            }

for sid, info in found.items():
    print(f"selId={sid} horse={info['horse']} venue={info['venue']} mktId={info['market_id']} time={info['time']}")

missing = sel_ids - set(found.keys())
if missing:
    print(f"NOT FOUND: {missing}")

import json, requests, sys

sys.stdout.reconfigure(encoding='utf-8')

with open('betfair-creds.json') as f:
    c = json.load(f)
resp = requests.post('https://identitysso-cert.betfair.com/api/certlogin',
    data={'username': c['username'], 'password': c['password']},
    headers={'X-Application': c['app_key'], 'Content-Type': 'application/x-www-form-urlencoded'},
    cert=('betfair-client.crt','betfair-client.key'), timeout=30)
token = resp.json()['sessionToken']
app_key = c['app_key']
headers = {'X-Application': app_key, 'X-Authentication': token, 'Content-Type': 'application/json'}

# Try listEvents for today's horse racing at Musselburgh
url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listEvents/'
r = requests.post(url, headers=headers, json={
    "filter": {
        "eventTypeIds": ["7"],
        "venues": ["Musselburgh"],
        "marketStartTime": {"from": "2026-03-20T00:00:00Z", "to": "2026-03-21T00:00:00Z"}
    }
}, timeout=30)
print("listEvents response:", r.text[:2000])

# Also try listMarketTypes
print("\nTrying listMarketCatalogue with WIN markets for today:")
url2 = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/'
r2 = requests.post(url2, headers=headers, json={
    "filter": {
        "eventTypeIds": ["7"],
        "venues": ["Musselburgh"],
        "marketTypeCodes": ["WIN"],
        "marketStartTime": {"from": "2026-03-20T15:00:00Z", "to": "2026-03-20T16:00:00Z"}
    },
    "marketProjection": ["RUNNER_DESCRIPTION", "MARKET_START_TIME"],
    "maxResults": 5
}, timeout=30)
print("listMarketCatalogue WIN response:", r2.text[:2000])

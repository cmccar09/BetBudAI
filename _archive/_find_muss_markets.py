"""Try different Betfair API approaches to find Musselburgh 15:22 markets."""
import json, requests, sys
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding='utf-8')

with open('betfair-creds.json') as f:
    c = json.load(f)
resp = requests.post('https://identitysso-cert.betfair.com/api/certlogin',
    data={'username': c['username'], 'password': c['password']},
    headers={'X-Application': c['app_key'], 'Content-Type': 'application/x-www-form-urlencoded'},
    cert=('betfair-client.crt','betfair-client.key'), timeout=30)
token = resp.json()['sessionToken']
app_key = c['app_key']
bf_headers = {'X-Application': app_key, 'X-Authentication': token, 'Content-Type': 'application/json'}

# Try listMarketCatalogue with broad filters
cat_url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/'

# Approach 1: Search by text query for "Light Fandango"
print("=== Approach 1: Text search for 'Light Fandango' ===")
r = requests.post(cat_url, headers=bf_headers, json={
    'filter': {
        'textQuery': 'Light Fandango',
        'eventTypeIds': ['7'],  # Horse Racing
    },
    'maxResults': '10',
    'marketProjection': ['RUNNER_DESCRIPTION', 'MARKET_START_TIME', 'EVENT']
}, timeout=30)
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))

# Approach 2: Search all Musselburgh markets with broad date range
print("\n=== Approach 2: Musselburgh markets (broad date range) ===")
r2 = requests.post(cat_url, headers=bf_headers, json={
    'filter': {
        'eventTypeIds': ['7'],
        'venues': ['Musselburgh'],
        'marketStartTime': {
            'from': '2026-03-20T00:00:00Z',
            'to': '2026-03-20T23:59:00Z'
        }
    },
    'maxResults': '50',
    'marketProjection': ['RUNNER_DESCRIPTION', 'MARKET_START_TIME', 'EVENT', 'MARKET_DESCRIPTION']
}, timeout=30)
print(f"Status: {r2.status_code}")
data2 = r2.json()
print(json.dumps(data2, indent=2))

# Approach 3: listEvents for Musselburgh today
print("\n=== Approach 3: listEvents for Musselburgh today ===")
events_url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listEvents/'
r3 = requests.post(events_url, headers=bf_headers, json={
    'filter': {
        'eventTypeIds': ['7'],
        'venues': ['Musselburgh'],
        'marketStartTime': {
            'from': '2026-03-19T00:00:00Z',
            'to': '2026-03-21T00:00:00Z'
        }
    }
}, timeout=30)
print(f"Status: {r3.status_code}")
print(json.dumps(r3.json(), indent=2))

# Approach 4: listMarketCatalogue without venue, just search today's horse racing
print("\n=== Approach 4: All today's horse racing markets (no venue filter) ===")
r4 = requests.post(cat_url, headers=bf_headers, json={
    'filter': {
        'eventTypeIds': ['7'],
        'marketStartTime': {
            'from': '2026-03-20T15:15:00Z',
            'to': '2026-03-20T15:30:00Z'
        }
    },
    'maxResults': '50',
    'marketProjection': ['RUNNER_DESCRIPTION', 'MARKET_START_TIME', 'EVENT', 'MARKET_DESCRIPTION']
}, timeout=30)
print(f"Status: {r4.status_code}")
print(json.dumps(r4.json(), indent=2))

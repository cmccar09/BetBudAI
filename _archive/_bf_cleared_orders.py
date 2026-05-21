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

# Try listClearedOrders for today
url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listClearedOrders/'
r = requests.post(url, headers=headers, json={
    "betStatus": "SETTLED",
    "settledDateRange": {"from": "2026-03-20T00:00:00Z", "to": "2026-03-21T00:00:00Z"},
    "recordCount": 100
}, timeout=30)
print("listClearedOrders:")
data = r.json()
print(json.dumps(data, indent=2)[:5000])

"""
Get results for Best Night and Constitution Hill from Betfair with fresh auth
Also better cross-reference Wolverhampton races
"""
import requests
import json
import boto3

with open('betfair-creds.json') as f:
    creds = json.load(f)

APP_KEY = creds['app_key']
USERNAME = creds['username']
PASSWORD = creds['password']
CERT = ('./betfair-client.crt', './betfair-client.key')

def login():
    r = requests.post(
        'https://identitysso-cert.betfair.com/api/certlogin',
        data={'username': USERNAME, 'password': PASSWORD},
        headers={'X-Application': APP_KEY, 'Content-Type': 'application/x-www-form-urlencoded'},
        cert=CERT, timeout=20
    )
    d = r.json()
    token = d.get('sessionToken') if d.get('loginStatus') == 'SUCCESS' else None
    if token:
        creds['session_token'] = token
        with open('betfair-creds.json', 'w') as f:
            json.dump(creds, f, indent=2)
        print("Logged in OK")
    else:
        print(f"Login failed: {d}")
    return token

def bf(method, params, token):
    r = requests.post(
        f'https://api.betfair.com/exchange/betting/rest/v1.0/{method}/',
        json=params,
        headers={'X-Application': APP_KEY, 'X-Authentication': token, 'Content-Type': 'application/json'},
        timeout=30
    )
    if r.status_code == 200:
        result = r.json()
        if isinstance(result, dict) and result.get('faultcode'):
            print(f"  API fault: {result.get('faultstring')}")
            return None
        return result
    print(f"  HTTP {r.status_code}: {r.text[:200]}")
    return None

token = login()
if not token:
    exit(1)

TARGET_HORSES = ['Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted', 'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan']

def norm(s):
    return (s or '').strip().lower()

# Get all 23 markets again
markets_cat = bf('listMarketCatalogue', {
    "filter": {
        "eventTypeIds": ["7"],
        "marketCountries": ["GB"],
        "marketTypeCodes": ["WIN"],
        "marketStartTime": {"from": "2026-03-25T00:00:00Z", "to": "2026-03-26T00:00:00Z"}
    },
    "sort": "FIRST_TO_START",
    "maxResults": 200,
    "marketProjection": ["RUNNER_DESCRIPTION", "EVENT", "MARKET_START_TIME"]
}, token)

if not markets_cat:
    print("No markets")
    exit()

mkt_map = {m['marketId']: m for m in markets_cat}
print(f"Got {len(mkt_map)} markets")

# Check specific races
target_market_ids = []
for mkt_id, m in mkt_map.items():
    runners = m.get('runners', [])
    for r in runners:
        if any(norm(r.get('runnerName','')) == norm(h) for h in TARGET_HORSES):
            target_market_ids.append(mkt_id)
            break

print(f"Target markets: {target_market_ids}")

# Get market books for target markets
ALL_RESULTS = {}

books = bf('listMarketBook', {
    "marketIds": target_market_ids,
    "priceProjection": {"priceData": ["SP_TRADED"]},
}, token)

print(f"\nBooks returned: {len(books or [])}")
for b in (books or []):
    mkt_id = b['marketId']
    status = b.get('status', '?')
    m = mkt_map.get(mkt_id, {})
    venue = m.get('event', {}).get('venue', '?')
    start = m.get('marketStartTime', '')[11:16]
    runners_cat = {r['selectionId']: r for r in m.get('runners', [])}
    runners_book = b.get('runners', [])
    
    print(f"\n{venue} {start} [{mkt_id}] status={status}")
    
    for rb in runners_book:
        sel_id = rb['selectionId']
        rstatus = rb.get('status', '?')
        rname = runners_cat.get(sel_id, {}).get('runnerName', f'sel_{sel_id}')
        sp = rb.get('sp', {})
        print(f"  {rstatus:8} {rname} sp_actual={sp.get('actualSP','?')}")
        
        if any(norm(rname) == norm(h) for h in TARGET_HORSES):
            if rstatus == 'WINNER':
                ALL_RESULTS[rname] = {'won': True, 'course': venue, 'time': start}
                print(f"   *** WON!")
            elif rstatus == 'LOSER':
                # Find winner
                winner = next((runners_cat.get(r['selectionId'],{}).get('runnerName','?') 
                               for r in runners_book if r.get('status')=='WINNER'), '?')
                ALL_RESULTS[rname] = {'won': False, 'winner': winner, 'course': venue, 'time': start}
                print(f"   --- LOST (winner={winner})")

print("\n=== RESULTS FROM BETFAIR ===")
for h in TARGET_HORSES:
    if h in ALL_RESULTS:
        r = ALL_RESULTS[h]
        status = 'WON' if r['won'] else f"LOST (winner={r.get('winner','?')})"
        print(f"  {h}: {status}")
    else:
        print(f"  {h}: NOT FOUND IN BETFAIR")

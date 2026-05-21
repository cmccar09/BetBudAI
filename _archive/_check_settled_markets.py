"""
Check Betfair for settled Taunton and Southwell markets today (March 25)
"""
import requests, json

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
    if r.status_code == 200:
        result = r.json()
        if isinstance(result, dict) and result.get('faultcode'):
            return None
        return result
    return None

def login():
    r = requests.post(
        'https://identitysso-cert.betfair.com/api/certlogin',
        data={'username': creds['username'], 'password': creds['password']},
        headers={'X-Application': APP_KEY, 'Content-Type': 'application/x-www-form-urlencoded'},
        cert=('./betfair-client.crt', './betfair-client.key'), timeout=20
    )
    d = r.json()
    if d.get('loginStatus') == 'SUCCESS':
        token = d['sessionToken']
        creds['session_token'] = token
        with open('betfair-creds.json', 'w') as fh:
            json.dump(creds, fh, indent=2)
        return token
    return None

TOKEN = login()
print("Logged in" if TOKEN else "Login failed")

TARGET_HORSES = ['Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted', 'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan']

def norm(s):
    return (s or '').strip().lower()

# Get ALL WIN markets today for target venues
# Include more venues to see settled ones
venues = ['Taunton', 'Southwell']
all_markets = []
for venue in venues:
    mkt = bf('listMarketCatalogue', {
        "filter": {
            "eventTypeIds": ["7"],
            "venues": [venue],
            "marketTypeCodes": ["WIN"],
            "marketStartTime": {"from": "2026-03-25T00:00:00Z", "to": "2026-03-26T00:00:00Z"}
        },
        "sort": "FIRST_TO_START",
        "maxResults": 50,
        "marketProjection": ["RUNNER_DESCRIPTION", "EVENT", "MARKET_START_TIME"]
    })
    if mkt:
        print(f"\n{venue}: {len(mkt)} markets found")
        all_markets.extend(mkt)
    else:
        print(f"\n{venue}: no markets")

print(f"\nTotal markets: {len(all_markets)}")

# Get market IDs
mkt_map = {m['marketId']: m for m in all_markets}
mkt_ids = list(mkt_map.keys())

if not mkt_ids:
    print("No markets found")
    exit()

# Get books
books = bf('listMarketBook', {
    "marketIds": mkt_ids,
    "priceProjection": {"priceData": ["SP_TRADED"]},
}, )

results = {}
print("\n=== Market Results ===")
for b in (books or []):
    mkt_id = b['marketId']
    status = b.get('status', '?')
    m = mkt_map.get(mkt_id, {})
    venue = m.get('event', {}).get('venue', '?')
    start = m.get('marketStartTime', '')[11:16]
    mname = m.get('marketName', '')
    runners_cat = {r['selectionId']: r for r in m.get('runners', [])}
    
    print(f"\n{venue} {start} [{status}] - {mname}")
    
    if status == 'CLOSED':
        winners = [r for r in b.get('runners', []) if r.get('status') == 'WINNER']
        if winners:
            winner_ids = {r['selectionId'] for r in winners}
            winner_name = runners_cat.get(list(winner_ids)[0], {}).get('runnerName', '?')
            print(f"  WINNER: {winner_name}")
            for rc in runners_cat.values():
                h = rc['runnerName']
                if any(norm(h) == norm(t) for t in TARGET_HORSES):
                    won = rc['selectionId'] in winner_ids
                    status_str = 'WON (lay LOST)' if won else f'LOST (lay WON, winner={winner_name})'
                    print(f"  ** {h}: {status_str}")
                    results[h] = {'won': won, 'winner': winner_name if not won else h, 'course': venue, 'time': start}
    elif status == 'OPEN':
        runners_list = [runners_cat.get(r['selectionId'], {}).get('runnerName','?') for r in b.get('runners', []) if r.get('status')=='ACTIVE']
        for h in TARGET_HORSES:
            if any(norm(h) == norm(r) for r in runners_list):
                print(f"  ** {h}: PENDING (market still OPEN)")

print("\n=== SUMMARY ===")
for h in TARGET_HORSES:
    if h in results:
        r = results[h]
        print(f"  {h}: {'WON' if r['won'] else 'LOST, winner=' + r['winner']}")
    else:
        print(f"  {h}: NOT FOUND / PENDING")

# Save to file for use in HTML gen
with open('_favs_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nSaved {len(results)} results to _favs_results.json")

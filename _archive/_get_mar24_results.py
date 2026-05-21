"""
Get March 24 race results from Betfair for all 9 favs-run target horses
Races ran on March 24 but bet_date = 2026-03-25 in DynamoDB
"""
import requests, json, boto3
from decimal import Decimal

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
    if d.get('loginStatus') == 'SUCCESS':
        token = d['sessionToken']
        creds['session_token'] = token
        with open('betfair-creds.json', 'w') as f:
            json.dump(creds, f, indent=2)
        return token
    print(f"Login failed: {d}")
    return None

def bf(method, params, token):
    r = requests.post(
        f'https://api.betfair.com/exchange/betting/rest/v1.0/{method}/',
        json=params,
        headers={'X-Application': APP_KEY, 'X-Authentication': token, 'Content-Type': 'application/json'},
        timeout=30
    )
    if r.status_code == 200:
        res = r.json()
        if isinstance(res, dict) and res.get('faultcode'):
            print(f"  API fault: {res}")
            return None
        return res
    print(f"  HTTP {r.status_code}: {r.text[:200]}")
    return None

TARGET_HORSES = ['Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted', 'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan']
TARGET_COURSES = {'taunton', 'southwell', 'wolverhampton', 'hereford', 'kempton'}

def norm(s):
    import re
    s = re.sub(r"\s*\([A-Z]{2,3}\)\s*$", "", (s or '').strip())
    return re.sub(r"\s+", " ", s).lower().strip()

token = login()
if not token:
    exit(1)

# Query for March 24 WIN markets
markets_cat = bf('listMarketCatalogue', {
    "filter": {
        "eventTypeIds": ["7"],
        "marketCountries": ["GB"],
        "marketTypeCodes": ["WIN"],
        "marketStartTime": {"from": "2026-03-24T00:00:00Z", "to": "2026-03-25T00:00:00Z"}
    },
    "sort": "FIRST_TO_START",
    "maxResults": 200,
    "marketProjection": ["RUNNER_DESCRIPTION", "EVENT", "MARKET_START_TIME"]
}, token)

if not markets_cat:
    print("No markets for March 24")
    exit()

print(f"March 24 markets: {len(markets_cat)}")

mkt_map = {m['marketId']: m for m in markets_cat}

# Find markets with target horses
target_market_ids = []
for mkt_id, m in mkt_map.items():
    venue = m.get('event', {}).get('venue', '')
    if norm(venue) not in TARGET_COURSES:
        continue
    for r in m.get('runners', []):
        if any(norm(r.get('runnerName','')) == norm(h) for h in TARGET_HORSES):
            target_market_ids.append(mkt_id)
            break

print(f"Target markets found: {len(target_market_ids)}")
for mid in target_market_ids:
    m = mkt_map[mid]
    venue = m.get('event', {}).get('venue', '?')
    start = m.get('marketStartTime', '')[11:16]
    mname = m.get('marketName', '?')
    print(f"  {venue} {start} - {mname} [{mid}]")

if not target_market_ids:
    print("No target markets found for March 24 at target courses!")
    print("\nAll March 24 GB markets:")
    for mkt_id, m in sorted(mkt_map.items(), key=lambda x: x[1].get('marketStartTime','')):
        venue = m.get('event', {}).get('venue', '?')
        start = m.get('marketStartTime', '')[11:16]
        mname = m.get('marketName', '?')
        print(f"  {venue:15} {start} {mname}")
    exit()

# Get market books
books = bf('listMarketBook', {
    "marketIds": target_market_ids,
    "priceProjection": {"priceData": ["SP_TRADED"]},
}, token)

all_results = {}
print("\n=== Market Results ===")
for b in (books or []):
    mkt_id = b['marketId']
    status = b.get('status', '?')
    m = mkt_map.get(mkt_id, {})
    venue = m.get('event', {}).get('venue', '?')
    start = m.get('marketStartTime', '')[11:16]
    mname = m.get('marketName', '?')
    runners_cat = {r['selectionId']: r for r in m.get('runners', [])}
    
    winners = [r for r in b.get('runners', []) if r.get('status') == 'WINNER']
    
    print(f"\n{venue} {start} [{status}] - {mname}")
    if winners:
        winner_ids = {r['selectionId'] for r in winners}
        winner_name = runners_cat.get(list(winner_ids)[0], {}).get('runnerName', '?')
        winner_name_norm = norm(winner_name)
        print(f"  WINNER: {winner_name}")
        
        for rc in runners_cat.values():
            h = rc['runnerName']
            for target in TARGET_HORSES:
                if norm(h) == norm(target):
                    won = rc['selectionId'] in winner_ids
                    all_results[target] = {
                        'won': won,
                        'winner': target if won else winner_name,
                        'course': venue,
                        'time': start,
                        'status': 'SETTLED',
                    }
                    print(f"  ** {target}: {'WON → LAY LOST' if won else 'LOST → LAY WON (winner=' + winner_name + ')'}")
    elif status == 'CLOSED':
        print(f"  CLOSED but no winners")
    else:
        print(f"  Status={status}, not settled")
        for rc in runners_cat.values():
            h = rc['runnerName']
            if any(norm(h) == norm(t) for t in TARGET_HORSES):
                print(f"  ** {h} was in this race")

print("\n\n=== FINAL SUMMARY ===")
for h in TARGET_HORSES:
    if h in all_results:
        r = all_results[h]
        print(f"  {h}: {'WON → LAY LOST 💸' if r['won'] else 'LOST → LAY WON ✓'} [{r['course']} {r['time']}] winner={r['winner']}")
    else:
        print(f"  {h}: NOT FOUND")

with open('_favs_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)
print(f"\nSaved {len(all_results)} results to _favs_results.json")

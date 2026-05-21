"""
Query Betfair settled markets for March 25, 2026 to get race results
"""
import requests
import json
from datetime import datetime

with open('betfair-creds.json') as f:
    creds = json.load(f)

SESSION_TOKEN = creds['session_token']
APP_KEY = creds['app_key']
USERNAME = creds['username']
PASSWORD = creds['password']

CERT = ('./betfair-client.crt', './betfair-client.key')
API_URL = 'https://api.betfair.com/exchange/betting/rest/v1.0/'

def get_new_session():
    """Get a fresh session token"""
    r = requests.post(
        'https://identitysso-cert.betfair.com/api/certlogin',
        data={'username': USERNAME, 'password': PASSWORD},
        headers={'X-Application': APP_KEY, 'Content-Type': 'application/x-www-form-urlencoded'},
        cert=CERT,
        timeout=20
    )
    d = r.json()
    if d.get('loginStatus') == 'SUCCESS':
        token = d['sessionToken']
        print(f"New session token obtained")
        creds['session_token'] = token
        with open('betfair-creds.json', 'w') as f:
            json.dump(creds, f, indent=2)
        return token
    else:
        print(f"Login failed: {d}")
        return None

def bf_call(method, params, token):
    headers = {
        'X-Application': APP_KEY,
        'X-Authentication': token,
        'Content-Type': 'application/json',
    }
    r = requests.post(f"{API_URL}{method}/", json=params, headers=headers, timeout=30)
    if r.status_code == 200:
        return r.json()
    print(f"Error {r.status_code}: {r.text[:200]}")
    return None

# Try with existing token first
print("Querying WIN markets for 25 March 2026...")

# Courses we're interested in
TARGET_COURSES = ['Wolverhampton', 'Kempton', 'Southwell', 'Hereford', 'Taunton']
TARGET_HORSES = ['Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted', 'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan']

def norm(s):
    return (s or '').strip().lower()

def fetch_results(token):
    # List markets for March 25, 2026
    params = {
        "filter": {
            "eventTypeIds": ["7"],  # 7 = Horse Racing
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
    }
    
    markets = bf_call('listMarketCatalogue', params, token)
    if not markets:
        return None
    
    print(f"Found {len(markets)} WIN markets for March 25")
    return markets

token = SESSION_TOKEN
markets = fetch_results(token)

if markets is None:
    print("Trying to get fresh session...")
    token = get_new_session()
    if token:
        markets = fetch_results(token)

if not markets:
    print("Could not fetch markets")
    exit(1)

# Filter for target courses and find runners
results = {}

for market in markets:
    event = market.get('event', {})
    venue = event.get('venue', '')
    event_name = event.get('name', '')
    market_name = market.get('marketName', '')
    market_id = market.get('marketId', '')
    start_time = market.get('marketStartTime', '')
    
    # Check if this venue matches our targets
    if not any(norm(venue) == norm(c) or norm(event_name).startswith(norm(c)) for c in TARGET_COURSES):
        continue
    
    runners = market.get('runners', [])
    print(f"\n{venue} {start_time[11:16]} - {market_name} [{market_id}]")
    
    for runner in runners:
        rname = runner.get('runnerName', '')
        selection_id = runner.get('selectionId', '')
        if any(norm(rname) == norm(h) for h in TARGET_HORSES):
            print(f"  ** TARGET: {rname} (selId={selection_id})")

# Now try to get settled bets/outcomes
print("\n\n--- Checking market books for winner info ---")
# Get market IDs for our relevant markets
relevant_market_ids = []
for market in markets:
    event = market.get('event', {})
    venue = event.get('venue', '')
    if any(norm(venue) == norm(c) for c in TARGET_COURSES):
        relevant_market_ids.append(market.get('marketId', ''))
        
print(f"Relevant market IDs: {len(relevant_market_ids)}")

if relevant_market_ids:
    # Fetch market books with winner info
    for i in range(0, len(relevant_market_ids), 25):
        batch = relevant_market_ids[i:i+25]
        book_params = {
            "marketIds": batch,
            "priceProjection": {"priceData": ["EX_BEST_OFFERS"]},
            "orderProjection": "EXECUTABLE",
            "matchProjection": "NO_ROLLUP"
        }
        books = bf_call('listMarketBook', book_params, token)
        if books:
            for book in books:
                mkt_status = book.get('status', '')
                if mkt_status == 'CLOSED':
                    mkt_id = book.get('marketId', '')
                    # Find this market
                    mkt_info = next((m for m in markets if m.get('marketId') == mkt_id), {})
                    venue = mkt_info.get('event', {}).get('venue', '')
                    start = mkt_info.get('marketStartTime', '')
                    mname = mkt_info.get('marketName', '')
                    
                    winners = [r for r in book.get('runners', []) if r.get('status') == 'WINNER']
                    losers = [r for r in book.get('runners', []) if r.get('status') == 'LOSER']
                    
                    if winners:
                        winner_selection_ids = {r['selectionId'] for r in winners}
                        print(f"\n{venue} {start[11:16]} - {mname} [CLOSED]")
                        # Match winner to horse name
                        for mkt_runner in mkt_info.get('runners', []):
                            if mkt_runner.get('selectionId') in winner_selection_ids:
                                wname = mkt_runner.get('runnerName', '?')
                                print(f"  WINNER: {wname}")
                                for h in TARGET_HORSES:
                                    if norm(h) == norm(wname):
                                        print(f"  --> TARGET HORSE WON!")
                                        results[h] = {'won': True, 'pos': 1}
                        # Check target losers
                        loser_ids = {r['selectionId'] for r in losers}
                        for mkt_runner in mkt_info.get('runners', []):
                            if mkt_runner.get('selectionId') in loser_ids:
                                rname = mkt_runner.get('runnerName', '?')
                                for h in TARGET_HORSES:
                                    if norm(h) == norm(rname):
                                        winner_name = next((mr.get('runnerName', '?') for mr in mkt_info.get('runners', []) if mr.get('selectionId') in winner_selection_ids), '?')
                                        print(f"  LOSER: {rname} (winner={winner_name})")
                                        results[h] = {'won': False, 'winner': winner_name}

print("\n\n=== FINAL RESULTS ===")
for horse in TARGET_HORSES:
    if horse in results:
        r = results[horse]
        if r['won']:
            print(f"{horse}: WON (lay LOST)")
        else:
            print(f"{horse}: LOST - winner: {r.get('winner','?')} (lay WON)")
    else:
        print(f"{horse}: NOT FOUND")

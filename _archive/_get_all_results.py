"""
Get race results from Betfair listMarketBook for all 23 markets
Plus try to infer results for missing courses from DynamoDB
"""
import requests
import json
import boto3
from boto3.dynamodb.conditions import Attr

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
        return r.json()
    print(f"  BF err {r.status_code}: {r.text[:150]}")
    return None

TARGET_HORSES = ['Montevetro', 'Time To Take Off', 'Constitution Hill',
    'Peckforton Hills', 'Hillberry Hill', 'Sorted', 'Best Night', 'Falls Of Acharn', 'Shadowfax Of Rohan']

def norm(s):
    return (s or '').strip().lower()

# Step 1: list 23 markets
markets_cat = bf('listMarketCatalogue', {
    "filter": {
        "eventTypeIds": ["7"],
        "marketCountries": ["GB"],
        "marketTypeCodes": ["WIN"],
        "marketStartTime": {"from": "2026-03-25T00:00:00Z", "to": "2026-03-26T00:00:00Z"}
    },
    "sort": "FIRST_TO_START",
    "maxResults": 200,
    "marketProjection": ["RUNNER_METADATA", "RUNNER_DESCRIPTION", "EVENT", "MARKET_START_TIME"]
})

if not markets_cat:
    print("No markets found")
    exit()

# Build market id -> info map
mkt_map = {m['marketId']: m for m in markets_cat}
mkt_ids = list(mkt_map.keys())
print(f"Got {len(mkt_ids)} markets")

# Step 2: get market books with runner status
results = {}
for i in range(0, len(mkt_ids), 25):
    batch = mkt_ids[i:i+25]
    books = bf('listMarketBook', {
        "marketIds": batch,
        "priceProjection": {"priceData": ["SP_TRADED"]},
    })
    if not books:
        continue
    for book in books:
        mkt_id = book.get('marketId')
        status = book.get('status', '')
        mkt_info = mkt_map.get(mkt_id, {})
        venue = mkt_info.get('event', {}).get('venue', '?')
        start = mkt_info.get('marketStartTime', '')[11:16]
        mname = mkt_info.get('marketName', '')
        runners_catalog = {r['selectionId']: r for r in mkt_info.get('runners', [])}
        
        winners = [r for r in book.get('runners', []) if r.get('status') == 'WINNER']
        if winners:
            # We have a winner
            for wr in winners:
                wname = runners_catalog.get(wr['selectionId'], {}).get('runnerName', '?')
                print(f"{venue:15} {start} {mname:25} | WINNER: {wname}")
                # Any target horse in this market?
                for r_cat in runners_catalog.values():
                    h = r_cat.get('runnerName','')
                    if any(norm(h) == norm(t) for t in TARGET_HORSES):
                        is_winner = r_cat['selectionId'] == wr['selectionId']
                        status_str = 'WON' if is_winner else f'LOST (winner={wname})'
                        print(f"  ** {h}: {status_str}")
                        results[h] = {'won': is_winner, 'winner': wname, 'course': venue, 'time': start}
        elif status in ('CLOSED', 'SETTLED'):
            print(f"{venue:15} {start} {mname:25} | CLOSED, no winners??")
        # else: OPEN/SUSPENDED - race not settled yet

# Step 3: for missing targets, check DynamoDB winner data
print("\n\n--- Checking DynamoDB for missing targets ---")
missing = [h for h in TARGET_HORSES if h not in results]
print(f"Missing: {missing}")

if missing:
    db = boto3.resource('dynamodb', region_name='eu-west-1')
    tbl = db.Table('SureBetBets')
    
    # Get all March 25 settled items to cross-reference
    resp = tbl.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-03-25'))
    all_mar25 = resp.get('Items', [])
    while resp.get('LastEvaluatedKey'):
        resp = tbl.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-03-25'),
            ExclusiveStartKey=resp['LastEvaluatedKey']
        )
        all_mar25.extend(resp.get('Items', []))
    settled_mar25 = [i for i in all_mar25 if i.get('outcome') in ('win','placed','loss','WIN','PLACED','LOSS','WON','LOST')]
    print(f"Settled DynamoDB items for Mar 25: {len(settled_mar25)}")
    
    # For each missing horse, look at same course/get winner from settled picks
    for h in missing:
        # Get horse's own record from DynamoDB to find race
        horse_records = [i for i in all_mar25 if norm(i.get('horse','')) == norm(h)]
        if not horse_records:
            print(f"  {h}: not in DB either")
            continue
        hr = horse_records[0]
        h_course = norm(hr.get('course',''))
        h_class = norm(hr.get('race_class',''))
        # Find settled picks at same course
        same_course = [i for i in settled_mar25 if norm(i.get('course','')) == h_course]
        if same_course:
            for sc in same_course:
                winner = sc.get('result_winner_name','?')
                print(f"  {h} @ {h_course}: settled pick {sc.get('horse','?')} → winner={winner}")
                if winner and winner != '?':
                    is_winner = norm(winner) == norm(h)
                    results[h] = {'won': is_winner, 'winner': winner if not is_winner else h, 'course': hr.get('course',''), 'time': hr.get('race_time','?')}
                    break

print("\n\n=== FINAL RESULTS ===")
for horse in TARGET_HORSES:
    if horse in results:
        r = results[horse]
        if r['won']:
            print(f"{horse}: WON (favourite won -> LAY LOST)")
        else:
            print(f"{horse}: LOST (favourite lost -> LAY WON) - winner={r.get('winner','?')}")
    else:
        print(f"{horse}: UNKNOWN")

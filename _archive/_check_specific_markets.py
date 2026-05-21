"""
Direct query of specific Betfair markets for status/winners
"""
import requests
import json

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
    print(f"  Error {r.status_code}: {r.text[:300]}")
    return None

# Best Night = 1.255718058, Constitution Hill = 1.255718113
market_ids = ['1.255718058', '1.255718113']

# Also get catalogue info for these
cat = bf('listMarketCatalogue', {
    "filter": {"marketIds": market_ids},
    "marketProjection": ["RUNNER_DESCRIPTION", "RUNNER_METADATA", "EVENT", "MARKET_START_TIME"]
})
print("Catalogue:")
for m in (cat or []):
    print(f"  {m['marketId']} | {m.get('event',{}).get('venue','?')} | {m.get('marketStartTime','')}")
    for r in m.get('runners', []):
        print(f"    {r['selectionId']} {r['runnerName']}")

# Get market book with all price projections
books = bf('listMarketBook', {
    "marketIds": market_ids,
    "priceProjection": {"priceData": ["SP_TRADED", "SP_PROJECTED", "EX_BEST_OFFERS", "EX_ALL_OFFERS"]},
    "orderProjection": "ALL",
    "matchProjection": "ROLLED_UP_BY_PRICE"
})

print("\nMarket Books:")
for b in (books or []):
    mkt_id = b['marketId']
    status = b.get('status')
    bsta = b.get('betDelay', '?')
    runners = b.get('runners', [])
    print(f"\n  Market {mkt_id}: status={status}")
    for r in runners:
        rname = f"sel_{r['selectionId']}"
        rstat = r.get('status')
        sp = r.get('sp', {})
        sp_near = sp.get('nearPrice')
        sp_far = sp.get('farPrice')
        sp_actual = sp.get('actualSP')
        print(f"    {rstat:8} | sp_near={sp_near} sp_far={sp_far} sp_actual={sp_actual} | {rname}")

# Also try to get cleared orders for these markets
print("\n\nTrying listClearedOrders...")
cleared = bf('listClearedOrders', {
    "betStatus": "SETTLED",
    "marketIds": market_ids,
    "recordCount": 10
})
print(f"Cleared orders: {cleared}")

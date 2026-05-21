"""Fetch live Betfair prices for today's Cheltenham races."""
import json, requests

creds = json.load(open('betfair-creds.json'))
SESSION = creds['session_token']
APP_KEY = creds['app_key']
H = {'X-Authentication': SESSION, 'X-Application': APP_KEY, 'content-type': 'application/json'}
BASE = 'https://api.betfair.com/exchange/betting/json-rpc/v1'

# Step 1: List win markets
r = requests.post(BASE, headers=H, json=[{
    'jsonrpc': '2.0', 'method': 'SportsAPING/v1.0/listMarketCatalogue',
    'params': {
        'filter': {'eventTypeIds': ['7'], 'marketCountries': ['GB'], 'marketTypeCodes': ['WIN']},
        'sort': 'FIRST_TO_START', 'maxResults': '20',
        'marketProjection': ['EVENT', 'MARKET_START_TIME', 'RUNNER_DESCRIPTION']
    }, 'id': 1
}])
markets = r.json()[0].get('result', [])

chelt_markets = [m for m in markets if 'cheltenham' in m.get('event', {}).get('name', '').lower()
                 or 'cheltenham' in m.get('event', {}).get('venue', '').lower()]

if not chelt_markets:
    chelt_markets = markets  # fallback — show all

print(f"Found {len(chelt_markets)} Cheltenham markets")
market_ids = [m['marketId'] for m in chelt_markets]

# Step 2: Get best available prices for each market
r2 = requests.post(BASE, headers=H, json=[{
    'jsonrpc': '2.0', 'method': 'SportsAPING/v1.0/listMarketBook',
    'params': {
        'marketIds': market_ids,
        'priceProjection': {'priceData': ['EX_BEST_OFFERS'], 'exBestOffersOverrides': {'rollupLimit': 3}},
        'orderProjection': 'EXECUTABLE',
        'matchProjection': 'ROLLED_UP_BY_PRICE',
    }, 'id': 2
}])
books = r2.json()[0].get('result', [])

# Build runner name map
runner_map = {}
for m in chelt_markets:
    for runner in m.get('runners', []):
        runner_map[(m['marketId'], runner['selectionId'])] = runner.get('runnerName', str(runner['selectionId']))

# Key picks to highlight
picks = {
    'Old Park Star': 'Supreme',
    'Kopek Des Bordes': 'Arkle',
    'Manlaga': 'Fred Winter',
    'Jagwar': 'Ultima',
    'Lossiemouth': 'Champion Hurdle',
    'Madara': 'Plate',
    'Backmersackme': 'Challenge Cup',
}

print()
print("=" * 72)
print("  LIVE BETFAIR PRICES - CHELTENHAM DAY 1")
print("=" * 72)

for m_info, book in zip(chelt_markets, books):
    ev_name = m_info.get('event', {}).get('name', '?')
    start   = m_info.get('marketStartTime', '?')[:16].replace('T', ' ')
    print(f"\n  {start}  {ev_name}")
    print(f"  {'Runner':<32} {'Best Back':>10}  {'Best Lay':>10}  {'Note'}")
    print(f"  {'-'*32}-{'-'*10}--{'-'*10}--{'-'*20}")

    runners_by_back = []
    for runner in book.get('runners', []):
        sel_id = runner['selectionId']
        name = runner_map.get((m_info['marketId'], sel_id), str(sel_id))
        status = runner.get('status', 'ACTIVE')
        if status == 'REMOVED':
            print(f"  {'NR: ' + name:<32}  WITHDRAWN")
            continue
        ex = runner.get('ex', {})
        back = ex.get('availableToBack', [])
        lay  = ex.get('availableToLay', [])
        best_back_dec = back[0]['price'] if back else 0
        best_lay_dec  = lay[0]['price']  if lay  else 0
        # Convert to fractional-ish display
        if best_back_dec > 1:
            frac_num = round(best_back_dec - 1, 2)
            back_str = f"{frac_num:.2f} ({best_back_dec:.1f})"
        else:
            back_str = "-"
        lay_str = f"{best_lay_dec:.1f}" if best_lay_dec > 1 else "-"
        runners_by_back.append((best_back_dec, name, back_str, lay_str))

    runners_by_back.sort(key=lambda x: x[0])
    for dec, name, back_str, lay_str in runners_by_back:
        note = ""
        for pick_name, race_short in picks.items():
            if pick_name.lower() in name.lower():
                note = f"<< OUR PICK ({race_short})"
                break
        print(f"  {name:<32} {back_str:>10}  {lay_str:>10}  {note}")

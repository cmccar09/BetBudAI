"""
Quick fetch of Cheltenham 2026 festival markets using existing Betfair credentials.
"""
import sys, os, json, requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDS_FILE = os.path.join(BASE_DIR, 'betfair-creds.json')
CRT_FILE   = os.path.join(BASE_DIR, 'betfair-client.crt')
KEY_FILE   = os.path.join(BASE_DIR, 'betfair-client.key')
LOGIN_URL  = 'https://identitysso-cert.betfair.com/api/certlogin'
API_URL    = 'https://api.betfair.com/exchange/betting/json-rpc/v1'

with open(CREDS_FILE) as f:
    creds = json.load(f)

APP_KEY  = creds['app_key']
USERNAME = creds['username']
PASSWORD = creds['password']

def get_session():
    r = requests.post(
        LOGIN_URL,
        data={'username': USERNAME, 'password': PASSWORD},
        cert=(CRT_FILE, KEY_FILE),
        headers={'X-Application': APP_KEY, 'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30
    )
    d = r.json()
    if d.get('loginStatus') == 'SUCCESS':
        print(f"[OK] Logged in")
        return d['sessionToken']
    raise Exception(f"Login failed: {d.get('loginStatus')}")

def bf(session, method, params):
    hdrs = {'X-Application': APP_KEY, 'X-Authentication': session, 'content-type': 'application/json'}
    payload = [{'jsonrpc':'2.0','method':f'SportsAPING/v1.0/{method}','params':params,'id':1}]
    r = requests.post(API_URL, json=payload, headers=hdrs, timeout=30)
    res = r.json()
    return res[0].get('result', []) if isinstance(res, list) else []

def fetch_day(session, date_str):
    markets = bf(session, 'listMarketCatalogue', {
        'filter': {
            'eventTypeIds': ['7'],
            'competitionIds': [],
            'marketCountries': ['GB'],
            'marketTypeCodes': ['WIN'],
            'marketStartTime': {'from': f'{date_str}T00:00:00Z','to': f'{date_str}T23:59:59Z'},
            'textQuery': 'Cheltenham'
        },
        'marketProjection': ['EVENT','MARKET_START_TIME','RUNNER_DESCRIPTION','MARKET_NAME','COMPETITION'],
        'sort': 'FIRST_TO_START',
        'maxResults': '50'
    })
    return [m for m in markets if 'Cheltenham' in str(m.get('event',{}).get('venue',''))
                                   or 'Cheltenham' in str(m.get('marketName',''))
                                   or 'Cheltenham' in str(m.get('event',{}).get('name',''))]

def fetch_odds(session, market_ids):
    if not market_ids: return {}
    books = bf(session, 'listMarketBook', {
        'marketIds': market_ids,
        'priceProjection': {'priceData':['EX_BEST_OFFERS'],'exBestOfferOverRides':{'bestPricesDepth':1}}
    })
    return {b['marketId']: b for b in books}

festival_days = {1:'2026-03-10', 2:'2026-03-11', 3:'2026-03-12', 4:'2026-03-13'}

print(f"\n{'='*70}")
print("CHELTENHAM FESTIVAL 2026 - MARKETS CHECK")
print(f"{'='*70}")

try:
    session = get_session()
except Exception as e:
    print(f"[ERROR] {e}"); sys.exit(1)

all_races = []
for day_num, date_str in festival_days.items():
    day_names = {1:'Champion Day', 2:'Ladies Day', 3:"St Patrick's Thursday", 4:'Gold Cup Day'}
    markets = fetch_day(session, date_str)
    print(f"\nDay {day_num} - {day_names[day_num]} ({date_str}): {len(markets)} markets found")

    if markets:
        books = fetch_odds(session, [m['marketId'] for m in markets])
        for m in sorted(markets, key=lambda x: x.get('marketStartTime','')):
            mid = m['marketId']
            name = m.get('marketName','')
            time_str = m.get('marketStartTime','')[11:16]
            runners_meta = {r['selectionId']: r['runnerName'] for r in m.get('runners',[])}
            book = books.get(mid,{})
            runners = []
            for runner in book.get('runners',[]):
                sid = runner['selectionId']
                nm  = runners_meta.get(sid, f'Runner {sid}')
                bk  = runner.get('ex',{}).get('availableToBack',[])
                odds_val = bk[0]['price'] if bk else None
                if runner.get('status') == 'ACTIVE':
                    runners.append({'name': nm, 'odds': odds_val, 'selection_id': sid})
            runners.sort(key=lambda x: x['odds'] or 999)
            all_races.append({'day': day_num, 'date': date_str, 'market_id': mid,
                              'market_name': name, 'start_time': time_str, 'runners': runners})
            print(f"  {time_str} {name} ({len(runners)} runners)")
            for r in runners[:6]:
                print(f"         {r['name']:<32} {r['odds']}")

output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cheltenham_races.json')
with open(output_file, 'w') as f:
    json.dump(all_races, f, indent=2)

total = sum(1 for d in festival_days if any(r['day']==d for r in all_races))
print(f"\n[OK] Saved {len(all_races)} markets to cheltenham_races.json")
if len(all_races) == 0:
    print("[NOTE] Markets not yet open on Betfair - they typically open 1 week before.")
    print("       Come back around 3-4 March 2026.")

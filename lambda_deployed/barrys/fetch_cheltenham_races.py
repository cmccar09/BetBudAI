"""
fetch_cheltenham_races.py
Fetches live Cheltenham Festival race data from Betfair
Stores runners + odds for each of the 28 festival races
"""
import sys
import os
import json
import requests
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from barrys.barrys_config import FESTIVAL_DAYS, FESTIVAL_RACES, DYNAMODB_TABLE, DYNAMODB_REGION

import boto3

dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION)

CERTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'certs')
BETFAIR_APP_KEY = os.environ.get('BETFAIR_APP_KEY', '')
TOKEN_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'betfair_token.json')

BETTING_API  = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
ACCOUNT_API  = 'https://api.betfair.com/exchange/account/json-rpc/v1'
LOGIN_URL    = 'https://identitysso-cert.betfair.com/api/certlogin'


def load_token():
    """Load cached Betfair token"""
    try:
        with open(TOKEN_FILE) as f:
            data = json.load(f)
            return data.get('token') or data.get('sessionToken')
    except Exception:
        return None


def get_betfair_session():
    """Get Betfair session, try cache first"""
    token = load_token()
    if token:
        return token

    # Try login
    crt = os.path.join(CERTS_DIR, 'client-2048.crt')
    key = os.path.join(CERTS_DIR, 'client-2048.key')
    username = os.environ.get('BETFAIR_USERNAME', '')
    password = os.environ.get('BETFAIR_PASSWORD', '')

    r = requests.post(
        LOGIN_URL,
        data={'username': username, 'password': password},
        cert=(crt, key),
        headers={'X-Application': BETFAIR_APP_KEY, 'Content-Type': 'application/x-www-form-urlencoded'},
        timeout=30
    )
    resp = r.json()
    if resp.get('loginStatus') == 'SUCCESS':
        token = resp['sessionToken']
        with open(TOKEN_FILE, 'w') as f:
            json.dump({'token': token, 'sessionToken': token}, f)
        return token
    raise Exception(f"Betfair login failed: {resp.get('loginStatus')}")


def betfair_request(session, method, params):
    """Make a Betfair API call"""
    headers = {
        'X-Application': BETFAIR_APP_KEY,
        'X-Authentication': session,
        'content-type': 'application/json'
    }
    payload = [{'jsonrpc': '2.0', 'method': f'SportsAPING/v1.0/{method}', 'params': params, 'id': 1}]
    r = requests.post(BETTING_API, json=payload, headers=headers, timeout=30)
    result = r.json()
    if isinstance(result, list):
        return result[0].get('result', [])
    return []


def fetch_cheltenham_markets(session, festival_date):
    """Fetch all Cheltenham WIN markets for a given date"""
    params = {
        'filter': {
            'eventTypeIds': ['7'],
            'marketCountries': ['GB', 'IE'],
            'marketTypeCodes': ['WIN'],
            'bspOnly': False,
            'marketStartTime': {
                'from': f'{festival_date}T00:00:00Z',
                'to':   f'{festival_date}T23:59:59Z'
            },
            'textQuery': 'Cheltenham'
        },
        'marketProjection': ['EVENT', 'MARKET_START_TIME', 'RUNNER_DESCRIPTION', 'MARKET_NAME'],
        'maxResults': 50
    }
    markets = betfair_request(session, 'listMarketCatalogue', params)
    return [m for m in markets if 'Cheltenham' in m.get('event', {}).get('venue', '') or
                                  'Cheltenham' in m.get('marketName', '')]


def fetch_runners_with_odds(session, market_ids):
    """Fetch runners and current odds for market IDs"""
    if not market_ids:
        return []
    params = {
        'marketIds': market_ids,
        'priceProjection': {'priceData': ['EX_BEST_OFFERS'], 'exBestOfferOverRides': {'bestPricesDepth': 3}},
        'orderProjection': 'EXECUTABLE',
        'matchProjection': 'NO_ROLLUP'
    }
    return betfair_request(session, 'listMarketBook', params)


def save_race_data(race_data_list):
    """Save fetched races to a local JSON file"""
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cheltenham_races.json')
    with open(output_file, 'w') as f:
        json.dump(race_data_list, f, indent=2, default=str)
    print(f"[OK] Saved {len(race_data_list)} races to cheltenham_races.json")


def main():
    print(f"\n{'='*70}")
    print("FETCHING CHELTENHAM FESTIVAL RACES FROM BETFAIR")
    print(f"{'='*70}\n")

    try:
        session = get_betfair_session()
        print("[OK] Betfair session obtained")
    except Exception as e:
        print(f"[ERROR] Could not get Betfair session: {e}")
        print("       Ensure BETFAIR_USERNAME, BETFAIR_PASSWORD, BETFAIR_APP_KEY are set,")
        print("       or that betfair_token.json exists with a valid token.")
        return

    all_races = []
    total_markets = 0

    for day_num, festival_date in FESTIVAL_DAYS.items():
        day_names = {1: "Champion Day", 2: "Ladies Day", 3: "St Patricks Thursday", 4: "Gold Cup Day"}
        print(f"\nDay {day_num} - {day_names[day_num]} ({festival_date})")

        markets = fetch_cheltenham_markets(session, festival_date)
        print(f"  Found {len(markets)} markets")

        if not markets:
            print(f"  [NOTE] No markets yet for {festival_date} (may open closer to festival)")
            continue

        market_ids = [m['marketId'] for m in markets]
        books = fetch_runners_with_odds(session, market_ids)
        books_by_id = {b['marketId']: b for b in books}

        for market in sorted(markets, key=lambda x: x.get('marketStartTime', '')):
            market_id = market['marketId']
            market_name = market.get('marketName', 'Unknown')
            start_time = market.get('marketStartTime', '')
            runners_meta = {r['selectionId']: r['runnerName'] for r in market.get('runners', [])}

            book = books_by_id.get(market_id, {})
            runners = []
            for runner in book.get('runners', []):
                sel_id = runner['selectionId']
                name = runners_meta.get(sel_id, f'Runner {sel_id}')
                ex = runner.get('ex', {})
                best_back = ex.get('availableToBack', [{}])[0].get('price') if ex.get('availableToBack') else None
                runners.append({
                    'selection_id': sel_id,
                    'name': name,
                    'odds': best_back,
                    'status': runner.get('status', 'ACTIVE')
                })

            # Sort by odds (shortest first)
            runners = [r for r in runners if r['status'] == 'ACTIVE' and r['odds']]
            runners.sort(key=lambda x: x['odds'])

            race_entry = {
                'market_id': market_id,
                'market_name': market_name,
                'day': day_num,
                'date': festival_date,
                'start_time': start_time,
                'runners': runners
            }
            all_races.append(race_entry)
            total_markets += 1

            print(f"  [{start_time[11:16]}] {market_name} - {len(runners)} runners")
            for r in runners[:5]:
                print(f"           {r['name']:<35} {r['odds']}")

    print(f"\n{'='*70}")
    print(f"Total fetched: {total_markets} races across {len(FESTIVAL_DAYS)} days")
    print(f"{'='*70}\n")

    if all_races:
        save_race_data(all_races)
    else:
        print("[NOTE] No live race data yet. Markets open ~1 week before festival.")
        print("       Run this script again closer to March 10, 2026.")


if __name__ == '__main__':
    main()

"""
Betfair Odds Fetcher
Fetches live odds from Betfair API for multiple sports
Supports: Horse Racing, Darts, Cricket, Rugby, Football
Uses session token from AWS Secrets Manager
"""

import json
import boto3
import requests
import datetime

secrets_client = boto3.client('secretsmanager')

# Betfair Event Type IDs
SPORT_EVENT_TYPES = {
    'horse_racing': '7',
    'darts': '3',
    'cricket': '4',
    'rugby': '5',
    'football': '1'
}

# Market types by sport
SPORT_MARKET_TYPES = {
    'horse_racing': ['WIN'],
    'football': ['MATCH_ODDS'],
    'rugby': ['MATCH_ODDS', 'OVER_UNDER_45_5', 'HANDICAP', 'FIRST_TRY_SCORER', 'WINNING_MARGIN'],
    'cricket': ['MATCH_ODDS', 'OVER_UNDER_TOTAL', 'TOP_BATSMAN', 'TOP_BOWLER', 'METHOD_OF_DISMISSAL'],
    'darts': ['MATCH_ODDS', 'OVER_UNDER_35', 'OVER_UNDER_65', 'TOTAL_180S', 'CORRECT_SCORE']
}

def get_betfair_session():
    """Get current Betfair session token - tries local login first, then Secrets Manager"""
    
    # Try local authentication first (for local testing)
    try:
        import os
        if os.path.exists('betfair-creds.json'):
            print("Using local authentication...")
            with open('betfair-creds.json', 'r') as f:
                creds = json.load(f)
            
            # Do interactive login
            url = "https://identitysso.betfair.com/api/login"
            headers = {
                'X-Application': creds['app_key'],
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            data = {
                'username': creds['username'],
                'password': creds['password']
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                session_token = result.get('sessionToken') or result.get('token')
                if session_token:
                    print(f"✓ Local authentication successful")
                    return creds['app_key'], session_token
    except Exception as e:
        print(f"Local auth failed, trying Secrets Manager: {e}")
    
    # Fall back to Secrets Manager (for Lambda) - do interactive login
    try:
        print("Getting credentials from Secrets Manager...")
        response = secrets_client.get_secret_value(SecretId='betfair-credentials')
        secret_string = response['SecretString']

        # Handle escaped quotes from PowerShell
        if secret_string.startswith('{\\'):
            secret_string = secret_string.replace('\\', '')

        credentials = json.loads(secret_string)
        
        # Do interactive login with username/password
        print("Authenticating with Betfair (interactive login)...")
        url = "https://identitysso.betfair.com/api/login"
        headers = {
            'X-Application': credentials['app_key'],
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        data = {
            'username': credentials['username'],
            'password': credentials['password']
        }
        
        login_response = requests.post(url, headers=headers, data=data, timeout=30)
        if login_response.status_code == 200:
            result = login_response.json()
            session_token = result.get('sessionToken') or result.get('token')
            if session_token:
                print(f"✓ Interactive authentication successful")
                return credentials['app_key'], session_token
            else:
                raise Exception(f"No session token in login response: {result}")
        else:
            raise Exception(f"Betfair login failed: {login_response.status_code} {login_response.text}")
    except Exception as e:
        print(f"Error getting Betfair session: {e}")
        raise Exception(f"Betfair authentication failed: {e}")

def fetch_betfair_markets(app_key, session_token, sport='horse_racing', market_types=None):
    """Fetch markets from Betfair for specified sport"""
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"

    now = datetime.datetime.now(datetime.timezone.utc)
    to_time = now + datetime.timedelta(days=5)

    event_type_id = SPORT_EVENT_TYPES.get(sport, '7')  # Default to horse racing

    # Use sport-specific market types if not provided
    if market_types is None:
        market_types = SPORT_MARKET_TYPES.get(sport, ['MATCH_ODDS'])

    # Base filter
    market_filter = {
        "eventTypeIds": [event_type_id],
        "marketStartTime": {
            "from": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": to_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        },
        "marketTypeCodes": market_types
    }

    # Sport-specific filters
    if sport == 'horse_racing':
        market_filter["marketCountries"] = ["GB", "IE"]

    # Request markets in next 24 hours
    request_body = {
        "filter": market_filter,
        "maxResults": 100,  # Betfair hard-limits RUNNER_METADATA projection to 100 markets per call
        "marketProjection": ["RUNNER_METADATA", "EVENT", "MARKET_START_TIME", "MARKET_DESCRIPTION"]
    }

    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    try:
        response = requests.post(url, json=request_body, headers=headers, timeout=30)

        if response.status_code == 401:
            raise Exception("Betfair session expired - will refresh on next schedule")

        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Betfair markets: {e}")
        raise

def fetch_betfair_odds(app_key, session_token, market_ids):
    """Fetch current odds for given market IDs"""
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"

    request_body = {
        "marketIds": market_ids,
        "priceProjection": {
            "priceData": ["EX_BEST_OFFERS"]
        }
    }

    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    try:
        response = requests.post(url, json=request_body, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching Betfair odds: {e}")
        raise

def get_live_betfair_races():
    """
    Main function to fetch live UK/IRE horse racing with odds
    Returns races in format compatible with main Lambda
    """
    print("Fetching Betfair session from Secrets Manager...")
    app_key, session_token = get_betfair_session()

    print("Fetching UK/IRE horse racing markets...")
    markets = fetch_betfair_markets(app_key, session_token)

    if not markets:
        print("No horse racing markets found")
        return []

    print(f"Found {len(markets)} markets, fetching odds...")

    # Betfair API limit is ~10 markets per request for listMarketBook
    # Batch the requests to avoid 400 errors
    odds_by_market = {}
    batch_size = 10

    for i in range(0, min(len(markets), 100), batch_size):  # 2026-04-13: raised from 30→100 to avoid missing evening races (e.g. Musselburgh 16:45 UTC)
        batch = markets[i:i+batch_size]
        market_ids = [market['marketId'] for market in batch]

        try:
            print(f"Fetching odds for batch {i//batch_size + 1} ({len(market_ids)} markets)...")
            odds_data = fetch_betfair_odds(app_key, session_token, market_ids)

            # Add to lookup
            for book in odds_data:
                odds_by_market[book['marketId']] = book
        except Exception as e:
            print(f"Error fetching odds batch {i//batch_size + 1}: {e}")
            continue

    # Format races for main Lambda
    races = []
    now = datetime.datetime.now(datetime.timezone.utc)

    for market in markets:
        market_id = market['marketId']
        market_start = datetime.datetime.strptime(market['marketStartTime'], "%Y-%m-%dT%H:%M:%S.%fZ")
        market_start = market_start.replace(tzinfo=datetime.timezone.utc)

        # Filter to 15 mins - 24 hours window
        time_diff = (market_start - now).total_seconds()
        if time_diff < 900 or time_diff > 86400:  # 15 mins to 24 hours
            continue

        # Get odds for this market
        odds = odds_by_market.get(market_id, {})
        runners_data = odds.get('runners', [])

        # Format runners with odds + full metadata (jockey, weight, age, OR, draw)
        runners = []
        for i, runner_meta in enumerate(market.get('runners', [])):
            runner_id = runner_meta['selectionId']
            runner_name = runner_meta['runnerName']

            # Extract all available metadata fields from Betfair RUNNER_METADATA
            meta = runner_meta.get('metadata', {})
            w_val = meta.get('WEIGHT_VALUE', '')
            w_lbs = 0
            if w_val:
                try:
                    w_str = str(w_val)
                    if '-' in w_str:
                        p = w_str.split('-')
                        w_lbs = int(p[0]) * 14 + int(p[1])
                    else:
                        w_lbs = int(w_str) * 14
                except Exception:
                    w_lbs = 0

            # Find odds for this runner
            runner_odds = next((r for r in runners_data if r['selectionId'] == runner_id), None)

            # Always include all runners — use best back price if available, else last traded, else 0
            # This ensures all horses appear in the full race card even if their market hasn't opened yet
            best_back = 0
            if runner_odds:
                avail = runner_odds.get('ex', {}).get('availableToBack', [])
                if avail:
                    best_back = avail[0]['price']
                elif runner_odds.get('lastPriceTraded'):
                    best_back = runner_odds['lastPriceTraded']

            runners.append({
                "name":            runner_name,
                "selectionId":     runner_id,
                "odds":            best_back,
                "jockey":          meta.get('JOCKEY_NAME', ''),
                "trainer":         meta.get('TRAINER_NAME', ''),
                "form":            meta.get('FORM', ''),
                "weight_lbs":      w_lbs,
                "weight_raw":      w_val,
                "age":             meta.get('AGE', ''),
                "official_rating": meta.get('OFFICIAL_RATING', ''),
                "draw":            meta.get('STALL_DRAW', runner_meta.get('metadata', {}).get('CLOTH_NUMBER', '')),
            })

        if runners:
            races.append({
                "market_id":   market_id,
                "race_time":   market['marketStartTime'],
                "course":      market.get('event', {}).get('venue', 'Unknown'),
                "market_name": market.get('marketName', ''),   # e.g. "6f Nov Stks", "1m Hcap"
                "runners":     runners,
                "start_time":  market_start,
            })

    # ── PRICE STEAM / DRIFT DETECTION (2026-03-30) ──────────────────────────
    # Compare current prices against the snapshot from the last fetch.
    # A horse whose price drops ≥ 20% is being backed ('steaming').
    # A horse whose price rises ≥ 25% is drifting (market losing confidence).
    # These are stored in 'price_movement' on each runner so the scoring engine
    # can reward backed horses and penalise drifters.
    _PH_FILE = 'price_history.json'
    try:
        import os as _os
        _prev_prices = {}
        if _os.path.exists(_PH_FILE):
            with open(_PH_FILE, 'r') as _f:
                _prev_prices = json.load(_f)  # {runner_id_str: price}
        _new_prices = {}
        for race in races:
            for runner in race.get('runners', []):
                sid = str(runner.get('selectionId', ''))
                cur = float(runner.get('odds', 0) or 0)
                if not sid or cur <= 1.0:
                    continue
                prev = _prev_prices.get(sid, cur)
                if prev > 1.0 and cur > 1.0:
                    # Convert to probability space for clean percentage change
                    # p_cur = 1/cur, p_prev = 1/prev
                    # steam = (p_cur - p_prev) / p_prev = prev/cur - 1
                    pct_move = (prev - cur) / prev   # positive = price shortened (backed)
                    if pct_move >= 0.20:
                        runner['price_movement'] = 'steaming'
                        runner['price_move_pct'] = round(pct_move * 100)
                    elif pct_move <= -0.25:
                        runner['price_movement'] = 'drifting'
                        runner['price_move_pct'] = round(pct_move * 100)
                    else:
                        runner['price_movement'] = 'stable'
                        runner['price_move_pct'] = 0
                _new_prices[sid] = cur
        # Save updated prices for next run
        with open(_PH_FILE, 'w') as _f:
            json.dump(_new_prices, _f)
    except Exception as _pe:
        print(f"  [price_steam] Warning: {_pe}")

    print(f"Returning {len(races)} races with odds in betting window")
    return races

def get_live_betfair_events(sport='darts'):
    """
    Fetch live events with ALL relevant markets for a sport (especially darts)
    Returns events grouped by match with all market types
    """
    print(f"Fetching Betfair session for {sport}...")
    app_key, session_token = get_betfair_session()

    print(f"Fetching {sport} markets...")
    markets = fetch_betfair_markets(app_key, session_token, sport=sport)

    if not markets:
        print(f"No {sport} markets found")
        return []

    print(f"Found {len(markets)} markets across all types")

    # Group markets by event
    events_by_id = {}
    for market in markets:
        event_id = market.get('event', {}).get('id')
        if not event_id:
            continue

        if event_id not in events_by_id:
            events_by_id[event_id] = {
                'event_id': event_id,
                'event_name': market.get('event', {}).get('name', 'Unknown'),
                'event_time': market.get('marketStartTime'),
                'venue': market.get('event', {}).get('venue', 'Unknown'),
                'markets': {}
            }

        # Add this market
        market_type = market.get('marketName', market.get('description', {}).get('marketType', 'UNKNOWN'))
        events_by_id[event_id]['markets'][market_type] = {
            'market_id': market['marketId'],
            'market_type': market_type,
            'runners': market.get('runners', [])
        }

    # Now fetch odds for all markets
    all_market_ids = []
    for event in events_by_id.values():
        for market_data in event['markets'].values():
            all_market_ids.append(market_data['market_id'])

    print(f"Fetching odds for {len(all_market_ids)} markets...")

    odds_by_market = {}
    batch_size = 10

    for i in range(0, len(all_market_ids), batch_size):
        batch = all_market_ids[i:i+batch_size]

        try:
            odds_data = fetch_betfair_odds(app_key, session_token, batch)
            for book in odds_data:
                odds_by_market[book['marketId']] = book
        except Exception as e:
            print(f"Error fetching odds batch: {e}")
            continue

    # Format events with all markets and odds
    events = []
    now = datetime.datetime.now(datetime.timezone.utc)

    for event_data in events_by_id.values():
        event_start = datetime.datetime.strptime(event_data['event_time'], "%Y-%m-%dT%H:%M:%S.%fZ")

        # Filter to 15 mins - 24 hours window
        time_diff = (event_start - now).total_seconds()
        if time_diff < 900 or time_diff > 86400:
            continue

        # Add odds to each market
        markets_with_odds = {}
        for market_type, market_data in event_data['markets'].items():
            market_id = market_data['market_id']
            odds = odds_by_market.get(market_id, {})
            runners_data = odds.get('runners', [])

            # Format runners with odds
            selections = []
            for runner_meta in market_data['runners']:
                runner_id = runner_meta['selectionId']
                runner_name = runner_meta['runnerName']

                runner_odds = next((r for r in runners_data if r['selectionId'] == runner_id), None)

                if runner_odds and runner_odds.get('ex', {}).get('availableToBack'):
                    best_back = runner_odds['ex']['availableToBack'][0]['price']
                    selections.append({
                        "name": runner_name,
                        "selectionId": runner_id,
                        "odds": best_back
                    })

            if selections:
                markets_with_odds[market_type] = {
                    "market_id": market_id,
                    "selections": selections
                }

        if markets_with_odds:
            events.append({
                "event_id": event_data['event_id'],
                "event_time": event_data['event_time'],
                "venue": event_data['venue'],
                "event_name": event_data['event_name'],
                "markets": markets_with_odds,
                "start_time": event_start
            })

    print(f"Returning {len(events)} events with multi-market odds")
    return events


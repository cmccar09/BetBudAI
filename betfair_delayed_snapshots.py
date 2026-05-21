#!/usr/bin/env python3
"""
betfair_delayed_snapshots.py
Fetches live horse racing odds from Betfair API and saves as snapshot JSON
Uses credentials from betfair-creds.json
"""

import json
import sys
import os
import argparse
from datetime import datetime, timedelta, timezone
import requests

def load_credentials():
    """Load Betfair credentials from betfair-creds.json"""
    creds_path = os.path.join(os.path.dirname(__file__), 'betfair-creds.json')
    
    if not os.path.exists(creds_path):
        raise FileNotFoundError(f"Credentials file not found: {creds_path}")
    
    with open(creds_path, 'r') as f:
        creds = json.load(f)
    
    return creds['app_key'], creds['session_token']

def fetch_markets(app_key, session_token, hours_ahead=24, event_type="7", countries=None):
    """Fetch UK/IRE racing markets from Betfair
    
    Args:
        event_type: '7' for Horse Racing, '4339' for Greyhound Racing
        countries: List of country codes or None for default ["GB", "IE"]
    """
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"
    
    now = datetime.now(timezone.utc)
    to_time = now + timedelta(hours=hours_ahead)
    
    sport_name = "Horse Racing" if event_type == "7" else "Greyhound Racing"
    
    # Use provided countries or default to GB and IE
    if countries is None:
        countries = ["GB", "IE"]
    
    payload = {
        "filter": {
            "eventTypeIds": [event_type],  # 7=Horses, 4339=Greyhounds
            "marketCountries": countries,
            "marketTypeCodes": ["WIN"],
            "marketStartTime": {
                "from": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": to_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        },
        "maxResults": 100,
        "marketProjection": ["RUNNER_METADATA", "EVENT", "MARKET_START_TIME", "COMPETITION", "RUNNER_DESCRIPTION", "MARKET_DESCRIPTION"]
    }
    
    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 401:
            print("ERROR: Betfair session expired - run betfair_session_refresh_eu.py", file=sys.stderr)
            sys.exit(1)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching markets: {e}", file=sys.stderr)
        sys.exit(1)

def fetch_odds(app_key, session_token, market_ids):
    """Fetch odds for given market IDs"""
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
    
    payload = {
        "marketIds": market_ids,
        "priceProjection": {
            "priceData": ["EX_BEST_OFFERS", "EX_ALL_OFFERS"]
        }
    }
    
    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"ERROR fetching odds: {e}", file=sys.stderr)
        return []

def format_snapshot(markets, odds_by_market):
    """Format data into snapshot structure for run_saved_prompt.py"""
    races = []
    now = datetime.now(timezone.utc)
    
    for market in markets:
        market_id = market['marketId']
        market_name = market.get('marketName', 'Unknown Race')
        
        # Parse market start time
        try:
            market_start = datetime.strptime(market['marketStartTime'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
        except ValueError:
            market_start = datetime.strptime(market['marketStartTime'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        
        # Filter: 15 mins ahead to 24 hours
        time_diff = (market_start - now).total_seconds()
        if time_diff < 900 or time_diff > 86400:  # 15 mins to 24 hours
            continue
        
        # Get venue/course info
        event = market.get('event', {})
        venue = event.get('venue', event.get('name', 'Unknown'))
        competition = market.get('competition', {}).get('name', 'Unknown')
        
        # Get race distance from market description
        market_desc = market.get('description', {})
        distance = market_desc.get('marketType', '')
        race_type = market_desc.get('raceType', '')
        
        # Get odds data for this market
        odds_data = odds_by_market.get(market_id, {})
        runners_odds = odds_data.get('runners', [])
        
        # Build runners list
        runners = []
        for runner_meta in market.get('runners', []):
            selection_id = runner_meta['selectionId']
            runner_name = runner_meta['runnerName']
            
            # Extract metadata (trap, form, trainer)
            metadata = runner_meta.get('metadata', {})
            # For greyhounds: try TRAP or cloth number, for horses: stall draw
            trap = metadata.get('TRAP') or metadata.get('CLOTH_NUMBER') or metadata.get('STALL_DRAW')
            # Extract form - may be in different fields for dogs vs horses
            form = metadata.get('FORM', '') or metadata.get('DAYS_SINCE_LAST_RUN', '')
            trainer = metadata.get('TRAINER_NAME', '') or metadata.get('COLOURS_DESCRIPTION', '')
            
            # For greyhounds, try to extract additional info from runner name if metadata is empty
            if not form and 'greyhound' in market_name.lower():
                # Greyhound names sometimes have form embedded (e.g., "1. Dog Name (123)")
                import re
                form_match = re.search(r'\(([^)]+)\)', runner_name)
                if form_match:
                    form = form_match.group(1)
            
            # Find matching odds
            runner_odds = next((r for r in runners_odds if r['selectionId'] == selection_id), None)
            
            # Extract best back odds and market depth
            best_back = None
            market_depth = []
            total_matched = 0
            
            if runner_odds and runner_odds.get('status') == 'ACTIVE':
                back_offers = runner_odds.get('ex', {}).get('availableToBack', [])
                if back_offers:
                    best_back = back_offers[0]['price']
                    # Get top 3 prices for depth analysis
                    market_depth = [{'price': offer['price'], 'size': offer['size']} 
                                   for offer in back_offers[:3]]
                
                total_matched = runner_odds.get('totalMatched', 0)
            
            if best_back:
                # Parse trap number from runner name if not in metadata (common for greyhounds)
                if not trap and runner_name:
                    import re
                    trap_match = re.match(r'^(\d+)\.', runner_name)
                    if trap_match:
                        trap = trap_match.group(1)
                
                runner_data = {
                    "name": runner_name,
                    "selectionId": selection_id,
                    "odds": best_back,
                    "trap": trap,
                    "form": form or "Unknown",  # Provide default if empty
                    "trainer": trainer or "Unknown",  # Provide default if empty
                    "total_matched": total_matched
                }
                
                # Add market depth if available
                if len(market_depth) > 1:
                    runner_data["market_depth"] = market_depth
                
                runners.append(runner_data)
        
        # Only include races with odds available
        if runners:
            race_data = {
                "market_id": market_id,
                "market_name": market_name,
                "venue": venue,
                "course": venue,  # Alias
                "competition": competition,
                "start_time": market['marketStartTime'],
                "runners": runners,
                "total_runners": len(runners)
            }
            
            # Add distance if available
            if distance:
                race_data["distance"] = distance
            if race_type:
                race_data["race_type"] = race_type
            
            races.append(race_data)
    
    return {
        "timestamp": now.isoformat() + "Z",
        "races": races,
        "total_races": len(races)
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch live Betfair horse racing odds")
    parser.add_argument('--out', type=str, default='response.json',
                        help='Output JSON file path (default: response.json)')
    parser.add_argument('--hours', type=int, default=24,
                        help='Hours ahead to fetch (default: 24)')
    parser.add_argument('--max_races', type=int, default=100,
                        help='Maximum races to fetch (default: 100)')
    parser.add_argument('--sport', type=str, choices=['horses', 'greyhounds'], default='horses',
                        help='Sport type: horses or greyhounds (default: horses)')
    parser.add_argument('--country', type=str, default=None,
                        help='Specific country code (IE, GB) or None for both (default: None)')
    
    args = parser.parse_args()
    
    # Map sport to event type ID
    event_type = "7" if args.sport == "horses" else "4339"
    sport_name = "Horse Racing" if args.sport == "horses" else "Greyhound Racing"
    
    # Handle country filter
    countries = None
    if args.country:
        countries = [args.country.upper()]
        print(f"Filtering to {args.country.upper()} only")
    
    print("Loading Betfair credentials...")
    app_key, session_token = load_credentials()
    
    print(f"Fetching {sport_name} markets (next {args.hours} hours)...")
    markets = fetch_markets(app_key, session_token, args.hours, event_type, countries)
    
    if not markets:
        print("WARNING: No markets found", file=sys.stderr)
        sys.exit(0)
    
    print(f"Found {len(markets)} markets")
    
    # Fetch odds in batches (Betfair limit ~10 per request)
    odds_by_market = {}
    batch_size = 10
    
    for i in range(0, min(len(markets), args.max_races), batch_size):
        batch = markets[i:i+batch_size]
        market_ids = [m['marketId'] for m in batch]
        
        print(f"Fetching odds batch {i//batch_size + 1}/{(min(len(markets), args.max_races) + batch_size - 1)//batch_size}...")
        odds_batch = fetch_odds(app_key, session_token, market_ids)
        
        for book in odds_batch:
            odds_by_market[book['marketId']] = book
    
    print(f"Fetched odds for {len(odds_by_market)} markets")
    
    # Format snapshot
    snapshot = format_snapshot(markets, odds_by_market)
    
    print(f"Formatted {snapshot['total_races']} races with odds")
    
    # Save to file
    with open(args.out, 'w') as f:
        json.dump(snapshot, f, indent=2)
    
    print(f"[OK] Saved snapshot to {args.out}")
    print(f"  Races: {snapshot['total_races']}")
    print(f"  Timestamp: {snapshot['timestamp']}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

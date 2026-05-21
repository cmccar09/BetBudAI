#!/usr/bin/env python3
"""Fetch and display today's race results from Betfair"""

import requests
import json
from datetime import datetime, timedelta

def get_betfair_session():
    """Get Betfair session token"""
    try:
        with open('betfair-creds.json', 'r') as f:
            creds = json.load(f)
    except:
        print("Error: betfair-creds.json not found")
        return None
    
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
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        result = response.json()
        return result.get('token') or result.get('sessionToken')
    return None

def get_todays_results(session_token, app_key):
    """Fetch today's settled races"""
    
    # Get today's date range
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"
    
    headers = {
        "X-Application": app_key,
        "X-Authentication": session_token,
        "Content-Type": "application/json"
    }
    
    payload = {
        "filter": {
            "eventTypeIds": ["7"],  # Horse Racing
            "marketCountries": ["GB", "IE"],
            "marketTypeCodes": ["WIN"],
            "marketStartTime": {
                "from": today.isoformat() + "Z",
                "to": tomorrow.isoformat() + "Z"
            }
        },
        "maxResults": 100,
        "marketProjection": ["MARKET_START_TIME", "RUNNER_DESCRIPTION", "EVENT"]
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"Error fetching markets: {response.status_code}")
        return []
    
    markets = response.json()
    
    # Get market results for settled races
    market_ids = [m['marketId'] for m in markets[:20]]  # First 20 markets
    
    results_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
    
    results_payload = {
        "marketIds": market_ids,
        "priceProjection": {
            "priceData": ["EX_BEST_OFFERS"]
        }
    }
    
    results_response = requests.post(results_url, headers=headers, json=results_payload)
    
    if results_response.status_code != 200:
        print(f"Error fetching results: {results_response.status_code}")
        return []
    
    market_books = results_response.json()
    
    # Match results with market info
    results = []
    for market_book in market_books:
        market_id = market_book['marketId']
        status = market_book.get('status')
        
        # Find corresponding market info
        market_info = next((m for m in markets if m['marketId'] == market_id), None)
        
        if status == 'CLOSED' and market_info:
            venue = market_info['event']['venue']
            race_time = market_info['marketStartTime']
            
            # Get winner(s)
            winners = []
            for runner in market_book.get('runners', []):
                if runner.get('status') == 'WINNER':
                    runner_id = runner['selectionId']
                    # Find runner name
                    runner_desc = next((r for r in market_info.get('runners', []) if r['selectionId'] == runner_id), None)
                    if runner_desc:
                        winners.append(runner_desc['runnerName'])
            
            if winners:
                results.append({
                    'venue': venue,
                    'time': race_time,
                    'winner': ', '.join(winners),
                    'market_id': market_id
                })
    
    return results

def main():
    print("="*70)
    print(f"FETCHING TODAY'S RACE RESULTS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*70)
    
    # Get session
    print("\n[1/3] Logging into Betfair...")
    try:
        with open('betfair-creds.json', 'r') as f:
            creds = json.load(f)
            app_key = creds['app_key']
    except:
        print("Error loading credentials")
        return
    
    session = get_betfair_session()
    if not session:
        print("Failed to get Betfair session")
        return
    print("  ✓ Logged in")
    
    # Get results
    print("\n[2/3] Fetching race results...")
    results = get_todays_results(session, app_key)
    print(f"  ✓ Found {len(results)} completed races")
    
    # Display results
    print("\n[3/3] Today's Results:")
    print("="*70)
    
    if results:
        for idx, result in enumerate(results, 1):
            time = datetime.fromisoformat(result['time'].replace('Z', ''))
            print(f"\n{idx}. {result['venue']} - {time.strftime('%H:%M')}")
            print(f"   Winner: {result['winner']}")
            print(f"   Market ID: {result['market_id']}")
    else:
        print("\nNo completed races found yet today.")
        print("(Races may still be running or results not yet settled)")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()

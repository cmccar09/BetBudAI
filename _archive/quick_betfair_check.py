"""
Quick Betfair API Check

Runs a single check to see what's currently available in Betfair API.
Use this to quickly test timing without long monitoring.
"""

import json
import requests
from datetime import datetime, timedelta

# Load Betfair credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

BETFAIR_USERNAME = creds['username']
BETFAIR_PASSWORD = creds['password']
APP_KEY = creds['app_key']
CERT_PATH = 'betfair-client.crt'
KEY_PATH = 'betfair-client.key'

def betfair_login():
    """Login to Betfair"""
    login_url = 'https://identitysso-cert.betfair.com/api/certlogin'
    
    try:
        response = requests.post(
            login_url,
            cert=(CERT_PATH, KEY_PATH),
            data={'username': BETFAIR_USERNAME, 'password': BETFAIR_PASSWORD},
            headers={'X-Application': APP_KEY}
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('sessionToken')
        return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def search_markets(session_token, hours_back=6):
    """Search for markets in the last X hours"""
    url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/'
    
    headers = {
        'X-Application': APP_KEY,
        'X-Authentication': session_token,
        'Content-Type': 'application/json'
    }
    
    current_time = datetime.now()
    from_time = current_time - timedelta(hours=hours_back)
    to_time = current_time + timedelta(hours=1)
    
    payload = {
        'filter': {
            'eventTypeIds': ['7'],  # Horse racing
            'marketTypeCodes': ['WIN'],
            'marketStartTime': {
                'from': from_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'to': to_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        },
        'marketProjection': ['RUNNER_DESCRIPTION', 'EVENT', 'MARKET_START_TIME'],
        'maxResults': 200,
        'sort': 'FIRST_TO_START'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API error: {response.status_code} - {response.text}")
        return None
    except Exception as e:
        print(f"Request error: {e}")
        return None

def check_market_status(session_token, market_ids):
    """Check status and results for specific markets"""
    url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/'
    
    headers = {
        'X-Application': APP_KEY,
        'X-Authentication': session_token,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'marketIds': market_ids,
        'priceProjection': {'priceData': ['EX_BEST_OFFERS']}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error checking market status: {e}")
        return None

def main():
    print("\n" + "="*80)
    print("QUICK BETFAIR API CHECK")
    print("="*80)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Login
    print("Logging in to Betfair...")
    session_token = betfair_login()
    
    if not session_token:
        print("❌ Login failed")
        return
    
    print("✓ Login successful\n")
    
    # Search for markets in last 6 hours
    print("Searching for markets in last 6 hours...")
    markets = search_markets(session_token, hours_back=6)
    
    if not markets:
        print("❌ No markets found or API error")
        return
    
    print(f"✓ Found {len(markets)} markets\n")
    
    # Group by time
    now = datetime.now()
    by_age = {'<1h': [], '1-2h': [], '2-4h': [], '4-6h': [], '>6h': []}
    
    for market in markets:
        start_time_str = market.get('marketStartTime', '')
        if start_time_str:
            start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            age_hours = (now - start_time).total_seconds() / 3600
            
            if age_hours < 1:
                by_age['<1h'].append(market)
            elif age_hours < 2:
                by_age['1-2h'].append(market)
            elif age_hours < 4:
                by_age['2-4h'].append(market)
            elif age_hours < 6:
                by_age['4-6h'].append(market)
            else:
                by_age['>6h'].append(market)
    
    print("Markets grouped by age:")
    print("-" * 80)
    for age_group, group_markets in by_age.items():
        if group_markets:
            print(f"\n{age_group} ago: {len(group_markets)} markets")
            for market in group_markets[:5]:  # Show first 5
                venue = market.get('event', {}).get('venue', 'Unknown')
                start_time = market.get('marketStartTime', 'Unknown')[:16]
                market_id = market.get('marketId', 'Unknown')
                print(f"  {start_time} {venue:20} {market_id}")
            if len(group_markets) > 5:
                print(f"  ... and {len(group_markets) - 5} more")
    
    # Check status of a few recent markets
    if markets:
        print("\n" + "="*80)
        print("CHECKING MARKET STATUS (sample of 5)")
        print("="*80)
        
        sample_ids = [m.get('marketId') for m in markets[:5]]
        statuses = check_market_status(session_token, sample_ids)
        
        if statuses:
            for status in statuses:
                market_id = status.get('marketId', 'Unknown')
                market_status = status.get('status', 'Unknown')
                is_complete = status.get('isMarketDataDelayed', False)
                
                print(f"\nMarket: {market_id}")
                print(f"  Status: {market_status}")
                print(f"  Complete: {is_complete}")
                
                if 'runners' in status:
                    print(f"  Runners: {len(status['runners'])}")
                    for runner in status['runners'][:3]:
                        runner_status = runner.get('status', 'Unknown')
                        print(f"    Runner status: {runner_status}")
    
    print("\n" + "="*80)
    print("KEY FINDINGS:")
    print("="*80)
    print(f"Total markets in last 6 hours: {len(markets)}")
    print(f"Markets <1 hour old: {len(by_age['<1h'])}")
    print(f"Markets 1-2 hours old: {len(by_age['1-2h'])}")
    print(f"Markets 2-4 hours old: {len(by_age['2-4h'])}")
    print(f"Markets 4-6 hours old: {len(by_age['4-6h'])}")
    print(f"Markets >6 hours old: {len(by_age['>6h'])}")
    
    print("\n💡 TIP: Results typically appear 10-30 minutes after race finish")
    print("💡 TIP: Results stay available for approximately 24-48 hours")
    print("💡 TIP: Best time to fetch: 30-60 minutes after race finish")
    print("="*80)

if __name__ == '__main__':
    main()

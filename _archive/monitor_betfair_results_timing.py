"""
Betfair API Results Timing Monitor

Monitors when race results appear in Betfair API and for how long.
Critical for understanding timing windows for automated learning loop.

Run this script during racing hours to collect timing data.
"""

import boto3
import json
import time
from datetime import datetime, timedelta
import requests
import os

# Load Betfair credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

BETFAIR_USERNAME = creds['username']
BETFAIR_PASSWORD = creds['password']
APP_KEY = creds['app_key']
CERT_PATH = 'betfair-client.crt'
KEY_PATH = 'betfair-client.key'

# DynamoDB setup
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def betfair_login():
    """Login to Betfair using certificate authentication"""
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
            if result.get('sessionToken'):
                return result['sessionToken']
            else:
                print(f"Login failed: {result}")
                return None
        else:
            print(f"Login HTTP error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Login exception: {e}")
        return None

def check_market_results(session_token, market_ids):
    """Check if results are available for given market IDs"""
    url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/'
    
    headers = {
        'X-Application': APP_KEY,
        'X-Authentication': session_token,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'marketIds': market_ids,
        'priceProjection': {
            'priceData': ['EX_BEST_OFFERS']
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error checking markets: {e}")
        return None

def search_settled_markets(session_token, from_date, to_date):
    """Search for settled markets in date range"""
    url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/'
    
    headers = {
        'X-Application': APP_KEY,
        'X-Authentication': session_token,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'filter': {
            'eventTypeIds': ['7'],  # Horse racing
            'marketTypeCodes': ['WIN'],
            'marketStartTime': {
                'from': from_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'to': to_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        },
        'marketProjection': ['RUNNER_DESCRIPTION', 'EVENT', 'MARKET_START_TIME'],
        'maxResults': 100,
        'sort': 'FIRST_TO_START'
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error searching markets: {e}")
        return None

def get_todays_races():
    """Get races from our database that we're tracking"""
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        FilterExpression='show_in_ui = :ui',
        ExpressionAttributeValues={
            ':date': datetime.now().strftime('%Y-%m-%d'),
            ':ui': True
        }
    )
    
    races = {}
    for item in response['Items']:
        race_key = f"{item.get('course')}_{item.get('race_time')}"
        if race_key not in races:
            races[race_key] = {
                'course': item.get('course'),
                'race_time': item.get('race_time'),
                'horses': []
            }
        races[race_key]['horses'].append(item.get('horse_name', 'Unknown'))
    
    return races

def monitor_results_timing(check_interval_minutes=5, duration_hours=6):
    """
    Monitor Betfair API to understand when results appear and how long they're available
    
    Args:
        check_interval_minutes: How often to check (default 5 mins)
        duration_hours: How long to monitor (default 6 hours)
    """
    
    print("\n" + "="*80)
    print("BETFAIR RESULTS TIMING MONITOR")
    print("="*80)
    print(f"Check interval: Every {check_interval_minutes} minutes")
    print(f"Duration: {duration_hours} hours")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")
    
    # Login to Betfair
    session_token = betfair_login()
    if not session_token:
        print("ERROR: Failed to login to Betfair")
        return
    
    print("✓ Betfair login successful")
    
    # Get today's races we're tracking
    races = get_todays_races()
    print(f"✓ Tracking {len(races)} races from our database\n")
    
    # Create monitoring log
    log_file = f"betfair_timing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=duration_hours)
    check_count = 0
    
    results_first_seen = {}  # Track when results first appear
    results_last_seen = {}   # Track when results disappear
    
    try:
        while datetime.now() < end_time:
            check_count += 1
            current_time = datetime.now()
            
            print(f"\n[Check #{check_count}] {current_time.strftime('%H:%M:%S')}")
            print("-" * 60)
            
            # Search for markets in last 3 hours
            search_from = current_time - timedelta(hours=3)
            search_to = current_time + timedelta(hours=1)
            
            markets = search_settled_markets(session_token, search_from, search_to)
            
            if markets:
                print(f"Found {len(markets)} markets in API")
                
                # Log findings
                with open(log_file, 'a') as f:
                    f.write(f"\n[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] Check #{check_count}\n")
                    f.write(f"Markets found: {len(markets)}\n")
                    
                    for market in markets:
                        venue = market.get('event', {}).get('venue', 'Unknown')
                        start_time_str = market.get('marketStartTime', 'Unknown')
                        market_id = market.get('marketId', 'Unknown')
                        
                        # Track first and last seen
                        if market_id not in results_first_seen:
                            results_first_seen[market_id] = current_time
                            print(f"  NEW: {venue} {start_time_str[:16]} (Market ID: {market_id})")
                            f.write(f"  FIRST SEEN: {venue} {start_time_str[:16]} ID:{market_id}\n")
                        else:
                            results_last_seen[market_id] = current_time
                        
                        f.write(f"  {venue} {start_time_str[:16]} ID:{market_id}\n")
                
                # Calculate timing statistics
                if results_first_seen:
                    print(f"\nTiming Statistics:")
                    print(f"  Total markets tracked: {len(results_first_seen)}")
                    
                    # Calculate average delay from race start to API availability
                    for market_id, first_seen in results_first_seen.items():
                        if market_id in results_last_seen:
                            duration = results_last_seen[market_id] - first_seen
                            print(f"  Market {market_id[:10]}... available for {duration}")
            else:
                print("No markets found in API")
                with open(log_file, 'a') as f:
                    f.write(f"\n[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] No markets found\n")
            
            # Wait for next check
            print(f"\nNext check in {check_interval_minutes} minutes...")
            time.sleep(check_interval_minutes * 60)
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    
    # Final summary
    print("\n" + "="*80)
    print("MONITORING SUMMARY")
    print("="*80)
    print(f"Total checks performed: {check_count}")
    print(f"Total markets seen: {len(results_first_seen)}")
    print(f"Log file: {log_file}")
    
    if results_first_seen:
        print(f"\nResults Availability Timeline:")
        for market_id, first_seen in sorted(results_first_seen.items(), key=lambda x: x[1]):
            if market_id in results_last_seen:
                duration = results_last_seen[market_id] - first_seen
                print(f"  {market_id[:20]}... First: {first_seen.strftime('%H:%M')} | "
                      f"Last: {results_last_seen[market_id].strftime('%H:%M')} | "
                      f"Duration: {duration}")
            else:
                print(f"  {market_id[:20]}... First: {first_seen.strftime('%H:%M')} | Still available")
    
    print("\n" + "="*80)
    print(f"Full log saved to: {log_file}")
    print("="*80)

if __name__ == '__main__':
    import sys
    
    # Allow custom parameters
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    
    print("\nBetfair Results Timing Monitor")
    print(f"This will check every {interval} minutes for {duration} hours")
    print("Press Ctrl+C to stop early\n")
    
    monitor_results_timing(check_interval_minutes=interval, duration_hours=duration)

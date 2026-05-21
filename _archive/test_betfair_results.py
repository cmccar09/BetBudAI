import sys
sys.path.insert(0, 'lambda-results-fetcher')

from betfair_cert_auth import authenticate_with_certificate
import requests
import os
from datetime import datetime, timedelta
import json

# Get credentials
username = os.environ.get('BETFAIR_USERNAME')
password = os.environ.get('BETFAIR_PASSWORD')
app_key = os.environ.get('BETFAIR_APP_KEY')

print(f"\n=== BETFAIR API RESULTS TEST ===")
print(f"Time: {datetime.utcnow().isoformat()}")
print(f"Testing authentication and market results retrieval...\n")

# Authenticate
print("1. Authenticating with Betfair...")
session_token = authenticate_with_certificate(username, password, app_key)

if not session_token:
    print("ERROR: Authentication failed!")
    sys.exit(1)

print(f"✓ Authentication successful!")
print(f"Session token: {session_token[:20]}...{session_token[-10:]}\n")

# Get today's settled markets
print("2. Fetching horse racing markets from today...")
now = datetime.utcnow()
today_start = now.replace(hour=0, minute=0, second=0)

url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"
headers = {
    "X-Application": app_key,
    "X-Authentication": session_token,
    "Content-Type": "application/json"
}

market_filter = {
    "filter": {
        "eventTypeIds": ["7"],  # Horse Racing
        "marketCountries": ["GB", "IE"],
        "marketTypeCodes": ["WIN"],
        "marketStartTime": {
            "from": today_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "to": now.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    },
    "maxResults": "20",
    "marketProjection": ["EVENT", "MARKET_START_TIME"]
}

try:
    response = requests.post(url, headers=headers, json=market_filter, timeout=30)
    response.raise_for_status()
    markets = response.json()
    
    print(f"✓ Found {len(markets)} markets from today\n")
    
    if len(markets) > 0:
        # Get results for first few markets
        market_ids = [m['marketId'] for m in markets[:5]]
        
        print(f"3. Fetching results for {len(market_ids)} markets...")
        
        book_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
        book_payload = {
            "marketIds": market_ids,
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS", "EX_TRADED"]
            }
        }
        
        book_response = requests.post(book_url, headers=headers, json=book_payload, timeout=30)
        book_response.raise_for_status()
        books = book_response.json()
        
        print(f"✓ Retrieved {len(books)} market results\n")
        
        # Display results
        print("=== RACE RESULTS ===\n")
        for i, book in enumerate(books[:5], 1):
            market_id = book.get('marketId')
            status = book.get('status')
            
            # Find market details
            market_details = next((m for m in markets if m['marketId'] == market_id), {})
            event_name = market_details.get('event', {}).get('name', 'Unknown')
            race_time = market_details.get('marketStartTime', 'Unknown')
            
            print(f"Race {i}: {event_name}")
            print(f"  Market ID: {market_id}")
            print(f"  Time: {race_time}")
            print(f"  Status: {status}")
            
            if status in ['CLOSED', 'SETTLED']:
                # Find winner
                for runner in book.get('runners', []):
                    if runner.get('status') == 'WINNER':
                        print(f"  🏆 WINNER: {runner.get('runnerName', 'Unknown')} (ID: {runner.get('selectionId')})")
                        print(f"      Final odds: {runner.get('lastPriceTraded', 'N/A')}")
                
                # Show placed horses
                placed = [r for r in book.get('runners', []) if r.get('status') == 'PLACED']
                if placed:
                    print(f"  📍 Placed horses: {len(placed)}")
                    for p in placed:
                        print(f"      {p.get('runnerName', 'Unknown')} @ {p.get('lastPriceTraded', 'N/A')}")
            elif status == 'OPEN':
                print(f"  ⏳ Race still running (not settled)")
            
            print()
        
    else:
        print("No markets found from today yet")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

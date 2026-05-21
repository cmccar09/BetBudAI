"""
Test Betfair API to see what runner statuses are returned
"""

import requests
import json
from datetime import datetime, timedelta

# Load credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

APP_KEY = creds['app_key']
SESSION_TOKEN = creds['session_token']

print("\n" + "="*80)
print("TESTING BETFAIR RUNNER STATUSES")
print("="*80 + "\n")

# Get a completed market from yesterday
api_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"

yesterday = (datetime.utcnow() - timedelta(days=1))
today = datetime.utcnow()

headers = {
    'X-Application': APP_KEY,
    'X-Authentication': SESSION_TOKEN,
    'Content-Type': 'application/json'
}

# Get completed horse racing markets from today
payload = {
    "filter": {
        "eventTypeIds": ["7"],  # Horse Racing
        "marketCountries": ["GB", "IE"],
        "marketTypeCodes": ["WIN"],
        "marketStartTime": {
            "from": today.strftime("%Y-%m-%dT00:00:00Z"),
            "to": today.strftime("%Y-%m-%dT23:59:59Z")
        }
    },
    "maxResults": 20,
    "marketProjection": ["EVENT", "MARKET_START_TIME", "RUNNER_DESCRIPTION"]
}

try:
    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    markets = response.json()
    
    print(f"Found {len(markets)} completed markets from yesterday\n")
    
    if markets:
        # Get detailed results for first market
        market_id = markets[0]['marketId']
        event_name = markets[0]['event']['name']
        
        print(f"Checking market: {event_name}")
        print(f"Market ID: {market_id}\n")
        
        # Get market book with results
        book_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
        
        book_payload = {
            "marketIds": [market_id],
            "priceProjection": {
                "priceData": ["EX_BEST_OFFERS"]
            }
        }
        
        book_response = requests.post(book_url, headers=headers, json=book_payload, timeout=30)
        book_response.raise_for_status()
        book_data = book_response.json()
        
        if book_data and len(book_data) > 0:
            market_book = book_data[0]
            
            print(f"Market status: {market_book.get('status')}")
            print(f"Number of runners: {market_book.get('numberOfActiveRunners')}")
            print(f"\nRunner statuses:")
            print("-" * 80)
            
            for runner in market_book.get('runners', []):
                selection_id = runner.get('selectionId')
                status = runner.get('status')
                
                # Find runner name from catalog
                runner_name = "Unknown"
                for catalog_runner in markets[0].get('runners', []):
                    if catalog_runner.get('selectionId') == selection_id:
                        runner_name = catalog_runner.get('runnerName', 'Unknown')
                        break
                
                print(f"  {runner_name:30} - Status: {status}")
            
            print("\n" + "="*80)
            print("AVAILABLE STATUSES:")
            unique_statuses = set([r.get('status') for r in market_book.get('runners', [])])
            for status in unique_statuses:
                print(f"  - {status}")
            print("="*80 + "\n")
            
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

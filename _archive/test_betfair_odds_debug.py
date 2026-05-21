"""
Debug script to test Betfair API odds fetching
Tests certificate authentication and API calls step by step
"""

import json
import requests
import datetime
import os

def test_cert_authentication():
    """Test certificate authentication"""
    print("=" * 60)
    print("STEP 1: Testing Certificate Authentication")
    print("=" * 60)
    
    # Load credentials
    try:
        with open('betfair-creds.json', 'r') as f:
            creds = json.load(f)
            username = creds['username']
            password = creds['password']
            app_key = creds['app_key']
            print(f"✓ Loaded credentials for user: {username}")
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return None, None
    
    # Check certificate files
    cert_path = 'betfair-client.crt'
    key_path = 'betfair-client.key'
    
    if not os.path.exists(cert_path):
        print(f"❌ Certificate file not found: {cert_path}")
        return None, None
    if not os.path.exists(key_path):
        print(f"❌ Key file not found: {key_path}")
        return None, None
    
    print(f"✓ Certificate files found")
    
    # Interactive (cert) login endpoint
    url = "https://identitysso-cert.betfair.com/api/certlogin"
    
    headers = {
        'X-Application': app_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'username': username,
        'password': password
    }
    
    try:
        print(f"\nAttempting certificate login...")
        response = requests.post(
            url,
            headers=headers,
            data=data,
            cert=(cert_path, key_path),
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('loginStatus') == 'SUCCESS':
                session_token = result.get('sessionToken')
                print(f"\n✓ Certificate authentication SUCCESSFUL")
                print(f"  Session token: {session_token[:30]}...")
                return app_key, session_token
            else:
                print(f"\n❌ Login failed: {result.get('loginStatus')}")
                return None, None
        else:
            print(f"\n❌ Certificate auth failed: HTTP {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"\n❌ Exception during authentication: {e}")
        return None, None

def test_list_markets(app_key, session_token):
    """Test listing markets"""
    print("\n" + "=" * 60)
    print("STEP 2: Testing Market Listing (Horse Racing)")
    print("=" * 60)
    
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"
    
    now = datetime.datetime.utcnow()
    to_time = now + datetime.timedelta(hours=24)
    
    request_body = {
        "filter": {
            "eventTypeIds": ["7"],  # Horse racing
            "marketStartTime": {
                "from": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": to_time.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "marketTypeCodes": ["WIN"],
            "marketCountries": ["GB", "IE"]
        },
        "maxResults": 10,
        "marketProjection": ["RUNNER_METADATA", "EVENT", "MARKET_START_TIME", "MARKET_DESCRIPTION"]
    }
    
    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        print(f"\nFetching markets...")
        response = requests.post(url, json=request_body, headers=headers, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            markets = response.json()
            print(f"\n✓ Market listing SUCCESSFUL")
            print(f"  Found {len(markets)} markets")
            
            if markets:
                market = markets[0]
                print(f"\n  Sample market:")
                print(f"    Market ID: {market['marketId']}")
                print(f"    Event: {market.get('event', {}).get('name', 'Unknown')}")
                print(f"    Venue: {market.get('event', {}).get('venue', 'Unknown')}")
                print(f"    Start Time: {market.get('marketStartTime')}")
                print(f"    Runners: {len(market.get('runners', []))}")
                return markets
            else:
                print(f"\n⚠ No markets found (may be timing issue)")
                return []
        else:
            print(f"\n❌ Market listing failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"\n❌ Exception during market listing: {e}")
        return []

def test_list_market_book(app_key, session_token, markets):
    """Test fetching odds (market book)"""
    print("\n" + "=" * 60)
    print("STEP 3: Testing Odds Fetching (Market Book)")
    print("=" * 60)
    
    if not markets:
        print("❌ No markets to fetch odds for")
        return
    
    # Get first market
    market_id = markets[0]['marketId']
    print(f"\nFetching odds for market: {market_id}")
    
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
    
    request_body = {
        "marketIds": [market_id],
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
        response = requests.post(url, json=request_body, headers=headers, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            market_books = response.json()
            print(f"\n✓ Odds fetching SUCCESSFUL")
            
            if market_books:
                book = market_books[0]
                print(f"\n  Market ID: {book['marketId']}")
                print(f"  Status: {book.get('status')}")
                print(f"  Total Matched: £{book.get('totalMatched', 0):.2f}")
                print(f"  Runners: {len(book.get('runners', []))}")
                
                # Show odds for each runner
                print(f"\n  Runner Odds:")
                for runner in book.get('runners', []):
                    selection_id = runner['selectionId']
                    status = runner.get('status')
                    
                    # Get best back price
                    back_prices = runner.get('ex', {}).get('availableToBack', [])
                    if back_prices:
                        best_price = back_prices[0]['price']
                        size = back_prices[0]['size']
                        print(f"    Selection {selection_id}: {best_price} (£{size:.2f} available) - Status: {status}")
                    else:
                        print(f"    Selection {selection_id}: NO ODDS AVAILABLE - Status: {status}")
                
                # Save full response for inspection
                with open('betfair_odds_debug_response.json', 'w') as f:
                    json.dump(market_books, f, indent=2)
                print(f"\n  Full response saved to: betfair_odds_debug_response.json")
                
            else:
                print(f"\n⚠ No market books returned")
        else:
            print(f"\n❌ Odds fetching failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Exception during odds fetching: {e}")

def main():
    """Main test function"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "BETFAIR API ODDS DIAGNOSTIC TEST" + " " * 16 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    # Step 1: Authenticate
    app_key, session_token = test_cert_authentication()
    if not app_key or not session_token:
        print("\n❌ Authentication failed - cannot proceed")
        return
    
    # Step 2: List markets
    markets = test_list_markets(app_key, session_token)
    
    # Step 3: Fetch odds
    if markets:
        test_list_market_book(app_key, session_token, markets)
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()

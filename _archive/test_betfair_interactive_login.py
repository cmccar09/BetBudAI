"""
Test Betfair Interactive Login (Non-Certificate Method)
This uses standard username/password authentication without certificates
"""

import json
import requests
import datetime

def test_interactive_login():
    """Test interactive (non-certificate) login"""
    print("=" * 60)
    print("STEP 1: Testing Interactive Login (No Certificate)")
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
    
    # Interactive (non-cert) login endpoint
    url = "https://identitysso.betfair.com/api/login"
    
    headers = {
        'X-Application': app_key,
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    
    data = {
        'username': username,
        'password': password
    }
    
    try:
        print(f"\nAttempting interactive login (username/password only)...")
        response = requests.post(
            url,
            headers=headers,
            data=data,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for both response formats
            if result.get('loginStatus') == 'SUCCESS' or result.get('status') == 'SUCCESS':
                # Try different token field names
                session_token = result.get('sessionToken') or result.get('token')
                
                if session_token:
                    print(f"\n✓ Interactive login SUCCESSFUL!")
                    print(f"  Session token: {session_token[:30]}...")
                    print(f"\n  Note: This session will expire in ~8 hours")
                    return app_key, session_token
                else:
                    print(f"\n❌ Login succeeded but no token in response")
                    print(f"   Response: {result}")
                    return None, None
            else:
                print(f"\n❌ Login failed: {result.get('loginStatus') or result.get('status')}")
                if result.get('loginStatus') == 'INVALID_USERNAME_OR_PASSWORD':
                    print(f"   Check your username and password in betfair-creds.json")
                return None, None
        else:
            print(f"\n❌ Login failed: HTTP {response.status_code}")
            return None, None
            
    except Exception as e:
        print(f"\n❌ Exception during login: {e}")
        return None, None

def test_list_markets(app_key, session_token):
    """Test listing markets"""
    print("\n" + "=" * 60)
    print("STEP 2: Testing Market Listing")
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
        "maxResults": 5,
        "marketProjection": ["RUNNER_METADATA", "EVENT", "MARKET_START_TIME"]
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
                for i, market in enumerate(markets[:3], 1):
                    print(f"\n  Market {i}:")
                    print(f"    ID: {market['marketId']}")
                    print(f"    Event: {market.get('event', {}).get('name', 'Unknown')}")
                    print(f"    Venue: {market.get('event', {}).get('venue', 'Unknown')}")
                    print(f"    Time: {market.get('marketStartTime')}")
                return markets
            else:
                print(f"\n  No markets found (timing issue - try different times)")
                return []
        else:
            print(f"\n❌ Market listing failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        return []

def test_fetch_odds(app_key, session_token, markets):
    """Test fetching odds"""
    print("\n" + "=" * 60)
    print("STEP 3: Testing Odds Fetching")
    print("=" * 60)
    
    if not markets:
        print("❌ No markets to fetch odds for")
        return
    
    market_id = markets[0]['marketId']
    print(f"\nFetching odds for market: {market_id}")
    
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
    
    request_body = {
        "marketIds": [market_id],
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
        
        print(f"Response Status: {response.status_code}")
        
        if response.status_code == 200:
            market_books = response.json()
            print(f"\n✓ ODDS FETCHING SUCCESSFUL!")
            
            if market_books:
                book = market_books[0]
                print(f"\n  Market: {book['marketId']}")
                print(f"  Status: {book.get('status')}")
                print(f"  Total Matched: £{book.get('totalMatched', 0):.2f}")
                
                print(f"\n  Runner Odds:")
                for runner in book.get('runners', [])[:5]:
                    selection_id = runner['selectionId']
                    back_prices = runner.get('ex', {}).get('availableToBack', [])
                    if back_prices:
                        best_price = back_prices[0]['price']
                        print(f"    Selection {selection_id}: {best_price}")
                    else:
                        print(f"    Selection {selection_id}: No odds")
                
                # Save response
                with open('betfair_interactive_login_success.json', 'w') as f:
                    json.dump({
                        'app_key': app_key,
                        'session_token': session_token,
                        'markets': markets[:2],
                        'odds': market_books
                    }, f, indent=2)
                
                print(f"\n  ✓ Full response saved to: betfair_interactive_login_success.json")
                
        else:
            print(f"\n❌ Odds fetching failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")

def main():
    print("\n╔" + "═" * 58 + "╗")
    print("║" + " " * 6 + "BETFAIR INTERACTIVE LOGIN TEST" + " " * 22 + "║")
    print("║" + " " * 10 + "(No Certificate Required)" + " " * 23 + "║")
    print("╚" + "═" * 58 + "╝\n")
    
    # Step 1: Login
    app_key, session_token = test_interactive_login()
    if not app_key or not session_token:
        print("\n❌ Login failed - cannot proceed")
        print("\nPossible issues:")
        print("  - Wrong username/password in betfair-creds.json")
        print("  - Account locked or suspended")
        print("  - 2FA enabled (needs different approach)")
        return
    
    # Step 2: List markets
    markets = test_list_markets(app_key, session_token)
    
    # Step 3: Fetch odds
    if markets:
        test_fetch_odds(app_key, session_token, markets)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    if app_key and session_token:
        print("\n✓ SUCCESS! Interactive login works!")
        print("\nYou can use this method for now while we fix the certificate issue.")
        print("\nSession token saved to: betfair_interactive_login_success.json")
        print("Note: Session expires in ~8 hours (you'll need to re-login)")

if __name__ == "__main__":
    main()

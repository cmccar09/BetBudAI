#!/usr/bin/env python3
"""Quick test: Can we fetch today's race meetings from Betfair?"""
import json
import requests
from datetime import datetime, timedelta

# Load credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

print("=" * 60)
print("BETFAIR RACE MEETINGS TEST")
print("=" * 60)

# Step 1: Try certificate login
print("\n[1/2] Testing certificate authentication...")
cert_url = "https://identitysso-cert.betfair.com/api/certlogin"

try:
    response = requests.post(
        cert_url,
        headers={
            'X-Application': creds['app_key'],
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        data={'username': creds['username'], 'password': creds['password']},
        cert=('betfair-client.crt', 'betfair-client.key'),
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        login_status = result.get('loginStatus', result.get('status'))
        
        if login_status == 'SUCCESS':
            session_token = result.get('sessionToken')
            print(f"  [OK] Certificate login successful")
            print(f"  Token: {session_token[:40]}...")
        else:
            print(f"  [FAILED] Login status: {login_status}")
            print("  Certificate authentication not working")
            exit(1)
    else:
        print(f"  [FAILED] HTTP {response.status_code}")
        exit(1)
        
except Exception as e:
    print(f"  [ERROR] {e}")
    exit(1)

# Step 2: Test fetching race meetings
print("\n[2/2] Fetching today's race meetings...")

today = datetime.now()
tomorrow = today + timedelta(days=1)

api_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"
headers = {
    'X-Application': creds['app_key'],
    'X-Authentication': session_token,
    'Content-Type': 'application/json'
}

filter_params = {
    "filter": {
        "eventTypeIds": ["7"],  # Horse racing
        "marketCountries": ["GB", "IE"],
        "marketTypeCodes": ["WIN"],
        "marketStartTime": {
            "from": today.strftime("%Y-%m-%dT00:00:00Z"),
            "to": tomorrow.strftime("%Y-%m-%dT23:59:59Z")
        }
    },
    "maxResults": 50,
    "marketProjection": ["EVENT", "COMPETITION", "MARKET_START_TIME"]
}

try:
    response = requests.post(
        api_url,
        headers=headers,
        json=filter_params,
        timeout=15
    )
    
    if response.status_code == 200:
        markets = response.json()
        
        if isinstance(markets, list) and len(markets) > 0:
            print(f"  [OK] Found {len(markets)} race meetings")
            
            # Show first 5 meetings
            venues = set()
            for market in markets[:10]:
                event = market.get('event', {})
                venue = event.get('venue', 'Unknown')
                start_time = market.get('marketStartTime', '')[:16]
                venues.add(venue)
                print(f"    - {venue} at {start_time}")
            
            print(f"\n  Total venues: {len(venues)}")
            print("\n  [SUCCESS] Betfair is working for pulling race meetings!")
            
        else:
            print(f"  [NO DATA] API returned: {markets}")
            
    else:
        print(f"  [FAILED] HTTP {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        
except Exception as e:
    print(f"  [ERROR] {e}")
    exit(1)

print("\n" + "=" * 60)

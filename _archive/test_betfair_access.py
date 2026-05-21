"""
Test Betfair API access with certificate authentication
"""

import requests
import json
import os
from datetime import datetime, timedelta

# Load credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

USERNAME = creds['username']
PASSWORD = creds['password']
APP_KEY = creds['app_key']

# Certificate paths
CERT_PATH = 'betfair-client.crt'
KEY_PATH = 'betfair-client.key'

print("\n" + "="*80)
print("TESTING BETFAIR API ACCESS")
print("="*80 + "\n")

# Step 1: Authenticate
print("1. Testing certificate authentication...")
try:
    auth_url = "https://identitysso-cert.betfair.com/api/certlogin"
    
    response = requests.post(
        auth_url,
        cert=(CERT_PATH, KEY_PATH),
        data={
            'username': USERNAME,
            'password': PASSWORD
        },
        headers={'X-Application': APP_KEY}
    )
    
    if response.status_code == 200:
        auth_data = response.json()
        if auth_data.get('sessionToken'):
            session_token = auth_data['sessionToken']
            print(f"   ✓ Authentication SUCCESS")
            print(f"   Session token: {session_token[:20]}...")
        else:
            print(f"   ✗ Authentication FAILED: {auth_data}")
            exit(1)
    else:
        print(f"   ✗ Authentication FAILED: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
        
except Exception as e:
    print(f"   ✗ Authentication ERROR: {e}")
    exit(1)

# Step 2: Test API - Get event types
print("\n2. Testing API access - Getting event types...")
try:
    api_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listEventTypes/"
    
    headers = {
        'X-Application': APP_KEY,
        'X-Authentication': session_token,
        'content-type': 'application/json'
    }
    
    payload = {
        "filter": {}
    }
    
    response = requests.post(
        api_url,
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ API Access SUCCESS")
        print(f"   Found {len(data)} event types")
        
        # Find Horse Racing and Greyhound Racing
        for event in data:
            if event['eventType']['name'] in ['Horse Racing', 'Greyhound Racing']:
                print(f"     - {event['eventType']['name']}: {event['marketCount']} markets")
    else:
        print(f"   ✗ API Access FAILED: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
        
except Exception as e:
    print(f"   ✗ API ERROR: {e}")
    exit(1)

# Step 3: Test getting today's markets
print("\n3. Testing market data access - Today's races...")
try:
    today = datetime.utcnow()
    tomorrow = today + timedelta(days=1)
    
    api_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"
    
    payload = {
        "filter": {
            "eventTypeIds": ["7"],  # Horse Racing
            "marketTypeCodes": ["WIN"],
            "marketStartTime": {
                "from": today.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": tomorrow.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        },
        "maxResults": 5,
        "marketProjection": ["EVENT", "MARKET_START_TIME"]
    }
    
    response = requests.post(
        api_url,
        headers=headers,
        json=payload
    )
    
    if response.status_code == 200:
        markets = response.json()
        print(f"   ✓ Market Data Access SUCCESS")
        print(f"   Found {len(markets)} horse racing markets today")
        
        if markets:
            print(f"\n   Sample races:")
            for market in markets[:3]:
                event_name = market.get('event', {}).get('name', 'Unknown')
                start_time = market.get('marketStartTime', 'Unknown')
                print(f"     - {event_name} @ {start_time}")
    else:
        print(f"   ✗ Market Data Access FAILED: {response.status_code}")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"   ✗ Market Data ERROR: {e}")

print("\n" + "="*80)
print("BETFAIR API TEST COMPLETE")
print("="*80 + "\n")

#!/usr/bin/env python3
"""
Test Betfair API calls step by step
"""

import json
import requests
from datetime import datetime, timedelta

# Load credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

app_key = creds['app_key']
session_token = creds['session_token']

print("=" * 70)
print("Betfair API Diagnostic Test")
print("=" * 70)

# Test 1: Check session token validity
print("\n1. Testing session token validity...")
print(f"   App Key: {app_key[:20]}...")
print(f"   Session Token: {session_token[:20]}...")

headers = {
    'X-Application': app_key,
    'X-Authentication': session_token,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

# Simple API call - list event types
print("\n2. Testing listEventTypes (simplest API call)...")
try:
    r = requests.post(
        'https://api.betfair.com/exchange/betting/rest/v1.0/listEventTypes/',
        json={'filter': {}},
        headers=headers,
        timeout=10
    )
    print(f"   Status: {r.status_code}")
    
    if r.status_code == 200:
        result = r.json()
        print(f"   ✅ SUCCESS! Found {len(result)} event types")
        for et in result[:3]:
            print(f"      - {et['eventType']['name']}")
    else:
        print(f"   ❌ Error: {r.text[:200]}")
        
        # Parse error
        try:
            error = r.json()
            if 'faultcode' in error:
                print(f"   Error Code: {error['detail']['APINGException']['errorCode']}")
        except:
            pass
            
except Exception as e:
    print(f"   ❌ Exception: {e}")

# Test 2: List markets with corrected payload
print("\n3. Testing listMarketCatalogue (horse racing)...")

now = datetime.utcnow()
to_time = now + timedelta(hours=24)

# Simplified payload - remove potentially problematic fields
payload = {
    "filter": {
        "eventTypeIds": ["7"],  # Horse Racing
        "marketCountries": ["GB", "IE"],
        "marketTypeCodes": ["WIN"]
    },
    "maxResults": 10,
    "marketProjection": ["MARKET_START_TIME", "EVENT"]
}

print(f"   Payload: {json.dumps(payload, indent=2)}")

try:
    r = requests.post(
        'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/',
        json=payload,
        headers=headers,
        timeout=10
    )
    print(f"   Status: {r.status_code}")
    
    if r.status_code == 200:
        result = r.json()
        print(f"   ✅ SUCCESS! Found {len(result)} markets")
        for m in result[:3]:
            print(f"      - {m.get('event', {}).get('name', 'Unknown')}")
    else:
        print(f"   ❌ Error Response:")
        print(f"   {r.text[:500]}")
        
except Exception as e:
    print(f"   ❌ Exception: {e}")

print("\n" + "=" * 70)

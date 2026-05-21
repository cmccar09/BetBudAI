#!/usr/bin/env python3
"""
Try all Betfair authentication methods
"""

import json
import requests

def load_creds():
    with open('betfair-creds.json', 'r') as f:
        return json.load(f)

creds = load_creds()
username = creds['username']
password = creds['password']
app_key = creds['app_key']

print("=" * 60)
print("Testing Betfair Authentication Methods")
print("=" * 60)

# Method 1: Standard interactive login
print("\n1. Standard Interactive Login (non-cert)")
print("   URL: https://identitysso.betfair.com/api/login")
try:
    r = requests.post(
        'https://identitysso.betfair.com/api/login',
        headers={'X-Application': app_key, 'Content-Type': 'application/x-www-form-urlencoded'},
        data={'username': username, 'password': password},
        timeout=10
    )
    print(f"   Status: {r.status_code}")
    print(f"   Response: {r.text[:300]}")
except Exception as e:
    print(f"   Error: {e}")

# Method 2: Cert login with username/password
print("\n2. Cert Login with credentials")
print("   URL: https://identitysso-cert.betfair.com/api/certlogin")
try:
    r = requests.post(
        'https://identitysso-cert.betfair.com/api/certlogin',
        headers={'X-Application': app_key, 'Content-Type': 'application/x-www-form-urlencoded'},
        data={'username': username, 'password': password},
        cert=('betfair-client.crt', 'betfair-client.key'),
        timeout=10
    )
    print(f"   Status: {r.status_code}")
    result = r.json()
    print(f"   Result: {json.dumps(result, indent=2)}")
    
    if result.get('sessionToken'):
        print(f"\n   ✅ SUCCESS! Got session token")
        # Save it
        creds['session_token'] = result['sessionToken']
        with open('betfair-creds.json', 'w') as f:
            json.dump(creds, f, indent=2)
        print(f"   ✓ Saved to betfair-creds.json")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 60)

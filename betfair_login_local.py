#!/usr/bin/env python3
"""
Local Betfair Certificate Login
Gets a session token using local certificate files
"""

import json
import requests
import os

def load_credentials():
    """Load Betfair credentials from betfair-creds.json"""
    with open('betfair-creds.json', 'r') as f:
        creds = json.load(f)
    return creds

def login_with_cert():
    """Login to Betfair using certificate authentication"""
    
    creds = load_credentials()
    
    username = creds['username']
    password = creds['password']
    app_key = creds['app_key']
    
    # Check cert files exist
    cert_path = 'betfair-client.crt'
    key_path = 'betfair-client.key'
    
    if not os.path.exists(cert_path):
        print(f"ERROR: Certificate not found: {cert_path}")
        return None
    
    if not os.path.exists(key_path):
        print(f"ERROR: Private key not found: {key_path}")
        return None
    
    print(f"Logging in with certificate...")
    print(f"   Username: {username}")
    print(f"   Cert: {cert_path}")
    
    # Use cert login endpoint with credentials
    url = "https://identitysso-cert.betfair.com/api/certlogin"
    
    headers = {
        'X-Application': app_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'username': username,
        'password': password
    }
    
    print(f"   Trying certificate authentication with credentials...")
    try:
        response = requests.post(
            url,
            headers=headers,
            data=data,
            cert=(cert_path, key_path),
            timeout=30
        )
        
        print(f"   Response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Result: {json.dumps(result, indent=2)}")
            
            if result.get('loginStatus') == 'SUCCESS':
                session_token = result.get('sessionToken')
                print(f"\n[OK] Login successful!")
                print(f"   Session token: {session_token[:40]}...")
                
                # Update betfair-creds.json with new token
                creds['session_token'] = session_token
                with open('betfair-creds.json', 'w') as f:
                    json.dump(creds, f, indent=2)
                
                print(f"   [OK] Updated betfair-creds.json")
                
                return session_token
            else:
                print(f"\nERROR: Login failed: {result.get('loginStatus')}")
                print(f"   Error: {result.get('error', 'Unknown')}")
                return None
        else:
            print(f"\nERROR: HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"\nERROR: Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    token = login_with_cert()
    if token:
        print("\n✅ Ready to fetch Betfair data!")
    else:
        print("\n❌ Authentication failed")

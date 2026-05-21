#!/usr/bin/env python3
"""Refresh Betfair session token using username/password (non-cert method)"""
import json
import requests
import os

# Load credentials
script_dir = os.path.dirname(os.path.abspath(__file__))
creds_file = os.path.join(script_dir, 'betfair-creds.json')

with open(creds_file, 'r') as f:
    creds = json.load(f)

# Login to Betfair without certificate (interactive login)
login_url = "https://identitysso.betfair.com/api/login"
headers = {
    'X-Application': creds['app_key'],
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json'
}
data = {
    'username': creds['username'],
    'password': creds['password']
}

print("Refreshing Betfair session token (username/password method)...")

try:
    response = requests.post(login_url, headers=headers, data=data)
    
    if response.status_code == 200:
        result = response.json()
        # Non-cert login returns 'token' instead of 'sessionToken'
        session_token = result.get('token') or result.get('sessionToken')
        
        if session_token and result.get('status') == 'SUCCESS':
            # Update credentials file
            creds['session_token'] = session_token
            with open(creds_file, 'w') as f:
                json.dump(creds, f, indent=2)
            print(f"SUCCESS: Session token refreshed")
            print(f"   Token: {session_token[:20]}...")
            print(f"   Status: {result.get('status')}")
        else:
            print(f"ERROR: Login failed - {result.get('error', 'Unknown error')}")
            exit(1)
    else:
        print(f"ERROR: Request failed - HTTP {response.status_code}")
        print(response.text)
        exit(1)
        
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)

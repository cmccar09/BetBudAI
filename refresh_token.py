#!/usr/bin/env python3
"""Quick script to refresh Betfair session token using certificate authentication"""
import json
import requests
import os

# Load credentials
script_dir = os.path.dirname(os.path.abspath(__file__))
creds_file = os.path.join(script_dir, 'betfair-creds.json')

with open(creds_file, 'r') as f:
    creds = json.load(f)

# Get certificate paths
cert_file = os.path.join(script_dir, creds.get('cert_file', 'betfair-client.crt'))
key_file = os.path.join(script_dir, creds.get('key_file', 'betfair-client.key'))

# Verify certificate files exist
if not os.path.exists(cert_file):
    print(f"ERROR: Certificate file not found: {cert_file}")
    print(f"   Run: .\\generate_betfair_cert.ps1")
    exit(1)

if not os.path.exists(key_file):
    print(f"ERROR: Certificate key file not found: {key_file}")
    print(f"   Run: .\\generate_betfair_cert.ps1")
    exit(1)

# Login to Betfair with certificate authentication
login_url = "https://identitysso-cert.betfair.com/api/certlogin"
headers = {
    'X-Application': creds['app_key'],
    'Content-Type': 'application/x-www-form-urlencoded'
}
data = {
    'username': creds['username'],
    'password': creds['password']
}

print("Refreshing Betfair session token...")
print(f"Using certificate: {os.path.basename(cert_file)}")

try:
    # Make request with client certificate
    response = requests.post(
        login_url, 
        headers=headers, 
        data=data,
        cert=(cert_file, key_file)  # Client certificate authentication
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('sessionToken'):
            # Update credentials file
            creds['session_token'] = result['sessionToken']
            with open(creds_file, 'w') as f:
                json.dump(creds, f, indent=2)
            print(f"✅ Session token refreshed successfully")
            print(f"   Token: {result['sessionToken'][:20]}...")
            print(f"   Expires: ~8 hours from now")
        else:
            print(f"❌ Login failed: {result.get('loginStatus', 'Unknown error')}")
            if result.get('loginStatus') == 'CERT_AUTH_REQUIRED':
                print("   Your certificate may be invalid or expired")
                print("   Regenerate with: .\\generate_betfair_cert.ps1")
            exit(1)
    else:
        print(f"❌ Request failed: HTTP {response.status_code}")
        print(response.text)
        exit(1)
        
except requests.exceptions.SSLError as e:
    print(f"❌ SSL Certificate error: {e}")
    print("   Your certificate may be invalid or expired")
    print("   Regenerate with: .\\generate_betfair_cert.ps1")
    exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

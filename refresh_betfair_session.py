#!/usr/bin/env python3
"""
Refresh Betfair session token using certificate authentication
Updates both local betfair-creds.json and AWS Secrets Manager
"""

import json
import requests
import boto3
from datetime import datetime

# Load local credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

USERNAME = creds['username']
PASSWORD = creds['password']
APP_KEY = creds['app_key']
CERT_PATH = 'betfair-client.crt'
KEY_PATH = 'betfair-client.key'

print("\n" + "="*80)
print("REFRESHING BETFAIR SESSION TOKEN")
print("="*80 + "\n")

# Authenticate with certificate
print("1. Authenticating with certificate...")
auth_url = "https://identitysso-cert.betfair.com/api/certlogin"

try:
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
            new_token = auth_data['sessionToken']
            print(f"   ✓ Got new session token: {new_token[:20]}...")
        else:
            print(f"   ✗ Login failed: {auth_data}")
            exit(1)
    else:
        print(f"   ✗ Authentication failed: {response.status_code}")
        print(f"   Response: {response.text}")
        exit(1)
        
except Exception as e:
    print(f"   ✗ Error: {e}")
    exit(1)

# Update local file
print("\n2. Updating local betfair-creds.json...")
creds['session_token'] = new_token
creds['last_refresh'] = datetime.utcnow().isoformat()

with open('betfair-creds.json', 'w') as f:
    json.dump(creds, f, indent=2)

print("   ✓ Local credentials updated")

# Update AWS Secrets Manager
print("\n3. Updating AWS Secrets Manager (eu-west-1)...")
try:
    secrets_client = boto3.client('secretsmanager', region_name='eu-west-1')
    
    secrets_client.update_secret(
        SecretId='betfair-credentials',
        SecretString=json.dumps(creds)
    )
    
    print("   ✓ AWS Secrets Manager updated")
    
except Exception as e:
    print(f"   ✗ AWS update failed: {e}")
    print("   (Local file still updated)")

print("\n" + "="*80)
print("SESSION TOKEN REFRESH COMPLETE")
print("="*80 + "\n")

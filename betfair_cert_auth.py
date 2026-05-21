#!/usr/bin/env python3
"""
Betfair Certificate-Based Authentication for Lambda
Fixes the 403 error by using SSL certificates instead of username/password
"""

import os
import requests
import json
import boto3
from datetime import datetime, timedelta

def get_betfair_cert_from_secrets():
    """Retrieve Betfair certificate from AWS Secrets Manager"""
    
    secret_name = "betfair-ssl-certificate"
    region_name = "us-east-1"
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        
        secret = json.loads(get_secret_value_response['SecretString'])
        
        # Write cert and key to /tmp (Lambda's writable directory)
        cert_path = '/tmp/betfair-client.crt'
        key_path = '/tmp/betfair-client.key'
        
        with open(cert_path, 'w') as f:
            f.write(secret['certificate'])
        
        with open(key_path, 'w') as f:
            f.write(secret['private_key'])
        
        return cert_path, key_path
        
    except Exception as e:
        print(f"Error retrieving certificates from Secrets Manager: {e}")
        return None, None

def authenticate_with_certificate(username, password, app_key):
    """
    Authenticate with Betfair using SSL certificate
    Falls back to interactive login if certificate not available
    Returns session token if successful
    """
    
    # Try interactive login first (more reliable)
    print("Attempting interactive login (username/password)...")
    session_token = authenticate_without_certificate(username, password, app_key)
    if session_token:
        return session_token
    
    # Fallback to certificate if interactive fails
    print("Interactive login failed, trying certificate authentication...")
    
    # Get certificates from Secrets Manager
    cert_path, key_path = get_betfair_cert_from_secrets()
    
    if not cert_path or not key_path:
        print("WARNING: SSL certificates not found in Secrets Manager")
        return None
    
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
        response = requests.post(
            url,
            headers=headers,
            data=data,
            cert=(cert_path, key_path),
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('loginStatus') == 'SUCCESS':
                session_token = result.get('sessionToken')
                print(f"✓ Certificate authentication successful")
                print(f"  Session token: {session_token[:20]}...")
                return session_token
            else:
                print(f"❌ Login failed: {result.get('loginStatus')}")
                return None
        else:
            print(f"❌ Certificate auth failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during certificate authentication: {e}")
        return None

def authenticate_without_certificate(username, password, app_key):
    """
    Interactive authentication using username/password
    Works reliably without needing certificate upload
    """
    
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
        response = requests.post(url, headers=headers, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # Handle both response formats (token or sessionToken)
            session_token = result.get('sessionToken') or result.get('token')
            if session_token and (result.get('status') == 'SUCCESS' or result.get('loginStatus') == 'SUCCESS'):
                print(f"✓ Interactive authentication successful")
                print(f"  Session token: {session_token[:20]}...")
                return session_token
        
        print(f"Interactive auth failed: {response.status_code} - {response.text}")
        return None
        
    except Exception as e:
        print(f"Standard auth error: {e}")
        return None

def keep_alive_session(session_token, app_key):
    """
    Keep session alive (sessions expire after ~8 hours)
    Call this periodically in long-running processes
    """
    
    url = "https://identitysso.betfair.com/api/keepAlive"
    
    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token
    }
    
    try:
        response = requests.post(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'SUCCESS':
                print("✓ Session keep-alive successful")
                return True
        
        print(f"Keep-alive failed: {response.status_code}")
        return False
        
    except Exception as e:
        print(f"Keep-alive error: {e}")
        return False

def test_authentication():
    """Test Betfair authentication locally"""
    
    username = os.environ.get('BETFAIR_USERNAME', 'cmccar02')
    password = os.environ.get('BETFAIR_PASSWORD', 'Liv!23456')
    app_key = os.environ.get('BETFAIR_APP_KEY', 'XDDM8EHzaw8tokvQ')
    
    print("Testing Betfair authentication...")
    print(f"Username: {username}")
    print(f"App Key: {app_key[:20]}...")
    
    # Try certificate auth
    token = authenticate_with_certificate(username, password, app_key)
    
    if token:
        print(f"\n✅ SUCCESS!")
        print(f"Session Token: {token[:30]}...")
        
        # Test keep-alive
        print("\nTesting keep-alive...")
        keep_alive_session(token, app_key)
        
    else:
        print("\n❌ FAILED - Authentication did not return a session token")
        print("\nTroubleshooting:")
        print("1. Check Betfair account credentials are correct")
        print("2. Verify SSL certificates are in AWS Secrets Manager")
        print("3. Ensure account has API access enabled")

if __name__ == "__main__":
    test_authentication()

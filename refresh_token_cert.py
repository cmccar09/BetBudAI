#!/usr/bin/env python3
"""
Betfair session token refresh using SSL certificate authentication
Requires client certificate and key from Betfair Developer Portal
"""
import json
import requests
import sys
import os

def load_credentials():
    """Load credentials including certificate paths"""
    with open('betfair-creds.json', 'r') as f:
        creds = json.load(f)
    
    required = ['username', 'password', 'app_key']
    missing = [field for field in required if field not in creds]
    if missing:
        print(f"❌ Missing required fields in betfair-creds.json: {missing}")
        sys.exit(1)
    
    return creds

def betfair_login_with_cert(username, password, app_key, cert_file, key_file):
    """
    Login to Betfair using SSL certificate authentication
    
    Args:
        username: Betfair username
        password: Betfair password
        app_key: Betfair application key
        cert_file: Path to client certificate (.crt)
        key_file: Path to client private key (.key)
    
    Returns:
        Session token string
    """
    login_url = "https://identitysso-cert.betfair.com/api/certlogin"
    
    headers = {
        'X-Application': app_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'username': username,
        'password': password
    }
    
    print(f"Attempting certificate login for: {username}")
    print(f"Certificate: {cert_file}")
    print(f"Key: {key_file}")
    
    # Check certificate files exist
    if not os.path.exists(cert_file):
        raise FileNotFoundError(f"Certificate file not found: {cert_file}")
    if not os.path.exists(key_file):
        raise FileNotFoundError(f"Key file not found: {key_file}")
    
    try:
        response = requests.post(
            login_url,
            headers=headers,
            data=data,
            cert=(cert_file, key_file),
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('sessionToken'):
                return result['sessionToken']
            else:
                status = result.get('loginStatus', 'Unknown')
                
                # Provide helpful error messages
                if status == 'ACCOUNT_PENDING_PASSWORD_CHANGE':
                    print("\n" + "="*60)
                    print("⚠  ACTION REQUIRED: Password Change")
                    print("="*60)
                    print("\nYour Betfair account requires a password change.")
                    print("\nSteps to fix:")
                    print("1. Go to: https://www.betfair.com/")
                    print("2. Login with your current credentials")
                    print("3. Change your password when prompted")
                    print("4. Update betfair-creds.json with new password")
                    print("5. Run this script again")
                    print()
                    raise Exception(f"Login failed: {status}")
                elif status == 'CERT_AUTH_REQUIRED':
                    print("\nCertificate not recognized by Betfair.")
                    print("This can happen if:")
                    print("  - Certificate was just uploaded (wait 5-10 minutes)")
                    print("  - Certificate wasn't uploaded correctly")
                    print("  - Using wrong Betfair account")
                    raise Exception(f"Login failed: {status}")
                else:
                    raise Exception(f"Login failed: {status}")
        else:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.SSLError as e:
        raise Exception(f"SSL certificate error: {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {e}")

def update_credentials_file(session_token):
    """Update betfair-creds.json with new session token"""
    with open('betfair-creds.json', 'r') as f:
        creds = json.load(f)
    
    creds['session_token'] = session_token
    
    with open('betfair-creds.json', 'w') as f:
        json.dump(creds, f, indent=2)
    
    print(f"✅ Updated betfair-creds.json with new token")

def main():
    print("="*60)
    print("Betfair Session Token Refresh (Certificate Auth)")
    print("="*60)
    
    try:
        # Load credentials
        creds = load_credentials()
        
        # Get certificate paths
        cert_file = creds.get('cert_file', './betfair-client.crt')
        key_file = creds.get('key_file', './betfair-client.key')
        
        # Check if certificates exist
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            print("\n❌ Certificate files not found!")
            print("\nYou need to:")
            print("1. Download SSL certificate from: https://developer.betfair.com/")
            print("2. Save as betfair-client.crt and betfair-client.key")
            print("3. Update betfair-creds.json with paths")
            print("\nSee BETFAIR_CERT_SETUP.md for detailed instructions")
            sys.exit(1)
        
        # Login with certificate
        session_token = betfair_login_with_cert(
            creds['username'],
            creds['password'],
            creds['app_key'],
            cert_file,
            key_file
        )
        
        print(f"✅ Successfully obtained session token")
        print(f"   Token: {session_token[:20]}...")
        
        # Update credentials file
        update_credentials_file(session_token)
        
        print("\n" + "="*60)
        print("✅ Session token refresh complete!")
        print("="*60)
        
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("\nSee BETFAIR_CERT_SETUP.md for setup instructions")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

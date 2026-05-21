# Betfair Session Refresh Lambda for EU region
import json
import boto3
import requests
from datetime import datetime

def get_betfair_credentials():
    """Retrieve Betfair credentials from Secrets Manager"""
    secrets_client = boto3.client('secretsmanager', region_name='eu-west-1')
    secret = secrets_client.get_secret_value(SecretId='betfair-credentials')
    secret_string = secret['SecretString']
    
    # Handle escaped quotes
    if secret_string.startswith('{\\'):
        secret_string = secret_string.replace('\\', '')
    
    return json.loads(secret_string)

def betfair_login(username, password, app_key, cert_data=None, key_data=None):
    """
    Login to Betfair and get new session token
    Supports both certificate auth (preferred) and fallback to basic auth
    
    Args:
        username: Betfair username
        password: Betfair password
        app_key: Application key
        cert_data: Certificate file content (optional)
        key_data: Private key file content (optional)
    """
    login_url = "https://identitysso-cert.betfair.com/api/certlogin"
    
    headers = {
        "X-Application": app_key,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    payload = {
        "username": username,
        "password": password
    }
    
    print(f"Attempting Betfair login for user: {username}")
    
    # If certificate data provided, use certificate auth
    if cert_data and key_data:
        import tempfile
        import os
        
        # Write cert and key to temp files
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.crt') as cert_file:
            cert_file.write(cert_data)
            cert_path = cert_file.name
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.key') as key_file:
            key_file.write(key_data)
            key_path = key_file.name
        
        try:
            print("Using SSL certificate authentication")
            response = requests.post(
                login_url,
                headers=headers,
                data=payload,
                cert=(cert_path, key_path),
                timeout=10
            )
        finally:
            # Clean up temp files
            os.unlink(cert_path)
            os.unlink(key_path)
    else:
        # Fallback to basic auth (will likely fail with CERT_AUTH_REQUIRED)
        print("Warning: Using basic auth (certificates not provided)")
        response = requests.post(login_url, headers=headers, data=payload, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('sessionToken'):
            print("✅ Successfully obtained new session token")
            return result['sessionToken']
        else:
            error = result.get('loginStatus', 'Unknown error')
            raise Exception(f"Login failed: {error}")
    else:
        raise Exception(f"Login request failed: {response.status_code} - {response.text}")

def update_session_token(session_token):
    """Update session token in Secrets Manager"""
    secrets_client = boto3.client('secretsmanager', region_name='eu-west-1')
    
    # Get current secret
    current = secrets_client.get_secret_value(SecretId='betfair-credentials')
    secret_string = current['SecretString']
    
    # Handle escaped quotes
    if secret_string.startswith('{\\'):
        secret_string = secret_string.replace('\\', '')
    
    credentials = json.loads(secret_string)
    
    # Update token and timestamp
    credentials['session_token'] = session_token
    credentials['last_refresh'] = datetime.utcnow().isoformat()
    
    # Save back to Secrets Manager
    secrets_client.update_secret(
        SecretId='betfair-credentials',
        SecretString=json.dumps(credentials)
    )
    
    print(f"✅ Session token updated in Secrets Manager at {credentials['last_refresh']}")

def lambda_handler(event, context):
    """
    EventBridge scheduled function to refresh Betfair session token every 8 hours
    """
    try:
        print("=== Betfair Session Refresh Starting ===")
        
        # Get credentials from Secrets Manager
        credentials = get_betfair_credentials()
        username = credentials['username']
        password = credentials['password']
        app_key = credentials['app_key']
        
        # Get certificate data if available
        cert_data = credentials.get('cert_data')
        key_data = credentials.get('key_data')
        
        if not cert_data or not key_data:
            print("Warning: Certificate data not found in Secrets Manager")
            print("Add 'cert_data' and 'key_data' fields with certificate contents")
        
        # Login and get new token
        new_token = betfair_login(username, password, app_key, cert_data, key_data)
        
        # Update in Secrets Manager
        update_session_token(new_token)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Session token refreshed successfully',
                'timestamp': datetime.utcnow().isoformat(),
                'region': 'eu-west-1',
                'auth_method': 'certificate' if cert_data else 'basic'
            })
        }
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'region': 'eu-west-1'
            })
        }

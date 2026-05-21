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

def betfair_login(username, password, app_key):
    """Login to Betfair and get new session token"""
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
        
        # Get credentials
        credentials = get_betfair_credentials()
        username = credentials['username']
        password = credentials['password']
        app_key = credentials['app_key']
        
        # Login and get new token
        new_token = betfair_login(username, password, app_key)
        
        # Update in Secrets Manager
        update_session_token(new_token)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'message': 'Session token refreshed successfully',
                'timestamp': datetime.utcnow().isoformat(),
                'region': 'eu-west-1'
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

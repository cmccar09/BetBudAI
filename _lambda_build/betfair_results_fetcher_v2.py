#!/usr/bin/env python3
"""
Betfair Results Fetcher - Exchange API Version
Uses Betfair Exchange API to get market settlement/results
"""

import os
import json
import boto3
import requests
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
secretsmanager = boto3.client('secretsmanager', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def get_betfair_credentials():
    """Get Betfair credentials from local file, environment variables, or Secrets Manager"""
    # Try local file first (for local dev)
    local_creds_path = 'betfair-creds.json'
    if os.path.exists(local_creds_path):
        try:
            with open(local_creds_path, 'r') as f:
                creds = json.load(f)
            print(f"Using credentials from local betfair-creds.json")
            return creds['username'], creds['password'], creds['app_key']
        except Exception as e:
            print(f"Error reading local credentials: {e}")
    
    # Try environment variables (preferred for Lambda)
    username = os.environ.get('BETFAIR_USERNAME')
    password = os.environ.get('BETFAIR_PASSWORD')
    app_key = os.environ.get('BETFAIR_APP_KEY')
    
    if username and password and app_key:
        print(f"Using credentials from environment variables")
        return username, password, app_key
    
    # Fallback to Secrets Manager
    try:
        print(f"Using credentials from Secrets Manager")
        response = secretsmanager.get_secret_value(SecretId='betfair-credentials')
        creds = json.loads(response['SecretString'])
        return creds['username'], creds['password'], creds['app_key']
    except Exception as e:
        print(f"Error getting credentials: {e}")
        return None, None, None

def get_betfair_cert_from_secrets():
    """Retrieve Betfair SSL certificate from local files or Secrets Manager"""
    # Check for local cert files first (for local dev)
    local_cert = 'betfair-client.crt'
    local_key = 'betfair-client.key'
    
    if os.path.exists(local_cert) and os.path.exists(local_key):
        print(f"Using local certificate files: {local_cert} and {local_key}")
        return local_cert, local_key
    
    # Fallback to Secrets Manager
    try:
        print("Retrieving SSL certificates from Secrets Manager (eu-west-1)...")
        response = secretsmanager.get_secret_value(SecretId='betfair-ssl-certificate')
        secret = json.loads(response['SecretString'])
        
        # Write cert and key - use current directory for Windows, /tmp for Lambda
        import tempfile
        import platform
        
        if platform.system() == 'Windows':
            cert_path = os.path.join(os.getcwd(), 'betfair-client.crt')
            key_path = os.path.join(os.getcwd(), 'betfair-client.key')
        else:
            cert_path = '/tmp/betfair-client.crt'
            key_path = '/tmp/betfair-client.key'
        
        with open(cert_path, 'w') as f:
            f.write(secret['certificate'])
        
        with open(key_path, 'w') as f:
            f.write(secret['private_key'])
        
        print(f"[OK] Certificates written to {cert_path} and {key_path}")
        return cert_path, key_path
    except Exception as e:
        print(f"[ERROR] Error getting certificates: {e}")
        return None, None

def betfair_login(username, password, app_key):
    """Login to Betfair using certificate authentication"""
    
    # Get certificates
    cert_path, key_path = get_betfair_cert_from_secrets()
    if not cert_path:
        print("[ERROR] No certificates available")
        return None
    
    # Certificate login endpoint
    login_url = "https://identitysso-cert.betfair.com/api/certlogin"
    
    headers = {
        'X-Application': app_key,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'username': username,
        'password': password
    }
    
    try:
        print(f"Attempting certificate login for user {username}...")
        response = requests.post(
            login_url, 
            headers=headers, 
            data=data, 
            cert=(cert_path, key_path),
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        result = response.json()
        print(f"Response body: {result}")
        
        response.raise_for_status()
        
        if result.get('sessionToken') or result.get('token'):
            session_token = result.get('sessionToken') or result.get('token')
            print(f"[OK] Betfair certificate login successful")
            return session_token
        else:
            print(f"[ERROR] Login failed: {result}")
            return None
    except Exception as e:
        print(f"[ERROR] Login error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response text: {e.response.text}")
        return None

def get_pending_bets():
    """Get bets without results from last 2 days (horses only - greyhounds disabled)"""
    today = datetime.utcnow().strftime('%Y-%m-%d')
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    pending_bets = []
    
    for date in [today, yesterday]:
        try:
            response = table.query(
                KeyConditionExpression='bet_date = :date',
                FilterExpression='attribute_not_exists(actual_result) AND sport = :sport',
                ExpressionAttributeValues={
                    ':date': date,
                    ':sport': 'horses'
                }
            )
            pending_bets.extend(response.get('Items', []))
        except Exception as e:
            print(f"Error querying {date}: {e}")
    
    # Filter for races >1 hour ago and with market_id
    cutoff_time = datetime.utcnow() - timedelta(hours=1)
    ready_bets = []
    
    for bet in pending_bets:
        market_id = bet.get('market_id', '').strip()
        if not market_id:
            continue
            
        race_time_str = bet.get('race_time', '')
        try:
            # Try multiple date formats
            race_time = None
            for fmt in ['%m/%d/%Y %H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ']:
                try:
                    race_time = datetime.strptime(race_time_str, fmt)
                    break
                except:
                    continue
            
            if race_time and race_time < cutoff_time:
                ready_bets.append(bet)
        except Exception as e:
            print(f"Error parsing time {race_time_str}: {e}")
    
    print(f"Found {len(ready_bets)} bets ready for results (with market_id, >1hr old)")
    return ready_bets

def get_market_results(market_ids, session_token, app_key):
    """Get settled market data from Betfair Exchange API"""
    
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
    
    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    all_results = {}
    
    # Process in batches of 5 (to avoid TOO_MUCH_DATA error)
    for i in range(0, len(market_ids), 5):
        batch = market_ids[i:i+5]
        
        payload = {
            "marketIds": batch,
            "priceProjection": {
                "priceData": ["SP_TRADED", "EX_TRADED"]
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            results = response.json()
            
            for market in results:
                market_id = market.get('marketId')
                all_results[market_id] = market
            
            print(f"Fetched results for {len(batch)} markets")
        except Exception as e:
            print(f"✗ Error fetching batch: {e}")
            if hasattr(e, 'response'):
                print(f"Response: {e.response.text}")
    
    return all_results

def extract_winner_info(market_data):
    """Extract winner and race result from market data"""
    winner_name = None
    winner_selection_id = None
    placed_horses = []
    
    for runner in market_data.get('runners', []):
        status = runner.get('status', '')
        selection_id = str(runner.get('selectionId', ''))
        
        # Get runner metadata (name is in metadata, not runner)
        runner_name = runner.get('runnerName', f'Selection {selection_id}')
        
        if status == 'WINNER':
            winner_name = runner_name
            winner_selection_id = selection_id
        
        if status in ['WINNER', 'LOSER']:
            placed_horses.append({
                'name': runner_name,
                'selection_id': selection_id,
                'status': status
            })
    
    return winner_name, winner_selection_id, placed_horses

def update_bet_with_result(bet, market_data):
    """Update bet in DynamoDB with result from market data"""
    
    bet_selection_id = str(bet.get('selection_id', '')).strip()
    market_id = bet.get('market_id')
    bet_id = bet['bet_id']
    bet_date = bet['bet_date']
    
    if not bet_selection_id:
        print(f"⚠️ Bet {bet_id} has no selection_id, skipping")
        return False
    
    # Extract winner info
    winner_name, winner_selection_id, placed_horses = extract_winner_info(market_data)
    
    if not winner_name:
        print(f"⚠️ Market {market_id} has no winner yet")
        return False
    
    # Determine if this bet won
    did_win = (bet_selection_id == winner_selection_id)
    actual_result = 'WIN' if did_win else 'LOSS'
    
    # Calculate profit/loss
    stake = float(bet.get('stake', 0))
    odds = float(bet.get('odds', 0))
    
    if did_win:
        profit = stake * (odds - 1)  # Profit = stake * (decimal odds - 1)
    else:
        profit = -stake  # Lost the stake
    
    # Update DynamoDB
    try:
        # Map actual_result to outcome format expected by UI
        outcome = 'WON' if actual_result == 'WIN' else 'LOST'
        
        table.update_item(
            Key={'bet_date': bet_date, 'bet_id': bet_id},
            UpdateExpression="""
                SET actual_result = :result,
                    #status = :status,
                    #outcome = :outcome,
                    race_winner = :winner,
                    profit = :profit,
                    result_captured_at = :timestamp
            """,
            ExpressionAttributeNames={
                '#status': 'status',
                '#outcome': 'outcome'
            },
            ExpressionAttributeValues={
                ':result': actual_result,
                ':status': 'settled',
                ':outcome': outcome,
                ':winner': winner_name,
                ':profit': Decimal(str(round(profit, 2))),
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
        
        result_icon = '✅' if did_win else '❌'
        print(f"{result_icon} {bet['horse']} @ {bet['course']}: {actual_result} (Winner: {winner_name}), Profit: £{profit:.2f}")
        return True
        
    except Exception as e:
        print(f"✗ Error updating bet {bet_id}: {e}")
        return False

def lambda_handler(event, context):
    """Main Lambda handler"""
    
    print("=== Betfair Results Fetcher ===")
    
    # Get credentials
    username, password, app_key = get_betfair_credentials()
    if not username:
        return {'statusCode': 500, 'body': 'Failed to get credentials'}
    
    # Login to Betfair
    session_token = betfair_login(username, password, app_key)
    if not session_token:
        return {'statusCode': 500, 'body': 'Betfair login failed'}
    
    # Get pending bets
    pending_bets = get_pending_bets()
    if not pending_bets:
        print("No pending bets to process")
        return {'statusCode': 200, 'body': {'message': 'No pending bets', 'updated': 0}}
    
    # Get unique market IDs
    market_ids = list(set([bet.get('market_id') for bet in pending_bets if bet.get('market_id')]))
    print(f"Fetching results for {len(market_ids)} unique markets")
    
    # Fetch market results from Betfair
    market_results = get_market_results(market_ids, session_token, app_key)
    
    # Update each bet
    updated_count = 0
    for bet in pending_bets:
        market_id = bet.get('market_id')
        if market_id in market_results:
            if update_bet_with_result(bet, market_results[market_id]):
                updated_count += 1
    
    print(f"\nUpdated {updated_count}/{len(pending_bets)} bets with results")
    
    return {
        'statusCode': 200,
        'body': {
            'message': 'Results processed',
            'pending_bets': len(pending_bets),
            'updated': updated_count
        }
    }

if __name__ == "__main__":
    # For local testing
    result = lambda_handler({}, {})
    print(json.dumps(result, indent=2, default=str))

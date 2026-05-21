"""
AWS Lambda function to fetch Betfair results and update DynamoDB
Runs hourly via EventBridge
"""

import json
import boto3
import requests
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
secrets_manager = boto3.client('secretsmanager', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def get_betfair_credentials():
    """Get Betfair credentials from Secrets Manager"""
    secret = secrets_manager.get_secret_value(SecretId='BetfairCredentials')
    creds = json.loads(secret['SecretString'])
    
    # Decode base64 cert and key, write to /tmp
    import base64
    cert_path = '/tmp/betfair-client.crt'
    key_path = '/tmp/betfair-client.key'
    
    with open(cert_path, 'wb') as f:
        f.write(base64.b64decode(creds['cert_content']))
    with open(key_path, 'wb') as f:
        f.write(base64.b64decode(creds['key_content']))
    
    creds['cert_path'] = cert_path
    creds['key_path'] = key_path
    return creds

def betfair_login(credentials):
    """Login to Betfair using certificate authentication"""
    url = 'https://identitysso-cert.betfair.com/api/certlogin'
    
    # Certificate authentication
    response = requests.post(
        url,
        headers={
            'X-Application': credentials['app_key'],
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        data=f"username={credentials['username']}&password={credentials['password']}",
        cert=(credentials['cert_path'], credentials['key_path'])
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('loginStatus') == 'SUCCESS':
            return result['sessionToken']
    
    raise Exception(f"Login failed: {response.text}")

def get_pending_bets():
    """Get bets without results from last 2 days (horses only)"""
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
    
    # Filter for races >1 hour ago
    cutoff_time = datetime.utcnow() - timedelta(hours=1)
    ready_bets = []
    
    for bet in pending_bets:
        market_id = bet.get('market_id', '').strip()
        if not market_id:
            continue
        
        race_time_str = bet.get('race_time', '')
        try:
            race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00')).replace(tzinfo=None)
            if race_time < cutoff_time:
                ready_bets.append(bet)
        except:
            continue
    
    return ready_bets

def fetch_betfair_results(session_token, market_ids, credentials):
    """Fetch race results from Betfair"""
    url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
    
    headers = {
        'X-Application': credentials['app_key'],
        'X-Authentication': session_token,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'jsonrpc': '2.0',
        'method': 'SportsAPING/v1.0/listMarketBook',
        'params': {
            'marketIds': market_ids,
            'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
            'orderProjection': 'ALL',
            'matchProjection': 'ROLLED_UP_BY_PRICE'
        },
        'id': 1
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json().get('result', [])
    
    return []

def update_bet_results(bets, market_results):
    """Update DynamoDB with race results"""
    updated = 0
    
    for bet in bets:
        market_id = bet.get('market_id')
        selection_id = str(bet.get('selection_id', ''))
        
        # Find market result
        market = next((m for m in market_results if m['marketId'] == market_id), None)
        if not market:
            continue
        
        # Find winner
        winner = None
        for runner in market.get('runners', []):
            if runner.get('status') == 'WINNER':
                winner = str(runner['selectionId'])
                break
        
        if not winner:
            continue
        
        # Determine outcome
        outcome = 'win' if winner == selection_id else 'loss'
        
        # Calculate profit
        stake = float(bet.get('stake', 2.0))
        odds = float(bet.get('odds', 0))
        bet_type = bet.get('bet_type', 'WIN').upper()
        
        if outcome == 'win':
            if bet_type == 'WIN':
                profit = stake * (odds - 1)
            else:  # EW
                ew_fraction = float(bet.get('ew_fraction', 0.2))
                profit = (stake/2) * (odds - 1) + (stake/2) * ((odds-1) * ew_fraction)
        else:
            profit = -stake
        
        # Update DynamoDB
        try:
            table.update_item(
                Key={
                    'bet_date': bet['bet_date'],
                    'bet_id': bet['bet_id']
                },
                UpdateExpression='SET outcome = :outcome, profit = :profit, actual_result = :result, updated_at = :timestamp',
                ExpressionAttributeValues={
                    ':outcome': outcome,
                    ':profit': Decimal(str(round(profit, 2))),
                    ':result': winner,
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            updated += 1
            print(f"✅ {bet.get('horse')} @ {bet.get('course')}: {outcome.upper()} (Profit: £{profit:+.2f})")
        except Exception as e:
            print(f"❌ Error updating {bet.get('horse')}: {e}")
    
    return updated

def lambda_handler(event, context):
    """Main Lambda handler"""
    try:
        print("=== Betfair Results Fetcher Lambda ===")
        
        # Get credentials from Secrets Manager
        credentials = get_betfair_credentials()
        
        # Login to Betfair
        session_token = betfair_login(credentials)
        print(f"✅ Logged in to Betfair")
        
        # Get pending bets
        pending_bets = get_pending_bets()
        print(f"Found {len(pending_bets)} pending bets")
        
        if not pending_bets:
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'No pending bets to process'})
            }
        
        # Get unique market IDs
        market_ids = list(set(bet['market_id'] for bet in pending_bets if bet.get('market_id')))
        
        # Fetch results from Betfair
        market_results = fetch_betfair_results(session_token, market_ids, credentials)
        print(f"Fetched results for {len(market_results)} markets")
        
        # Update DynamoDB
        updated = update_bet_results(pending_bets, market_results)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Results processed',
                'pending_bets': len(pending_bets),
                'updated': updated
            })
        }
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

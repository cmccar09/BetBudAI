#!/usr/bin/env python3
"""
Simple Betfair results fetcher using interactive (non-cert) login
"""
import json
import requests
import boto3
from datetime import datetime, timedelta

# Load credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

username = creds['username']
password = creds['password']
app_key = creds['app_key']

# AWS DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("=" * 60)
print("SIMPLE BETFAIR RESULTS FETCHER")
print("=" * 60)

# Step 1: Login (interactive - no cert required)
print("\n[1/4] Logging in to Betfair...")
login_url = "https://identitysso.betfair.com/api/login"
login_headers = {
    'X-Application': app_key,
    'Content-Type': 'application/x-www-form-urlencoded'
}
login_data = {
    'username': username,
    'password': password
}

try:
    login_response = requests.post(login_url, headers=login_headers, data=login_data, timeout=10)
    if login_response.status_code == 200:
        login_result = login_response.json()
        session_token = login_result.get('token') or login_result.get('sessionToken')
        
        if session_token:
            print(f"  [OK] Logged in successfully")
            print(f"  Session token: {session_token[:40]}...")
        else:
            print(f"  [ERROR] No token in response: {login_result}")
            exit(1)
    else:
        print(f"  [ERROR] Login failed: HTTP {login_response.status_code}")
        print(f"  Response: {login_response.text[:200]}")
        exit(1)
except Exception as e:
    print(f"  [ERROR] Login exception: {e}")
    exit(1)

# Step 2: Get pending bets
print("\n[2/4] Loading pending bets from database...")
pending = []
for i in range(3):  # Last 3 days
    date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    try:
        response = table.query(
            KeyConditionExpression='bet_date = :date',
            ExpressionAttributeValues={':date': date}
        )
        items = response.get('Items', [])
        for item in items:
            if not item.get('actual_result') and item.get('market_id'):
                pending.append(item)
    except Exception as e:
        print(f"  [ERROR] Database error for {date}: {e}")

print(f"  Found {len(pending)} picks without results")

if not pending:
    print("\n[OK] No pending bets")
    exit(0)

# Group by market
markets = {}
for pick in pending:
    market_id = pick.get('market_id')
    if market_id:
        if market_id not in markets:
            markets[market_id] = []
        markets[market_id].append(pick)

print(f"  {len(markets)} unique markets")

# Step 3: Fetch results from Betfair
print("\n[3/4] Fetching race results from Betfair...")
api_url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
api_headers = {
    'X-Application': app_key,
    'X-Authentication': session_token,
    'Content-Type': 'application/json'
}

updated_count = 0

for i, (market_id, picks) in enumerate(markets.items(), 1):
    venue = picks[0].get('course', 'Unknown')
    race_time = picks[0].get('race_time', '')[:16] if picks[0].get('race_time') else ''
    
    print(f"\n  [{i}/{len(markets)}] {venue} - {race_time}")
    
    # Fetch market book
    payload = {
        "jsonrpc": "2.0",
        "method": "SportsAPING/v1.0/listMarketBook",
        "params": {
            "marketIds": [market_id],
            "priceProjection": {"priceData": ["EX_BEST_OFFERS"]}
        },
        "id": 1
    }
    
    try:
        api_response = requests.post(api_url, headers=api_headers, json=payload, timeout=10)
        if api_response.status_code == 200:
            api_result = api_response.json()
            
            if 'result' in api_result and len(api_result['result']) > 0:
                market_data = api_result['result'][0]
                status = market_data.get('status', '')
                
                if status != 'CLOSED':
                    print(f"    Status: {status} (not closed yet)")
                    continue
                
                # Update each pick
                for pick in picks:
                    selection_id = str(pick.get('selection_id', ''))
                    
                    for runner in market_data.get('runners', []):
                        if str(runner.get('selectionId')) == selection_id:
                            runner_status = runner.get('status')
                            
                            if runner_status == 'WINNER':
                                result = 'WON'
                            elif runner_status == 'LOSER':
                                result = 'LOST'
                            elif runner_status == 'PLACED':
                                result = 'PLACED'
                            else:
                                continue
                            
                            # Update database
                            try:
                                table.update_item(
                                    Key={
                                        'bet_date': pick['bet_date'],
                                        'bet_id': pick['bet_id']
                                    },
                                    UpdateExpression='SET actual_result = :result',
                                    ExpressionAttributeValues={':result': result}
                                )
                                
                                name = pick.get('horse', 'Unknown')
                                print(f"    [OK] {name}: {result}")
                                updated_count += 1
                                
                            except Exception as e:
                                print(f"    [ERROR] DB update failed: {e}")
                            
                            break
            else:
                print(f"    [NO DATA] API returned no data")
        else:
            print(f"    [ERROR] HTTP {api_response.status_code}")
    except Exception as e:
        print(f"    [ERROR] {str(e)[:60]}")

# Step 4: Summary
print("\n" + "=" * 60)
print(f"RESULTS: Updated {updated_count}/{len(pending)} picks")
print("=" * 60)

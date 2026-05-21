# Test Lambda for EU region - Verify Betfair API access from eu-west-1
import json
import boto3
import requests
from datetime import datetime

def lambda_handler(event, context):
    """
    Simple test to verify Betfair API works from EU Lambda
    """
    try:
        # Get Betfair credentials from Secrets Manager (eu-west-1)
        secrets_client = boto3.client('secretsmanager', region_name='eu-west-1')
        secret = secrets_client.get_secret_value(SecretId='betfair-credentials')
        secret_string = secret['SecretString']
        
        # Handle escaped quotes from PowerShell
        if secret_string.startswith('{\\'):
            secret_string = secret_string.replace('\\', '')
        
        credentials = json.loads(secret_string)
        
        app_key = credentials.get('app_key')
        session_token = credentials.get('session_token')
        
        print(f"Testing Betfair API from EU region...")
        print(f"App Key: {app_key[:10]}...")
        print(f"Session Token: {session_token[:20]}...")
        
        # Test 1: List Markets (UK/IRE Horse Racing)
        markets_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"
        
        markets_payload = {
            "filter": {
                "eventTypeIds": ["7"],  # Horse Racing
                "marketCountries": ["GB", "IE"],
                "marketTypeCodes": ["WIN"]
            },
            "maxResults": 10,
            "marketProjection": ["COMPETITION", "EVENT", "EVENT_TYPE", "MARKET_START_TIME", "RUNNER_DESCRIPTION"]
        }
        
        headers = {
            "X-Application": app_key,
            "X-Authentication": session_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        print("Calling Betfair listMarketCatalogue API...")
        markets_response = requests.post(markets_url, json=markets_payload, headers=headers, timeout=10)
        
        print(f"Response Status Code: {markets_response.status_code}")
        print(f"Response Headers: {dict(markets_response.headers)}")
        
        if markets_response.status_code == 200:
            markets = markets_response.json()
            print(f"SUCCESS! Retrieved {len(markets)} markets from Betfair")
            
            # Test 2: Get odds for first market (if available)
            if markets:
                market_id = markets[0].get('marketId')
                market_name = markets[0].get('marketName')
                event_name = markets[0].get('event', {}).get('name', 'Unknown')
                
                print(f"Testing odds fetch for: {event_name} - {market_name}")
                
                odds_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
                odds_payload = {
                    "marketIds": [market_id],
                    "priceProjection": {
                        "priceData": ["EX_BEST_OFFERS"]
                    }
                }
                
                odds_response = requests.post(odds_url, json=odds_payload, headers=headers, timeout=10)
                
                if odds_response.status_code == 200:
                    odds_data = odds_response.json()
                    print(f"Odds fetch SUCCESS! Got data for market {market_id}")
                    
                    return {
                        "statusCode": 200,
                        "body": json.dumps({
                            "success": True,
                            "message": "✅ Betfair API accessible from eu-west-1!",
                            "markets_count": len(markets),
                            "sample_market": {
                                "event": event_name,
                                "market": market_name,
                                "market_id": market_id
                            },
                            "odds_test": "SUCCESS",
                            "region": "eu-west-1",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                    }
                else:
                    print(f"Odds fetch failed: {odds_response.status_code}")
                    print(f"Response: {odds_response.text}")
            
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "success": True,
                    "message": "✅ Betfair API accessible from eu-west-1!",
                    "markets_count": len(markets),
                    "region": "eu-west-1",
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
        else:
            error_message = markets_response.text
            print(f"ERROR: {error_message}")
            
            return {
                "statusCode": markets_response.status_code,
                "body": json.dumps({
                    "success": False,
                    "message": "❌ Betfair API blocked from eu-west-1",
                    "status_code": markets_response.status_code,
                    "error": error_message,
                    "region": "eu-west-1",
                    "timestamp": datetime.utcnow().isoformat()
                })
            }
            
    except Exception as e:
        print(f"EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "message": "Error testing Betfair access",
                "error": str(e),
                "region": "eu-west-1",
                "timestamp": datetime.utcnow().isoformat()
            })
        }

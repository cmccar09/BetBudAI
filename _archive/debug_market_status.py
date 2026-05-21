"""Debug script to check market status for today's races"""
import json
import requests
from datetime import datetime

# Load Betfair credentials
with open('betfair-creds.json') as f:
    creds = json.load(f)

session_token = creds['session_token']
app_key = creds['app_key']

headers = {
    'X-Application': app_key,
    'X-Authentication': session_token,
    'Content-Type': 'application/json'
}

# Get today's picks
import boto3
db = boto3.resource('dynamodb', region_name='us-east-1')
table = db.Table('SureBetBets')

response = table.scan(
    FilterExpression='begins_with(bet_date, :d)',
    ExpressionAttributeValues={':d': '2026-01-10'}
)

picks = response.get('Items', [])
market_ids = list(set([str(p.get('market_id')) for p in picks if p.get('market_id')]))

print(f"Checking {len(market_ids)} markets...")
print("="*70)

url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"

payload = {
    "marketIds": market_ids,
    "priceProjection": {
        "priceData": ["EX_BEST_OFFERS"]
    }
}

try:
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    
    if resp.status_code == 200:
        markets = resp.json()
        
        for market in markets:
            market_id = market.get('marketId')
            status = market.get('status')
            total_matched = market.get('totalMatched', 0)
            
            # Find corresponding pick
            pick = next((p for p in picks if str(p.get('market_id')) == market_id), None)
            race_info = f"{pick['course']} {pick['race_time']}" if pick else market_id
            
            print(f"\n{race_info}")
            print(f"  Market: {market_id}")
            print(f"  Status: {status}")
            print(f"  Matched: £{total_matched:,.0f}")
            
            if status in ['CLOSED', 'SETTLED']:
                for runner in market.get('runners', []):
                    runner_status = runner.get('status')
                    selection_id = runner.get('selectionId')
                    
                    # Find horse name
                    horse_pick = next((p for p in picks if str(p.get('selection_id')) == str(selection_id)), None)
                    horse_name = horse_pick['horse'] if horse_pick else f"Selection {selection_id}"
                    
                    if runner_status in ['WINNER', 'LOSER', 'PLACED']:
                        symbol = "[WIN]" if runner_status == "WINNER" else "[PLACE]" if runner_status == "PLACED" else "[LOST]"
                        print(f"    {symbol} {horse_name}: {runner_status}")
            elif status == 'OPEN':
                print(f"  Race still open (not run yet)")
            else:
                print(f"  Runners: {len(market.get('runners', []))}")
    else:
        print(f"API Error: {resp.status_code}")
        print(resp.text)
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*70)

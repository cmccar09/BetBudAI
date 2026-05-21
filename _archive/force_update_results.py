"""Force update results for specific closed markets"""
import json
import requests
import boto3
from datetime import datetime
from decimal import Decimal

# Load Betfair credentials
with open('betfair-creds.json') as f:
    creds = json.load(f)

session_token = creds['session_token']
app_key = creds['app_key']

# DynamoDB
db = boto3.resource('dynamodb', region_name='us-east-1')
table = db.Table('SureBetBets')

# Get today's picks
response = table.scan(
    FilterExpression='begins_with(bet_date, :d)',
    ExpressionAttributeValues={':d': '2026-01-10'}
)
picks = response.get('Items', [])

# Markets we know are CLOSED with results  
closed_markets = ['1.252491959', '1.252491973', '1.252492006', '1.252495884']  # Kempton 14:40, Lingfield 11:40, Lingfield 14:20, Fairyhouse 12:00

headers = {
    'X-Application': app_key,
    'X-Authentication': session_token,
    'Content-Type': 'application/json'
}

url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"

payload = {
    "marketIds": closed_markets,
    "priceProjection": {
        "priceData": ["EX_BEST_OFFERS"]
    }
}

print("="*70)
print("FORCE UPDATING CLOSED MARKETS")
print("="*70)

resp = requests.post(url, headers=headers, json=payload, timeout=10)

if resp.status_code == 200:
    markets = resp.json()
    
    for market in markets:
        market_id = market.get('marketId')
        status = market.get('status')
        
        print(f"\nMarket {market_id}: {status}")
        print(f"  Checking {len(market.get('runners', []))} runners...")
        
        for runner in market.get('runners', []):
            selection_id = str(runner.get('selectionId'))
            runner_status = runner.get('status')
            
            # Find corresponding pick
            pick = next((p for p in picks if str(p.get('selection_id')) == selection_id and p.get('outcome') is None), None)
            
            if not pick:
                # Debug: why no match?
                picks_in_market = [p for p in picks if str(p.get('market_id')) == market_id]
                if picks_in_market:
                    print(f"    Selection {selection_id} ({runner_status}): No pending pick match")
                    print(f"      Picks in this market: {[(p['horse'], p.get('selection_id'), p.get('outcome')) for p in picks_in_market]}")
                continue
            
            if pick:
                horse = pick['horse']
                bet_id = pick['bet_id']
                odds = float(pick.get('odds', 0))
                bet_type = pick.get('bet_type', 'WIN')
                
                # Map status to outcome
                if runner_status == 'WINNER':
                    outcome = 'WON'
                elif runner_status == 'LOSER':
                    outcome = 'LOST'
                elif runner_status == 'PLACED':
                    outcome = 'PLACED'
                else:
                    continue
                
                # Calculate profit/loss
                if outcome == 'WON':
                    if bet_type == 'WIN':
                        profit_loss = odds - 1.0
                    else:  # EW
                        place_odds = 1.0 + ((odds - 1.0) / 4.0)
                        profit_loss = (odds - 1.0) + (place_odds - 1.0)
                elif outcome == 'PLACED':
                    place_odds = 1.0 + ((odds - 1.0) / 4.0)
                    profit_loss = place_odds - 1.0 - 1.0
                else:  # LOST
                    profit_loss = -2.0 if bet_type == 'EW' else -1.0
                
                # Update DynamoDB
                table.update_item(
                    Key={'bet_id': bet_id},
                    UpdateExpression='SET outcome = :outcome, profit_loss = :pl, updated_at = :ts',
                    ExpressionAttributeValues={
                        ':outcome': outcome,
                        ':pl': Decimal(str(round(profit_loss, 2))),
                        ':ts': datetime.now().isoformat()
                    }
                )
                
                symbol = "[WIN]" if outcome == "WON" else "[PLACE]" if outcome == "PLACED" else "[LOST]"
                print(f"  {symbol} {horse}: {outcome} ({profit_loss:+.2f})")

print("\n" + "="*70)
print("Update complete")
print("="*70)

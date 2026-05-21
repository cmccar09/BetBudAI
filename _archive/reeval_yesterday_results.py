"""
Re-evaluate yesterday's results with updated EW logic
"""

import boto3
import requests
import json
from datetime import datetime, timedelta

# Load credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

APP_KEY = creds['app_key']
SESSION_TOKEN = creds['session_token']

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("\n" + "="*80)
print("RE-EVALUATING YESTERDAY'S RESULTS WITH EW LOGIC")
print("="*80 + "\n")

# Get yesterday's picks
yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

response = table.scan(
    FilterExpression='#dt = :date',
    ExpressionAttributeNames={'#dt': 'date'},
    ExpressionAttributeValues={':date': yesterday}
)

picks = response.get('Items', [])

if not picks:
    print(f"No picks found for {yesterday}")
    exit(0)

print(f"Found {len(picks)} picks for {yesterday}\n")

# Group by market_id
market_ids = list(set([p.get('market_id') for p in picks if p.get('market_id')]))

print(f"Checking {len(market_ids)} markets for results...\n")

# Fetch results from Betfair
api_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"

headers = {
    'X-Application': APP_KEY,
    'X-Authentication': SESSION_TOKEN,
    'Content-Type': 'application/json'
}

payload = {
    "marketIds": market_ids,
    "priceProjection": {
        "priceData": ["EX_BEST_OFFERS"]
    }
}

try:
    response = requests.post(api_url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    markets = response.json()
    
    print(f"Retrieved {len(markets)} market results\n")
    
except Exception as e:
    print(f"ERROR fetching results: {e}")
    exit(1)

# Update picks with results
updated = 0
ew_places = 0

for pick in picks:
    market_id = pick.get('market_id')
    selection_id = str(pick.get('selection_id'))
    horse_name = pick.get('horse', 'Unknown')
    bet_type = pick.get('bet_type', 'WIN')
    race_type = pick.get('sport', 'horses')
    current_result = pick.get('actual_result', 'PENDING')
    
    # Find market
    market = next((m for m in markets if m['marketId'] == market_id), None)
    
    if not market:
        print(f"  {horse_name}: Market not found")
        continue
    
    # Find runner
    runner = next((r for r in market.get('runners', []) if str(r['selectionId']) == selection_id), None)
    
    if not runner:
        print(f"  {horse_name}: Runner not found in results")
        continue
    
    # Determine result
    runner_status = runner.get('status')
    
    # For Each Way bets on horses, check if placed in each-way positions
    if bet_type == 'EW' and race_type == 'horses':
        if runner_status == 'WINNER':
            result = 'WON'
            result_desc = "WON (1st place)"
        elif runner_status == 'PLACED':
            # PLACED means finished in each-way positions
            result = 'WON'
            result_desc = "WON (placed - EW bet)"
            if current_result == 'LOST':
                ew_places += 1
                print(f"  {horse_name}: Changed LOST -> {result_desc}")
        elif runner_status == 'LOSER':
            result = 'LOST'
            result_desc = "LOST (outside EW places)"
        elif runner_status == 'REMOVED' or runner_status == 'REMOVED_VACANT':
            result = 'NON_RUNNER'
            result_desc = "NON-RUNNER"
        else:
            print(f"  {horse_name}: Unknown status ({runner_status})")
            continue
    else:
        # For WIN bets or greyhounds, only actual winner counts
        if runner_status == 'WINNER':
            result = 'WON'
            result_desc = "WON"
        elif runner_status == 'LOSER' or runner_status == 'PLACED':
            result = 'LOST'
            result_desc = "LOST"
        elif runner_status == 'REMOVED' or runner_status == 'REMOVED_VACANT':
            result = 'NON_RUNNER'
            result_desc = "NON-RUNNER"
        else:
            print(f"  {horse_name}: Unknown status ({runner_status})")
            continue
    
    # Update in DynamoDB if changed
    if result != current_result:
        try:
            table.update_item(
                Key={
                    'bet_date': pick['bet_date'],
                    'bet_id': pick['bet_id']
                },
                UpdateExpression='SET actual_result = :result, outcome = :outcome',
                ExpressionAttributeValues={
                    ':result': result,
                    ':outcome': result
                }
            )
            updated += 1
        except Exception as e:
            print(f"    ERROR updating: {e}")

print(f"\n{'='*80}")
print(f"SUMMARY:")
print(f"  EW places found: {ew_places}")
print(f"  Total updated: {updated}")
print(f"{'='*80}\n")

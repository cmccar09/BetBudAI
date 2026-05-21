import sys
sys.path.insert(0, 'lambda-results-fetcher')
from lambda_function import authenticate_with_certificate, fetch_market_results
import os
import json

username = os.environ.get('BETFAIR_USERNAME')
password = os.environ.get('BETFAIR_PASSWORD')
app_key = os.environ.get('BETFAIR_APP_KEY')

print('Authenticating...')
session = authenticate_with_certificate(username, password, app_key)
print(f'Session: {session[:20]}...\n')

# Test markets from today's picks
market_ids = ['1.252425860', '1.252461894', '1.252429556']
print(f'Fetching market data for {len(market_ids)} markets...\n')
results = fetch_market_results(market_ids, session, app_key)

for market in results:
    print(f'Market: {market.get("marketId")}')
    print(f'  Status: {market.get("status")}')
    print(f'  InPlay: {market.get("inplay", "N/A")}')
    print(f'  Runners: {len(market.get("runners", []))}')
    
    for runner in market.get('runners', []):
        status = runner.get('status', 'UNKNOWN')
        selection_id = runner.get('selectionId')
        last_price = runner.get('lastPriceTraded', 'N/A')
        print(f'    - Selection {selection_id}: status={status}, lastPrice={last_price}')
    print()

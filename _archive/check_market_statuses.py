"""
Check actual market from today's picks to see runner statuses
"""

import requests
import json
import boto3
from datetime import datetime

# Load credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

APP_KEY = creds['app_key']
SESSION_TOKEN = creds['session_token']

# Get one of yesterday's markets from DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

from datetime import timedelta
yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

response = table.scan(
    FilterExpression='#dt = :date',
    ExpressionAttributeNames={'#dt': 'date'},
    ExpressionAttributeValues={':date': yesterday},
    Limit=1
)

pick = response['Items'][0] if response.get('Items') else None

if not pick:
    print("No picks found")
    exit(1)

market_id = pick.get('market_id')
horse_name = pick.get('horse')

print(f"\nChecking market for: {horse_name}")
print(f"Market ID: {market_id}\n")

# Get market book
book_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"

headers = {
    'X-Application': APP_KEY,
    'X-Authentication': SESSION_TOKEN,
    'Content-Type': 'application/json'
}

book_payload = {
    "marketIds": [market_id],
    "priceProjection": {
        "priceData": ["EX_BEST_OFFERS"]
    }
}

try:
    book_response = requests.post(book_url, headers=headers, json=book_payload, timeout=30)
    book_response.raise_for_status()
    book_data = book_response.json()
    
    if book_data and len(book_data) > 0:
        market_book = book_data[0]
        
        print(f"Market status: {market_book.get('status')}")
        print(f"Number of runners: {len(market_book.get('runners', []))}")
        print(f"\nRunner statuses:")
        print("-" * 80)
        
        for runner in market_book.get('runners', []):
            selection_id = runner.get('selectionId')
            status = runner.get('status')
            last_price = runner.get('lastPriceTraded', 'N/A')
            
            print(f"  Selection {selection_id}: Status={status}, Last Price={last_price}")
        
        print("\n" + "="*80)
        print("UNIQUE STATUSES IN THIS MARKET:")
        unique_statuses = set([r.get('status') for r in market_book.get('runners', [])])
        for status in sorted(unique_statuses):
            count = sum(1 for r in market_book.get('runners', []) if r.get('status') == status)
            print(f"  {status}: {count} runners")
        print("="*80 + "\n")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

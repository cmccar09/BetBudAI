"""
Fetch results for completed races today using Betfair settled bets
"""

import boto3
import requests
import json
from datetime import datetime, timezone
from decimal import Decimal

# Load Betfair credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

APP_KEY = creds['app_key']
SESSION_TOKEN = creds['session_token']

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

headers = {
    'X-Application': APP_KEY,
    'X-Authentication': SESSION_TOKEN,
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

print("\n" + "="*80)
print("FETCHING SETTLED MARKETS FROM BETFAIR FOR TODAY")
print("="*80 + "\n")

# Get all horse racing markets that settled today
list_competitions_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listCompetitions/"

body = {
    "filter": {
        "eventTypeIds": ["7"],  # Horse racing
        "marketStartTime": {
            "from": "2026-02-25T00:00:00Z",
            "to": "2026-02-25T23:59:59Z"
        }
    }
}

print("Fetching UK/IRE racing competitions...\n")

response = requests.post(list_competitions_url, headers=headers, json=body)

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    print(response.text)
    exit(1)

competitions = response.json()
print(f"Found {len(competitions)} competitions\n")

# Now get all markets from today that are settled
list_markets_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"

# Get markets for Wincanton and Bangor-on-Dee
venues = ["Wincanton", "Bangor"]

for venue in venues:
    print(f"\n{'='*70}")
    print(f"Checking {venue}")
    print(f"{'='*70}\n")
    
    market_body = {
        "filter": {
            "eventTypeIds": ["7"],
            "marketTypeCodes": ["WIN"],
            "marketStartTime": {
                "from": "2026-02-25T00:00:00Z",
                "to": "2026-02-25T23:59:59Z"
            },
            "venues": [venue]
        },
        "maxResults": 100,
        "marketProjection": ["RUNNER_DESCRIPTION", "EVENT", "MARKET_START_TIME", "COMPETITION"]
    }
    
    market_response = requests.post(list_markets_url, headers=headers, json=market_body)
    
    if market_response.status_code == 200:
        markets = market_response.json()
        print(f"Found {len(markets)} markets\n")
        
        for market in markets:
            market_name = market.get('marketName', '')
            market_id = market.get('marketId')
            market_start = market.get('marketStartTime', '')
            event_name = market.get('event', {}).get('name', '')
            
            # Extract time
            if 'T' in market_start:
                race_time = market_start.split('T')[1][:5]
            else:
                race_time = ''
            
            print(f"{race_time} - {market_name}")
            print(f"  Event: {event_name}")
            print(f"  Market ID: {market_id}")
            
            # Get runners
            runners = market.get('runners', [])
            
            # Check market status
            check_result_url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
            
            result_body = {
                "marketIds": [market_id],
                "priceProjection": {"priceData": ["SP_AVAILABLE"]}
            }
            
            result_response = requests.post(check_result_url, headers=headers, json=result_body)
            
            if result_response.status_code == 200:
                market_books = result_response.json()
                
                for book in market_books:
                    status = book.get('status')
                    print(f"  Status: {status}")
                    
                    if status == 'CLOSED':
                        print("  SETTLED - Results:")
                        
                        book_runners = book.get('runners', [])
                        
                        results_dict = {}
                        
                        for book_runner in book_runners:
                            sel_id = book_runner.get('selectionId')
                            runner_status = book_runner.get('status')
                            
                            # Match to runner name
                            runner_name = "Unknown"
                            for r in runners:
                                if r.get('selectionId') == sel_id:
                                    runner_name = r.get('runnerName')
                                    break
                            
                            if runner_status == 'WINNER':
                                print(f"    1st: {runner_name} ✓")
                                results_dict[runner_name.lower()] = ('won', '1st')
                            elif runner_status == 'PLACED':
                                print(f"    PLACED: {runner_name}")
                                results_dict[runner_name.lower()] = ('placed', 'placed')
                            elif runner_status == 'LOSER':
                                results_dict[runner_name.lower()] = ('lost', 'unplaced')
                        
                        # Check if any of our 85+ picks are in this race
                        our_horses = {
                            'count of vendome': {'time': '14:30', 'venue': 'Bangor'},
                            'laughing john': {'time': '15:20', 'venue': 'Wincanton'},
                            'mammies boy': {'time': '15:20', 'venue': 'Wincanton'},
                            'betterforeveryone': {'time': '16:00', 'venue': 'Bangor'},
                            'jiair madrik': {'time': '16:30', 'venue': 'Bangor'}
                        }
                        
                        for horse_name, horse_info in our_horses.items():
                            if horse_info['time'] == race_time and horse_info['venue'] in venue:
                                if horse_name in results_dict:
                                    outcome, position = results_dict[horse_name]
                                    
                                    print(f"\n  *** OUR PICK: {horse_name.title()} - {outcome.upper()} ***")
                                    
                                    # Update database
                                    db_response = table.query(
                                        KeyConditionExpression='bet_date = :date',
                                        ExpressionAttributeValues={':date': '2026-02-25'}
                                    )
                                    
                                    for item in db_response['Items']:
                                        item_horse = item.get('horse', '').lower()
                                        item_time = item.get('race_time', '')
                                        
                                        if horse_name in item_horse.lower() and race_time in item_time:
                                            stake = float(item.get('stake', 6))
                                            odds = float(item.get('odds', 0))
                                            
                                            if outcome == 'won':
                                                pl = stake * (odds - 1)
                                            else:
                                                pl = -stake
                                            
                                            table.update_item(
                                                Key={
                                                    'bet_date': item['bet_date'],
                                                    'bet_id': item['bet_id']
                                                },
                                                UpdateExpression='SET outcome = :outcome, finishing_position = :pos, profit_loss = :pl, updated_at = :updated',
                                                ExpressionAttributeValues={
                                                    ':outcome': outcome,
                                                    ':pos': position,
                                                    ':pl': Decimal(str(round(pl, 2))),
                                                    ':updated': datetime.now(timezone.utc).isoformat()
                                                }
                                            )
                                            
                                            print(f"  ✓ Updated in database")
                                            print(f"    Stakes: £{stake} @ {odds}")
                                            print(f"    P/L: £{pl:.2f}")
            
            print()
    else:
        print(f"Error: {market_response.status_code}")

print("\n" + "="*80)
print("COMPLETE")
print("="*80)

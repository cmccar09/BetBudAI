"""Manual results check using Betfair API for completed races"""
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

# Today's races that should have completed
completed_races = [
    {'market_id': '1.238041562', 'name': 'Kempton 12:23', 'time': '12:23'},
    {'market_id': '1.238041581', 'name': 'Fairyhouse 12:00', 'time': '12:00'},
    {'market_id': '1.238074143', 'name': 'Lingfield 13:05', 'time': '13:05'},
    {'market_id': '1.238074146', 'name': 'Lingfield 14:20', 'time': '14:20'},
    {'market_id': '1.238074149', 'name': 'Lingfield 15:25', 'time': '15:25'},
]

print("="*70)
print("CHECKING COMPLETED RACES FOR RESULTS")
print("="*70)

for race in completed_races:
    print(f"\n{race['name']} (Market: {race['market_id']})")
    
    try:
        response = requests.post(
            'https://api.betfair.com/exchange/betting/json-rpc/v1',
            headers=headers,
            json={
                "jsonrpc": "2.0",
                "method": "SportsAPING/v1.0/listMarketBook",
                "params": {
                    "marketIds": [race['market_id']],
                    "priceProjection": {
                        "priceData": ["EX_BEST_OFFERS"]
                    }
                },
                "id": 1
            },
            timeout=10
        )
        
        data = response.json()
        
        if 'result' in data and data['result']:
            market = data['result'][0]
            status = market.get('status', 'UNKNOWN')
            
            print(f"  Status: {status}")
            
            if status == 'CLOSED':
                # Find winner
                for runner in market.get('runners', []):
                    if runner.get('status') == 'WINNER':
                        selection_id = runner['selectionId']
                        print(f"  Winner: Selection ID {selection_id}")
            elif status == 'SUSPENDED':
                print(f"  Race not complete yet")
            else:
                print(f"  Status: {status}")
    
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "="*70)

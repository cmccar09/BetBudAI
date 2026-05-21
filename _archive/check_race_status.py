import requests
import json
from datetime import datetime, timedelta

# Get credentials
with open('betfair-creds.json', 'r') as f:
    creds = json.load(f)

# Login
cert_file = 'betfair-client.crt'
key_file = 'betfair-client.key'

login_response = requests.post(
    'https://identitysso-cert.betfair.com/api/certlogin',
    cert=(cert_file, key_file),
    headers={'X-Application': creds['app_key']},
    data={'username': creds['username'], 'password': creds['password']}
)

session_token = login_response.json()['sessionToken']

# API setup
api_url = 'https://api.betfair.com/exchange/betting/json-rpc/v1'
headers = {
    'X-Application': creds['app_key'],
    'X-Authentication': session_token,
    'Content-Type': 'application/json'
}

# Get TODAY'S markets (wider range)
from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
to_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)

list_markets_request = {
    'jsonrpc': '2.0',
    'method': 'SportsAPING/v1.0/listMarketCatalogue',
    'params': {
        'filter': {
            'eventTypeIds': ['7'],
            'marketStartTime': {
                'from': from_date.isoformat() + 'Z',
                'to': to_date.isoformat() + 'Z'
            },
            'marketTypeCodes': ['WIN'],
            'marketCountries': ['GB', 'IE']
        },
        'maxResults': 200,
        'marketProjection': ['EVENT', 'MARKET_START_TIME']
    },
    'id': 1
}

markets_response = requests.post(api_url, json=list_markets_request, headers=headers)
markets = markets_response.json().get('result', [])

print(f"TODAY'S UK/IRELAND RACING - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print('='*80)

# Get market status
market_ids = [m['marketId'] for m in markets]

if market_ids:
    book_request = {
        'jsonrpc': '2.0',
        'method': 'SportsAPING/v1.0/listMarketBook',
        'params': {
            'marketIds': market_ids[:50],  # First 50
            'priceProjection': {'priceData': ['SP_AVAILABLE']}
        },
        'id': 1
    }
    
    book_response = requests.post(api_url, json=book_request, headers=headers)
    market_books = book_response.json().get('result', [])
    
    # Match and display
    from datetime import timezone
    now = datetime.now(timezone.utc)
    past_races = []
    upcoming_races = []
    
    for market in markets:
        market_id = market['marketId']
        venue = market.get('event', {}).get('venue', 'Unknown')
        start_time = market.get('marketStartTime', 'Unknown')
        
        if start_time != 'Unknown':
            dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            time_str = dt.strftime('%H:%M')
            
            # Find status
            status = 'Unknown'
            for book in market_books:
                if book['marketId'] == market_id:
                    status = book.get('status', 'Unknown')
                    break
            
            race_info = {
                'venue': venue,
                'time': time_str,
                'datetime': dt,
                'status': status,
                'market_id': market_id
            }
            
            if dt < now:
                past_races.append(race_info)
            else:
                upcoming_races.append(race_info)
    
    # Display past races (should have results)
    print(f"\nPAST RACES (should have results):")
    print('-'*80)
    for race in sorted(past_races, key=lambda x: x['datetime']):
        elapsed = (now - race['datetime']).total_seconds() / 60
        print(f"{race['venue']:20} {race['time']} - Status: {race['status']:12} ({int(elapsed)} mins ago)")
    
    print(f"\nUPCOMING RACES:")
    print('-'*80)
    for race in sorted(upcoming_races, key=lambda x: x['datetime'])[:10]:
        mins_until = (race['datetime'] - now).total_seconds() / 60
        print(f"{race['venue']:20} {race['time']} - Status: {race['status']:12} (in {int(mins_until)} mins)")
    
    print(f"\n{'='*80}")
    print(f"Past races: {len(past_races)} | Upcoming: {len(upcoming_races)}")
    
    # Count by status
    status_counts = {}
    for race in past_races + upcoming_races:
        s = race['status']
        status_counts[s] = status_counts.get(s, 0) + 1
    
    print(f"\nStatus breakdown:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

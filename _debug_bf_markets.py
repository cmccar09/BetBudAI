"""Debug: see what Betfair markets we're getting and why matching fails."""
import boto3, json, urllib.parse, urllib.request
from datetime import datetime, timedelta

sm = boto3.client('secretsmanager', region_name='eu-west-1')
creds = json.loads(sm.get_secret_value(SecretId='betfair-credentials')['SecretString'])
app_key = creds['app_key']
BF_BASE = 'https://api.betfair.com/exchange/betting/rest/v1.0'

# Auth
login_data = urllib.parse.urlencode({'username': creds['username'], 'password': creds['password']}).encode()
login_req = urllib.request.Request(
    'https://identitysso.betfair.com/api/login', data=login_data,
    headers={'X-Application': app_key, 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(login_req, timeout=10) as r:
    result = json.loads(r.read())
    session_token = result.get('sessionToken') or result.get('token')

print(f'Authenticated: {session_token[:20]}...')

bf_hdrs = {
    'X-Application': app_key, 'X-Authentication': session_token,
    'Content-Type': 'application/json', 'Accept': 'application/json',
}

def bf_post(endpoint, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f'{BF_BASE}/{endpoint}/', data=data, headers=bf_hdrs, method='POST')
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())

# Fetch ALL horse racing markets (GB/IE) in next 200 days
for mtype in ['ANTE_POST_WIN', 'WIN', 'ANTEPOST_WIN', 'EACH_WAY']:
    try:
        markets = bf_post('listMarketCatalogue', {
            'filter': {
                'eventTypeIds': ['7'],
                'marketCountries': ['GB', 'IE'],
                'marketTypeCodes': [mtype],
                'marketStartTime': {
                    'from': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'to': (datetime.utcnow() + timedelta(days=200)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                },
            },
            'maxResults': 200,
            'marketProjection': ['EVENT', 'MARKET_START_TIME', 'COMPETITION', 'MARKET_DESCRIPTION'],
        })
        print(f'\n=== {mtype}: {len(markets)} markets ===')
        # Show unique venues and dates
        for m in markets[:10]:
            event = m.get('event', {})
            venue = event.get('venue', '?')
            name = m.get('marketName', '?')
            comp = m.get('competition', {}).get('name', '?')
            start = m.get('marketStartTime', '')[:10]
            desc = m.get('description', {})
            print(f'  {start} | {venue:20s} | {name:30s} | comp: {comp}')
    except Exception as e:
        print(f'{mtype}: ERROR — {e}')

# Also try without market type filter to see what's available
print('\n=== ALL market types (no filter) ===')
try:
    markets = bf_post('listMarketCatalogue', {
        'filter': {
            'eventTypeIds': ['7'],
            'marketCountries': ['GB', 'IE'],
            'marketStartTime': {
                'from': (datetime.utcnow() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'to': (datetime.utcnow() + timedelta(days=200)).strftime('%Y-%m-%dT%H:%M:%SZ'),
            },
        },
        'maxResults': 100,
        'marketProjection': ['EVENT', 'MARKET_START_TIME', 'COMPETITION', 'MARKET_DESCRIPTION'],
    })
    print(f'Found: {len(markets)} markets (5-200 days out)')
    seen_types = set()
    for m in markets:
        event = m.get('event', {})
        venue = event.get('venue', '?')
        name = m.get('marketName', '?')
        desc = m.get('description', {})
        mtype = desc.get('marketType', '?')
        seen_types.add(mtype)
        start = m.get('marketStartTime', '')[:10]
        print(f'  {start} | {venue:20s} | {name:30s} | type: {mtype}')
    print(f'\nUnique market types seen: {seen_types}')
except Exception as e:
    print(f'ERROR: {e}')

# Also check Scottish Grand National specifically (tomorrow)
print('\n=== Markets for tomorrow (Ayr) ===')
try:
    markets = bf_post('listMarketCatalogue', {
        'filter': {
            'eventTypeIds': ['7'],
            'marketStartTime': {
                'from': '2026-04-18T00:00:00Z',
                'to': '2026-04-18T23:59:59Z',
            },
        },
        'maxResults': 100,
        'marketProjection': ['EVENT', 'MARKET_START_TIME', 'RUNNER_METADATA', 'COMPETITION', 'MARKET_DESCRIPTION'],
    })
    print(f'Found: {len(markets)} markets on Apr 18')
    for m in markets:
        event = m.get('event', {})
        venue = event.get('venue', '?')
        name = m.get('marketName', '?')
        runners = m.get('runners', [])
        start = m.get('marketStartTime', '')
        desc = m.get('description', {})
        mtype = desc.get('marketType', '?')
        print(f'  {start} | {venue:20s} | {name:30s} | type: {mtype} | {len(runners)} runners')
        if 'national' in name.lower() or 'national' in venue.lower() or venue.lower() == 'ayr':
            for run in runners[:5]:
                meta = run.get('metadata', {})
                print(f'    - {run["runnerName"]} (trainer: {meta.get("TRAINER_NAME", "?")})')
except Exception as e:
    print(f'ERROR: {e}')

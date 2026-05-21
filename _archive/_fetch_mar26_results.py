"""
Look up race results for River Voyage (Chepstow 15:50 Mar 26) and L'aventara (Hereford 15:30 Mar 25)
using Betfair API, then record the outcomes in the Mar 26 DynamoDB partition.
"""
import boto3
import json
import urllib.request
import urllib.parse
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key

sm = boto3.client('secretsmanager', region_name='eu-west-1')
creds = json.loads(sm.get_secret_value(SecretId='betfair-credentials')['SecretString'])
app_key = creds['app_key']
BF_BASE = 'https://api.betfair.com/exchange/betting/rest/v1.0'

# Authenticate
login_data = urllib.parse.urlencode({'username': creds['username'], 'password': creds['password']}).encode()
req = urllib.request.Request(
    'https://identitysso.betfair.com/api/login',
    data=login_data,
    headers={'X-Application': app_key, 'Content-Type': 'application/x-www-form-urlencoded'},
    method='POST'
)
with urllib.request.urlopen(req, timeout=10) as r:
    result = json.loads(r.read())
session_token = result.get('sessionToken') or result.get('token')
print(f"Betfair login: {'OK' if session_token else 'FAILED'}")

bf_hdrs = {
    'X-Application': app_key,
    'X-Authentication': session_token,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

def bf_post(endpoint, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(f'{BF_BASE}/{endpoint}/', data=data, headers=bf_hdrs, method='POST')
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# Search for Chepstow 15:50 on Mar 26 and Hereford 15:30 on Mar 25
races_to_find = [
    {'venue': 'Chepstow', 'time_from': '2026-03-26T15:45:00Z', 'time_to': '2026-03-26T15:55:00Z', 'horse': 'River Voyage'},
    {'venue': 'Hereford', 'time_from': '2026-03-25T15:25:00Z', 'time_to': '2026-03-25T15:35:00Z', 'horse': "L'aventara"},
]

results = {}

for race in races_to_find:
    print(f"\nSearching for {race['venue']} {race['time_from'][:16]}...")
    try:
        cat = bf_post('listMarketCatalogue', {
            'filter': {
                'eventTypeIds': ['7'],
                'venues': [race['venue']],
                'marketStartTime': {'from': race['time_from'], 'to': race['time_to']},
                'marketCountries': ['GB', 'IE'],
            },
            'marketProjection': ['RUNNER_DESCRIPTION', 'RACE_DETAILS'],
            'sort': 'FIRST_TO_START',
            'maxResults': '5',
        })
        if cat:
            for mkt in cat:
                print(f"  Market: {mkt.get('marketId')} {mkt.get('marketName')} {mkt.get('description', {}).get('marketTime','')}")
                runners = {str(r.get('selectionId')): r.get('runnerName','') for r in mkt.get('runners', [])}
                for sid, name in runners.items():
                    if race['horse'].lower() in name.lower():
                        print(f"  TARGET RUNNER: {name} selectionId={sid}")
                        results[race['horse']] = {'market_id': mkt['marketId'], 'selection_id': sid}
                
                # If we found a market, get its book
                book = bf_post('listMarketBook', {
                    'marketIds': [mkt['marketId']],
                    'priceProjection': {'priceData': []},
                })
                if book:
                    b = book[0] if isinstance(book, list) else book
                    status = b.get('status')
                    print(f"  Status: {status}")
                    for r in b.get('runners', []):
                        rn = runners.get(str(r.get('selectionId')), str(r.get('selectionId')))
                        pos = r.get('sortPriority','?')
                        st = r.get('status','')
                        print(f"    pos={pos} status={st} name={rn}")
        else:
            print(f"  No markets found for {race['venue']}")
    except Exception as e:
        print(f"  Error: {e}")

# Now update DynamoDB with any found market/selection IDs and outcomes
if results:
    ddb = boto3.resource('dynamodb', region_name='eu-west-1')
    tbl = ddb.Table('SureBetBets')
    resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-03-26'))
    items = resp['Items']
    
    for item in items:
        horse = str(item.get('horse', '')).strip()
        if horse in results:
            info = results[horse]
            print(f"\nUpdating market_id/selection_id for {horse}...")
            tbl.update_item(
                Key={'bet_id': item['bet_id'], 'bet_date': item['bet_date']},
                UpdateExpression='SET market_id = :m, selection_id = :s',
                ExpressionAttributeValues={':m': info['market_id'], ':s': Decimal(str(info['selection_id']))},
            )
            print(f"  -> market_id={info['market_id']} sel_id={info['selection_id']}")

"""Test Betfair API using token from Secrets Manager - simulates Lambda flow."""
import json, boto3, requests

sm = boto3.client('secretsmanager', region_name='eu-west-1')
raw = sm.get_secret_value(SecretId='betfair-credentials')['SecretString']
creds = json.loads(raw)
print('Token from Secrets Manager (first 20):', creds.get('session_token', '')[:20])
print('App key:', creds.get('app_key', '')[:10])

headers = {
    'X-Application':   creds['app_key'],
    'X-Authentication': creds['session_token'],
    'Content-Type':    'application/json',
}

r = requests.post(
    'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/',
    headers=headers,
    json={
        'filter': {
            'eventTypeIds':    ['7'],
            'marketCountries': ['GB'],
            'marketTypeCodes': ['WIN'],
            'textQuery':       'Cheltenham',
        },
        'marketProjection': ['RUNNER_DESCRIPTION', 'EVENT'],
        'maxResults': 50,
    },
    timeout=20,
)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'Markets found: {len(data)}')
    for m in data[:3]:
        runners = m.get('runners', [])
        print(f'  {m["marketId"]} - {m["marketName"]} - {len(runners)} runners')
        for run in runners[:3]:
            print(f'    {run["selectionId"]} - {run["runnerName"]}')
else:
    print(f'Error: {r.text[:400]}')

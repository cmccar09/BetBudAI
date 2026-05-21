"""Wide brute-force search for Light Fandango's Betfair market."""
import json, requests, sys

sys.stdout.reconfigure(encoding='utf-8')

with open('betfair-creds.json') as f:
    c = json.load(f)
resp = requests.post('https://identitysso-cert.betfair.com/api/certlogin',
    data={'username': c['username'], 'password': c['password']},
    headers={'X-Application': c['app_key'], 'Content-Type': 'application/x-www-form-urlencoded'},
    cert=('betfair-client.crt','betfair-client.key'), timeout=30)
token = resp.json()['sessionToken']
app_key = c['app_key']
bf_headers = {'X-Application': app_key, 'X-Authentication': token, 'Content-Type': 'application/json'}
url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/'

TARGET_SEL = '69557379'  # Light Fandango

# Try ranges further below the known 15:55 market (1.255511254)
# The 15:22 market could be anywhere from 1.255480000 to 1.255511253
ranges = [
    (255511254, 255514635, 50),  # between known Musselburgh and Newbury markets
    (255490000, 255503837, 50),  # below known Lingfield markets
    (255514644, 255520000, 50),  # above known Newbury markets
]

for (start, end, step) in ranges:
    print(f"Searching 1.{start} to 1.{end} (step {step})...")
    for s in range(start, end, step):
        candidates = ['1.' + str(s + i) for i in range(step)]
        try:
            r = requests.post(url, headers=bf_headers,
                json={'marketIds': candidates[:50], 'priceProjection': {'priceData': ['EX_TRADED']}},
                timeout=30)
            data = r.json()
            if not isinstance(data, list):
                continue
            for m in data:
                if not isinstance(m, dict):
                    continue
                runners = m.get('runners', [])
                sel_ids = [str(run['selectionId']) for run in runners]
                if TARGET_SEL in sel_ids:
                    mid = m['marketId']
                    winner = next(
                        (str(run['selectionId']) for run in runners if run.get('status') == 'WINNER'),
                        'unknown'
                    )
                    print(f'\nFOUND! Market {mid}')
                    print(f'Winner sel_id: {winner}')
                    print(f'Light Fandango WON: {winner == TARGET_SEL}')
                    exit()
        except Exception as e:
            print(f"Error at {s}: {e}")

print("\nNot found in searched range")

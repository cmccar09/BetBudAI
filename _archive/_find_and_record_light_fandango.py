import json, requests, sys, boto3
from decimal import Decimal
from datetime import datetime

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

TARGET_SEL = '69557379'  # Light Fandango selection ID
found_mid = None
found_winner = None

# The 15:22 Musselburgh market must be in range below 1.255511254 (the 15:55 market)
# Try a wide range
print("Searching for Light Fandango's market...")
for start in range(1255510500, 1255511255, 15):
    candidates = ['1.' + str(start + i) for i in range(15)]
    try:
        r = requests.post(url, headers=bf_headers,
            json={'marketIds': candidates, 'priceProjection': {'priceData': ['EX_TRADED']}},
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
                found_mid = m['marketId']
                found_winner = next(
                    (str(run['selectionId']) for run in runners if run.get('status') == 'WINNER'),
                    None
                )
                print(f"FOUND! Market {found_mid}")
                print(f"  Winner sel_id: {found_winner}")
                print(f"  Light Fandango WON: {found_winner == TARGET_SEL}")
                break
        if found_mid:
            break
    except Exception as e:
        pass

if not found_mid:
    # Try even wider range
    print("Trying wider range 1.255509000 - 1.255510500 ...")
    for start in range(1255509000, 1255510500, 30):
        candidates = ['1.' + str(start + i) for i in range(30)]
        try:
            r = requests.post(url, headers=bf_headers,
                json={'marketIds': candidates, 'priceProjection': {'priceData': ['EX_TRADED']}},
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
                    found_mid = m['marketId']
                    found_winner = next(
                        (str(run['selectionId']) for run in runners if run.get('status') == 'WINNER'),
                        None
                    )
                    print(f"FOUND! Market {found_mid}")
                    print(f"  Winner sel_id: {found_winner}")
                    print(f"  Light Fandango WON: {found_winner == TARGET_SEL}")
                    break
            if found_mid:
                break
        except Exception as e:
            pass

if found_mid:
    # Update DynamoDB
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('SureBetBets')
    from boto3.dynamodb.conditions import Key, Attr
    
    resp2 = table.query(
        KeyConditionExpression=Key('bet_date').eq('2026-03-20'),
        FilterExpression=Attr('horse').eq('Light Fandango')
    )
    lf_picks = resp2.get('Items', [])
    print(f"\nLight Fandango picks in DB: {len(lf_picks)}")
    
    for pick in lf_picks:
        sel_id = str(pick.get('selection_id', '') or '')
        did_win = (sel_id == found_winner)
        stake = float(pick.get('stake', 0) or 0)
        odds = float(pick.get('odds', 0) or 0)
        profit = Decimal(str(round(stake * (odds - 1), 2))) if did_win and stake else (Decimal(str(-stake)) if stake else Decimal('0'))
        outcome = 'WON' if did_win else 'LOST'
        
        table.update_item(
            Key={'bet_date': pick['bet_date'], 'bet_id': pick['bet_id']},
            UpdateExpression="SET outcome = :oc, actual_result = :ar, result_won = :rw, market_id = :mid, profit = :p, #status = :st, result_captured_at = :ts",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':oc': outcome,
                ':ar': 'WIN' if did_win else 'LOSS',
                ':rw': did_win,
                ':mid': found_mid,
                ':p': profit,
                ':st': 'settled',
                ':ts': datetime.utcnow().isoformat()
            }
        )
        icon = 'WIN  >>>' if did_win else 'LOSS'
        print(f"  [{icon}] Light Fandango | market={found_mid} | P&L: {profit}")
else:
    print("\nCould not find Light Fandango's market - leaving as PENDING")

"""
Fetch and record results for today's UI picks by matching horse name
against Betfair market data.
"""
import os, sys, json, boto3, requests
from decimal import Decimal
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
secretsmanager = boto3.client('secretsmanager', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

TODAY = datetime.now().strftime('%Y-%m-%d')

# ---------- credentials ----------
def get_creds():
    if os.path.exists('betfair-creds.json'):
        with open('betfair-creds.json') as f:
            c = json.load(f)
        return c['username'], c['password'], c['app_key']
    resp = secretsmanager.get_secret_value(SecretId='betfair-credentials')
    c = json.loads(resp['SecretString'])
    return c['username'], c['password'], c['app_key']

def get_cert():
    if os.path.exists('betfair-client.crt') and os.path.exists('betfair-client.key'):
        return 'betfair-client.crt', 'betfair-client.key'
    resp = secretsmanager.get_secret_value(SecretId='betfair-ssl-certificate')
    s = json.loads(resp['SecretString'])
    with open('betfair-client.crt', 'w') as f: f.write(s['certificate'])
    with open('betfair-client.key', 'w') as f: f.write(s['private_key'])
    return 'betfair-client.crt', 'betfair-client.key'

def login(username, password, app_key):
    cert = get_cert()
    resp = requests.post(
        'https://identitysso-cert.betfair.com/api/certlogin',
        data={'username': username, 'password': password},
        headers={'X-Application': app_key, 'Content-Type': 'application/x-www-form-urlencoded'},
        cert=cert, timeout=30
    )
    data = resp.json()
    if data.get('loginStatus') == 'SUCCESS':
        print(f"[OK] Logged in as {username}")
        return data['sessionToken']
    raise Exception(f"Login failed: {data}")

def get_market_book(market_ids, session_token, app_key):
    """Fetch settled runner data for given market IDs"""
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
    }
    results = {}
    for i in range(0, len(market_ids), 5):
        batch = market_ids[i:i+5]
        payload = {
            "marketIds": batch,
            "priceProjection": {"priceData": ["EX_TRADED"]},
            "orderProjection": "ALL",
            "matchProjection": "NO_ROLLUP",
            "includeOverallPosition": False,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        for market in resp.json():
            results[market['marketId']] = market
    return results

def get_runners_for_market(market_id, session_token, app_key):
    """Get full runner names via listRunners catalogue"""
    url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/"
    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
    }
    payload = {
        "filter": {"marketIds": [market_id]},
        "marketProjection": ["RUNNER_DESCRIPTION"],
        "maxResults": 1
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    data = resp.json()
    if data and 'runners' in data[0]:
        return {str(r['selectionId']): r['runnerName'] for r in data[0]['runners']}
    return {}

# ---------- main ----------
username, password, app_key = get_creds()
session_token = login(username, password, app_key)

# Get today's UI picks
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(TODAY)
)
all_items = response.get('Items', [])
ui_picks = [i for i in all_items
            if i.get('show_in_ui') == True
            and str(i.get('outcome', '')).upper() not in ['WIN', 'WON', 'LOSS', 'LOST', 'PLACED']]

print(f"Pending UI picks: {len(ui_picks)}")

# Group by market_id
markets_needed = {}
for pick in ui_picks:
    mid = str(pick.get('market_id', '') or '').strip()
    if mid:
        markets_needed.setdefault(mid, []).append(pick)
    else:
        print(f"  [SKIP] {pick.get('horse')} - no market_id")

print(f"Markets to fetch: {list(markets_needed.keys())}")

# Fetch market books (runner list + winner)
market_books = get_market_book(list(markets_needed.keys()), session_token, app_key)

# For each market get the runner name catalogue
runner_names_cache = {}

updated = 0
for market_id, picks in markets_needed.items():
    market_data = market_books.get(market_id)
    if not market_data:
        print(f"  [NO DATA] market {market_id}")
        continue

    # Get runner names for this market (catalogue call)
    if market_id not in runner_names_cache:
        runner_names_cache[market_id] = get_runners_for_market(market_id, session_token, app_key)
    sel_id_to_name = runner_names_cache[market_id]
    name_to_sel_id = {v.upper(): k for k, v in sel_id_to_name.items()}

    # Find the winner (status WINNER)
    winner_name = None
    winner_sel_id = None
    placed_ids = []
    for runner in market_data.get('runners', []):
        sel_id = str(runner['selectionId'])
        status = runner.get('status', '')
        rname = sel_id_to_name.get(sel_id, f'Sel {sel_id}')
        if status == 'WINNER':
            winner_name = rname
            winner_sel_id = sel_id
        elif runner.get('totalMatched', 0) and runner.get('lastPriceTraded', 0):
            placed_ids.append(sel_id)

    if not winner_name:
        # Try sorting by SP/reduction
        runners_sorted = sorted(
            market_data.get('runners', []),
            key=lambda r: float(r.get('lastPriceTraded', 999) or 999)
        )
        if runners_sorted:
            winner_sel_id = str(runners_sorted[0]['selectionId'])
            winner_name = sel_id_to_name.get(winner_sel_id, f'Sel {winner_sel_id}')

    print(f"\nMarket {market_id} - Winner: {winner_name}")
    print(f"  Runner catalogue: {sel_id_to_name}")

    for pick in picks:
        horse = pick.get('horse', '').strip()
        bet_id = pick['bet_id']
        bet_date = pick['bet_date']
        stake = float(pick.get('stake', 0) or 0)
        odds = float(pick.get('odds', 0) or 0)

        # Find selection_id for this horse (fuzzy match on name)
        horse_upper = horse.upper()
        sel_id = name_to_sel_id.get(horse_upper)
        if not sel_id:
            # Try partial match
            for rname, sid in name_to_sel_id.items():
                if horse_upper in rname or rname in horse_upper:
                    sel_id = sid
                    break

        if not sel_id:
            print(f"  [NO MATCH] {horse} not found in market runners")
            continue

        did_win = (sel_id == winner_sel_id)
        is_placed = sel_id in placed_ids and not did_win

        if did_win:
            outcome = 'WON'
            profit = Decimal(str(round(stake * (odds - 1), 2)))
            label = 'WIN'
        elif is_placed:
            outcome = 'PLACED'
            profit = Decimal('0')
            label = 'PLACED'
        else:
            outcome = 'LOST'
            profit = Decimal(str(-stake)) if stake else Decimal('0')
            label = 'LOSS'

        table.update_item(
            Key={'bet_date': bet_date, 'bet_id': bet_id},
            UpdateExpression="""
                SET outcome = :oc,
                    actual_result = :ar,
                    result_won = :rw,
                    result_winner_name = :wn,
                    profit = :profit,
                    #status = :st,
                    result_captured_at = :ts
            """,
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':oc': outcome,
                ':ar': label,
                ':rw': did_win,
                ':wn': winner_name,
                ':profit': profit,
                ':st': 'settled',
                ':ts': datetime.utcnow().isoformat()
            }
        )
        icon = 'WIN  >>>' if did_win else ('PLACED' if is_placed else 'LOSS')
        print(f"  [{icon}] {horse} (sel={sel_id}) | Winner: {winner_name} | P&L: {profit}")
        updated += 1

print(f"\n=== Updated {updated} picks ===")

# Re-query and show summary
response2 = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(TODAY)
)
ui2 = [i for i in response2.get('Items', []) if i.get('show_in_ui') == True]
wins = sum(1 for p in ui2 if str(p.get('outcome','')).upper() in ['WIN','WON'])
losses = sum(1 for p in ui2 if str(p.get('outcome','')).upper() in ['LOSS','LOST'])
placed = sum(1 for p in ui2 if str(p.get('outcome','')).upper() == 'PLACED')
pending = sum(1 for p in ui2 if str(p.get('outcome','')).upper() not in ['WIN','WON','LOSS','LOST','PLACED'])
tot_profit = sum(float(p.get('profit',0) or 0) for p in ui2)

print(f"\nFINAL SUMMARY for {TODAY}")
print(f"  W:{wins}  P:{placed}  L:{losses}  Pending:{pending}")
print(f"  Total P&L: {'+'if tot_profit>=0 else ''}GBP{tot_profit:.2f}")
for p in sorted(ui2, key=lambda x: str(x.get('race_time',''))):
    oc = str(p.get('outcome','PENDING')).upper()
    mark = 'WIN  >>>  ' if oc in ['WIN','WON'] else ('PLACED   ' if oc=='PLACED' else ('LOSS     ' if oc in ['LOSS','LOST'] else 'PENDING  '))
    pr = float(p.get('profit',0) or 0)
    pl_str = ('+' if pr>=0 else '')+f'{pr:.2f}'
    print(f"  {mark} | {p.get('horse','?'):30} | {p.get('course','?'):15} | {str(p.get('race_time',''))[:16]} | P&L: {pl_str}")

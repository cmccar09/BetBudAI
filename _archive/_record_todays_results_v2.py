"""
Record today's results using market_book winner selection_ids matched
against the selection_id already stored on each pick.
"""
import sys, json, requests, boto3
from decimal import Decimal
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr

sys.stdout.reconfigure(encoding='utf-8')

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
TODAY = datetime.now().strftime('%Y-%m-%d')

# ── Betfair login ────────────────────────────────────────────────────────────
with open('betfair-creds.json') as f:
    c = json.load(f)
resp = requests.post(
    'https://identitysso-cert.betfair.com/api/certlogin',
    data={'username': c['username'], 'password': c['password']},
    headers={'X-Application': c['app_key'], 'Content-Type': 'application/x-www-form-urlencoded'},
    cert=('betfair-client.crt', 'betfair-client.key'), timeout=30
)
token = resp.json()['sessionToken']
app_key = c['app_key']
print(f"[OK] Logged in")

# ── Get pending UI picks ─────────────────────────────────────────────────────
response = table.query(KeyConditionExpression=Key('bet_date').eq(TODAY))
all_items = response.get('Items', [])
pending = [
    i for i in all_items
    if i.get('show_in_ui') == True
    and str(i.get('outcome', '')).upper() not in ['WIN', 'WON', 'LOSS', 'LOST', 'PLACED']
]
print(f"Pending UI picks: {len(pending)}")

# ── For picks missing market_id, try to find it from other picks in same race ─
# (Sanilam and Peacenik have duplicate entries — one has market_id, one doesn't)
def find_market_id(sel_id, all_items):
    """Find market_id for a selection_id from any item in the table"""
    for i in all_items:
        if str(i.get('selection_id', '')) == str(sel_id) and i.get('market_id'):
            return str(i['market_id'])
    return None

# Also scan for market IDs from all today's data
market_id_lookup = {}
for it in all_items:
    sel = str(it.get('selection_id', ''))
    mid = str(it.get('market_id', '') or '')
    if sel and mid:
        market_id_lookup[sel] = mid

# Fill missing market_ids from lookup
for pick in pending:
    if not pick.get('market_id'):
        sel = str(pick.get('selection_id', ''))
        if sel in market_id_lookup:
            pick['market_id'] = market_id_lookup[sel]
            print(f"  Resolved market_id for {pick['horse']}: {pick['market_id']}")

# Light Fandango has no market_id at all - try to find via Betfair markets for Musselburgh
light_fandango_picks = [p for p in pending if not p.get('market_id')]
if light_fandango_picks:
    print(f"\n{len(light_fandango_picks)} picks still missing market_id:")
    for p in light_fandango_picks:
        print(f"  {p['horse']} sel_id={p.get('selection_id')}")
    # Try to find via listMarketCatalogue for Musselburgh horse racing
    url2 = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/'
    headers2 = {'X-Application': app_key, 'X-Authentication': token, 'Content-Type': 'application/json'}
    payload2 = {
        "filter": {
            "eventTypeIds": ["7"],
            "venues": ["Musselburgh"],
            "marketStartTime": {"from": f"{TODAY}T14:00:00Z", "to": f"{TODAY}T17:00:00Z"}
        },
        "marketProjection": ["RUNNER_DESCRIPTION", "MARKET_START_TIME"],
        "maxResults": 20
    }
    r2 = requests.post(url2, headers=headers2, json=payload2, timeout=30)
    resp_data = r2.json()
    markets = resp_data if isinstance(resp_data, list) else []
    print(f"\n  Musselburgh markets today: {len(markets)}")
    for m in markets:
        if not isinstance(m, dict):
            continue
        mid = m.get('marketId')
        mname = m.get('marketName', '')
        mtime = m.get('marketStartTime', '')
        runners = m.get('runners', [])
        print(f"  {mid} | {mname} | {mtime}")
        for run in runners:
            sel_id = str(run.get('selectionId'))
            for pick in light_fandango_picks:
                if str(pick.get('selection_id', '')) == sel_id:
                    pick['market_id'] = mid
                    print(f"    -> FOUND {pick['horse']} sel={sel_id} in market {mid}")

# ── Fetch market books for all unique market_ids ─────────────────────────────
markets_needed = list(set(str(p.get('market_id', '')) for p in pending if p.get('market_id')))
print(f"\nFetching {len(markets_needed)} markets: {markets_needed}")

url = "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/"
headers = {'X-Application': app_key, 'X-Authentication': token, 'Content-Type': 'application/json'}
market_books = {}
for i in range(0, len(markets_needed), 5):
    batch = markets_needed[i:i+5]
    payload = {"marketIds": batch, "priceProjection": {"priceData": ["EX_TRADED"]}}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    for m in r.json():
        market_books[m['marketId']] = m

# Build winner map: market_id -> winner_selection_id
winner_map = {}
for mid, mdata in market_books.items():
    for runner in mdata.get('runners', []):
        if runner.get('status') == 'WINNER':
            winner_map[mid] = str(runner['selectionId'])
            break

print(f"\nWinner map: {winner_map}")

# ── Update each pending pick ─────────────────────────────────────────────────
updated = 0
for pick in pending:
    mid = str(pick.get('market_id', '') or '')
    sel_id = str(pick.get('selection_id', '') or '')
    horse = pick.get('horse', '?')
    bet_id = pick['bet_id']
    bet_date = pick['bet_date']
    stake = float(pick.get('stake', 0) or 0)
    odds = float(pick.get('odds', 0) or 0)

    if not mid or mid not in winner_map:
        print(f"  [SKIP] {horse} - no market_id or no winner found")
        continue

    winner_sel_id = winner_map[mid]
    did_win = (sel_id == winner_sel_id)

    if did_win:
        outcome = 'WON'
        profit = Decimal(str(round(stake * (odds - 1), 2))) if stake and odds else Decimal('0')
        label = 'WIN'
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
                profit = :profit,
                #status = :st,
                result_captured_at = :ts
        """,
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={
            ':oc': outcome,
            ':ar': label,
            ':rw': did_win,
            ':profit': profit,
            ':st': 'settled',
            ':ts': datetime.utcnow().isoformat()
        }
    )
    icon = 'WIN   >>>  ' if did_win else 'LOSS       '
    print(f"  [{icon}] {horse:30} sel={sel_id} | winner_sel={winner_sel_id} | P&L: {profit}")
    updated += 1

print(f"\n=== Updated {updated}/{len(pending)} picks ===")

# ── Final summary ────────────────────────────────────────────────────────────
resp2 = table.query(KeyConditionExpression=Key('bet_date').eq(TODAY))
ui2 = [i for i in resp2['Items'] if i.get('show_in_ui') == True]
wins    = sum(1 for p in ui2 if str(p.get('outcome','')).upper() in ['WIN','WON'])
losses  = sum(1 for p in ui2 if str(p.get('outcome','')).upper() in ['LOSS','LOST'])
placed  = sum(1 for p in ui2 if str(p.get('outcome','')).upper() == 'PLACED')
pending_c = sum(1 for p in ui2 if str(p.get('outcome','')).upper() not in ['WIN','WON','LOSS','LOST','PLACED'])
tot_profit = sum(float(p.get('profit', 0) or 0) for p in ui2)
pl_str = ('+' if tot_profit >= 0 else '') + f'GBP{tot_profit:.2f}'

print(f"\n=== TODAY {TODAY} RESULTS ===")
print(f"W:{wins}  P:{placed}  L:{losses}  Pending:{pending_c}  |  P&L: {pl_str}\n")
for p in sorted(ui2, key=lambda x: str(x.get('race_time', ''))):
    oc = str(p.get('outcome', 'PENDING')).upper()
    if oc in ['WIN', 'WON']:      mark = 'WIN  '
    elif oc == 'PLACED':           mark = 'PLACED'
    elif oc in ['LOSS', 'LOST']:   mark = 'LOSS '
    else:                          mark = 'PEND '
    pr = float(p.get('profit', 0) or 0)
    print(f"  {mark} | {p.get('horse','?'):30} | {p.get('course','?'):15} | {str(p.get('race_time',''))[:16]} | {('+' if pr>=0 else '')+str(round(pr,2))}")

"""
Lambda: surebet-results-fetch
=================================
Phase : Evening
Input : {"date": "YYYY-MM-DD"}
Output: {"success": true, "date": "...", "results_recorded": N, "winners": N}

Uses the Betfair Exchange API to find markets that settled today, then
updates any matching DynamoDB picks (by market_id + selection_id) with:
  outcome, result_won, result_winner_name, finished_position, result_emoji

Credentials: AWS Secrets Manager → 'betfair-credentials'
"""

import os
import json
import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import urllib.request
import urllib.parse

REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')


# ── Betfair helpers ───────────────────────────────────────────────────────────

def _get_bf_session():
    sm   = boto3.client('secretsmanager', region_name=REGION)
    raw  = sm.get_secret_value(SecretId='betfair-credentials')['SecretString']
    cred = json.loads(raw)
    url  = 'https://identitysso.betfair.com/api/login'
    data = urllib.parse.urlencode({
        'username': cred['username'],
        'password': cred['password'],
    }).encode()
    req  = urllib.request.Request(url, data=data, method='POST', headers={
        'X-Application'  : cred['app_key'],
        'Content-Type'   : 'application/x-www-form-urlencoded',
        'Accept'         : 'application/json',
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read().decode())
    token = result.get('sessionToken') or result.get('token')
    if not token:
        raise RuntimeError(f"Betfair login failed: {result}")
    return cred['app_key'], token


def _bf_post(endpoint, body, app_key, session_token):
    url  = f'https://api.betfair.com/exchange/betting/rest/v1.0/{endpoint}/'
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data, method='POST', headers={
        'X-Application'  : app_key,
        'X-Authentication': session_token,
        'Content-Type'   : 'application/json',
        'Accept'         : 'application/json',
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


# ── main handler ──────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    date_str = event.get('date', datetime.datetime.utcnow().strftime('%Y-%m-%d'))

    # Date window (UTC)
    date_from = f'{date_str}T00:00:00Z'
    date_to   = f'{date_str}T23:59:59Z'

    # ── 1. Authenticate ───────────────────────────────────────────────────────
    app_key, session_token = _get_bf_session()

    # ── 2. List settled GB/IE WIN markets for today ───────────────────────────
    markets = _bf_post('listMarketCatalogue', {
        'filter': {
            'eventTypeIds'   : ['7'],
            'marketTypeCodes': ['WIN'],
            'marketCountries': ['GB', 'IE'],
            'marketStartTime': {'from': date_from, 'to': date_to},
        },
        'maxResults': 200,
        'marketProjection': ['RUNNER_METADATA', 'EVENT'],
    }, app_key, session_token)

    if not markets:
        print(f"[sf_results_fetch] No markets found for {date_str}")
        return {'success': True, 'date': date_str, 'results_recorded': 0, 'winners': 0}

    market_ids = [m['marketId'] for m in markets]

    # ── 3. Fetch settled data (winner positions) ──────────────────────────────
    # listMarketBook with ORDER_STATUS filter catches EXECUTION_COMPLETE markets
    results_map = {}   # market_id → {winner_selection_id, winner_name}
    batch_size  = 10
    for i in range(0, len(market_ids), batch_size):
        batch = market_ids[i:i+batch_size]
        books = _bf_post('listMarketBook', {
            'marketIds'      : batch,
            'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
            'orderProjection': 'ALL',
        }, app_key, session_token)

        for book in books:
            mid    = book.get('marketId', '')
            status = book.get('status', '')
            if status not in ('CLOSED', 'SETTLED', 'EXECUTION_COMPLETE'):
                continue
            for runner in book.get('runners', []):
                if runner.get('status') == 'WINNER':
                    # find runner name from market catalogue
                    market_meta = next((m for m in markets if m['marketId'] == mid), {})
                    runner_meta = next(
                        (r for r in market_meta.get('runners', [])
                         if r['selectionId'] == runner['selectionId']),
                        {}
                    )
                    results_map[mid] = {
                        'winner_selection_id': runner['selectionId'],
                        'winner_name'        : runner_meta.get('runnerName', 'Unknown'),
                        'total_matched'      : float(runner.get('totalMatched', 0)),
                    }
                    break   # only need the winner

    print(f"[sf_results_fetch] Got results for {len(results_map)}/{len(market_ids)} markets")

    # ── 4. Load today's picks from DynamoDB ───────────────────────────────────
    db    = boto3.resource('dynamodb', region_name=REGION)
    table = db.Table('SureBetBets')
    resp  = table.query(KeyConditionExpression=Key('bet_date').eq(date_str))
    picks = resp.get('Items', [])

    recorded = 0
    winners  = 0

    for pick in picks:
        market_id    = str(pick.get('market_id', ''))
        selection_id = int(pick.get('selection_id', 0))

        if market_id not in results_map:
            continue   # race result not available yet

        result       = results_map[market_id]
        won          = (result['winner_selection_id'] == selection_id)
        outcome      = 'WON' if won else 'LOST'
        emoji        = '✅ WIN' if won else '❌ LOSS'

        table.update_item(
            Key={'bet_date': date_str, 'bet_id': pick['bet_id']},
            UpdateExpression=(
                'SET outcome=:o, result_won=:w, result_winner_name=:wn, '
                'result_emoji=:e, result_recorded_at=:at'
            ),
            ExpressionAttributeValues={
                ':o' : outcome,
                ':w' : won,
                ':wn': result['winner_name'],
                ':e' : emoji,
                ':at': datetime.datetime.utcnow().isoformat(),
            },
        )
        recorded += 1
        if won:
            winners += 1

    print(f"[sf_results_fetch] {recorded} picks updated ({winners} winners) for {date_str}")

    return {
        'success'         : True,
        'date'            : date_str,
        'results_recorded': recorded,
        'winners'         : winners,
    }

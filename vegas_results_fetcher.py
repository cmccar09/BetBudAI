"""
Lambda: surebet-vegas-results
==============================
Dedicated results settlement for Vegas value picks — independent of the
shared SureBet-Results-Poll pipeline that serves the main product.

Built standalone 2026-08-28 after three separate settlement bugs in a
single day (2026-08-27), all traced back to Vegas picks depending on
machinery designed around a different pick type's assumptions: a
show_in_ui gate Vegas never sets, a `course` vs `venue` field mismatch,
and an unpaginated query that silently missed Vegas records sorted
behind hundreds of other picks in the same date partition. Full
postmortems in .claude/skills/vegas.md. This fetcher only ever touches
pick_type='vegas' records and makes no assumption about how any other
pick type is shaped.

Sources, in order:
  1. Sporting Life fast-results (PRIMARY) — fast, and gives full
     finishing order so WIN / PLACED / LOSS can all be determined, not
     just win-or-not. Reuses sl_results_fetcher.py's proven scraper
     (bundled alongside this file in the Lambda zip) rather than
     reimplementing HTML/JSON parsing.
  2. Betfair settled WIN markets (FALLBACK) — only used for picks SL's
     feed hasn't caught yet. Betfair's listMarketBook reports every
     runner's WINNER/LOSER status on a settled market (not just the
     winner), so this catches losers too — the older sf_results_fetch.py
     name-fallback only ever caught winners, leaving losers PENDING
     forever; that limitation is fixed here as a side effect of building
     this properly. What Betfair genuinely can't give us is placed
     detail (2nd/3rd) — a WIN market only has WINNER/LOSER, so a
     Betfair-sourced settlement is always 'win' or 'loss', never
     'placed'. Picks that settle via SL keep the richer 3-way outcome.

Schedule: every 30 min, 12:00-20:00 BST (EventBridge cron is UTC-only,
no DST awareness — during BST that's 11:00-19:30 UTC, cron(0/30 11-19 * * ? *)).
Same fixed-UTC-window convention as the existing SureBet-ResultsPoll-30Min
rule; outside BST (GMT months) this drifts an hour early relative to UK
local midday-8pm, matching that existing rule's behavior.

Input : {"date": "YYYY-MM-DD"}  (defaults to today, UTC)
Output: {"success": true, "date": "...", "settled": N, "pending_before": N,
         "still_pending": N, "source_breakdown": {"sporting_life": N, "betfair": N}}
"""

import os
import re
import json
import datetime
import urllib.request
import urllib.parse

import boto3
from boto3.dynamodb.conditions import Key, Attr

import sl_results_fetcher as slr  # bundled alongside this file in the zip

REGION = os.environ.get('AWS_DEFAULT_REGION', 'eu-west-1')


# ── Betfair fallback (name-matched, no market_id needed) ───────────────────────

def _bf_session():
    sm = boto3.client('secretsmanager', region_name=REGION)
    cred = json.loads(sm.get_secret_value(SecretId='betfair-credentials')['SecretString'])
    url = 'https://identitysso.betfair.com/api/login'
    data = urllib.parse.urlencode({
        'username': cred['username'],
        'password': cred['password'],
    }).encode()
    req = urllib.request.Request(url, data=data, method='POST', headers={
        'X-Application':   cred['app_key'],
        'Content-Type':    'application/x-www-form-urlencoded',
        'Accept':          'application/json',
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read().decode())
    token = result.get('sessionToken') or result.get('token')
    if not token:
        raise RuntimeError(f'Betfair login failed: {result}')
    return cred['app_key'], token


def _bf_post(endpoint, body, app_key, session_token):
    url = f'https://api.betfair.com/exchange/betting/rest/v1.0/{endpoint}/'
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method='POST', headers={
        'X-Application':    app_key,
        'X-Authentication': session_token,
        'Content-Type':     'application/json',
        'Accept':           'application/json',
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def fetch_betfair_settled(date_str):
    """Return {norm(horse_name): 'win'|'loss'} for every runner in every settled
    GB/IE WIN market today. No placed detail is possible from a WIN market —
    only WINNER/LOSER — so this is strictly a fallback for whatever SL's feed
    hasn't reported yet, not a source of finishing position."""
    app_key, token = _bf_session()

    markets = _bf_post('listMarketCatalogue', {
        'filter': {
            'eventTypeIds':    ['7'],
            'marketTypeCodes': ['WIN'],
            'marketCountries': ['GB', 'IE'],
            'marketStartTime': {'from': f'{date_str}T00:00:00Z', 'to': f'{date_str}T23:59:59Z'},
        },
        'maxResults':       200,
        'marketProjection':  ['RUNNER_METADATA'],
    }, app_key, token)
    if not markets:
        return {}

    status_map = {}
    market_ids = [m['marketId'] for m in markets]
    for i in range(0, len(market_ids), 10):
        batch = market_ids[i:i + 10]
        books = _bf_post('listMarketBook', {
            'marketIds':       batch,
            'priceProjection': {'priceData': []},
        }, app_key, token)
        for book in books:
            if book.get('status') not in ('CLOSED', 'SETTLED'):
                continue
            mid  = book.get('marketId')
            meta = next((m for m in markets if m['marketId'] == mid), {})
            for runner in book.get('runners', []):
                rstatus = runner.get('status')
                if rstatus not in ('WINNER', 'LOSER'):
                    continue
                rmeta = next(
                    (r for r in meta.get('runners', []) if r['selectionId'] == runner['selectionId']), {}
                )
                rname = rmeta.get('runnerName', '')
                if rname:
                    status_map[slr.norm(rname)] = 'win' if rstatus == 'WINNER' else 'loss'
    return status_map


# ── Main handler ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    target_date = event.get('date') or datetime.datetime.utcnow().strftime('%Y-%m-%d')
    print(f'[vegas_results] Running for {target_date}')

    db    = boto3.resource('dynamodb', region_name=REGION)
    table = db.Table('SureBetBets')

    kw = {
        'KeyConditionExpression': Key('bet_date').eq(target_date),
        'FilterExpression':       Attr('pick_type').eq('vegas'),
    }
    resp  = table.query(**kw)
    picks = resp.get('Items', [])
    while resp.get('LastEvaluatedKey'):
        resp = table.query(**kw, ExclusiveStartKey=resp['LastEvaluatedKey'])
        picks.extend(resp.get('Items', []))

    pending = [p for p in picks if not p.get('outcome')]
    print(f'[vegas_results] {len(picks)} vegas picks total, {len(pending)} pending')
    if not pending:
        return {
            'success': True, 'date': target_date, 'settled': 0,
            'pending_before': 0, 'still_pending': 0,
            'source_breakdown': {'sporting_life': 0, 'betfair': 0},
        }

    # PRIMARY: Sporting Life fast-results
    try:
        race_results, _ = slr.fetch_fast_results()
    except Exception as e:
        print(f'[vegas_results] SL fast-results fetch failed: {e}')
        race_results = {}

    bf_status = None  # lazy-loaded only if any pick actually needs the fallback
    sl_settled = 0
    bf_settled = 0

    for pick in pending:
        horse      = pick.get('horse', '')
        venue      = pick.get('venue', '')
        race_time  = pick.get('race_time', '')
        m = re.search(r'(\d{4}-\d{2}-\d{2})T(\d{2}:\d{2})', race_time)
        if not m:
            print(f'[vegas_results] SKIP {horse} — unparseable race_time {race_time!r}')
            continue
        race_date, race_hhmm = m.group(1), m.group(2)
        local_hhmm = slr._to_uk_local_hhmm(race_hhmm, race_date)

        winner, all_runners, source = None, [], None
        try:
            th, tm = map(int, local_hhmm.split(':'))
            target_mins = th * 60 + tm
        except ValueError:
            target_mins = None

        if target_mins is not None:
            for mins, w, off_time, runners in race_results.get(slr.norm_course(venue), []):
                if abs(mins - target_mins) <= 15:
                    winner, all_runners, source = w, runners, 'sporting_life'
                    break

        outcome, finish_pos, winner_name = None, None, None

        if source == 'sporting_life':
            for i, r in enumerate(all_runners):
                if slr.norm(r) == slr.norm(horse):
                    finish_pos = i + 1
                    break
            if finish_pos == 1:
                outcome = 'win'
            elif finish_pos in (2, 3):
                outcome = 'placed'
            else:
                outcome = 'loss'
            winner_name = winner
        else:
            # FALLBACK: Betfair — binary win/loss only, no placed detail
            if bf_status is None:
                try:
                    bf_status = fetch_betfair_settled(target_date)
                except Exception as e:
                    print(f'[vegas_results] Betfair fallback unavailable: {e}')
                    bf_status = {}
            st = bf_status.get(slr.norm(horse))
            if st == 'win':
                outcome, finish_pos, winner_name, source = 'win', 1, horse, 'betfair'
            elif st == 'loss':
                outcome, finish_pos, winner_name, source = 'loss', None, None, 'betfair'
            else:
                continue  # not settled anywhere yet — leave pending

        icon = {'win': '✅', 'placed': '\U0001F948', 'loss': '❌'}.get(outcome, '?')
        print(f'  {icon} {outcome.upper():<7} | {horse:<28} | via {source:<13} '
              f'| finish={finish_pos or "?"} winner={winner_name or "?"}')

        update_expr = 'SET outcome = :o, result_source = :src, result_recorded_at = :at'
        vals = {
            ':o':   outcome,
            ':src': source,
            ':at':  datetime.datetime.utcnow().isoformat(),
        }
        if finish_pos is not None:
            update_expr += ', finish_position = :fp'
            vals[':fp'] = finish_pos
        if winner_name:
            update_expr += ', result_winner_name = :w'
            vals[':w'] = winner_name

        table.update_item(
            Key={'bet_date': target_date, 'bet_id': pick['bet_id']},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=vals,
        )
        if source == 'sporting_life':
            sl_settled += 1
        else:
            bf_settled += 1

    settled = sl_settled + bf_settled
    print(f'[vegas_results] Settled {settled}/{len(pending)} '
          f'(SL: {sl_settled}, Betfair: {bf_settled})')

    return {
        'success':         True,
        'date':            target_date,
        'settled':         settled,
        'pending_before':  len(pending),
        'still_pending':   len(pending) - settled,
        'source_breakdown': {'sporting_life': sl_settled, 'betfair': bf_settled},
    }

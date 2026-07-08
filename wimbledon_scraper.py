"""
wimbledon_scraper.py — Daily Wimbledon data scraper Lambda.

Runs once daily (Step Functions / EventBridge schedule) during the Wimbledon
window (late June – mid July) and writes fresh data to DynamoDB:

  1. ESPN scoreboard API (free, public, no auth) — match results + schedule
     for Men's Singles and Women's Singles, all rounds.
  2. Betfair Exchange outright WINNER market — top 5 contenders with live
     odds for Men's and Women's singles titles.

Storage: BetBudAI_Sports table
  PK 'sport' = 'wimbledon'
  SK 'data_key':
    'MATCHES'        — all match results + schedule (men's + women's)
    'OUTRIGHT_MEN'    — top contenders, men's singles winner market
    'OUTRIGHT_WOMEN'  — top contenders, women's singles winner market
    'META'            — last_updated, tournament dates, current round

Entry point: lambda_handler(event, context) — invoked by Step Functions.
"""

import json
import boto3
import requests
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
sports_table = dynamodb.Table('BetBudAI_Sports')

ESPN_BASE = 'https://site.api.espn.com/apis/site/v2/sports/tennis'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

TOURNAMENT_START = '2026-06-29'
TOURNAMENT_END   = '2026-07-12'

# Fallback top-5 outright contenders (real pre-tournament research) — used for
# tips predictions when Betfair odds aren't live, so Round 1 picks still work.
FALLBACK_OUTRIGHT_MEN = [
    {'name': 'Jannik Sinner'}, {'name': 'Novak Djokovic'}, {'name': 'Alexander Zverev'},
    {'name': 'Ben Shelton'}, {'name': 'Felix Auger-Aliassime'},
]
FALLBACK_OUTRIGHT_WOMEN = [
    {'name': 'Aryna Sabalenka'}, {'name': 'Elena Rybakina'}, {'name': 'Iga Swiatek'},
    {'name': 'Coco Gauff'}, {'name': 'Naomi Osaka'},
]


# Wimbledon champions, last 5 years — static reference data.
PREVIOUS_CHAMPIONS_MEN = [
    {'year': 2025, 'winner': 'Jannik Sinner',   'country': 'Italy'},
    {'year': 2024, 'winner': 'Carlos Alcaraz',  'country': 'Spain'},
    {'year': 2023, 'winner': 'Carlos Alcaraz',  'country': 'Spain'},
    {'year': 2022, 'winner': 'Novak Djokovic',  'country': 'Serbia'},
    {'year': 2021, 'winner': 'Novak Djokovic',  'country': 'Serbia'},
]
PREVIOUS_CHAMPIONS_WOMEN = [
    {'year': 2025, 'winner': 'Iga Świątek',       'country': 'Poland'},
    {'year': 2024, 'winner': 'Barbora Krejčíková', 'country': 'Czech Republic'},
    {'year': 2023, 'winner': 'Markéta Vondroušová','country': 'Czech Republic'},
    {'year': 2022, 'winner': 'Elena Rybakina',    'country': 'Kazakhstan'},
    {'year': 2021, 'winner': 'Ashleigh Barty',    'country': 'Australia'},
]


def _to_decimal(obj):
    """Recursively convert floats to Decimal for DynamoDB storage."""
    if isinstance(obj, float):
        return Decimal(str(round(obj, 3)))
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    return obj


# ── ESPN scoreboard scrape ──────────────────────────────────────────────────

def fetch_espn_matches():
    """Fetch the full Wimbledon scoreboard (all rounds, M+W singles) from ESPN."""
    try:
        resp = requests.get(f'{ESPN_BASE}/atp/scoreboard', headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f'[wimbledon_scraper] ESPN fetch failed: {e}')
        return []

    events = data.get('events', [])
    if not events:
        return []

    matches = []
    for grouping in events[0].get('groupings', []):
        gname = grouping.get('grouping', {}).get('displayName', '')
        if gname not in ('Men\'s Singles', 'Women\'s Singles'):
            continue
        tour = 'mens' if gname == 'Men\'s Singles' else 'womens'

        for comp in grouping.get('competitions', []):
            status = comp.get('status', {}).get('type', {})
            competitors = comp.get('competitors', [])
            if len(competitors) != 2:
                continue

            p1, p2 = competitors[0], competitors[1]
            winner = p1.get('athlete', {}).get('displayName', '') if p1.get('winner') else (
                     p2.get('athlete', {}).get('displayName', '') if p2.get('winner') else '')

            notes = comp.get('notes', [])
            result_text = notes[0]['text'] if notes else ''

            round_info = comp.get('round', {}) or {}

            matches.append({
                'match_id':   comp.get('id', ''),
                'tour':       tour,
                'date':       comp.get('date', ''),
                'court':      comp.get('venue', {}).get('court', ''),
                'round':      round_info.get('displayName', ''),
                'round_id':   int(round_info.get('id', 0) or 0),
                'status':     status.get('description', 'Scheduled'),
                'completed':  bool(status.get('completed', False)),
                'player1':    p1.get('athlete', {}).get('displayName', ''),
                'player2':    p2.get('athlete', {}).get('displayName', ''),
                'flag1':      p1.get('athlete', {}).get('flag', {}).get('alt', ''),
                'flag2':      p2.get('athlete', {}).get('flag', {}).get('alt', ''),
                'winner':     winner,
                'result_text': result_text,
                'sets1':      [s.get('value', 0) for s in p1.get('linescores', [])],
                'sets2':      [s.get('value', 0) for s in p2.get('linescores', [])],
            })

    print(f'[wimbledon_scraper] ESPN: {len(matches)} matches parsed')
    return matches


# ── Form analysis & predictions ─────────────────────────────────────────────

def _straight_sets_win(sets1, sets2, winner_is_p1):
    """True if the winner dropped zero sets."""
    if not sets1 or not sets2:
        return False
    lost = sets2 if winner_is_p1 else sets1
    won = sets1 if winner_is_p1 else sets2
    sets_lost = sum(1 for w, l in zip(won, lost) if l > w)
    return sets_lost == 0


def generate_tips(matches, outright_men=None, outright_women=None):
    """
    Build 'in-form players' and simple predictions for scheduled matches,
    using only real data already scraped this run — no fabricated confidence.
    Form signal: won last completed match in straight sets = in form.
    Falls back to outright market position (top-5 contender vs unranked
    opponent) for early-round matches where neither player has played yet
    this tournament — otherwise Round 1 would never get any predictions.
    """
    # Build form map: player -> {'last_result': 'straight_sets_win'|'win'|'loss', 'round': str}
    form = {}
    completed_sorted = sorted(
        [m for m in matches if m['completed']],
        key=lambda m: m.get('round_id', 0)
    )
    for m in completed_sorted:
        if not m['winner']:
            continue
        loser = m['player2'] if m['winner'] == m['player1'] else m['player1']
        winner_is_p1 = m['winner'] == m['player1']
        straight = _straight_sets_win(m['sets1'], m['sets2'], winner_is_p1)
        form[m['winner']] = {'result': 'straight_sets_win' if straight else 'win', 'round': m['round'], 'tour': m['tour']}
        form[loser] = {'result': 'loss', 'round': m['round'], 'tour': m['tour']}

    # In-form players: won their last match in straight sets, in the latest round played
    if completed_sorted:
        latest_round_id = max(m.get('round_id', 0) for m in completed_sorted)
    else:
        latest_round_id = 0
    in_form = []
    for m in completed_sorted:
        if m.get('round_id', 0) != latest_round_id:
            continue
        if not m['winner']:
            continue
        winner_is_p1 = m['winner'] == m['player1']
        if _straight_sets_win(m['sets1'], m['sets2'], winner_is_p1):
            in_form.append({
                'player': m['winner'],
                'tour': m['tour'],
                'round': m['round'],
                'result': m['result_text'],
            })

    # Outright top-5 contenders, by tour — used as a fallback signal for
    # matches where neither player has played yet this tournament (Round 1).
    outright_names = {
        (o.get('name') or '').strip()
        for o in (outright_men or []) + (outright_women or [])
    }

    # Predictions for next scheduled matches. Outright market position is the
    # strongest signal we have (reflects full ranking/seeding, not one match's
    # set score) so it takes priority whenever exactly one player is a top-5
    # contender — otherwise a top seed can get picked against on a technicality
    # (e.g. "won last match in straight sets" beating a genuine #1 seed who
    # won in 4). Form (straight-sets win > win > loss) is the fallback when
    # outright status doesn't separate the two players.
    _rank = {'straight_sets_win': 3, 'win': 2, 'loss': 1}
    predictions = []
    scheduled = [m for m in matches if not m['completed'] and m['player1'] and m['player2']]
    for m in scheduled[:40]:   # cap — only the next batch of matches
        f1 = form.get(m['player1'])
        f2 = form.get(m['player2'])
        p1_top5 = m['player1'] in outright_names
        p2_top5 = m['player2'] in outright_names

        if p1_top5 != p2_top5:
            favourite = m['player1'] if p1_top5 else m['player2']
            predictions.append({
                'match_id': m['match_id'], 'tour': m['tour'], 'round': m['round'],
                'player1': m['player1'], 'player2': m['player2'],
                'predicted_winner': favourite,
                'reason': f'{favourite} is a top-5 outright market contender',
            })
        elif f1 and f2:
            r1 = _rank.get(f1['result'], 0)
            r2 = _rank.get(f2['result'], 0)
            if r1 == r2:
                continue   # too close to call from form alone
            favourite = m['player1'] if r1 > r2 else m['player2']
            fav_form = f1 if r1 > r2 else f2
            reason = ('won last match in straight sets' if fav_form['result'] == 'straight_sets_win'
                       else 'won last match')
            predictions.append({
                'match_id': m['match_id'], 'tour': m['tour'], 'round': m['round'],
                'player1': m['player1'], 'player2': m['player2'],
                'predicted_winner': favourite, 'reason': f'{favourite} {reason}',
            })

    return {'in_form': in_form[:10], 'predictions': predictions[:15]}


def score_yesterday_picks(matches, predictions):
    """
    Check how yesterday's predictions performed against completed results.
    Compares prediction['predicted_winner'] to completed match['winner'].
    Returns a performance dict with win/loss counts and details.
    Only evaluates predictions for matches that have since completed.
    """
    from datetime import datetime, timezone, timedelta
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')

    completed_yesterday = {
        (m['player1'], m['player2']): m
        for m in matches
        if m.get('completed') and (m.get('date') or '')[:10] == yesterday
    }

    results = []
    for p in predictions:
        key = (p['player1'], p['player2'])
        if key not in completed_yesterday:
            continue
        m = completed_yesterday[key]
        correct = m.get('winner') == p['predicted_winner']
        results.append({
            'player1': p['player1'],
            'player2': p['player2'],
            'predicted': p['predicted_winner'],
            'actual': m.get('winner', ''),
            'correct': correct,
            'round': p.get('round', ''),
            'result_text': m.get('result_text', ''),
        })

    won = sum(1 for r in results if r['correct'])
    total = len(results)
    return {
        'date': yesterday,
        'total': total,
        'correct': won,
        'incorrect': total - won,
        'win_pct': round((won / total) * 100) if total else None,
        'picks': results,
    }


# ── Betfair outright winner market ──────────────────────────────────────────

def fetch_betfair_outright(market_label_filter):
    """
    Fetch top 5 contenders for the Wimbledon outright WINNER market.
    market_label_filter: 'Men' or 'Women' — used to disambiguate the two markets.
    """
    try:
        from betfair_odds_fetcher import get_betfair_session
        app_key, session_token = get_betfair_session()
    except Exception as e:
        print(f'[wimbledon_scraper] Betfair auth failed: {e}')
        return []

    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    # Find the outright winner market for Wimbledon
    catalogue_req = {
        'filter': {
            'eventTypeIds': ['2'],   # Tennis
            'textQuery': 'Wimbledon',
            'marketTypeCodes': ['WINNER'],
        },
        'maxResults': 20,
        'marketProjection': ['RUNNER_DESCRIPTION', 'EVENT', 'MARKET_DESCRIPTION'],
    }
    try:
        resp = requests.post(
            'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/',
            json=catalogue_req, headers=headers, timeout=20)
        resp.raise_for_status()
        markets = resp.json()
    except Exception as e:
        print(f'[wimbledon_scraper] Betfair catalogue fetch failed: {e}')
        return []

    target_market = None
    for m in markets:
        event_name = m.get('event', {}).get('name', '') or ''
        market_name = m.get('marketName', '') or ''
        haystack = f'{event_name} {market_name}'.lower()
        if market_label_filter.lower() in haystack and 'winner' in haystack:
            target_market = m
            break
    if not target_market:
        print(f'[wimbledon_scraper] No Betfair outright market found for {market_label_filter}')
        return []

    market_id = target_market['marketId']
    runner_names = {r['selectionId']: r.get('runnerName', '') for r in target_market.get('runners', [])}

    try:
        book_resp = requests.post(
            'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/',
            json={
                'marketIds': [market_id],
                'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
            }, headers=headers, timeout=20)
        book_resp.raise_for_status()
        books = book_resp.json()
    except Exception as e:
        print(f'[wimbledon_scraper] Betfair odds fetch failed: {e}')
        return []

    if not books:
        return []

    runners_odds = []
    for r in books[0].get('runners', []):
        sel_id = r.get('selectionId')
        avail = r.get('ex', {}).get('availableToBack', [])
        best_price = avail[0]['price'] if avail else None
        if best_price:
            runners_odds.append({
                'name': runner_names.get(sel_id, 'Unknown'),
                'odds': best_price,
            })

    runners_odds.sort(key=lambda x: x['odds'])
    return runners_odds[:5]


# ── Main handler ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    now_iso = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    print(f'[wimbledon_scraper] Starting daily scrape at {now_iso}')

    matches = fetch_espn_matches()
    outright_men = fetch_betfair_outright('Men')
    outright_women = fetch_betfair_outright('Women')
    tips = generate_tips(
        matches,
        outright_men or FALLBACK_OUTRIGHT_MEN,
        outright_women or FALLBACK_OUTRIGHT_WOMEN,
    ) if matches else {'in_form': [], 'predictions': []}

    # Score yesterday's predictions against actual results
    yesterday_perf = score_yesterday_picks(matches, tips['predictions']) if matches else {}

    # Determine current round from most recent completed matches
    completed = [m for m in matches if m['completed']]
    current_round = len(completed)

    try:
        if matches:
            sports_table.put_item(Item=_to_decimal({
                'sport': 'wimbledon',
                'data_key': 'MATCHES',
                'matches': matches,
                'updated_at': now_iso,
            }))
            print(f'[wimbledon_scraper] Saved {len(matches)} matches')

        sports_table.put_item(Item=_to_decimal({
            'sport': 'wimbledon',
            'data_key': 'TIPS',
            'in_form': tips['in_form'],
            'predictions': tips['predictions'],
            'yesterday_performance': yesterday_perf,
            'updated_at': now_iso,
        }))
        print(f'[wimbledon_scraper] Saved tips: {len(tips["in_form"])} in-form, {len(tips["predictions"])} predictions, yesterday={yesterday_perf.get("correct",0)}/{yesterday_perf.get("total",0)}')

        sports_table.put_item(Item=_to_decimal({
            'sport': 'wimbledon',
            'data_key': 'HISTORY',
            'previous_champions_men': PREVIOUS_CHAMPIONS_MEN,
            'previous_champions_women': PREVIOUS_CHAMPIONS_WOMEN,
            'updated_at': now_iso,
        }))

        if outright_men:
            sports_table.put_item(Item=_to_decimal({
                'sport': 'wimbledon',
                'data_key': 'OUTRIGHT_MEN',
                'contenders': outright_men,
                'updated_at': now_iso,
            }))
            print(f'[wimbledon_scraper] Saved men\'s outright: {outright_men}')

        if outright_women:
            sports_table.put_item(Item=_to_decimal({
                'sport': 'wimbledon',
                'data_key': 'OUTRIGHT_WOMEN',
                'contenders': outright_women,
                'updated_at': now_iso,
            }))
            print(f'[wimbledon_scraper] Saved women\'s outright: {outright_women}')

        sports_table.put_item(Item=_to_decimal({
            'sport': 'wimbledon',
            'data_key': 'META',
            'tournament_start': TOURNAMENT_START,
            'tournament_end': TOURNAMENT_END,
            'updated_at': now_iso,
            'is_live': TOURNAMENT_START <= today <= TOURNAMENT_END,
            'matches_completed': len(completed),
            'matches_total': len(matches),
        }))
    except Exception as e:
        print(f'[wimbledon_scraper] DynamoDB write error: {e}')
        return {'statusCode': 500, 'body': json.dumps({'success': False, 'error': str(e)})}

    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'matches_scraped': len(matches),
            'outright_men_count': len(outright_men),
            'outright_women_count': len(outright_women),
            'updated_at': now_iso,
        })
    }


if __name__ == '__main__':
    print(json.dumps(lambda_handler({}, None), indent=2))

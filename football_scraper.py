"""
football_scraper.py — Weekly English football predictions Lambda.

Covers: Premier League 2026/27, UEFA Champions League, UEFA Europa League.

Data sources:
  1. ESPN site API — PL/UCL/EL fixtures, results, standings
  2. Betfair Exchange — outright winner markets (PL, UCL, EL)
  3. Static predictions — BetBud pre-season analysis & weekly match tips

Storage: BetBudAI_Sports table
  PK 'sport' = 'football'
  SK 'data_key':
    'META'           — season status, last_updated
    'PL_PREDICTIONS' — title race, top 4, relegation, Golden Boot
    'PL_FIXTURES'    — upcoming fixtures with match predictions
    'PL_STANDINGS'   — current league table
    'UCL_DATA'       — UCL English clubs, outright contenders, fixtures
    'EL_DATA'        — EL English clubs, outright contenders, fixtures

Entry point: lambda_handler(event, context) — invoked by Step Functions.
"""

import json
import math
import requests
import boto3
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
sports_table = dynamodb.Table('BetBudAI_Sports')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
ESPN_SOCCER = 'https://site.api.espn.com/apis/site/v2/sports/soccer'

# ─── Pre-season static predictions (verified July 2026) ──────────────────────
# PL 2026/27 season starts August 2026.
# Predictions based on squad strength, transfer activity, and pre-season market.

PL_TITLE_PREDICTION = {
    'team':       'Arsenal',
    'odds':       '3/1',
    'decimal':    4.0,
    'confidence': 72,
    'reasoning':  'Defending champions — Arsenal ended Man City\'s dominance in 2025/26 and have the squad depth and momentum to back up. Mikel Arteta\'s system is now at peak maturity. First choice to retain.',
}

PL_TOP_FOUR = [
    {'pos': 1, 'team': 'Arsenal',           'odds': '3/1',  'decimal': 4.0,  'badge': '🔴', 'note': 'Defending champions — Arteta squad at peak maturity'},
    {'pos': 2, 'team': 'Manchester City',   'odds': '4/1',  'decimal': 5.0,  'badge': '🔵', 'note': 'Enzo Maresca takes over — Haaland the difference-maker, lost Rodri'},
    {'pos': 3, 'team': 'Liverpool',         'odds': '5/1',  'decimal': 6.0,  'badge': '❤️', 'note': 'Massive rebuild — Wirtz + Isak arrival is a statement of intent'},
    {'pos': 4, 'team': 'Chelsea',           'odds': '10/1', 'decimal': 11.0, 'badge': '🔵', 'note': 'Maresca left for City — new era at Stamford Bridge'},
]

PL_TOP_SIX_CONTENDERS = [
    {'team': 'Manchester United', 'odds': '12/1', 'decimal': 13.0},
    {'team': 'Tottenham Hotspur', 'odds': '14/1', 'decimal': 15.0},
    {'team': 'Newcastle United',  'odds': '16/1', 'decimal': 17.0},
    {'team': 'Aston Villa',       'odds': '20/1', 'decimal': 21.0},
]

PL_RELEGATION = [
    {'team': 'Coventry City',  'odds': '4/9',  'decimal': 1.44, 'note': 'Promoted side — first PL season, brutal fixtures early'},
    {'team': 'Hull City',      'odds': '1/2',  'decimal': 1.5,  'note': 'Promoted — squad thin at PL level'},
    {'team': 'Sunderland',     'odds': '4/7',  'decimal': 1.57, 'note': 'Back in top flight — punching at ceiling'},
    {'team': 'Ipswich Town',   'odds': '5/6',  'decimal': 1.83, 'note': 'Second season up — quality gap still apparent'},
]

PL_GOLDEN_BOOT = [
    {'player': 'Erling Haaland',   'team': 'Man City',  'goals_last_season': 27, 'odds': '3/1',  'decimal': 4.0},
    {'player': 'Alexander Isak',   'team': 'Liverpool', 'goals_last_season': 21, 'odds': '6/1',  'decimal': 7.0},
    {'player': 'Bukayo Saka',      'team': 'Arsenal',   'goals_last_season': 20, 'odds': '8/1',  'decimal': 9.0},
    {'player': 'Florian Wirtz',    'team': 'Liverpool', 'goals_last_season': 18, 'odds': '8/1',  'decimal': 9.0},
    {'player': 'Cole Palmer',      'team': 'Chelsea',   'goals_last_season': 18, 'odds': '10/1', 'decimal': 11.0},
]

UCL_ENGLISH_CLUBS = [
    {'team': 'Arsenal',          'how': 'PL Champions'},
    {'team': 'Manchester City',  'how': 'PL 2nd'},
    {'team': 'Liverpool',        'how': 'PL 3rd'},
    {'team': 'Chelsea',          'how': 'PL 4th'},
]

UCL_CONTENDERS = [
    {'pos': 1, 'team': 'Real Madrid',      'odds': '3/1',  'decimal': 4.0},
    {'pos': 2, 'team': 'Manchester City',  'odds': '9/2',  'decimal': 5.5},
    {'pos': 3, 'team': 'Bayern Munich',    'odds': '5/1',  'decimal': 6.0},
    {'pos': 4, 'team': 'PSG',             'odds': '7/1',  'decimal': 8.0},
    {'pos': 5, 'team': 'Arsenal',          'odds': '12/1', 'decimal': 13.0},
    {'pos': 6, 'team': 'Liverpool',        'odds': '14/1', 'decimal': 15.0},
]

EL_ENGLISH_CLUBS = [
    {'team': 'Manchester United', 'how': 'PL 5th / Cup winner'},
    {'team': 'Tottenham Hotspur', 'how': 'PL 6th'},
]

EL_CONTENDERS = [
    {'pos': 1, 'team': 'Bayer Leverkusen',  'odds': '5/1',  'decimal': 6.0},
    {'pos': 2, 'team': 'Atletico Madrid',   'odds': '6/1',  'decimal': 7.0},
    {'pos': 3, 'team': 'Roma',             'odds': '8/1',  'decimal': 9.0},
    {'pos': 4, 'team': 'Manchester United', 'odds': '9/1',  'decimal': 10.0},
    {'pos': 5, 'team': 'Tottenham Hotspur', 'odds': '12/1', 'decimal': 13.0},
    {'pos': 6, 'team': 'Lazio',            'odds': '14/1', 'decimal': 15.0},
]

# Team strength ratings for match prediction model
TEAM_STRENGTH = {
    # Updated 2026/27: Arsenal defending champions, Man City lost Pep+Rodri, Liverpool rebuilt with Isak+Wirtz
    'Arsenal': 93, 'Manchester City': 90, 'Liverpool': 91, 'Chelsea': 80,
    'Manchester United': 76, 'Tottenham Hotspur': 76, 'Newcastle United': 75,
    'Aston Villa': 73, 'Brighton & Hove Albion': 70, 'West Ham United': 68,
    'Brentford': 66, 'Fulham': 65, 'Crystal Palace': 64,
    'Wolverhampton Wanderers': 63, 'Everton': 62, 'Bournemouth': 61,
    'Nottingham Forest': 60, 'Ipswich Town': 55, 'Leicester City': 57,
    'Southampton': 54,
    # Promoted 2026/27 — Source: Sky Sports fixtures, verified 21 Aug 2026
    'Coventry City': 58, 'Hull City': 56, 'Sunderland': 57, 'Leeds United': 61,
    # European clubs
    'Real Madrid': 96, 'Bayern Munich': 92, 'PSG': 89,
    'Inter Milan': 85, 'Atletico Madrid': 84, 'Bayer Leverkusen': 83,
    'Juventus': 80, 'AC Milan': 80, 'Roma': 76, 'Lazio': 74,
    'Ajax': 74, 'Borussia Dortmund': 81, 'Barcelona': 88,
    'Porto': 76, 'Benfica': 75, 'Sporting CP': 74, 'Celtic': 70,
}


# ─── Key first-scorer picks per team (verified 2026/27 squads) ───────────────
FIRST_SCORERS = {
    'Manchester City':          {'name': 'Erling Haaland',         'odds': '7/4',  'note': 'Penalty taker · leads PL scorers'},
    'Arsenal':                  {'name': 'Bukayo Saka',             'odds': '9/2',  'note': 'Set-piece specialist · top Arsenal scorer'},
    'Liverpool':                {'name': 'Alexander Isak',          'odds': '9/4',  'note': 'Signed from Newcastle · clinical finisher · key man'},
    'Chelsea':                  {'name': 'Cole Palmer',             'odds': '7/2',  'note': 'Penalty taker · free-kick threat'},
    # Source: ESPN (Højlund's permanent Napoli move confirmed 17 May 2026) +
    # manutd.com (Sesko's own club page, confirms he kept #30 rather than take
    # the vacated #9 after Højlund's exit) — verified 30 Aug 2026
    'Manchester United':        {'name': 'Benjamin Sesko',          'odds': '4/1',  'note': "Højlund's permanent replacement · target man since 2025"},
    'Tottenham Hotspur':        {'name': 'Heung-min Son',           'odds': '7/2',  'note': 'Consistent scorer · strong finisher'},
    # Source: ESPN (Isak's British-record move to Liverpool, referenced in
    # CLAUDE.md's verified 2026/27 facts) + footballfancast.com (Woltemade,
    # Newcastle's £69m record signing from Stuttgart) — verified 30 Aug 2026.
    # Woltemade was used in a deeper role at times last season, so this is a
    # softer pick than most entries here — worth a lineup check before relying on it.
    'Newcastle United':         {'name': 'Nick Woltemade',          'odds': '9/2',  'note': 'Record £69m signing · main striker option post-Isak'},
    'Aston Villa':              {'name': 'Ollie Watkins',           'odds': '7/2',  'note': 'England striker · high xG returns'},
    'Brighton & Hove Albion':   {'name': 'Evan Ferguson',           'odds': '5/1',  'note': 'Young clinical finisher'},
    'West Ham United':          {'name': 'Jarrod Bowen',            'odds': '4/1',  'note': 'Top West Ham scorer · box threat'},
    'Brentford':                {'name': 'Yoane Wissa',             'odds': '5/1',  'note': 'Clinical from range'},
    'Fulham':                   {'name': 'Raúl Jiménez',            'odds': '5/1',  'note': 'Experienced finisher'},
    'Crystal Palace':           {'name': 'Eberechi Eze',            'odds': '6/1',  'note': 'Creative scorer · free kicks'},
    'Wolverhampton Wanderers':  {'name': 'Hwang Hee-chan',          'odds': '7/1',  'note': 'Fast clinical finisher'},
    'Everton':                  {'name': 'Dominic Calvert-Lewin',   'odds': '7/1',  'note': 'Aerial threat · penalty taker'},
    'Bournemouth':              {'name': 'Evanilson',               'odds': '5/1',  'note': 'Brazilian striker · good movement'},
    'Nottingham Forest':        {'name': 'Chris Wood',              'odds': '5/1',  'note': 'Penalty taker · target man'},
    'Ipswich Town':             {'name': 'Liam Delap',              'odds': '9/2',  'note': 'Powerful striker · Man City product'},
    'Leicester City':           {'name': 'Patson Daka',             'odds': '6/1',  'note': 'Pacy striker · strong finisher'},
    'Southampton':              {'name': 'Adam Armstrong',           'odds': '7/1',  'note': 'Pace merchant · top scorer'},
}

# ─── Correct-score approximate odds map ──────────────────────────────────────
CORRECT_SCORE_ODDS = {
    '1-0': '5/1', '2-0': '7/1', '2-1': '9/1', '3-0': '11/1',
    '3-1': '16/1', '3-2': '22/1', '1-1': '5/1', '0-0': '9/1',
    '0-1': '6/1', '1-2': '10/1', '0-2': '9/1', '0-3': '14/1',
}


def float_to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, dict):
        return {k: float_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [float_to_decimal(i) for i in obj]
    return obj


def save(data_key, payload):
    item = {'sport': 'football', 'data_key': data_key, 'updated_at': datetime.now(timezone.utc).isoformat()}
    for k, v in payload.items():
        item[k] = float_to_decimal(v) if isinstance(v, (float, dict, list)) else v
    sports_table.put_item(Item=item)


def predict_match(home, away):
    """Poisson-based prediction — score, result, and BTTS all from the same model.
    The predicted score is always drawn from scorelines that agree with BOTH the
    BTTS verdict AND the predicted result, so none of the three can contradict
    each other."""
    h_str = TEAM_STRENGTH.get(home, 65) + 5  # +5 home advantage
    a_str = TEAM_STRENGTH.get(away, 65)
    lam_h = strength_to_avg_goals(h_str, a_str)
    lam_a = strength_to_avg_goals(a_str, h_str)

    probs = {}
    p_home_win = p_draw = p_away_win = 0.0

    for h in range(6):
        ph = math.exp(-lam_h) * (lam_h ** h) / math.factorial(h)
        for a in range(6):
            pa  = math.exp(-lam_a) * (lam_a ** a) / math.factorial(a)
            probs[(h, a)] = ph * pa
            if h > a:   p_home_win += ph * pa
            elif h == a: p_draw    += ph * pa
            else:        p_away_win += ph * pa

    # Result + confidence
    if p_home_win >= p_away_win and p_home_win >= p_draw:
        result = 'home_win'; conf = round(p_home_win * 100)
    elif p_away_win > p_home_win and p_away_win >= p_draw:
        result = 'away_win'; conf = round(p_away_win * 100)
    else:
        result = 'draw';     conf = round(p_draw * 100)

    # BTTS verdict — computed here so score selection can be consistent with it
    btts_pct = calc_btts_prob(lam_h, lam_a)
    btts_yes = btts_pct >= 50

    # Pick the scoreline CLOSEST to each team's own expected goals (naive rounding
    # of lam_h/lam_a) among scorelines that agree with BOTH the BTTS verdict and
    # the predicted result — not the single globally most-probable cell.
    #
    # Two distinct bugs lived here before this (found 2026-08-28 and 2026-08-30):
    # picking the global argmax cell ignores how lopsided the actual match is.
    # Poisson probability concentrates so heavily on low totals that (2,1)/(1,2)
    # wins the argmax across almost any realistic PL lam_h/lam_a pair — a 57%
    # confidence near-lock and a 40% confidence coin-flip both landed on the exact
    # same "2-1" (found 2026-08-30), because the argmax barely moves with the
    # actual gap between the teams. Anchoring on the naive expected-goals cell
    # instead lets the shown score actually track lam_h/lam_a — a big favourite's
    # higher lam_h pulls the score toward 3-0/3-1, a near-even match stays 1-1/2-1
    # — while the closest-valid-cell search still guarantees the three outputs
    # (score, BTTS, result) never contradict each other, which was the original
    # 2026-08-28 bug (e.g. an away_win shown with a 1-1 scoreline).
    if result == 'home_win':
        result_ok = lambda s: s[0] > s[1]
    elif result == 'away_win':
        result_ok = lambda s: s[1] > s[0]
    else:
        result_ok = lambda s: s[0] == s[1]

    #   BTTS Yes → both teams must score (h>0 AND a>0)
    #   BTTS No  → at least one team must get 0 (h=0 OR a=0)
    if btts_yes:
        btts_ok = lambda s: s[0] > 0 and s[1] > 0
    else:
        btts_ok = lambda s: s[0] == 0 or s[1] == 0

    candidates = {s: p for s, p in probs.items() if result_ok(s) and btts_ok(s)}
    # Practically always non-empty within a 6x6 grid (e.g. home_win+BTTS-No has
    # (1,0); home_win+BTTS-Yes has (2,1); same pattern for away_win/draw), but
    # fall back to result-only agreement, then a sane default, just in case.
    if not candidates:
        candidates = {s: p for s, p in probs.items() if result_ok(s)}

    if candidates:
        naive_h, naive_a = round(lam_h), round(lam_a)
        best_score = min(
            candidates,
            key=lambda s: (abs(s[0] - naive_h) + abs(s[1] - naive_a), -candidates[s]),
        )
    else:
        best_score = (1, 0) if result == 'home_win' else (0, 1) if result == 'away_win' else (0, 0)

    return {
        'result':     result,
        'score':      f'{best_score[0]}-{best_score[1]}',
        'confidence': conf,
        'btts_pct':   btts_pct,
    }


def _parse_espn_events(events, limit):
    """Convert ESPN event dicts to BetBud fixture dicts."""
    out = []
    for ev in events[:limit]:
        comp = (ev.get('competitions') or [{}])[0]
        competitors = comp.get('competitors', [])
        if len(competitors) < 2:
            continue
        home = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
        away = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])
        completed = (comp.get('status') or {}).get('type', {}).get('completed', False)
        ht = home.get('team', {}).get('displayName', '')
        at = away.get('team', {}).get('displayName', '')
        fx = {
            'id':         ev.get('id', ''),
            'date':       ev.get('date', ''),
            'home':       ht,
            'away':       at,
            'home_score': int(home.get('score', 0)) if completed else None,
            'away_score': int(away.get('score', 0)) if completed else None,
            'completed':  completed,
            'status':     (comp.get('status') or {}).get('type', {}).get('name', 'STATUS_SCHEDULED'),
            'venue':      (comp.get('venue') or {}).get('fullName', ''),
        }
        if not completed:
            fx['prediction'] = predict_match(ht, at)
        out.append(fx)
    return out


def decimal_to_fractional(decimal_odds):
    """Convert Betfair decimal odds to nearest standard fractional string."""
    # Map common decimals to bookmaker fractional equivalents
    MAP = [
        (1.07, '1/14'), (1.10, '1/10'), (1.14, '1/7'), (1.20, '1/5'),
        (1.25, '1/4'),  (1.33, '2/7'),  (1.40, '2/5'), (1.44, '4/9'),
        (1.50, '1/2'),  (1.57, '4/7'),  (1.62, '5/8'), (1.67, '4/6'),
        (1.72, '8/11'), (1.80, '4/5'),  (1.83, '5/6'), (1.91, '10/11'),
        (2.00, 'Evens'), (2.10, '11/10'), (2.20, '6/5'), (2.25, '5/4'),
        (2.38, '11/8'), (2.50, '6/4'),  (2.62, '13/8'), (2.75, '7/4'),
        (3.00, '2/1'),  (3.25, '9/4'),  (3.50, '5/2'), (4.00, '3/1'),
        (4.50, '7/2'),  (5.00, '4/1'),  (6.00, '5/1'), (7.00, '6/1'),
        (8.00, '7/1'),  (9.00, '8/1'),  (10.0, '9/1'), (11.0, '10/1'),
        (13.0, '12/1'), (17.0, '16/1'), (21.0, '20/1'),
    ]
    for threshold, frac in MAP:
        if decimal_odds <= threshold:
            return frac
    n = round(decimal_odds) - 1
    return f'{n}/1'


def _betfair_refresh_token(sm, secret):
    """Re-login to Betfair and persist the new session token to Secrets Manager."""
    try:
        r = requests.post(
            'https://identitysso.betfair.com/api/login',
            headers={'X-Application': secret['app_key'], 'Content-Type': 'application/x-www-form-urlencoded'},
            data={'username': secret['username'], 'password': secret['password']},
            timeout=10,
        )
        resp = r.json()
        if resp.get('status') == 'SUCCESS':
            secret['session_token'] = resp['token']
            secret['last_refresh']  = datetime.now(timezone.utc).isoformat()
            sm.update_secret(SecretId='betfair-credentials', SecretString=json.dumps(secret))
            return resp['token']
    except Exception:
        pass
    return None


def fetch_betfair_football_odds(fixtures):
    """Fetch live 1X2 MATCH_ODDS from Betfair for upcoming PL fixtures.
    Auto-refreshes the session token if expired.
    Returns dict keyed by Betfair event name → {runner_name: decimal_price}."""
    try:
        import boto3 as _boto3
        sm = _boto3.client('secretsmanager', region_name='eu-west-1')
        secret = json.loads(sm.get_secret_value(SecretId='betfair-credentials')['SecretString'])
        app_key = secret.get('app_key', '')
        session_token = secret.get('session_token', '')
        if not app_key or not session_token:
            return {}

        # Find MATCH_ODDS markets for English Premier League (eventTypeId=1, competitionId=10932509)
        catalogue_url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/'
        headers = {
            'X-Application': app_key, 'X-Authentication': session_token,
            'Content-Type': 'application/json', 'Accept': 'application/json',
        }
        cat_body = {
            'filter': {
                'eventTypeIds': ['1'],
                'competitionIds': ['10932509'],  # Premier League
                'marketTypeCodes': ['MATCH_ODDS'],
                'inPlayOnly': False,
            },
            'marketProjection': ['RUNNER_DESCRIPTION', 'EVENT'],
            'maxResults': 20,
        }
        r = requests.post(catalogue_url, headers=headers, json=cat_body, timeout=10)
        markets = r.json() if r.status_code == 200 else []

        # Auto-refresh token if session expired, then retry once
        if isinstance(markets, dict) and markets.get('detail', {}).get('APINGException', {}).get('errorCode') == 'INVALID_SESSION_INFORMATION':
            new_token = _betfair_refresh_token(sm, secret)
            if new_token:
                headers['X-Authentication'] = new_token
                r = requests.post(catalogue_url, headers=headers, json=cat_body, timeout=10)
                markets = r.json() if r.status_code == 200 else []

        if not markets or isinstance(markets, dict):
            return {}

        # Build market_id → fixture mapping
        market_ids = [m['marketId'] for m in markets]
        books_url = 'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/'
        books_body = {
            'marketIds': market_ids,
            'priceProjection': {'priceData': ['EX_BEST_OFFERS'], 'exBestOffersOverrides': {'bestPricesDepth': 1}},
        }
        r2 = requests.post(books_url, headers=headers, json=books_body, timeout=10)
        books = {b['marketId']: b for b in (r2.json() if r2.status_code == 200 else [])}

        result = {}
        for m in markets:
            mid   = m['marketId']
            event = m.get('event', {}).get('name', '')  # e.g. "Arsenal v Coventry City"
            book  = books.get(mid, {})
            runners = book.get('runners', [])
            runner_map = {r['selectionId']: r for r in runners}
            cat_runners = m.get('runners', [])

            odds_map = {}
            for cr in cat_runners:
                sid  = cr['selectionId']
                name = cr.get('runnerName', '')
                bk   = runner_map.get(sid, {})
                best = (bk.get('ex', {}).get('availableToBack') or [{}])[0]
                price = best.get('price')
                if price:
                    odds_map[name] = price

            if len(odds_map) >= 2:
                result[event] = odds_map  # e.g. {'Arsenal': 1.14, 'The Draw': 7.0, 'Coventry City': 18.0}

        return result
    except Exception:
        return {}


def match_betfair_odds(fixture_home, fixture_away, bf_odds_map):
    """Find Betfair odds for a fixture — Betfair event names use 'v' not 'vs'."""
    for event_name, odds in bf_odds_map.items():
        parts = event_name.lower().replace(' v ', ' vs ').split(' vs ')
        if len(parts) == 2:
            h, a = parts[0].strip(), parts[1].strip()
            if (fixture_home.lower() in h or h in fixture_home.lower()) and \
               (fixture_away.lower() in a or a in fixture_away.lower()):
                return odds
    return {}


def fetch_espn_fixtures(league, limit=10):
    """Generic ESPN scoreboard fetch — tries scoreboard, then a 7-day date window."""
    urls = [
        f'{ESPN_SOCCER}/{league}/scoreboard',
        f'{ESPN_SOCCER}/{league}/scoreboard?limit=100',
    ]
    # Also try a date-range window covering the next 10 days
    today_ts  = datetime.now(timezone.utc)
    date_from = today_ts.strftime('%Y%m%d')
    date_to   = (today_ts.replace(day=today_ts.day + 10)
                 if today_ts.day + 10 <= 28
                 else today_ts).strftime('%Y%m%d')
    urls.append(f'{ESPN_SOCCER}/{league}/scoreboard?dates={date_from}-{date_to}')

    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                continue
            events = r.json().get('events', [])
            if events:
                result = _parse_espn_events(events, limit)
                if result:
                    print(f'[football] ESPN {league}: {len(result)} fixtures from {url}')
                    return result
        except Exception as e:
            print(f'ESPN {league} fetch error ({url}): {e}')

    print(f'[football] ESPN {league}: all attempts returned 0 events')
    return []


# Source: skysports.com/football/fixtures, verified 21 Aug 2026
# Full GW1 + GW2 schedule. Update each week from Sky Sports/BBC/FotMob. Never invent.
STATIC_PL_FIXTURES = [
    # GW1 — 21-24 August 2026
    {'id': 'g1f1',  'date': '2026-08-21T19:00Z', 'home': 'Arsenal',                'away': 'Coventry City',         'completed': True,  'home_score': 3, 'away_score': 0, 'status': 'STATUS_FINAL', 'venue': 'Emirates Stadium'},
    {'id': 'g1f2',  'date': '2026-08-22T11:30Z', 'home': 'Hull City',              'away': 'Manchester United',     'completed': True,  'home_score': 2, 'away_score': 0, 'status': 'STATUS_FINAL', 'venue': 'MKM Stadium'},
    {'id': 'g1f3',  'date': '2026-08-22T14:00Z', 'home': 'Everton',                'away': 'Crystal Palace',        'completed': True,  'home_score': 2, 'away_score': 0, 'status': 'STATUS_FINAL', 'venue': 'Goodison Park'},
    {'id': 'g1f4',  'date': '2026-08-22T14:00Z', 'home': 'Ipswich Town',           'away': 'Sunderland',            'completed': True,  'home_score': 2, 'away_score': 1, 'status': 'STATUS_FINAL', 'venue': 'Portman Road'},
    {'id': 'g1f5',  'date': '2026-08-22T14:00Z', 'home': 'Nottingham Forest',      'away': 'Leeds United',          'completed': True,  'home_score': 0, 'away_score': 1, 'status': 'STATUS_FINAL', 'venue': 'City Ground'},
    {'id': 'g1f6',  'date': '2026-08-22T16:30Z', 'home': 'Brentford',              'away': 'Tottenham Hotspur',     'completed': True,  'home_score': 3, 'away_score': 0, 'status': 'STATUS_FINAL', 'venue': 'Gtech Community Stadium'},
    {'id': 'g1f7',  'date': '2026-08-23T13:00Z', 'home': 'Brighton & Hove Albion', 'away': 'Aston Villa',           'completed': True,  'home_score': 4, 'away_score': 0, 'status': 'STATUS_FINAL', 'venue': 'Amex Stadium'},
    {'id': 'g1f8',  'date': '2026-08-23T13:00Z', 'home': 'Manchester City',        'away': 'Bournemouth',           'completed': True,  'home_score': 2, 'away_score': 1, 'status': 'STATUS_FINAL', 'venue': 'Etihad Stadium'},
    {'id': 'g1f9',  'date': '2026-08-23T15:30Z', 'home': 'Newcastle United',       'away': 'Liverpool',             'completed': True,  'home_score': 2, 'away_score': 2, 'status': 'STATUS_FINAL', 'venue': "St. James' Park"},
    # Source: ESPN match report + Bleacher Report, verified 30 Aug 2026 — Fulham 2-3 Chelsea (Xabi Alonso's first win as Chelsea manager)
    {'id': 'g1f10', 'date': '2026-08-24T19:00Z', 'home': 'Fulham',                 'away': 'Chelsea',               'completed': True,  'home_score': 2, 'away_score': 3, 'status': 'STATUS_FINAL', 'venue': 'Craven Cottage'},
    # GW2 — 28-31 August 2026
    # Source: ESPN match report, verified 30 Aug 2026 — Cherki brace + Haaland, City 4-1 at Selhurst Park
    {'id': 'g2f1',  'date': '2026-08-28T19:00Z', 'home': 'Crystal Palace',         'away': 'Manchester City',       'completed': True,  'home_score': 1, 'away_score': 4, 'status': 'STATUS_FINAL', 'venue': 'Selhurst Park'},
    # Source: ESPN + Al Jazeera match report, verified 30 Aug 2026 — Munoz equalised late for Liverpool after trailing Forest
    {'id': 'g2f2',  'date': '2026-08-29T11:30Z', 'home': 'Liverpool',              'away': 'Nottingham Forest',     'completed': True,  'home_score': 2, 'away_score': 2, 'status': 'STATUS_FINAL', 'venue': 'Anfield'},
    # Source: ESPN + NBC Sports match report, verified 30 Aug 2026 — Elanga + Wissa for Newcastle's first win of the season
    {'id': 'g2f3',  'date': '2026-08-29T16:30Z', 'home': 'Tottenham Hotspur',      'away': 'Newcastle United',      'completed': True,  'home_score': 0, 'away_score': 2, 'status': 'STATUS_FINAL', 'venue': 'Tottenham Hotspur Stadium'},
    {'id': 'g2f4',  'date': '2026-08-30T13:00Z', 'home': 'Chelsea',                'away': 'Brighton & Hove Albion','completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Stamford Bridge'},
    {'id': 'g2f5',  'date': '2026-08-31T19:00Z', 'home': 'Aston Villa',            'away': 'Arsenal',               'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Villa Park'},
    # GW2 continued — 5 fixtures missing from the original list (found 2026-08-30
    # via a Google sports-widget cross-check; a full gameweek is 10 matches, this
    # list only ever had 5). Source: ESPN/Sky Sports match reports, verified 30 Aug 2026.
    {'id': 'g2f6',  'date': '2026-08-29T14:00Z', 'home': 'Bournemouth',            'away': 'Everton',               'completed': True,  'home_score': 1, 'away_score': 1, 'status': 'STATUS_FINAL', 'venue': 'Vitality Stadium'},
    {'id': 'g2f7',  'date': '2026-08-29T14:00Z', 'home': 'Coventry City',          'away': 'Hull City',             'completed': True,  'home_score': 0, 'away_score': 1, 'status': 'STATUS_FINAL', 'venue': 'CBS Arena'},
    {'id': 'g2f8',  'date': '2026-08-30T13:00Z', 'home': 'Leeds United',           'away': 'Brentford',             'completed': True,  'home_score': 1, 'away_score': 1, 'status': 'STATUS_FINAL', 'venue': 'Elland Road'},
    # Reverted to pending 2026-08-30: three separate searches for this result
    # returned three different scores (0-1, 1-0, 3-1) because search results kept
    # conflating this fixture with an EARLIER, DIFFERENT Sunderland-Fulham meeting
    # from 22 Feb 2026 (last season) - same two clubs, wrong match entirely.
    # Do not re-add a score here without a source that explicitly confirms the
    # 30 Aug 2026 date, not just the team names.
    {'id': 'g2f9',  'date': '2026-08-30T13:00Z', 'home': 'Sunderland',             'away': 'Fulham',                'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Stadium of Light'},
    # Not yet confirmed finished at time of writing — searches only surfaced
    # older (2024/25) Man Utd-Ipswich meetings, not this fixture's result.
    # Leave pending until a real 2026 score can be verified — do not guess.
    {'id': 'g2f10', 'date': '2026-08-30T15:30Z', 'home': 'Manchester United',      'away': 'Ipswich Town',          'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Old Trafford'},
    # GW3 — 4-6 September 2026
    # Source: Sky Sports (skysports.com "Premier League 2026/27 fixtures live on Sky Sports"), verified 30 Aug 2026 —
    # TV-selected fixtures with confirmed times; remaining GW3 fixtures default to standard Saturday 15:00 BST kickoff
    {'id': 'g3f1',  'date': '2026-09-04T19:00Z', 'home': 'Ipswich Town',           'away': 'Liverpool',             'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Portman Road'},
    {'id': 'g3f2',  'date': '2026-09-05T14:00Z', 'home': 'Nottingham Forest',      'away': 'Tottenham Hotspur',     'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'City Ground'},
    {'id': 'g3f3',  'date': '2026-09-05T14:00Z', 'home': 'Brentford',              'away': 'Sunderland',            'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Gtech Community Stadium'},
    {'id': 'g3f4',  'date': '2026-09-05T14:00Z', 'home': 'Brighton & Hove Albion', 'away': 'Leeds United',          'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Amex Stadium'},
    {'id': 'g3f5',  'date': '2026-09-05T14:00Z', 'home': 'Fulham',                 'away': 'Crystal Palace',        'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Craven Cottage'},
    {'id': 'g3f6',  'date': '2026-09-05T14:00Z', 'home': 'Manchester City',        'away': 'Coventry City',         'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Etihad Stadium'},
    # Corrected 2026-08-30: moved to 12:30 BST for TV, not standard 15:00 — confirmed via newcastleunited.com's own fixture page
    {'id': 'g3f7',  'date': '2026-09-05T11:30Z', 'home': 'Newcastle United',       'away': 'Bournemouth',           'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': "St. James' Park"},
    {'id': 'g3f8',  'date': '2026-09-05T16:30Z', 'home': 'Hull City',              'away': 'Aston Villa',           'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'MKM Stadium'},
    {'id': 'g3f9',  'date': '2026-09-06T13:00Z', 'home': 'Everton',                'away': 'Manchester United',     'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Goodison Park'},
    {'id': 'g3f10', 'date': '2026-09-06T15:30Z', 'home': 'Arsenal',                'away': 'Chelsea',               'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Emirates Stadium'},
    # GW4 — 12-14 September 2026
    # Source: user-supplied official fixture list, verified 30 Aug 2026
    {'id': 'g4f1',  'date': '2026-09-12T14:00Z', 'home': 'Aston Villa',            'away': 'Nottingham Forest',     'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Villa Park'},
    {'id': 'g4f2',  'date': '2026-09-12T14:00Z', 'home': 'Bournemouth',            'away': 'Brentford',             'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Vitality Stadium'},
    {'id': 'g4f3',  'date': '2026-09-12T14:00Z', 'home': 'Chelsea',                'away': 'Hull City',             'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Stamford Bridge'},
    {'id': 'g4f4',  'date': '2026-09-12T14:00Z', 'home': 'Crystal Palace',         'away': 'Ipswich Town',          'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Selhurst Park'},
    {'id': 'g4f5',  'date': '2026-09-12T14:00Z', 'home': 'Liverpool',              'away': 'Fulham',                'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Anfield'},
    {'id': 'g4f6',  'date': '2026-09-12T16:30Z', 'home': 'Tottenham Hotspur',      'away': 'Everton',               'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Tottenham Hotspur Stadium'},
    {'id': 'g4f7',  'date': '2026-09-12T19:00Z', 'home': 'Sunderland',             'away': 'Arsenal',               'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Stadium of Light'},
    {'id': 'g4f8',  'date': '2026-09-13T13:00Z', 'home': 'Coventry City',          'away': 'Brighton & Hove Albion','completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'CBS Arena'},
    # Kept as reported by the user's source (Sun 13 Sept, 16:30 BST); one other
    # search result suggested Sat 12 Sept 14:00 UTC instead but without a clear
    # source of its own — flag for re-verification closer to the date.
    {'id': 'g4f9',  'date': '2026-09-13T15:30Z', 'home': 'Manchester United',      'away': 'Manchester City',       'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Old Trafford'},
    {'id': 'g4f10', 'date': '2026-09-14T19:00Z', 'home': 'Leeds United',           'away': 'Newcastle United',      'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Elland Road'},
    # GW5 — 18-20 September 2026
    # Source: user-supplied official fixture list, verified 30 Aug 2026
    {'id': 'g5f1',  'date': '2026-09-18T19:00Z', 'home': 'Brentford',              'away': 'Chelsea',               'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Gtech Community Stadium'},
    {'id': 'g5f2',  'date': '2026-09-19T11:30Z', 'home': 'Tottenham Hotspur',      'away': 'Aston Villa',           'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Tottenham Hotspur Stadium'},
    {'id': 'g5f3',  'date': '2026-09-19T14:00Z', 'home': 'Brighton & Hove Albion', 'away': 'Arsenal',               'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Amex Stadium'},
    {'id': 'g5f4',  'date': '2026-09-19T14:00Z', 'home': 'Everton',                'away': 'Ipswich Town',          'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Goodison Park'},
    {'id': 'g5f5',  'date': '2026-09-19T14:00Z', 'home': 'Leeds United',           'away': 'Crystal Palace',        'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Elland Road'},
    {'id': 'g5f6',  'date': '2026-09-19T14:00Z', 'home': 'Newcastle United',       'away': 'Hull City',             'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': "St. James' Park"},
    {'id': 'g5f7',  'date': '2026-09-19T16:30Z', 'home': 'Nottingham Forest',      'away': 'Coventry City',         'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'City Ground'},
    {'id': 'g5f8',  'date': '2026-09-20T13:00Z', 'home': 'Bournemouth',            'away': 'Liverpool',             'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Vitality Stadium'},
    {'id': 'g5f9',  'date': '2026-09-20T13:00Z', 'home': 'Manchester City',        'away': 'Sunderland',            'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Etihad Stadium'},
    {'id': 'g5f10', 'date': '2026-09-20T15:30Z', 'home': 'Fulham',                 'away': 'Manchester United',     'completed': False, 'status': 'STATUS_SCHEDULED', 'venue': 'Craven Cottage'},
]


def fetch_pl_standings():
    """Fetch PL standings from ESPN."""
    try:
        r = requests.get(f'{ESPN_SOCCER}/eng.1/standings', headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return []
        out = []
        for group in r.json().get('standings', []):
            for entry in group.get('entries', []):
                stats = {s['name']: s.get('value', 0) for s in entry.get('stats', [])}
                out.append({
                    'pos':    entry.get('rank', 0),
                    'team':   entry.get('team', {}).get('displayName', ''),
                    'played': int(stats.get('gamesPlayed', 0)),
                    'won':    int(stats.get('wins', 0)),
                    'drawn':  int(stats.get('ties', 0)),
                    'lost':   int(stats.get('losses', 0)),
                    'gf':     int(stats.get('pointsFor', 0)),
                    'ga':     int(stats.get('pointsAgainst', 0)),
                    'gd':     int(stats.get('pointDifferential', 0)),
                    'pts':    int(stats.get('points', 0)),
                })
        return sorted(out, key=lambda x: x['pos'])
    except Exception as e:
        print(f'ESPN PL standings error: {e}')
        return []


def decimal_to_fractional(dec):
    """Convert decimal odds to nearest fractional string."""
    if not dec or dec <= 1:
        return 'N/A'
    profit = dec - 1
    mappings = [
        (0.17, '1/6'), (0.2, '1/5'), (0.25, '1/4'), (0.33, '1/3'),
        (0.4, '2/5'), (0.5, '1/2'), (0.57, '4/7'), (0.67, '2/3'),
        (0.75, '3/4'), (0.80, '4/5'), (0.91, '10/11'), (1.0, 'Evens'),
        (1.1, '11/10'), (1.25, '5/4'), (1.5, '6/4'), (2.0, '2/1'),
        (2.5, '5/2'), (3.0, '3/1'), (3.5, '7/2'), (4.0, '4/1'),
        (4.5, '9/2'), (5.0, '5/1'), (6.0, '6/1'), (7.0, '7/1'),
        (9.0, '9/1'), (10.0, '10/1'), (12.0, '12/1'), (16.0, '16/1'),
    ]
    return min(mappings, key=lambda m: abs(m[0] - profit))[1]


def calc_team_stats(standings):
    """Derive avg goals scored/conceded per game from league table."""
    stats = {}
    for row in standings:
        played = max(row.get('played', 0), 1)
        stats[row['team']] = {
            'avg_for':     round(row.get('gf', 0) / played, 2),
            'avg_against': round(row.get('ga', 0) / played, 2),
        }
    return stats


def strength_to_avg_goals(strength, opponent_strength=None):
    """Map team strength (51-96) to expected goals scored per game.

    Base rate calibrated to PL averages: elite clubs ~1.8-2.0, mid-table ~1.1-1.3,
    promoted ~0.7-0.9. Without `opponent_strength` this is opponent-blind — Liverpool's
    expected goals would be identical whether they're playing Forest or Man City,
    which is exactly why predicted scores used to converge on the same "2-1" for
    every fixture regardless of how lopsided the actual matchup was (found
    2026-08-30). When `opponent_strength` is given, scale the base rate by the
    strength gap: a weaker opponent's defense concedes more, a stronger one concedes
    less. Capped so this adjusts rather than dominates the base attacking rate.
    """
    base = 0.7 + max(strength - 51, 0) * 0.025
    if opponent_strength is not None:
        gap = strength - opponent_strength
        base *= max(0.4, min(2.3, 1 + gap / 70))
    return round(base, 2)


def calc_btts_prob(avg_home_for, avg_away_for):
    """Poisson probability both teams score ≥ 1 goal."""
    p_home = 1 - math.exp(-max(avg_home_for, 0.1))
    p_away = 1 - math.exp(-max(avg_away_for, 0.1))
    return round(p_home * p_away * 100)


def generate_match_bets(fx, team_stats, bf_odds_map=None):
    """Return 3-pick bet card (Safe, Value, Longshot) for an upcoming fixture."""
    home, away = fx.get('home', ''), fx.get('away', '')
    pred   = fx.get('prediction', {})
    result = pred.get('result', 'home_win')
    score  = pred.get('score', '2-1')
    conf   = pred.get('confidence', 50)

    # Use live stats from standings when available; fall back to strength-derived goals
    def _stats(team):
        if team in team_stats:
            return team_stats[team]
        s = TEAM_STRENGTH.get(team, 65)
        avg = strength_to_avg_goals(s)
        return {'avg_for': avg, 'avg_against': strength_to_avg_goals(72 - (s - 65))}

    h_stats = _stats(home)
    a_stats = _stats(away)

    # ── Safe Pick: match result — live Betfair odds where available ──────────
    h_str = TEAM_STRENGTH.get(home, 65) + 5
    a_str = TEAM_STRENGTH.get(away, 65)
    bf    = match_betfair_odds(home, away, bf_odds_map or {})

    if result == 'home_win':
        result_label = f'{home} Win'
        bf_price     = bf.get(home) or bf.get(f'{home} FC')
    elif result == 'away_win':
        result_label = f'{away} Win'
        bf_price     = bf.get(away) or bf.get(f'{away} FC')
    else:
        result_label = 'Draw'
        bf_price     = bf.get('The Draw') or bf.get('Draw')

    if bf_price:
        live_odds = decimal_to_fractional(float(bf_price))
        odds_source = f'Betfair {float(bf_price):.2f}'
    else:
        # Fallback: convert model confidence to approximate odds
        # Use implied probability (with 10% overround) → decimal → fractional
        implied = max(conf / 100, 0.05)
        decimal_approx = round(1 / implied * 0.90, 2)  # 10% book margin
        live_odds   = decimal_to_fractional(decimal_approx)
        odds_source = f'model {conf}% (no live price)'

    safe_pick = {
        'market':     'Match Result',
        'pick':       result_label,
        'odds':       live_odds,
        'confidence': conf,
        'reason':     f'{home} {h_str} vs {away} {a_str} — {odds_source}',
    }

    # ── Value Pick: BTTS ─────────────────────────────────────────────────────
    # Use btts_pct from predict_match (already in pred dict) so score + BTTS
    # are always derived from the same model and can never contradict.
    btts_pct = pred.get('btts_pct') or calc_btts_prob(h_stats['avg_for'], a_stats['avg_for'])
    combined  = h_stats['avg_for'] + a_stats['avg_for']

    if btts_pct >= 58:
        value_pick = {
            'market': 'Both Teams to Score',
            'pick':   'Yes',
            'odds':   '4/5',
            'pct':    btts_pct,
            'reason': f'BTTS {btts_pct}% — {home} avg {h_stats["avg_for"]:.1f} scored, {away} avg {a_stats["avg_for"]:.1f}',
        }
    elif btts_pct >= 50 and combined > 2.5:
        over_pct = round(min((combined / 2.5) * 50, 80))
        value_pick = {
            'market': 'Total Goals',
            'pick':   'Over 2.5',
            'odds':   'Evens',
            'pct':    over_pct,
            'reason': f'Combined {combined:.1f} avg goals/game — over 2.5 expected (~{over_pct}%)',
        }
    elif btts_pct >= 50:
        value_pick = {
            'market': 'Both Teams to Score',
            'pick':   'Yes',
            'odds':   'Evens',
            'pct':    btts_pct,
            'reason': f'BTTS {btts_pct}% — balanced scoring match expected',
        }
    else:
        no_pct = 100 - btts_pct
        value_pick = {
            'market': 'Both Teams to Score',
            'pick':   'No',
            'odds':   '4/5',
            'pct':    no_pct,
            'reason': f'BTTS No ({no_pct}%) — predicted score {score} consistent with clean sheet',
        }

    # ── Longshot: first scorer from stronger team ─────────────────────────────
    stronger = home if result in ('home_win', 'draw') else away
    scorer   = FIRST_SCORERS.get(stronger)
    if scorer and conf >= 52:
        longshot = {
            'market': 'First Goalscorer',
            'pick':   scorer['name'],
            'team':   stronger,
            'odds':   scorer['odds'],
            'reason': scorer['note'],
        }
    else:
        longshot = {
            'market': 'Correct Score',
            'pick':   score,
            'odds':   CORRECT_SCORE_ODDS.get(score, '10/1'),
            'reason': f'Model predicted scoreline — result confidence {conf}%',
        }

    return {'safe': safe_pick, 'value': value_pick, 'longshot': longshot}


# ─── Daily learning loop ────────────────────────────────────────────────────
# Snapshot each fixture's prediction the FIRST time it's seen upcoming, before
# kickoff. This is the only reliable way to later ask "was our prediction
# right" — recomputing predict_match() after the fact uses TODAY's
# TEAM_STRENGTH values, not whatever was actually shown to subscribers before
# the match. Once a fixture is marked completed (STATIC_PL_FIXTURES or ESPN),
# backfill the actual result into that same snapshot and score it. History
# entries are immutable once scored — a fixture is graded once, from the
# prediction that was live pre-match, never re-graded.
#
# Added 2026-08-29. Starts from zero: nothing is retroactively graded for
# fixtures that completed before this existed (there's no honest pre-match
# snapshot for them) — accuracy numbers only accumulate from here forward.

def update_prediction_history(all_fixtures):
    """Returns (history_dict, changed_bool). history is keyed by fixture id."""
    try:
        resp = sports_table.get_item(Key={'sport': 'football', 'data_key': 'PL_PREDICTION_HISTORY'})
        history = dict((resp.get('Item') or {}).get('entries', {}) or {})
    except Exception as e:
        print(f'[learning] could not load PL_PREDICTION_HISTORY: {e}')
        history = {}

    changed = False
    for fx in all_fixtures:
        home, away = fx.get('home'), fx.get('away')
        fid = fx.get('id') or (f"{home}-{away}-{fx.get('date', '')[:10]}" if home and away else None)
        if not fid or not home or not away:
            continue

        entry = history.get(fid)

        if entry is None:
            if not fx.get('completed'):
                pred = fx.get('prediction') or predict_match(home, away)
                history[fid] = {
                    'home': home, 'away': away, 'date': fx.get('date', ''),
                    'pred_result':     pred['result'],
                    'pred_score':      pred['score'],
                    'pred_confidence': pred['confidence'],
                    'pred_btts_pct':   pred['btts_pct'],
                    'actual_recorded': False,
                }
                changed = True
            continue

        if entry.get('actual_recorded'):
            # One-time backfill: entries graded before miss analysis existed
            # (2026-08-30) won't have it yet. Only ADDS the analysis field —
            # never touches the actual grading, which stays immutable.
            if not entry.get('score_correct', True) and 'miss_analysis' not in entry:
                entry['miss_analysis'] = _analyze_score_miss(entry, entry['home'], entry['away'])
                changed = True
            continue

        hs, aws_ = fx.get('home_score'), fx.get('away_score')
        if fx.get('completed') and hs is not None and aws_ is not None:
            actual_result = 'home_win' if hs > aws_ else ('away_win' if aws_ > hs else 'draw')
            actual_score  = f'{hs}-{aws_}'
            actual_btts   = hs > 0 and aws_ > 0
            entry.update({
                'actual_result':  actual_result,
                'actual_score':   actual_score,
                'actual_btts':    actual_btts,
                'result_correct': entry['pred_result'] == actual_result,
                'score_correct':  entry['pred_score'] == actual_score,
                'btts_correct':   (entry['pred_btts_pct'] >= 50) == actual_btts,
                'actual_recorded': True,
            })
            if not entry['score_correct']:
                entry['miss_analysis'] = _analyze_score_miss(entry, home, away)
            changed = True

    return history, changed


def _analyze_score_miss(entry, home, away):
    """Explain WHY a wrong score prediction was wrong, not just that it was.

    Two very different kinds of miss, and only one of them is actionable:
      - 'right_result_wrong_margin': picked the correct side, exact goals off.
        Expected noise — even a good model rarely nails the exact scoreline.
        Nothing to adjust for.
      - 'wrong_result': picked the wrong side entirely. This is the real
        signal — it means TEAM_STRENGTH mis-rated one or both teams for this
        matchup. Identifies which team outperformed the model's expectation
        (the one whose actual goal margin exceeded what was predicted) so a
        recurring pattern is visible for the next TEAM_STRENGTH review.
    """
    ph, pa = map(int, entry['pred_score'].split('-'))
    ah, aa = map(int, entry['actual_score'].split('-'))
    pred_margin, actual_margin = ph - pa, ah - aa

    if entry['result_correct']:
        return {
            'miss_type': 'right_result_wrong_margin',
            'note': (f"Correctly backed {entry['pred_result'].replace('_', ' ')} but the margin was off "
                     f"({entry['pred_score']} predicted vs {entry['actual_score']} actual) - normal variance, not a strength-rating issue."),
        }

    # Wrong side entirely — work out which team beat its expected margin.
    surprised_team, flat_team = (home, away) if actual_margin > pred_margin else (away, home)
    return {
        'miss_type':       'wrong_result',
        'confident_miss':  entry['pred_confidence'] >= 60,
        'predicted':       f"{entry['pred_result']} ({entry['pred_score']}, {entry['pred_confidence']}% conf)",
        'actual':          f"{entry['actual_result']} ({entry['actual_score']})",
        'margin_error':    actual_margin - pred_margin,
        'surprised_team':  surprised_team,
        'underrated_team': flat_team,
        'note': (f"Backed {entry['pred_result'].replace('_', ' ')} at {entry['pred_confidence']}% confidence - "
                 f"{surprised_team} outperformed what TEAM_STRENGTH expected of them."),
    }


def update_team_strength_signals(history):
    """Aggregate wrong-RESULT misses (not margin-only misses — those are
    expected noise) by team, so a recurring "this team keeps beating our
    rating" pattern is visible for the next manual TEAM_STRENGTH review
    instead of being buried inside individual fixture history entries.

    Deliberately NOT automatic — a team surprising the model twice isn't
    enough evidence to safely auto-adjust a live scoring input, and an
    ungoverned feedback loop nudging its own strength ratings from its own
    recent misses is exactly the kind of thing that quietly drifts wrong
    without anyone noticing. This surfaces the signal; a human still decides
    whether to act on it during the weekly TEAM_STRENGTH review.
    """
    tracker = {}
    for entry in history.values():
        ma = entry.get('miss_analysis')
        if not ma or ma.get('miss_type') != 'wrong_result':
            continue
        surprised, flat = ma['surprised_team'], ma['underrated_team']
        tracker.setdefault(surprised, {'overperformed': 0, 'underperformed': 0, 'recent_notes': []})
        tracker.setdefault(flat, {'overperformed': 0, 'underperformed': 0, 'recent_notes': []})
        tracker[surprised]['overperformed'] += 1
        tracker[flat]['underperformed'] += 1
        tracker[surprised]['recent_notes'].append(f"{entry['date'][:10]}: {ma['note']}")

    review = []
    for team, t in tracker.items():
        net = t['overperformed'] - t['underperformed']
        if abs(net) >= 2:
            review.append({
                'team':         team,
                'net_surprises': net,
                'suggestion':   'consider raising TEAM_STRENGTH' if net > 0 else 'consider lowering TEAM_STRENGTH',
                'recent_notes': t['recent_notes'][-3:],
            })

    return tracker, review


def compute_learning_summary(history):
    scored = [e for e in history.values() if e.get('actual_recorded')]
    n = len(scored)
    if n == 0:
        return {
            'n': 0,
            'message': 'No predictions have completed yet - accuracy accumulates as '
                       'snapshotted fixtures finish. Check back after this game week.',
        }

    result_acc = round(100 * sum(1 for e in scored if e['result_correct']) / n, 1)
    score_acc  = round(100 * sum(1 for e in scored if e['score_correct']) / n, 1)
    btts_acc   = round(100 * sum(1 for e in scored if e['btts_correct']) / n, 1)

    bands = []
    for lo, hi in [(0, 50), (50, 60), (60, 70), (70, 80), (80, 101)]:
        b = [e for e in scored if lo <= e['pred_confidence'] < hi]
        if b:
            bands.append({
                'band':                    f'{lo}-{min(hi, 100)}%',
                'n':                       len(b),
                'mean_predicted_confidence': round(sum(e['pred_confidence'] for e in b) / len(b), 1),
                'actual_hit_rate':         round(100 * sum(1 for e in b if e['result_correct']) / len(b), 1),
            })

    misses = [e for e in scored if not e.get('score_correct') and e.get('miss_analysis')]
    misses.sort(key=lambda e: e['date'], reverse=True)

    return {
        'n':                   n,
        'result_accuracy_pct': result_acc,
        'score_accuracy_pct':  score_acc,
        'btts_accuracy_pct':   btts_acc,
        'calibration_bands':   bands,
        'recent_misses': [
            {'home': e['home'], 'away': e['away'], 'date': e['date'], **e['miss_analysis']}
            for e in misses[:10]
        ],
    }


def run_learning_loop(all_fixtures):
    """Call once per scraper run. Returns the learning summary dict."""
    history, changed = update_prediction_history(all_fixtures)
    summary = compute_learning_summary(history)
    _tracker, teams_to_review = update_team_strength_signals(history)
    summary['teams_to_review'] = teams_to_review
    if changed:
        save('PL_PREDICTION_HISTORY', {'entries': history})
    save('PL_LEARNING', summary)
    return summary


def lambda_handler(event, context):
    now = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).date().isoformat()
    season_start = '2026-08-09'
    is_pre_season = today < season_start

    pl_fixtures  = fetch_espn_fixtures('eng.1', limit=12)
    pl_standings = fetch_pl_standings()
    ucl_fixtures = fetch_espn_fixtures('UEFA.CL', limit=8)
    el_fixtures  = fetch_espn_fixtures('UEFA.EL', limit=8)

    # Generate match-bet cards for upcoming PL fixtures
    team_stats = calc_team_stats(pl_standings)
    # Seed predictions on static fixtures (no ESPN data needed)
    for fx in STATIC_PL_FIXTURES:
        if not fx.get('prediction'):
            fx['prediction'] = predict_match(fx['home'], fx['away'])

    # Fetch live Betfair MATCH_ODDS for PL fixtures (1X2 prices)
    bf_odds_map = fetch_betfair_football_odds(STATIC_PL_FIXTURES)

    if pl_fixtures:
        source_fixtures = pl_fixtures
    else:
        # Filter static fixtures to upcoming only, sorted nearest first
        now_iso = datetime.now(timezone.utc).isoformat()
        upcoming = [f for f in STATIC_PL_FIXTURES if f['date'] >= now_iso[:10]]
        source_fixtures = sorted(upcoming, key=lambda f: f['date']) or STATIC_PL_FIXTURES
    # Every upcoming fixture gets a bet card, not just the first 5 — the cap was
    # cutting off real matches once more than one game week's worth of fixtures
    # was in the list (found 2026-08-30, right after adding GW3 on top of the
    # remaining GW2 fixtures).
    weekly_bets = []
    for fx in source_fixtures:
        if not fx.get('completed') and fx.get('prediction'):
            fx['bets'] = generate_match_bets(fx, team_stats, bf_odds_map)
            weekly_bets.append(fx)

    save('META', {
        'season':           '2026/27',
        'status':           'pre_season' if is_pre_season else 'in_progress',
        'season_start':     season_start,
        'last_updated':     now,
        'pl_live':          len(pl_fixtures) > 0,
        'ucl_live':         len(ucl_fixtures) > 0,
        'el_live':          len(el_fixtures) > 0,
        'standings_live':   len(pl_standings) > 0,
    })

    save('PL_PREDICTIONS', {
        'title':         PL_TITLE_PREDICTION,
        'top_four':      PL_TOP_FOUR,
        'top_six':       PL_TOP_SIX_CONTENDERS,
        'relegation':    PL_RELEGATION,
        'golden_boot':   PL_GOLDEN_BOOT,
        'season':        '2026/27',
    })

    # Save all fixtures (ESPN live if available, else full static list including completed results)
    all_fixtures_to_save = pl_fixtures if pl_fixtures else STATIC_PL_FIXTURES
    save('PL_FIXTURES', {
        'fixtures': all_fixtures_to_save,
        'is_live':  len(pl_fixtures) > 0,
    })

    # Learning loop always reads STATIC_PL_FIXTURES specifically, not whichever
    # source happened to be live this run — its fixture `id`s are stable and
    # manually curated (see skill's "Fixture ID convention"), so history entries
    # never fork into duplicates if ESPN availability flips between runs.
    try:
        run_learning_loop(STATIC_PL_FIXTURES)
    except Exception as e:
        print(f'[learning] run_learning_loop failed: {e}')

    save('PL_WEEKLY_BETS', {
        'fixtures':   weekly_bets,
        'generated':  now,
        'count':      len(weekly_bets),
    })

    save('PL_STANDINGS', {
        'standings': pl_standings,
        'is_live':   len(pl_standings) > 0,
    })

    save('UCL_DATA', {
        'english_clubs': UCL_ENGLISH_CLUBS,
        'contenders':    UCL_CONTENDERS,
        'fixtures':      ucl_fixtures,
        'final_date':    '2027-05-31',
        'group_draw':    'August 2026',
        'season':        '2026/27',
    })

    save('EL_DATA', {
        'english_clubs': EL_ENGLISH_CLUBS,
        'contenders':    EL_CONTENDERS,
        'fixtures':      el_fixtures,
        'final_date':    '2027-05-21',
        'group_draw':    'August 2026',
        'season':        '2026/27',
    })

    return {
        'statusCode': 200,
        'body': json.dumps({
            'success':     True,
            'updated_at':  now,
            'pre_season':  is_pre_season,
            'pl_fixtures': len(pl_fixtures),
            'standings':   len(pl_standings),
            'ucl':         len(ucl_fixtures),
            'el':          len(el_fixtures),
            'weekly_bets': len(weekly_bets),
        })
    }

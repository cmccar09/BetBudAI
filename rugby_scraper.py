"""
rugby_scraper.py — Daily Nations Championship 2026 rugby data scraper Lambda.

The Nations Championship is rugby's new global competition (inaugural 2026),
replacing the old summer tour format. 12 teams (Six Nations vs SANZAAR+Fiji/Japan),
6 rounds: 3 in July ("southern series"), 3 in November ("northern series"),
plus a Finals Weekend. This is genuinely live/upcoming rugby — unlike Rugby
World Cup (next is 2027), URC and Premiership (both off-season through summer).

Data sources:
  1. Hardcoded fixture list (static — confirmed by World Rugby, won't change)
  2. BBC Sport __INITIAL_DATA__ JSON blob — match results, scraped per fixture
     date once that date has passed (same pattern proven against Six Nations
     2026 data: home/away team, full-time score, status).
  3. Betfair Exchange outright WINNER market — top 5 contenders, live odds

Storage: BetBudAI_Sports table
  PK 'sport' = 'rugby'
  SK 'data_key':
    'FIXTURES'  — all scheduled fixtures (July + November rounds)
    'RESULTS'   — completed match results scraped so far
    'OUTRIGHT'  — top 5 outright winner contenders with live odds
    'META'      — last_updated, tournament dates, is_live flag

Entry point: lambda_handler(event, context) — invoked by Step Functions.
"""

import json
import re
import boto3
import requests
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
sports_table = dynamodb.Table('BetBudAI_Sports')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

TOURNAMENT_START = '2026-07-04'
TOURNAMENT_END   = '2026-11-29'   # July rounds + November Finals Weekend window

# Static fixture list — confirmed by World Rugby (verified 2026-06-30).
# November round dates are provisional windows; refined as official dates confirm.
FIXTURES = [
    # Round 1 — 4 July (Southern Series)
    {'round': 1, 'date': '2026-07-04', 'home': 'New Zealand', 'away': 'France'},
    {'round': 1, 'date': '2026-07-04', 'home': 'Japan',       'away': 'Italy'},
    {'round': 1, 'date': '2026-07-04', 'home': 'South Africa','away': 'England'},
    {'round': 1, 'date': '2026-07-04', 'home': 'Australia',   'away': 'Ireland'},
    {'round': 1, 'date': '2026-07-04', 'home': 'Fiji',        'away': 'Wales'},
    {'round': 1, 'date': '2026-07-04', 'home': 'Argentina',   'away': 'Scotland'},
    # Round 2 — 11 July
    {'round': 2, 'date': '2026-07-11', 'home': 'New Zealand', 'away': 'Italy'},
    {'round': 2, 'date': '2026-07-11', 'home': 'Japan',       'away': 'Ireland'},
    {'round': 2, 'date': '2026-07-11', 'home': 'South Africa','away': 'Scotland'},
    {'round': 2, 'date': '2026-07-11', 'home': 'Australia',   'away': 'France'},
    {'round': 2, 'date': '2026-07-11', 'home': 'Fiji',        'away': 'England'},
    {'round': 2, 'date': '2026-07-11', 'home': 'Argentina',   'away': 'Wales'},
    # Round 3 — 18 July
    {'round': 3, 'date': '2026-07-18', 'home': 'Japan',       'away': 'France'},
    {'round': 3, 'date': '2026-07-18', 'home': 'Australia',   'away': 'Italy'},
    {'round': 3, 'date': '2026-07-18', 'home': 'South Africa','away': 'Wales'},
    {'round': 3, 'date': '2026-07-18', 'home': 'New Zealand', 'away': 'Ireland'},
    {'round': 3, 'date': '2026-07-18', 'home': 'Fiji',        'away': 'Scotland'},
    {'round': 3, 'date': '2026-07-18', 'home': 'Argentina',   'away': 'England'},
    # Round 4 — 6-8 November (Northern Series begins)
    {'round': 4, 'date': '2026-11-06', 'home': 'Ireland',     'away': 'Argentina', 'venue': 'Aviva Stadium, Dublin'},
    {'round': 4, 'date': '2026-11-07', 'home': 'Italy',       'away': 'South Africa'},
    {'round': 4, 'date': '2026-11-07', 'home': 'Scotland',    'away': 'New Zealand', 'venue': 'Murrayfield, Edinburgh'},
    {'round': 4, 'date': '2026-11-07', 'home': 'Wales',       'away': 'Japan', 'venue': 'Principality Stadium, Cardiff'},
    {'round': 4, 'date': '2026-11-07', 'home': 'France',      'away': 'Fiji', 'venue': 'Groupama Stadium, Lyon'},
    {'round': 4, 'date': '2026-11-08', 'home': 'England',     'away': 'Australia', 'venue': 'Allianz Stadium, Twickenham'},
    # Round 5 — 13-15 November
    {'round': 5, 'date': '2026-11-14', 'home': 'Ireland',     'away': 'Fiji', 'venue': 'Aviva Stadium, Dublin'},
    {'round': 5, 'date': '2026-11-14', 'home': 'France',      'away': 'South Africa'},
    {'round': 5, 'date': '2026-11-14', 'home': 'Italy',       'away': 'Argentina'},
    {'round': 5, 'date': '2026-11-14', 'home': 'Wales',       'away': 'New Zealand', 'venue': 'Principality Stadium, Cardiff'},
    {'round': 5, 'date': '2026-11-14', 'home': 'England',     'away': 'Japan', 'venue': 'Allianz Stadium, Twickenham'},
    {'round': 5, 'date': '2026-11-14', 'home': 'Scotland',    'away': 'Australia', 'venue': 'Murrayfield, Edinburgh'},
    # Round 6 — 21 November
    {'round': 6, 'date': '2026-11-21', 'home': 'Ireland',     'away': 'South Africa', 'venue': 'Aviva Stadium, Dublin'},
    {'round': 6, 'date': '2026-11-21', 'home': 'England',     'away': 'New Zealand', 'venue': 'Allianz Stadium, Twickenham'},
    {'round': 6, 'date': '2026-11-21', 'home': 'Scotland',    'away': 'Japan', 'venue': 'Murrayfield, Edinburgh'},
    {'round': 6, 'date': '2026-11-21', 'home': 'Italy',       'away': 'Fiji'},
    {'round': 6, 'date': '2026-11-21', 'home': 'France',      'away': 'Argentina'},
    {'round': 6, 'date': '2026-11-21', 'home': 'Wales',       'away': 'Australia', 'venue': 'Principality Stadium, Cardiff'},
    # Finals Weekend — 27-29 November, opponents TBC by standings (1st v 1st Grand Final at Twickenham)
]

# Rugby World Cup 2027 (Australia, 1 Oct - 13 Nov 2027) — ante-post/futures betting.
# Pools confirmed at the December 2025 draw (verified 2026-06-30).
RWC_2027_POOLS = {
    'Pool A': ['Australia', 'New Zealand', 'Chile', 'Hong Kong China'],
    'Pool B': ['South Africa', 'Italy', 'Georgia', 'Romania'],
    'Pool C': ['Argentina', 'Fiji', 'Spain', 'Canada'],
    'Pool D': ['Ireland', 'Scotland', 'Uruguay', 'Portugal'],
    'Pool E': ['France', 'Japan', 'USA', 'Samoa'],
    'Pool F': ['England', 'Wales', 'Tonga', 'Zimbabwe'],
}
RWC_2027_DATES = {'start': '2027-10-01', 'end': '2027-11-13', 'host': 'Australia'}
RWC_2027_OUTRIGHT_FALLBACK = [
    {'name': 'New Zealand',  'odds': 3.5},
    {'name': 'South Africa', 'odds': 4.0},
    {'name': 'France',       'odds': 6.5},
    {'name': 'Ireland',      'odds': 6.5},
    {'name': 'Australia',    'odds': 7.5},
]
# Pool winner predictions — based on current world-class tier within each pool.
# Clearly the strongest side in 5 of 6 pools; Pool A (hosts AUS vs world #1 NZ)
# is genuinely the closest call.
# Storylines sourced from World Rugby's official draw analysis (verified 2026-06-30,
# rugbyworldcup.com/en/news/1019497/rwc-2027-draw-interesting-statistics).
RWC_2027_POOL_PREDICTIONS = {
    'Pool A': {
        'predicted_winner': 'New Zealand',
        'note': 'Tightest pool — hosts Australia face World Rugby #1-2 ranked rivals New Zealand in the pool stage for the first time ever at a World Cup.',
        'storyline': 'Australia v New Zealand — first-ever RWC pool meeting (last met in the 2015 final). Hong Kong China are pool debutants.',
    },
    'Pool B': {
        'predicted_winner': 'South Africa',
        'note': 'Defending champions, heavy favourites over Italy/Georgia/Romania.',
        'storyline': 'South Africa drawn in Pool B for the 3rd straight tournament — and have always had at least one European nation in their pool.',
    },
    'Pool C': {
        'predicted_winner': 'Argentina',
        'note': 'Clear gap over Fiji, Spain, Canada.',
        'storyline': "Argentina's first-ever World Cup meetings with both Spain and Canada. Australia face a South American pool rival for the 5th time (Argentina '91/'03, Uruguay '15/'19).",
    },
    'Pool D': {
        'predicted_winner': 'Ireland',
        'note': 'Top tier over Scotland, Uruguay, Portugal.',
        'storyline': 'Ireland v Scotland — 3rd consecutive World Cup pairing. Portugal v Uruguay meet at a Rugby World Cup for the first time ever.',
    },
    'Pool E': {
        'predicted_winner': 'France',
        'note': 'Strong favourites over Japan, USA, Samoa.',
        'storyline': 'Japan and Samoa drawn together for the 4th tournament running — Japan have won the last 3 meetings (USA won the first, back in 1987).',
    },
    'Pool F': {
        'predicted_winner': 'England',
        'note': 'Edge over Wales, with Tonga/Zimbabwe well below both.',
        'storyline': "Zimbabwe's first-ever World Cup matchup against a Pacific Islands nation (Tonga).",
    },
}

# Full Rugby World Cup history, 1987-2023 — scraped from Wikipedia (verified 2026-06-30).
# South Africa's 4 titles (most ever, incl. 2 in a row) is the headline context
# for why they're 2027 favourites alongside New Zealand.
RWC_HISTORY = [
    {'year': 1987, 'host': 'New Zealand & Australia', 'winner': 'New Zealand', 'runner_up': 'France'},
    {'year': 1991, 'host': 'England, France, Ireland, Scotland, Wales', 'winner': 'Australia', 'runner_up': 'England'},
    {'year': 1995, 'host': 'South Africa', 'winner': 'South Africa', 'runner_up': 'New Zealand'},
    {'year': 1999, 'host': 'Wales', 'winner': 'Australia', 'runner_up': 'France'},
    {'year': 2003, 'host': 'Australia', 'winner': 'England', 'runner_up': 'Australia'},
    {'year': 2007, 'host': 'France', 'winner': 'South Africa', 'runner_up': 'England'},
    {'year': 2011, 'host': 'New Zealand', 'winner': 'New Zealand', 'runner_up': 'France'},
    {'year': 2015, 'host': 'England', 'winner': 'New Zealand', 'runner_up': 'Australia'},
    {'year': 2019, 'host': 'Japan', 'winner': 'South Africa', 'runner_up': 'England'},
    {'year': 2023, 'host': 'France', 'winner': 'South Africa', 'runner_up': 'New Zealand'},
]
RWC_TITLE_COUNTS = [
    {'team': 'South Africa', 'titles': 4, 'years': [1995, 2007, 2019, 2023]},
    {'team': 'New Zealand',  'titles': 3, 'years': [1987, 2011, 2015]},
    {'team': 'Australia',    'titles': 2, 'years': [1991, 1999]},
    {'team': 'England',      'titles': 1, 'years': [2003]},
]

# Nations Championship is brand new (no prior history) — show context from the
# competitions it effectively succeeds: the Six Nations (just completed, March
# 2026) and the Rugby Championship (Southern Hemisphere equivalent, 2025).
SIX_NATIONS_2026 = {
    'name': 'Six Nations 2026',
    'winner': 'France',
    'note': "Second successive title — beat England 48-46 in a final-day decider on a Thomas Ramos penalty. No Grand Slam; France's only loss was to Scotland.",
}
RUGBY_CHAMPIONSHIP_2025 = {
    'name': 'Rugby Championship 2025',
    'winner': 'South Africa',
    'note': 'Beat Argentina 29-27 in the final round to retain the title — their 6th Rugby Championship/Tri Nations crown.',
}


def _to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(round(obj, 3)))
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    return obj


# ── BBC Sport scrape ─────────────────────────────────────────────────────────

def fetch_bbc_results_for_date(date_str):
    """
    Fetch BBC Sport rugby-union results for a given date (YYYY-MM-DD).
    Returns list of {home, away, home_score, away_score, status, tournament}.
    """
    url = f'https://www.bbc.co.uk/sport/rugby-union/scores-fixtures/{date_str}'
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return []
        html = resp.text
    except Exception as e:
        print(f'[rugby_scraper] BBC fetch failed for {date_str}: {e}')
        return []

    m = re.search(r'window\.__INITIAL_DATA__\s*=\s*"(.+?)";\s*</script>', html, re.DOTALL)
    if not m:
        return []
    try:
        decoded = json.loads('"' + m.group(1) + '"')
        data = json.loads(decoded)
    except Exception as e:
        print(f'[rugby_scraper] BBC JSON parse failed for {date_str}: {e}')
        return []

    key = next((k for k in data.get('data', {}).keys() if k.startswith('sport-data-scores-fixtures')), None)
    if not key:
        return []
    fixtures_data = data['data'][key].get('data', {})

    matches = []
    for group in fixtures_data.get('eventGroups', []):
        for sg in group.get('secondaryGroups', []):
            for ev in sg.get('events', []):
                home = ev.get('home', {})
                away = ev.get('away', {})

                # Try scorers (home/away), from groupedActions "Tries" entry
                home_tries, away_tries = [], []
                for ga in ev.get('groupedActions', []):
                    if ga.get('groupName', {}).get('fullName') == 'Tries':
                        home_tries = ga.get('homeTeamActions', [])
                        away_tries = ga.get('awayTeamActions', [])
                        break

                matches.append({
                    'home': home.get('fullName', ''),
                    'away': away.get('fullName', ''),
                    'home_score': home.get('score', ''),
                    'away_score': away.get('score', ''),
                    'status': ev.get('status', ''),
                    'tournament': ev.get('tournament', {}).get('name', ''),
                    'venue': ev.get('venue', {}).get('name', ''),
                    'home_tries': home_tries,
                    'away_tries': away_tries,
                })
    return matches


def fetch_all_available_results(today):
    """For each fixture whose date has passed, find its result from BBC Sport."""
    results = []
    dates_needed = sorted(set(f['date'] for f in FIXTURES if f['date'] <= today))
    bbc_cache = {}
    for d in dates_needed:
        bbc_cache[d] = fetch_bbc_results_for_date(d)

    for fixture in FIXTURES:
        if fixture['date'] > today:
            continue
        day_matches = bbc_cache.get(fixture['date'], [])
        for m in day_matches:
            if (fixture['home'].lower() in m['home'].lower() or m['home'].lower() in fixture['home'].lower()) and \
               (fixture['away'].lower() in m['away'].lower() or m['away'].lower() in fixture['away'].lower()):
                if m['status'] == 'PostEvent' and m['home_score'] and m['away_score']:
                    results.append({
                        'round': fixture['round'],
                        'date': fixture['date'],
                        'home': fixture['home'],
                        'away': fixture['away'],
                        'home_score': m['home_score'],
                        'away_score': m['away_score'],
                        'winner': fixture['home'] if int(m['home_score']) > int(m['away_score']) else (
                                  fixture['away'] if int(m['away_score']) > int(m['home_score']) else 'Draw'),
                        'venue': m.get('venue', ''),
                        'home_tries': m.get('home_tries', []),
                        'away_tries': m.get('away_tries', []),
                    })
                break
    return results


# ── Form analysis & predictions ─────────────────────────────────────────────

# Fallback strength tier (1=strongest) when live Betfair odds aren't available.
# Based on: Six Nations 2026 final standings (France won, beat England in a
# decider), Rugby Championship 2025 standings (South Africa won, NZ 2nd,
# Australia 3rd), and general current World Rugby form.
STRENGTH_TIER = {
    'South Africa': 1, 'New Zealand': 2, 'France': 3, 'Ireland': 4,
    'England': 5, 'Argentina': 6, 'Australia': 7, 'Scotland': 8,
    'Wales': 9, 'Fiji': 10, 'Italy': 11, 'Japan': 12,
}


# Real Six Nations 2026 top try-scorer (verified) — used as a "key player to
# watch" note for matches involving France, rather than a guessed first-try pick.
KEY_TRY_SCORER = {
    # NOTE: Bielle-Biarrey RESTED for Nations Championship (not selected).
    # Penaud recalled — France's all-time leading try scorer, right wing.
    # Dupont also unavailable (Toulouse/Montpellier Top 14 final clash).
    'France': {'player': 'Damian Penaud', 'note': "France's all-time leading try scorer — recalled to Nations Championship squad. Bielle-Biarrey rested, Dupont unavailable."},
}


def _margin_band(tier_gap):
    """Translate a strength-tier gap into a realistic winning-margin range — not a fake exact score."""
    if tier_gap <= 1:
        return '1-8 pts (tight)'
    elif tier_gap <= 3:
        return '9-15 pts'
    elif tier_gap <= 6:
        return '16-24 pts'
    return '25+ pts'


def generate_tips(fixtures, results, outright_odds):
    """
    Predict each fixture's winner using live Betfair outright odds where
    available (lower odds = stronger team), falling back to STRENGTH_TIER
    (built from real recent results: Six Nations 2026 + Rugby Championship
    2025 standings) when odds aren't available for a team.
    Also estimates a realistic winning-margin band (not a fabricated exact
    score) and flags a real key try-scorer where we have verified data.
    """
    odds_map = {o['name']: o['odds'] for o in outright_odds} if outright_odds else {}
    completed_pairs = {(r['home'], r['away']) for r in results}

    predictions = []
    for f in fixtures:
        if (f['home'], f['away']) in completed_pairs:
            continue   # already played — no prediction needed

        home_odds = odds_map.get(f['home'])
        away_odds = odds_map.get(f['away'])
        home_tier = STRENGTH_TIER.get(f['home'], 13)
        away_tier = STRENGTH_TIER.get(f['away'], 13)

        if home_odds and away_odds:
            favourite = f['home'] if home_odds < away_odds else f['away']
            reason = f'Shorter outright odds ({fmt_frac_simple(min(home_odds, away_odds))}) to win the whole competition'
        else:
            if home_tier == away_tier:
                continue
            favourite = f['home'] if home_tier < away_tier else f['away']
            reason = 'Stronger recent form (Six Nations / Rugby Championship 2025-26 results)'

        margin = _margin_band(abs(home_tier - away_tier))
        key_scorer = KEY_TRY_SCORER.get(f['home']) or KEY_TRY_SCORER.get(f['away'])

        predictions.append({
            'round': f['round'],
            'date': f['date'],
            'home': f['home'],
            'away': f['away'],
            'venue': f.get('venue', ''),
            'predicted_winner': favourite,
            'reason': reason,
            'predicted_margin': margin,
            'key_try_scorer': key_scorer,
        })

    return {'predictions': predictions[:18]}


def fmt_frac_simple(decimal_odds):
    if not decimal_odds or decimal_odds <= 1:
        return '-'
    n = round((decimal_odds - 1) * 4)
    return f'{n}/4' if n else 'evens'


# ── Betfair outright winner market ──────────────────────────────────────────

def _fetch_betfair_outright_market(text_query):
    """Fetch top 5 contenders for a rugby outright WINNER market matching text_query."""
    try:
        from betfair_odds_fetcher import get_betfair_session
        app_key, session_token = get_betfair_session()
    except Exception as e:
        print(f'[rugby_scraper] Betfair auth failed: {e}')
        return []

    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    catalogue_req = {
        'filter': {
            'eventTypeIds': ['5'],   # Rugby Union on Betfair
            'textQuery': text_query,
            'marketTypeCodes': ['WINNER'],
        },
        'maxResults': 10,
        'marketProjection': ['RUNNER_DESCRIPTION', 'EVENT', 'MARKET_DESCRIPTION'],
    }
    try:
        resp = requests.post(
            'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/',
            json=catalogue_req, headers=headers, timeout=20)
        resp.raise_for_status()
        markets = resp.json()
    except Exception as e:
        print(f'[rugby_scraper] Betfair catalogue fetch failed for "{text_query}": {e}')
        return []

    if not markets:
        print(f'[rugby_scraper] No Betfair outright market found for "{text_query}"')
        return []

    target_market = markets[0]
    market_id = target_market['marketId']
    runner_names = {r['selectionId']: r.get('runnerName', '') for r in target_market.get('runners', [])}

    try:
        book_resp = requests.post(
            'https://api.betfair.com/exchange/betting/rest/v1.0/listMarketBook/',
            json={'marketIds': [market_id], 'priceProjection': {'priceData': ['EX_BEST_OFFERS']}},
            headers=headers, timeout=20)
        book_resp.raise_for_status()
        books = book_resp.json()
    except Exception as e:
        print(f'[rugby_scraper] Betfair odds fetch failed for "{text_query}": {e}')
        return []

    if not books:
        return []

    runners_odds = []
    for r in books[0].get('runners', []):
        sel_id = r.get('selectionId')
        avail = r.get('ex', {}).get('availableToBack', [])
        best_price = avail[0]['price'] if avail else None
        if best_price:
            runners_odds.append({'name': runner_names.get(sel_id, 'Unknown'), 'odds': best_price})

    runners_odds.sort(key=lambda x: x['odds'])
    return runners_odds[:5]


def fetch_betfair_outright():
    """Fetch top 5 contenders for the Nations Championship outright WINNER market."""
    return _fetch_betfair_outright_market('Nations Championship')


def fetch_rwc_2027_outright():
    """Fetch top 5 contenders for the Rugby World Cup 2027 outright WINNER market."""
    return _fetch_betfair_outright_market('Rugby World Cup 2027')


# ── Main handler ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    now_iso = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    print(f'[rugby_scraper] Starting daily scrape at {now_iso}')

    is_live = TOURNAMENT_START <= today <= TOURNAMENT_END
    outright = fetch_betfair_outright()
    rwc_outright = fetch_rwc_2027_outright()
    results = fetch_all_available_results(today) if today >= TOURNAMENT_START else []
    tips = generate_tips(FIXTURES, results, outright)

    try:
        sports_table.put_item(Item=_to_decimal({
            'sport': 'rugby',
            'data_key': 'FIXTURES',
            'fixtures': FIXTURES,
            'updated_at': now_iso,
        }))

        sports_table.put_item(Item=_to_decimal({
            'sport': 'rugby',
            'data_key': 'RWC_2027',
            'pools': RWC_2027_POOLS,
            'dates': RWC_2027_DATES,
            'pool_predictions': RWC_2027_POOL_PREDICTIONS,
            'outright': rwc_outright if rwc_outright else RWC_2027_OUTRIGHT_FALLBACK,
            'outright_is_live': bool(rwc_outright),
            'history': RWC_HISTORY,
            'title_counts': RWC_TITLE_COUNTS,
            'updated_at': now_iso,
        }))
        print(f'[rugby_scraper] Saved RWC 2027 data, outright live={bool(rwc_outright)}')

        sports_table.put_item(Item=_to_decimal({
            'sport': 'rugby',
            'data_key': 'TIPS',
            'predictions': tips['predictions'],
            'updated_at': now_iso,
        }))
        print(f'[rugby_scraper] Saved {len(tips["predictions"])} predictions')

        sports_table.put_item(Item=_to_decimal({
            'sport': 'rugby',
            'data_key': 'HISTORY',
            'six_nations_2026': SIX_NATIONS_2026,
            'rugby_championship_2025': RUGBY_CHAMPIONSHIP_2025,
            'updated_at': now_iso,
        }))

        if results:
            sports_table.put_item(Item=_to_decimal({
                'sport': 'rugby',
                'data_key': 'RESULTS',
                'results': results,
                'updated_at': now_iso,
            }))
            print(f'[rugby_scraper] Saved {len(results)} match results')

        if outright:
            sports_table.put_item(Item=_to_decimal({
                'sport': 'rugby',
                'data_key': 'OUTRIGHT',
                'contenders': outright,
                'updated_at': now_iso,
            }))
            print(f'[rugby_scraper] Saved outright: {outright}')

        sports_table.put_item(Item=_to_decimal({
            'sport': 'rugby',
            'data_key': 'META',
            'tournament_start': TOURNAMENT_START,
            'tournament_end': TOURNAMENT_END,
            'updated_at': now_iso,
            'is_live': is_live,
            'matches_completed': len(results),
            'matches_total': len(FIXTURES),
        }))
    except Exception as e:
        print(f'[rugby_scraper] DynamoDB write error: {e}')
        return {'statusCode': 500, 'body': json.dumps({'success': False, 'error': str(e)})}

    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'results_scraped': len(results),
            'outright_count': len(outright),
            'is_live': is_live,
            'updated_at': now_iso,
        })
    }


if __name__ == '__main__':
    print(json.dumps(lambda_handler({}, None), indent=2))

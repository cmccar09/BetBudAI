"""
nfl_scraper.py — NFL data scraper Lambda.

Runs once daily and writes to DynamoDB:

  1. ESPN NFL API — teams, standings, scoreboard (live games Sep–Feb)
  2. Betfair Exchange — Super Bowl outright futures

Storage: BetBudAI_Sports table
  PK 'sport' = 'nfl'
  SK 'data_key':
    'TEAMS'            — all 32 NFL franchises with conference/division
    'STANDINGS'        — current season standings by conference
    'SUPERBOWL_FUTURES'— top 10 Super Bowl winner contenders with Betfair odds
    'SCOREBOARD'       — today's games (live during season; empty offseason)
    'HISTORY'          — last 5 Super Bowl winners
    'TIPS'             — BetBudAI pick and value signals
    'META'             — last_updated, season phase

Entry point: lambda_handler(event, context)
"""

import json
import boto3
import requests
from datetime import datetime, timezone, date
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
sports_table = dynamodb.Table('BetBudAI_Sports')

ESPN_BASE = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# Betfair market ID for Super Bowl LXI Winner (update each season)
BETFAIR_SB_MARKET = '1.179086500'

# Current season phase
SEASON_PHASE = 'offseason'  # 'preseason', 'regular', 'playoffs', 'offseason'

SUPERBOWL_HISTORY = [
    {'year': 2025, 'sb': 'LIX',   'winner': 'Philadelphia Eagles', 'defeated': 'Kansas City Chiefs', 'score': '40-22'},
    {'year': 2024, 'sb': 'LVIII', 'winner': 'Kansas City Chiefs',  'defeated': 'San Francisco 49ers', 'score': '25-22 OT'},
    {'year': 2023, 'sb': 'LVII',  'winner': 'Kansas City Chiefs',  'defeated': 'Philadelphia Eagles', 'score': '38-35'},
    {'year': 2022, 'sb': 'LVI',   'winner': 'Los Angeles Rams',    'defeated': 'Cincinnati Bengals',  'score': '23-20'},
    {'year': 2021, 'sb': 'LV',    'winner': 'Tampa Bay Buccaneers','defeated': 'Kansas City Chiefs',  'score': '31-9'},
]

FALLBACK_SUPERBOWL = [
    {'name': 'Philadelphia Eagles',     'odds': 7.0},
    {'name': 'San Francisco 49ers',     'odds': 7.5},
    {'name': 'Kansas City Chiefs',      'odds': 8.0},
    {'name': 'Detroit Lions',           'odds': 9.0},
    {'name': 'Baltimore Ravens',        'odds': 10.0},
    {'name': 'Dallas Cowboys',          'odds': 14.0},
    {'name': 'Miami Dolphins',          'odds': 16.0},
    {'name': 'Buffalo Bills',           'odds': 18.0},
    {'name': 'Cincinnati Bengals',      'odds': 20.0},
    {'name': 'Houston Texans',          'odds': 22.0},
]


def _to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(round(obj, 3)))
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    return obj


def _put(data_key, payload):
    sports_table.put_item(Item={
        'sport': 'nfl',
        'data_key': data_key,
        **_to_decimal(payload),
        'updated_at': datetime.now(timezone.utc).isoformat(),
    })


# ── ESPN scrapes ───────────────────────────────────────────────────────────────

def fetch_espn_standings():
    try:
        resp = requests.get(f'{ESPN_BASE}/standings', headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        conferences = []
        for conf in data.get('children', []):
            conf_name = conf.get('name', '')
            divisions = []
            for division in conf.get('children', []):
                div_name = division.get('name', '')
                entries = []
                for entry in division.get('standings', {}).get('entries', []):
                    team = entry.get('team', {})
                    stats = {s['name']: s.get('displayValue', '') for s in entry.get('stats', [])}
                    entries.append({
                        'team': team.get('displayName', ''),
                        'abbreviation': team.get('abbreviation', ''),
                        'wins': stats.get('wins', ''),
                        'losses': stats.get('losses', ''),
                        'pct': stats.get('winPercent', ''),
                        'division_record': stats.get('divisionRecord', ''),
                    })
                divisions.append({'division': div_name, 'teams': entries})
            conferences.append({'conference': conf_name, 'divisions': divisions})
        return conferences
    except Exception as e:
        print(f'[nfl] standings fetch failed: {e}')
        return []


def fetch_espn_teams():
    try:
        resp = requests.get(f'{ESPN_BASE}/teams', headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        teams = []
        for group in data.get('sports', [{}])[0].get('leagues', [{}])[0].get('teams', []):
            t = group.get('team', {})
            teams.append({
                'id': t.get('id'),
                'name': t.get('displayName'),
                'abbreviation': t.get('abbreviation'),
                'location': t.get('location'),
                'conference': t.get('conferenceId', ''),
                'color': t.get('color'),
                'logo': (t.get('logos') or [{}])[0].get('href', ''),
            })
        return teams
    except Exception as e:
        print(f'[nfl] teams fetch failed: {e}')
        return []


def fetch_espn_scoreboard():
    """Live games during season, empty payload offseason."""
    today = date.today().isoformat().replace('-', '')
    try:
        resp = requests.get(f'{ESPN_BASE}/scoreboard?dates={today}', headers=HEADERS, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        games = []
        for event in data.get('events', []):
            competitions = event.get('competitions', [{}])
            comp = competitions[0] if competitions else {}
            competitors = comp.get('competitors', [])
            home = next((c for c in competitors if c.get('homeAway') == 'home'), {})
            away = next((c for c in competitors if c.get('homeAway') == 'away'), {})
            games.append({
                'id': event.get('id'),
                'date': event.get('date', ''),
                'name': event.get('name', ''),
                'week': event.get('week', {}).get('text', ''),
                'status': comp.get('status', {}).get('type', {}).get('description', ''),
                'home': {
                    'team': home.get('team', {}).get('displayName', ''),
                    'score': home.get('score', '-'),
                    'record': home.get('records', [{}])[0].get('summary', '') if home.get('records') else '',
                },
                'away': {
                    'team': away.get('team', {}).get('displayName', ''),
                    'score': away.get('score', '-'),
                    'record': away.get('records', [{}])[0].get('summary', '') if away.get('records') else '',
                },
                'venue': comp.get('venue', {}).get('fullName', ''),
            })
        return games
    except Exception as e:
        print(f'[nfl] scoreboard fetch failed: {e}')
        return []


def fetch_betfair_superbowl():
    """Fetch Super Bowl outright odds from Betfair Exchange."""
    try:
        session = boto3.client('secretsmanager', region_name='eu-west-1')
        secret = json.loads(session.get_secret_value(SecretId='betfair-credentials')['SecretString'])
        headers = {
            'X-Authentication': secret.get('session_token', ''),
            'X-Application': secret.get('app_key', ''),
            'Content-Type': 'application/json',
        }
        payload = json.dumps([{
            'marketId': BETFAIR_SB_MARKET,
            'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
        }])
        resp = requests.post(
            'https://api.betfair.com/exchange/betting/json-rpc/v1',
            headers=headers,
            data=payload,
            timeout=10,
        )
        markets = resp.json()
        runners = markets[0].get('result', {}).get('runners', [])
        contenders = []
        for r in sorted(runners, key=lambda x: x.get('lastPriceTraded', 999)):
            best_back = (r.get('ex', {}).get('availableToBack') or [{}])[0].get('price', 0)
            if best_back > 1:
                contenders.append({
                    'name': r.get('runnerName', ''),
                    'odds': best_back,
                    'selection_id': r.get('selectionId'),
                })
        return contenders[:10] if contenders else FALLBACK_SUPERBOWL
    except Exception as e:
        print(f'[nfl] Betfair SB futures failed: {e}')
        return FALLBACK_SUPERBOWL


def generate_tips(futures, standings):
    if not futures:
        return {'pick': None, 'note': 'No futures data'}
    top = futures[0]
    value = [c for c in futures if c.get('odds', 0) >= 15.0]
    return {
        'championship_pick': top.get('name'),
        'championship_odds': top.get('odds'),
        'value_picks': value[:3],
        'season_phase': SEASON_PHASE,
        'note': (
            'NFL offseason: training camps open ~July 22. Pre-season games start August. '
            'Super Bowl futures are live year-round — early value before depth charts settle.'
        ) if SEASON_PHASE == 'offseason' else '',
    }


# ── Lambda handler ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    print('[nfl] scraper starting')
    now = datetime.now(timezone.utc).isoformat()

    standings = fetch_espn_standings()
    teams = fetch_espn_teams()
    scoreboard = fetch_espn_scoreboard()
    futures = fetch_betfair_superbowl()
    tips = generate_tips(futures, standings)

    _put('STANDINGS',         {'standings': standings})
    _put('TEAMS',             {'teams': teams})
    _put('SCOREBOARD',        {'games': scoreboard, 'date': date.today().isoformat()})
    _put('SUPERBOWL_FUTURES', {'contenders': futures})
    _put('HISTORY',           {'superbowl_history': SUPERBOWL_HISTORY})
    _put('TIPS',              tips)
    _put('META', {
        'last_updated': now,
        'season_phase': SEASON_PHASE,
        'teams_count': len(teams),
        'futures_count': len(futures),
        'games_today': len(scoreboard),
    })

    print(f'[nfl] done — {len(futures)} SB futures, {len(scoreboard)} games today')
    return {'statusCode': 200, 'sport': 'nfl', 'last_updated': now}

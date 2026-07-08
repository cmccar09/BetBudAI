"""
basketball_scraper.py — NBA data scraper Lambda.

Runs once daily (Step Functions / EventBridge) and writes to DynamoDB:

  1. ESPN NBA API — teams, standings, scoreboard (Summer League in July)
  2. Betfair Exchange — NBA championship outright futures

Storage: BetBudAI_Sports table
  PK 'sport' = 'basketball'
  SK 'data_key':
    'TEAMS'        — all 30 NBA franchises with conference/division
    'STANDINGS'    — current season standings by conference
    'OUTRIGHT'     — NBA championship futures (top 10 contenders)
    'SUMMER_LEAGUE'— Summer League scores (July only)
    'HISTORY'      — last 5 NBA champions
    'TIPS'         — BetBudAI pick and value signals
    'META'         — last_updated, season phase, current date

Entry point: lambda_handler(event, context)
"""

import json
import boto3
import requests
from datetime import datetime, timezone, date
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
sports_table = dynamodb.Table('BetBudAI_Sports')

ESPN_BASE = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# Betfair market ID for NBA Championship Winner (update each season)
BETFAIR_NBA_MARKET = '1.179086398'

# Current season phase (update as needed)
SEASON_PHASE = 'offseason'  # 'regular', 'playoffs', 'finals', 'offseason', 'summer_league'

PREVIOUS_CHAMPIONS = [
    {'year': 2024, 'winner': 'Boston Celtics',    'defeated': 'Dallas Mavericks', 'series': '4-1'},
    {'year': 2023, 'winner': 'Denver Nuggets',    'defeated': 'Miami Heat',       'series': '4-1'},
    {'year': 2022, 'winner': 'Golden State Warriors', 'defeated': 'Boston Celtics', 'series': '4-2'},
    {'year': 2021, 'winner': 'Milwaukee Bucks',   'defeated': 'Phoenix Suns',     'series': '4-2'},
    {'year': 2020, 'winner': 'Los Angeles Lakers','defeated': 'Miami Heat',        'series': '4-2'},
]

FALLBACK_OUTRIGHT = [
    {'name': 'Boston Celtics',        'odds': 4.0},
    {'name': 'Oklahoma City Thunder', 'odds': 5.0},
    {'name': 'Denver Nuggets',        'odds': 7.0},
    {'name': 'Golden State Warriors', 'odds': 9.0},
    {'name': 'Cleveland Cavaliers',   'odds': 10.0},
    {'name': 'New York Knicks',       'odds': 12.0},
    {'name': 'Minnesota Timberwolves','odds': 14.0},
    {'name': 'Los Angeles Lakers',    'odds': 18.0},
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
        'sport': 'basketball',
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
        for group in data.get('children', []):
            conf_name = group.get('name', '')
            entries = []
            for entry in group.get('standings', {}).get('entries', []):
                team = entry.get('team', {})
                stats = {s['name']: s.get('displayValue', '') for s in entry.get('stats', [])}
                entries.append({
                    'team': team.get('displayName', ''),
                    'abbreviation': team.get('abbreviation', ''),
                    'wins': stats.get('wins', ''),
                    'losses': stats.get('losses', ''),
                    'pct': stats.get('winPercent', ''),
                    'gb': stats.get('gamesBehind', ''),
                })
            conferences.append({'conference': conf_name, 'teams': entries})
        return conferences
    except Exception as e:
        print(f'[basketball] standings fetch failed: {e}')
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
                'color': t.get('color'),
                'logo': (t.get('logos') or [{}])[0].get('href', ''),
            })
        return teams
    except Exception as e:
        print(f'[basketball] teams fetch failed: {e}')
        return []


def fetch_summer_league_scores():
    """Summer League runs in July — fetch scoreboard for NBA Summer League."""
    today = date.today().isoformat().replace('-', '')
    try:
        url = f'{ESPN_BASE}/scoreboard?dates={today}&groups=7'  # group 7 = Summer League
        resp = requests.get(url, headers=HEADERS, timeout=10)
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
                'status': comp.get('status', {}).get('type', {}).get('description', ''),
                'home': {'team': home.get('team', {}).get('displayName', ''), 'score': home.get('score', '-')},
                'away': {'team': away.get('team', {}).get('displayName', ''), 'score': away.get('score', '-')},
            })
        return games
    except Exception as e:
        print(f'[basketball] summer league fetch failed: {e}')
        return []


def fetch_betfair_outright():
    """Fetch NBA Championship winner odds from Betfair Exchange."""
    try:
        session = boto3.client('secretsmanager', region_name='eu-west-1')
        secret = json.loads(session.get_secret_value(SecretId='betfair-credentials')['SecretString'])
        headers = {
            'X-Authentication': secret.get('session_token', ''),
            'X-Application': secret.get('app_key', ''),
            'Content-Type': 'application/json',
        }
        payload = json.dumps([{
            'marketId': BETFAIR_NBA_MARKET,
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
        return contenders[:10] if contenders else FALLBACK_OUTRIGHT
    except Exception as e:
        print(f'[basketball] Betfair outright failed: {e}')
        return FALLBACK_OUTRIGHT


def generate_tips(outright, standings):
    """Generate BetBudAI pick + value signals from outright and standings data."""
    if not outright:
        return {'pick': None, 'value': None, 'reasoning': 'No outright data available'}

    top = outright[0]
    value_picks = [c for c in outright if c.get('odds', 0) >= 10.0]

    tips = {
        'championship_pick': top.get('name'),
        'championship_odds': top.get('odds'),
        'value_picks': value_picks[:3],
        'season_phase': SEASON_PHASE,
        'note': (
            'NBA offseason: futures betting active. Training camps open late July. '
            'Summer League form is noise for regular season — focus on roster moves and odds drift.'
        ) if SEASON_PHASE == 'offseason' else '',
    }
    return tips


# ── Lambda handler ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    print('[basketball] scraper starting')
    now = datetime.now(timezone.utc).isoformat()

    standings = fetch_espn_standings()
    teams = fetch_espn_teams()
    summer_league = fetch_summer_league_scores()
    outright = fetch_betfair_outright()
    tips = generate_tips(outright, standings)

    _put('STANDINGS',     {'standings': standings})
    _put('TEAMS',         {'teams': teams})
    _put('SUMMER_LEAGUE', {'games': summer_league, 'date': date.today().isoformat()})
    _put('OUTRIGHT',      {'contenders': outright})
    _put('HISTORY',       {'previous_champions': PREVIOUS_CHAMPIONS})
    _put('TIPS',          tips)
    _put('META', {
        'last_updated': now,
        'season_phase': SEASON_PHASE,
        'teams_count': len(teams),
        'outright_count': len(outright),
        'summer_league_games': len(summer_league),
    })

    print(f'[basketball] done — {len(outright)} outright, {len(summer_league)} SL games')
    return {'statusCode': 200, 'sport': 'basketball', 'last_updated': now}

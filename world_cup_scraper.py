"""
world_cup_scraper.py — Daily World Cup 2026 data scraper Lambda.

Runs at 06:00 UTC daily as part of SureBet-Sports-DailyRefresh fan-out.
Scrapes ESPN's fifa.world API for match results, goal scorers (including
live Golden Boot tracking), and bracket progression. Includes fixed bracket
half analysis so BetBudAI can surface which teams have easier/harder routes.

Data stored in BetBudAI_Sports:
  PK 'worldcup'  SK 'RESULTS'    — all completed R32+ results with scorers
  PK 'worldcup'  SK 'BRACKET'    — bracket halves + progression analysis
  PK 'worldcup'  SK 'GOLDEN_BOOT'— top scorers with goal counts
  PK 'worldcup'  SK 'META'       — last_updated, stage, days since start
"""

import json
import re
import boto3
import requests
from datetime import datetime, timezone, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
sports_table = dynamodb.Table('BetBudAI_Sports')

ESPN_URL = 'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

TOURNAMENT_START = '2026-06-11'   # Group stage began (Mexico vs South Africa, June 11)
TOURNAMENT_END   = '2026-07-19'   # Final

# ── Fixed bracket structure ──────────────────────────────────────────────────
# Sourced: Sky Sports bracket analysis + ESPN bracket visualization (2026-07-01).
# The bracket is fixed — no redraw. Two halves feed separate semi-finals.
# Teams in the same half CANNOT meet before the final.

BRACKET_HALVES = {
    'half_1': {
        'label': 'Half 1 — France / Spain side',
        'description': (
            'France and Spain are on the same side of the bracket. '
            'If both progress as expected, they meet in a semi-final. '
            'France face Paraguay next (R16). Spain face Austria. '
            'This half is stronger on paper — France, Spain, Portugal, Belgium.'
        ),
        'teams': ['France', 'Spain', 'Portugal', 'Belgium', 'Norway', 'Paraguay',
                  'Morocco', 'Canada', 'Switzerland', 'Colombia', 'Mexico'],
    },
    'half_2': {
        'label': 'Half 2 — Argentina / England side',
        'description': (
            'Argentina and England are both through to the R16 from this half. '
            'ARGENTINA: face Egypt (R16, July 7) — straightforward. '
            'QF likely vs Switzerland or Colombia winner. Path to final is still '
            'the easier half of the draw. '
            'ENGLAND: beat Mexico 3-2, face Norway (QF) after Norway\'s shock win '
            'over Brazil. Norway are dangerous — Haaland-led counter-attacking side. '
            'BRAZIL OUT: Norway eliminated Brazil 2-1 (biggest upset of the tournament). '
            'This half no longer has the Brazil threat, making Argentina\'s route even clearer.'
        ),
        'teams': ['Argentina', 'England', 'Norway', 'Switzerland', 'Colombia',
                  'Egypt', 'Morocco', 'USA', 'Belgium'],
    },
}

BRACKET_ANALYSIS = {
    'headline': 'Argentina have the easier route to the final',
    'detail': (
        'The bracket draw gave Argentina the softer half — and it just got easier. '
        'Brazil were eliminated by Norway 2-1 (biggest upset of the tournament). '
        'Argentina\'s remaining path: Egypt (R16) → Colombia or Switzerland (QF) → '
        'England or Norway (SF). France\'s path: Morocco (QF) → Spain probable SF. '
        'Argentina face easier opponents at every stage before a likely final against France.'
    ),
    'mbappe_note': (
        'Mbappé: France beat Paraguay 1-0 (R16, Jul 4). '
        'France face Morocco in the QF (Jul 9). '
        'If Mbappé is fit and firing, France remain BetBud\'s strongest outright recommendation.'
    ),
    'betbud_top_bet': {
        'team': 'Argentina',
        'bet_type': 'World Cup Winner',
        'odds_fractional': '5/2',
        'odds_decimal': 3.5,
        'confidence': 'HIGH VALUE',
        'summary': '⭐ Argentina — BetBud\'s top pick for the 2026 World Cup. Messi leads Golden Boot.',
        'reasoning': (
            'Argentina are QF favourites with the clearest path to the final. '
            'Messi leads the Golden Boot with 8 goals. Their QF draw: Switzerland — '
            'who needed penalties to beat Colombia. Compare to France (vs Morocco) or '
            'England (vs Haaland/Norway). Argentina have the best player, easiest remaining '
            'draw, and 2022 tournament pedigree. BetBud recommendation: still strong value.'
        ),
        'key_stats': [
            'Messi 8 goals — Golden Boot leader, 1 ahead of Mbappé and Haaland',
            'QF vs Switzerland (beat Colombia on pens) — most winnable QF draw',
            'Brazil eliminated — easier half of draw confirmed',
            'Argentina beat Egypt 3-2 (close, showed resilience)',
            '2022 World Cup champions — know how to win under pressure',
        ],
        'forecast_final': 'Argentina vs France — rematch of the 2022 final',
    },
}


def _to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(round(obj, 3)))
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    return obj


def _clean_name(name):
    """Handle ESPN's occasional encoding issues."""
    if not name:
        return ''
    try:
        return name.encode('latin-1').decode('utf-8')
    except Exception:
        return name


# ── ESPN scrape ──────────────────────────────────────────────────────────────

def fetch_results_for_date(date_str):
    """
    Fetch match results + goal scorers for a given YYYYMMDD date string.
    Returns list of dicts with home/away/score/scorers.
    """
    try:
        resp = requests.get(ESPN_URL, params={'dates': date_str}, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f'[wc_scraper] ESPN fetch failed for {date_str}: {e}')
        return []

    results = []
    for event in data.get('events', []):
        for comp in event.get('competitions', []):
            status = comp.get('status', {}).get('type', {})
            if status.get('state') not in ('post', 'in'):
                continue   # skip scheduled matches

            competitors = comp.get('competitors', [])
            if len(competitors) != 2:
                continue
            home = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
            away = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])

            scorers = []
            for det in comp.get('details', []):
                if det.get('scoringPlay'):
                    for athlete in det.get('athletesInvolved', []):
                        scorers.append({
                            'name': _clean_name(athlete.get('displayName', '')),
                            'minute': det.get('clock', {}).get('displayValue', ''),
                            'team': home.get('team', {}).get('displayName', '') if
                                    det.get('team', {}).get('id') == home.get('team', {}).get('id') else
                                    away.get('team', {}).get('displayName', ''),
                        })

            result = {
                'date': date_str,
                'home': _clean_name(home.get('team', {}).get('displayName', '')),
                'away': _clean_name(away.get('team', {}).get('displayName', '')),
                'home_score': home.get('score', '0'),
                'away_score': away.get('score', '0'),
                'status': status.get('description', ''),
                'completed': status.get('completed', False),
                'winner': _clean_name(
                    home.get('team', {}).get('displayName', '') if home.get('winner') else
                    away.get('team', {}).get('displayName', '') if away.get('winner') else ''
                ),
                'scorers': scorers,
            }
            results.append(result)
    return results


def fetch_all_results(today):
    """Fetch results from tournament start to today."""
    start = datetime.strptime(TOURNAMENT_START, '%Y-%m-%d')
    end = datetime.strptime(today, '%Y-%m-%d')
    results = []
    current = start
    while current <= end:
        date_str = current.strftime('%Y%m%d')
        day_results = fetch_results_for_date(date_str)
        results.extend(day_results)
        current += timedelta(days=1)
    return [r for r in results if r['completed']]


def build_golden_boot(results):
    """Aggregate goal scorers across all results to build the Golden Boot table."""
    goals = {}
    for r in results:
        for s in r.get('scorers', []):
            name = s['name']
            if not name:
                continue
            if name not in goals:
                goals[name] = {'name': name, 'team': s['team'], 'goals': 0, 'matches': set()}
            goals[name]['goals'] += 1
            goals[name]['matches'].add(r['date'])

    leaderboard = []
    for name, data in goals.items():
        leaderboard.append({
            'name': name,
            'team': data['team'],
            'goals': data['goals'],
        })
    leaderboard.sort(key=lambda x: -x['goals'])
    return leaderboard[:20]


# ── Main handler ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    now_iso = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    print(f'[wc_scraper] Starting daily scrape at {now_iso}')

    is_live = TOURNAMENT_START <= today <= TOURNAMENT_END
    results = fetch_all_results(today) if is_live else []
    golden_boot = build_golden_boot(results)

    print(f'[wc_scraper] {len(results)} completed matches, {len(golden_boot)} scorers')

    # Update Mbappé note based on actual current goals
    mbappe_goals = next((p['goals'] for p in golden_boot if 'Mbapp' in p['name']), 0)
    updated_analysis = dict(BRACKET_ANALYSIS)
    if mbappe_goals:
        updated_analysis['mbappe_note'] = (
            f'Mbappé: {mbappe_goals} goals so far — joint Golden Boot leader. '
            f'Hit a brace vs Sweden (3-0, June 30) including a penalty at 45\' and '
            f'a third for France at 74\'. France face Paraguay in R16. '
            f'If fit, France remain BetBud\'s strongest outright recommendation.'
        )

    try:
        sports_table.put_item(Item=_to_decimal({
            'sport': 'worldcup',
            'data_key': 'RESULTS',
            'results': results,
            'updated_at': now_iso,
        }))
        sports_table.put_item(Item=_to_decimal({
            'sport': 'worldcup',
            'data_key': 'BRACKET',
            'halves': BRACKET_HALVES,
            'analysis': updated_analysis,
            'updated_at': now_iso,
        }))
        sports_table.put_item(Item=_to_decimal({
            'sport': 'worldcup',
            'data_key': 'GOLDEN_BOOT',
            'leaderboard': golden_boot,
            'updated_at': now_iso,
        }))
        sports_table.put_item(Item=_to_decimal({
            'sport': 'worldcup',
            'data_key': 'META',
            'tournament_start': TOURNAMENT_START,
            'tournament_end': TOURNAMENT_END,
            'is_live': is_live,
            'matches_completed': len(results),
            'updated_at': now_iso,
        }))
    except Exception as e:
        print(f'[wc_scraper] DynamoDB write error: {e}')
        return {'statusCode': 500, 'body': json.dumps({'success': False, 'error': str(e)})}

    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'matches_completed': len(results),
            'top_scorers': golden_boot[:5],
            'updated_at': now_iso,
        }, default=str)
    }


if __name__ == '__main__':
    print(json.dumps(lambda_handler({}, None), indent=2, default=str))

"""
gaa_scraper.py — Cork GAA club championship data scraper Lambda.

Covers Cork's club championships across both codes (hurling + football), all
grades. Unlike the other sport pages (ESPN/BBC APIs), there is no clean
structured API for county club GAA — the real sources are Cork GAA's own site
(gaacork.ie), Wikipedia's per-grade per-year pages (kept reasonably current
during the season), and local sports media (Echo Live / Irish Examiner,
HoganStand). This scraper therefore follows the same pattern as darts_scraper.py:
verified static seed data, manually refreshed against real sources, rather
than a live automated feed — DO NOT invent group draws, fixtures, or results
that haven't been confirmed against one of those sources.

Data verified 2026-07-27 against: gaacork.ie (Master Fixture Plan 2026,
published 2025-12-22 — https://gaacork.ie/2025/12/22/masterfixtureplan2026/),
Wikipedia (2026 Cork Premier Senior/Senior A/Premier Intermediate/
Intermediate A/Premier Junior Hurling/Football Championship pages), Echo
Live Cork Sport. The Master Fixture Plan is the authoritative source for
Round 1 dates — it superseded slightly different dates found in an earlier
pass (this scraper's dates below reflect the corrected Master Fixture Plan
figures, not the earlier estimate).

Storage: BetBudAI_Sports table
  PK 'sport' = 'gaa'
  SK 'data_key':
    'GRADES'   — full grade ladder both codes: clubs, divisions/colleges, sponsor, dates, status
    'PSHC'     — Premier Senior Hurling Championship detail (defending champion, stats)
    'PSFC'     — Premier Senior Football Championship detail (stats, top scorers)
    'TIPS'     — division-winner predictions, one per grade, honest about confidence
    'HISTORY'  — recent champions where verified
    'META'     — last_updated, season window

Entry point: lambda_handler(event, context) — invoked by Step Functions
(once added to the SureBet-Sports-DailyRefresh fan-out — see gaa-page.md skill).

NOTE ON ODDS: Cork club championships are NOT reliably covered by Betfair
Exchange or mainstream Irish bookmaker outright markets the way All-Ireland
inter-county competitions are. The Betfair fetch below is attempted (some
bookmakers occasionally run "County Championship winner" specials for
high-profile counties) but is expected to usually return nothing — tips here
are analysis-based (defending champion, current-season form, verified stats),
not odds-driven, and the frontend must make that distinction clear rather
than implying a live market exists when it doesn't.
"""

import json
import boto3
import requests
from datetime import datetime, timezone
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
sports_table = dynamodb.Table('BetBudAI_Sports')

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

SEASON_START = '2026-07-24'   # PSFC Championship Round 1 (Master Fixture Plan, gaacork.ie)
SEASON_END = '2026-10-31'     # finals typically played across October

# County League context (different competition from the Championship below —
# kept for reference since it's real verified data, per the Master Fixture Plan)
COUNTY_LEAGUES = {
    'football': {'name': 'McCarthy Insurance Group Football League', 'start': '2026-03-01', 'final': '2026-07-03 to 2026-07-05'},
    'hurling': {'name': 'RedFM Hurling League', 'start': '2026-03-08', 'final': '2026-07-10 to 2026-07-12'},
}

# ── Grade ladder — verified 2026-07-27 ───────────────────────────────────────
# Only grades with a confirmed 2026 Wikipedia/gaacork.ie page are listed.
# Football grades below Premier Intermediate (Intermediate A, Premier Junior,
# Junior A/B/C) were NOT independently confirmed for 2026 as of this scrape —
# marked 'status': 'unconfirmed' rather than guessed at.
GRADES = [
    {
        'code': 'hurling', 'grade': 'Premier Senior', 'key': 'PSHC',
        'clubs': 12, 'divisions_colleges': 6, 'sponsor': 'Co-Op Superstores',
        'start': '2026-07-31', 'end': '2026-10-31',
        'defending_champion': 'Sarsfields', 'status': 'confirmed',
    },
    {
        'code': 'hurling', 'grade': 'Senior A', 'key': 'SAHC',
        'clubs': 12, 'divisions_colleges': None, 'sponsor': None,
        'start': '2026-08-01', 'end': '2026-10-31',
        'defending_champion': None, 'status': 'confirmed_structure_only',
    },
    {
        'code': 'hurling', 'grade': 'Premier Intermediate', 'key': 'PIHC',
        'clubs': 12, 'divisions_colleges': None, 'sponsor': None,
        'start': '2026-08-01', 'end': '2026-10-31',
        'defending_champion': None, 'status': 'confirmed_structure_only',
    },
    {
        'code': 'hurling', 'grade': 'Intermediate A', 'key': 'IAHC',
        'clubs': 12, 'divisions_colleges': None, 'sponsor': None,
        'start': '2026-08-01', 'end': '2026-10-31',
        'defending_champion': None, 'status': 'confirmed_structure_only',
    },
    {
        'code': 'hurling', 'grade': 'Premier Junior', 'key': 'PJHC',
        'clubs': 12, 'divisions_colleges': None, 'sponsor': None,
        'start': '2026-08-01', 'end': '2026-10-31',
        'defending_champion': None, 'status': 'confirmed_structure_only',
    },
    {
        'code': 'football', 'grade': 'Premier Senior', 'key': 'PSFC',
        'clubs': 12, 'divisions_colleges': 10, 'sponsor': 'McCarthy Insurance Group',
        'start': '2026-07-24', 'end': '2026-10-31',
        'defending_champion': None, 'status': 'confirmed',
    },
    {
        'code': 'football', 'grade': 'Senior A', 'key': 'SAFC',
        'clubs': None, 'divisions_colleges': None, 'sponsor': None,
        'start': None, 'end': None,
        'defending_champion': None, 'status': 'confirmed_exists_details_tbc',
    },
    {
        'code': 'football', 'grade': 'Premier Intermediate', 'key': 'PIFC',
        'clubs': None, 'divisions_colleges': None, 'sponsor': None,
        'start': None, 'end': None,
        'defending_champion': None, 'status': 'confirmed_exists_details_tbc',
    },
]

# ── Premier Senior Football Championship — real 2026 detail (verified 2026-07-27) ──
PSFC_DETAIL = {
    'name': '2026 Cork Premier Senior Football Championship',
    'edition': '7th staging (138th county football championship overall)',
    'sponsor': 'McCarthy Insurance Group',
    'structure': '12 clubs + 8 divisional boards + 2 universities (UCC, MTU/CIT) — group stage then knockout',
    'draw_date': '2025-12-09',
    'window': '24 July – October 2026 (Championship Round 1 per Master Fixture Plan; separate McCarthy '
              'Insurance Group Football League ran March–early July, see league_context)',
    'stats_as_of': '2026-07-27 (4 group matches played — consistent with Round 1 having just been played '
                   'over the 24-26 July opening weekend)',
    'top_scorers': [
        {'player': 'Mark Lenahan', 'team': 'Avondhu (divisional)', 'tally': '2-12'},
        {'player': 'Ben Twomey', 'team': 'Avondhu (divisional)', 'tally': '3-07'},
    ],
    'note': 'Divisional sides (e.g. Avondhu, representing a rural district board rather than a single '
            'club) compete in the group series alongside the 12 senior clubs and the two universities, '
            'per long-standing Cork GAA tradition — they cannot win the county title itself.',
    'league_context': COUNTY_LEAGUES['football'],
}

# ── Premier Senior Hurling Championship — real 2026 detail (verified 2026-07-27) ──
PSHC_DETAIL = {
    'name': '2026 Cork Premier Senior Hurling Championship',
    'sponsor': 'Co-Op Superstores',
    'structure': '12 clubs + 6 divisional boards + 1 university — 21 teams total eligible across group/divisional sections',
    'draw_date': '2025-12-09',
    'window': '31 July – October 2026 (Championship Round 1 per Master Fixture Plan; separate RedFM '
              'Hurling League ran March–early July, see league_context)',
    'defending_champion': 'Sarsfields',
    'note': 'Sarsfields enter as defending champions from 2025.',
    'league_context': COUNTY_LEAGUES['hurling'],
}


def _to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(round(obj, 3)))
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    return obj


# ── Betfair outright attempt (expected to usually return nothing — see module docstring) ──

def _fetch_betfair_outright_market(text_query):
    try:
        from betfair_odds_fetcher import get_betfair_session
        app_key, session_token = get_betfair_session()
    except Exception as e:
        print(f'[gaa_scraper] Betfair auth failed: {e}')
        return []

    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    catalogue_req = {
        'filter': {'textQuery': text_query, 'marketTypeCodes': ['WINNER']},
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
        print(f'[gaa_scraper] Betfair catalogue fetch failed for "{text_query}": {e}')
        return []

    if not markets:
        print(f'[gaa_scraper] No Betfair outright market found for "{text_query}" (expected — see module docstring)')
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
        print(f'[gaa_scraper] Betfair odds fetch failed for "{text_query}": {e}')
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


# ── Tips — honest about confidence level per grade ──────────────────────────

def generate_tips():
    """
    One prediction per grade. PSHC/PSFC get a reasoned pick from verified
    data (defending champion / early stats). Every other grade is marked
    'insufficient public data' rather than guessing — group draws and form
    for the lower grades aren't reliably available without a manual check
    against gaacork.ie, and this project's rule is never to fabricate a pick
    dressed up as analysis.
    """
    tips = []
    for g in GRADES:
        if g['key'] == 'PSHC':
            tips.append({
                'code': 'hurling', 'grade': 'Premier Senior', 'key': 'PSHC',
                'predicted_winner': 'Sarsfields',
                'reason': 'Defending champions (2025) — strongest verified signal available pre-group-stage.',
                'confidence': 'low-medium — based on defending-champion status only, group draw/form not yet factored in',
            })
        elif g['key'] == 'PSFC':
            tips.append({
                'code': 'football', 'grade': 'Premier Senior', 'key': 'PSFC',
                'predicted_winner': None,
                'reason': 'No defending-champion or standings data strong enough yet for a real pick — '
                          'early individual stats (Avondhu\'s Lenahan/Twomey) reflect a divisional side, '
                          'which cannot win the county title itself.',
                'confidence': 'insufficient data for a confident tip',
            })
        else:
            tips.append({
                'code': g['code'], 'grade': g['grade'], 'key': g['key'],
                'predicted_winner': None,
                'reason': 'Group draw / current form not independently verified for this grade — check gaacork.ie directly.',
                'confidence': 'insufficient data for a confident tip',
            })
    return tips


# ── Main handler ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    now_iso = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    print(f'[gaa_scraper] Starting scrape at {now_iso}')

    is_live = SEASON_START <= today <= SEASON_END
    outright_psfc = _fetch_betfair_outright_market('Cork Senior Football Championship')
    outright_pshc = _fetch_betfair_outright_market('Cork Senior Hurling Championship')
    tips = generate_tips()

    try:
        sports_table.put_item(Item=_to_decimal({
            'sport': 'gaa', 'data_key': 'GRADES', 'grades': GRADES, 'updated_at': now_iso,
        }))
        sports_table.put_item(Item=_to_decimal({
            'sport': 'gaa', 'data_key': 'PSFC', **PSFC_DETAIL,
            'outright': outright_psfc, 'outright_is_live': bool(outright_psfc),
            'updated_at': now_iso,
        }))
        sports_table.put_item(Item=_to_decimal({
            'sport': 'gaa', 'data_key': 'PSHC', **PSHC_DETAIL,
            'outright': outright_pshc, 'outright_is_live': bool(outright_pshc),
            'updated_at': now_iso,
        }))
        sports_table.put_item(Item=_to_decimal({
            'sport': 'gaa', 'data_key': 'TIPS', 'tips': tips, 'updated_at': now_iso,
        }))
        sports_table.put_item(Item=_to_decimal({
            'sport': 'gaa', 'data_key': 'META',
            'season_start': SEASON_START, 'season_end': SEASON_END,
            'is_live': is_live, 'updated_at': now_iso,
            'grades_confirmed': sum(1 for g in GRADES if g['status'] == 'confirmed'),
            'grades_total': len(GRADES),
        }))
        print(f'[gaa_scraper] Saved GAA data — {len(GRADES)} grades, outright PSFC={bool(outright_psfc)}, PSHC={bool(outright_pshc)}')
    except Exception as e:
        print(f'[gaa_scraper] DynamoDB write error: {e}')
        return {'statusCode': 500, 'body': json.dumps({'success': False, 'error': str(e)})}

    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'grades_saved': len(GRADES),
            'is_live': is_live,
            'updated_at': now_iso,
        })
    }


if __name__ == '__main__':
    print(json.dumps(lambda_handler({}, None), indent=2))

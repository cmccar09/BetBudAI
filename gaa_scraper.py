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

PSHC/PSFC results, fixtures and standings refreshed 2026-09-07 against the
live Wikipedia pages for each championship (URLs in the RESULTS section
below), cross-checked with a news search for the PSHC quarter-final draw
(no contradicting source found). Only PSHC/PSFC have real results/fixtures
data — the lower grades (Senior A, Premier Intermediate, etc.) remain
structure-only per the GRADES 'status' field; do not backfill their
results/fixtures without an actual source, same rule as everything else here.

Storage: BetBudAI_Sports table
  PK 'sport' = 'gaa'
  SK 'data_key':
    'GRADES'    — full grade ladder both codes: clubs, divisions/colleges, sponsor, dates, status
    'PSHC'      — Premier Senior Hurling Championship detail (defending champion, stats)
    'PSFC'      — Premier Senior Football Championship detail (stats, top scorers)
    'RESULTS'   — {'hurling': [...], 'football': [...]} — completed match results, PSHC/PSFC only
    'FIXTURES'  — {'hurling': [...], 'football': [...]} — upcoming/knockout fixtures, PSHC/PSFC only
    'STANDINGS' — {'hurling': {...}, 'football': {...}} — group tables, PSHC/PSFC only
    'TIPS'      — division-winner predictions, one per grade, honest about confidence
    'HISTORY'   — recent champions where verified
    'META'      — last_updated, season window

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

# ── Premier Senior Football Championship — real 2026 detail (verified 2026-07-27, results/fixtures refreshed 2026-09-07) ──
PSFC_DETAIL = {
    'name': '2026 Cork Premier Senior Football Championship',
    'edition': '7th staging (138th county football championship overall)',
    'sponsor': 'McCarthy Insurance Group',
    'structure': '12 clubs + 8 divisional boards + 2 universities (UCC, MTU/CIT) — group stage then knockout',
    'draw_date': '2025-12-09',
    'window': '24 July – October 2026 (Championship Round 1 per Master Fixture Plan; separate McCarthy '
              'Insurance Group Football League ran March–early July, see league_context)',
    'stats_as_of': '2026-09-07 (Round 2 complete in all 3 club groups, Round 3 scheduled 13 Sept; '
                   'divisional section finished — Carbery through to preliminary QF)',
    'top_scorers': [
        {'player': 'Mark Lenahan', 'team': 'Avondhu (divisional)', 'tally': '3-14'},
    ],
    'note': 'Divisional sides (e.g. Avondhu, representing a rural district board rather than a single '
            'club) compete in the group series alongside the 12 senior clubs and the two universities, '
            'per long-standing Cork GAA tradition — they cannot win the county title itself.',
    'league_context': COUNTY_LEAGUES['football'],
}

# ── PSFC results + fixtures — Source: Wikipedia "2026 Cork Premier Senior
# Football Championship" (https://en.wikipedia.org/wiki/2026_Cork_Premier_Senior_Football_Championship).
# Verified 2026-09-07. Divisional section (Seandún/Avondhu/MTU Cork/Imokilly/
# Beara/Duhallow/Carbery/Muskerry/UCC) is a separate qualifying competition
# that feeds one team (Carbery, as Division champions) into the club knockout —
# included here for completeness, not part of the 12-club group table.
PSFC_RESULTS = [
    # Group 1
    {'group': 'Group 1', 'round': 1, 'date': '2026-07-24', 'home': "St Finbarr's", 'home_score': '2-15', 'away': 'Carrigaline', 'away_score': '1-20'},
    {'group': 'Group 1', 'round': 1, 'date': '2026-07-25', 'home': 'Mallow', 'home_score': '0-14', 'away': 'Douglas', 'away_score': '4-10'},
    {'group': 'Group 1', 'round': 2, 'date': '2026-08-14', 'home': 'Douglas', 'home_score': '1-11', 'away': "St Finbarr's", 'away_score': '3-16'},
    {'group': 'Group 1', 'round': 2, 'date': '2026-08-16', 'home': 'Carrigaline', 'home_score': '0-16', 'away': 'Mallow', 'away_score': '0-14'},
    # Group 2
    {'group': 'Group 2', 'round': 1, 'date': '2026-07-25', 'home': 'Newcestown', 'home_score': '2-16', 'away': 'Nemo Rangers', 'away_score': '1-13'},
    {'group': 'Group 2', 'round': 1, 'date': '2026-07-26', 'home': "St Michael's", 'home_score': '1-05', 'away': 'Valley Rovers', 'away_score': '1-07'},
    {'group': 'Group 2', 'round': 2, 'date': '2026-08-15', 'home': 'Valley Rovers', 'home_score': '1-16', 'away': 'Newcestown', 'away_score': '3-09'},
    {'group': 'Group 2', 'round': 2, 'date': '2026-08-16', 'home': 'Nemo Rangers', 'home_score': '1-21', 'away': "St Michael's", 'away_score': '2-10'},
    # Group 3
    {'group': 'Group 3', 'round': 1, 'date': '2026-07-25', 'home': 'Knocknagree', 'home_score': '0-13', 'away': 'Clonakilty', 'away_score': '1-18'},
    {'group': 'Group 3', 'round': 1, 'date': '2026-07-26', 'home': 'Castlehaven', 'home_score': '0-22', 'away': 'Ballincollig', 'away_score': '3-10'},
    {'group': 'Group 3', 'round': 2, 'date': '2026-08-16', 'home': 'Clonakilty', 'home_score': '1-12', 'away': 'Castlehaven', 'away_score': '1-12', 'note': 'draw'},
    {'group': 'Group 3', 'round': 2, 'date': '2026-08-16', 'home': 'Ballincollig', 'home_score': '0-13', 'away': 'Knocknagree', 'away_score': '2-18'},
    # Divisional section (feeds Division champion into the club knockout)
    {'group': 'Divisional', 'round': 1, 'date': '2026-04-07', 'home': 'Seandún', 'home_score': '3-14', 'away': 'Avondhu', 'away_score': '3-17'},
    {'group': 'Divisional', 'round': 1, 'date': '2026-04-07', 'home': 'MTU Cork', 'home_score': '0-05', 'away': 'Imokilly', 'away_score': '0-16'},
    {'group': 'Divisional', 'round': 2, 'date': '2026-04-14', 'home': 'Beara', 'home_score': '1-07', 'away': 'Avondhu', 'away_score': '3-05'},
    {'group': 'Divisional', 'round': 3, 'date': '2026-04-21', 'home': 'Avondhu', 'home_score': '1-16', 'away': 'Imokilly', 'away_score': '1-06'},
    {'group': 'Divisional', 'round': 'Semi-final', 'date': '2026-06-30', 'home': 'Duhallow', 'home_score': '1-23', 'away': 'Carbery', 'away_score': '3-18'},
    {'group': 'Divisional', 'round': 'Semi-final', 'date': '2026-07-07', 'home': 'Avondhu', 'home_score': '3-12', 'away': 'Muskerry', 'away_score': '3-17'},
    {'group': 'Divisional', 'round': 'Final', 'date': '2026-07-10', 'home': 'Carbery', 'home_score': '2-23', 'away': 'Muskerry', 'away_score': '2-15'},
    {'group': 'Divisional', 'round': 'Preliminary QF', 'date': '2026-08-09', 'home': 'Carbery', 'home_score': None, 'away': 'UCC', 'away_score': None, 'note': 'Carbery won walkover'},
]

PSFC_STANDINGS = {
    'Group 1': [{'team': 'Carrigaline', 'pts': 4}, {'team': "St Finbarr's", 'pts': 2}, {'team': 'Douglas', 'pts': 2}, {'team': 'Mallow', 'pts': 0}],
    'Group 2': [{'team': 'Valley Rovers', 'pts': 4}, {'team': 'Newcestown', 'pts': 2}, {'team': 'Nemo Rangers', 'pts': 2}, {'team': "St Michael's", 'pts': 0}],
    'Group 3': [{'team': 'Clonakilty', 'pts': 3}, {'team': 'Castlehaven', 'pts': 3}, {'team': 'Knocknagree', 'pts': 2}, {'team': 'Ballincollig', 'pts': 0}],
}

PSFC_FIXTURES = [
    {'group': 'Group 1', 'round': 3, 'date': '2026-09-13', 'home': 'Carrigaline', 'away': 'Douglas'},
    {'group': 'Group 1', 'round': 3, 'date': '2026-09-13', 'home': "St Finbarr's", 'away': 'Mallow'},
    {'group': 'Group 2', 'round': 3, 'date': '2026-09-13', 'home': 'Nemo Rangers', 'away': 'Valley Rovers'},
    {'group': 'Group 2', 'round': 3, 'date': '2026-09-13', 'home': 'Newcestown', 'away': "St Michael's"},
    {'group': 'Group 3', 'round': 3, 'date': '2026-09-13', 'home': 'Ballincollig', 'away': 'Clonakilty'},
    {'group': 'Group 3', 'round': 3, 'date': '2026-09-13', 'home': 'Castlehaven', 'away': 'Knocknagree'},
    {'stage': 'Quarter-final', 'date': None, 'home': 'TBD', 'away': 'TBD', 'note': 'October — pairings depend on Round 3 group results, not yet determined'},
    {'stage': 'Semi-final', 'date': None, 'home': 'TBD', 'away': 'TBD'},
    {'stage': 'Final', 'date': None, 'home': 'TBD', 'away': 'TBD'},
]

# ── Premier Senior Hurling Championship — real 2026 detail (verified 2026-07-27, results/fixtures refreshed 2026-09-07) ──
PSHC_DETAIL = {
    'name': '2026 Cork Premier Senior Hurling Championship',
    'sponsor': 'Co-Op Superstores',
    'structure': '12 clubs + 6 divisional boards + 1 university — 21 teams total eligible across group/divisional sections',
    'draw_date': '2025-12-09',
    'window': '31 July – October 2026 (Championship Round 1 per Master Fixture Plan; separate RedFM '
              'Hurling League ran March–early July, see league_context)',
    'defending_champion': 'Sarsfields',
    'note': 'Sarsfields enter as defending champions from 2025 — through to the quarter-final after '
            'finishing level on points in Group 2 (see RESULTS/standings below).',
    'stats_as_of': '2026-09-07 (group stage complete, all 3 groups through Round 3; quarter-final draw made)',
    'top_scorer': {'player': 'Jack Leahy', 'tally': '3-17'},
    'league_context': COUNTY_LEAGUES['hurling'],
}

# ── PSHC results + fixtures — Source: Wikipedia "2026 Cork Premier Senior
# Hurling Championship" (https://en.wikipedia.org/wiki/2026_Cork_Premier_Senior_Hurling_Championship),
# cross-checked against a live news search for the quarter-final draw (no
# contradicting source found; QF pairings below reflect the single Wikipedia
# source, not independently reconfirmed pairing-by-pairing — flagged per this
# scraper's own "don't invent, don't oversell a single source" rule). Verified 2026-09-07.
PSHC_RESULTS = [
    # Group 1
    {'group': 'Group 1', 'round': 1, 'date': '2026-08-01', 'home': 'Kanturk', 'home_score': '3-25', 'away': "Fr O'Neill's", 'away_score': '2-15'},
    {'group': 'Group 1', 'round': 1, 'date': '2026-08-01', 'home': 'Blackrock', 'home_score': '1-22', 'away': 'Glen Rovers', 'away_score': '1-20'},
    {'group': 'Group 1', 'round': 2, 'date': '2026-08-23', 'home': "Fr O'Neill's", 'home_score': '2-23', 'away': 'Blackrock', 'away_score': '3-29'},
    {'group': 'Group 1', 'round': 2, 'date': '2026-08-23', 'home': 'Glen Rovers', 'home_score': '3-20', 'away': 'Kanturk', 'away_score': '1-24'},
    {'group': 'Group 1', 'round': 3, 'date': '2026-09-06', 'home': 'Blackrock', 'home_score': '2-16', 'away': 'Kanturk', 'away_score': '2-27'},
    {'group': 'Group 1', 'round': 3, 'date': '2026-09-06', 'home': 'Glen Rovers', 'home_score': '1-24', 'away': "Fr O'Neill's", 'away_score': '3-12'},
    # Group 2
    {'group': 'Group 2', 'round': 1, 'date': '2026-07-31', 'home': 'Douglas', 'home_score': '0-22', 'away': 'Newtownshandrum', 'away_score': '2-16'},
    {'group': 'Group 2', 'round': 1, 'date': '2026-08-01', 'home': 'Sarsfields', 'home_score': '0-19', 'away': 'Charleville', 'away_score': '0-21'},
    {'group': 'Group 2', 'round': 2, 'date': '2026-08-22', 'home': 'Newtownshandrum', 'home_score': '4-14', 'away': 'Sarsfields', 'away_score': '4-21'},
    {'group': 'Group 2', 'round': 2, 'date': '2026-08-22', 'home': 'Charleville', 'home_score': '0-19', 'away': 'Douglas', 'away_score': '0-14'},
    {'group': 'Group 2', 'round': 3, 'date': '2026-09-06', 'home': 'Douglas', 'home_score': '1-19', 'away': 'Sarsfields', 'away_score': '3-22'},
    {'group': 'Group 2', 'round': 3, 'date': '2026-09-06', 'home': 'Newtownshandrum', 'home_score': '1-21', 'away': 'Charleville', 'away_score': '1-17'},
    # Group 3
    {'group': 'Group 3', 'round': 1, 'date': '2026-07-31', 'home': 'Midleton', 'home_score': '0-25', 'away': "St Finbarr's", 'away_score': '0-17'},
    {'group': 'Group 3', 'round': 1, 'date': '2026-08-01', 'home': 'Bride Rovers', 'home_score': '1-20', 'away': 'Newcestown', 'away_score': '0-14'},
    {'group': 'Group 3', 'round': 2, 'date': '2026-08-22', 'home': 'Newcestown', 'home_score': '1-17', 'away': 'Midleton', 'away_score': '1-18'},
    {'group': 'Group 3', 'round': 2, 'date': '2026-08-22', 'home': "St Finbarr's", 'home_score': '3-21', 'away': 'Bride Rovers', 'away_score': '1-18'},
    {'group': 'Group 3', 'round': 3, 'date': '2026-09-06', 'home': 'Midleton', 'home_score': '2-15', 'away': 'Bride Rovers', 'away_score': '2-13'},
    # 1-18 = 21, 0-21 = 21 — a draw, not a St Finbarr's win. The Wikipedia
    # page's own "def." framing here was wrong (checked against Irish
    # Examiner: "Honours even between St Finbarr's and Newcestown" — a draw).
    {'group': 'Group 3', 'round': 3, 'date': '2026-09-06', 'home': "St Finbarr's", 'home_score': '1-18', 'away': 'Newcestown', 'away_score': '0-21', 'note': 'draw'},
    # Divisional/colleges section — winner (Imokilly) enters the club knockout at QF stage
    {'group': 'Divisional', 'round': 'Semi-final', 'date': '2026-08-05', 'home': 'UCC', 'home_score': '0-19', 'away': 'Imokilly', 'away_score': '4-26'},
    {'group': 'Divisional', 'round': 'Semi-final', 'date': '2026-08-09', 'home': 'Seandún', 'home_score': '1-30', 'away': 'Muskerry', 'away_score': '0-32', 'note': 'AET'},
    {'group': 'Divisional', 'round': 'Final', 'date': '2026-08-30', 'home': 'Imokilly', 'home_score': '3-22', 'away': 'Seandún', 'away_score': '1-18'},
]

PSHC_STANDINGS = {
    'Group 1': [{'team': 'Kanturk', 'pts': 4}, {'team': 'Glen Rovers', 'pts': 4}, {'team': 'Blackrock', 'pts': 4}, {'team': "Fr O'Neill's", 'pts': 0}],
    'Group 2': [{'team': 'Charleville', 'pts': 4}, {'team': 'Sarsfields', 'pts': 4}, {'team': 'Newtownshandrum', 'pts': 3}, {'team': 'Douglas', 'pts': 1}],
    'Group 3': [{'team': 'Midleton', 'pts': 6}, {'team': "St Finbarr's", 'pts': 3}, {'team': 'Bride Rovers', 'pts': 2}, {'team': 'Newcestown', 'pts': 1}],
}

PSHC_FIXTURES = [
    # Only 3 quarter-finals — Midleton (Group 3 winners, 6pts) go straight to a
    # semi-final per the source rather than playing a QF; do not invent a 4th
    # QF pairing to make the bracket "look" symmetric.
    {'stage': 'Relegation playoff', 'date': None, 'home': 'Douglas', 'away': "Fr O'Neill's"},
    {'stage': 'Quarter-final', 'date': None, 'home': 'Kanturk', 'away': 'Sarsfields'},
    {'stage': 'Quarter-final', 'date': None, 'home': 'Charleville', 'away': 'Glen Rovers'},
    {'stage': 'Quarter-final', 'date': None, 'home': "St Finbarr's", 'away': 'Imokilly'},
    {'stage': 'Semi-final', 'date': None, 'home': 'Midleton', 'away': 'TBD', 'note': 'vs winner of Kanturk/Sarsfields — Midleton have a direct semi-final berth as Group 3 winners'},
    {'stage': 'Semi-final', 'date': None, 'home': 'TBD', 'away': 'TBD', 'note': 'Winner of Charleville/Glen Rovers vs winner of St Finbarr\'s/Imokilly'},
    {'stage': 'Final', 'date': None, 'home': 'TBD', 'away': 'TBD'},
]


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
                'reason': 'Defending champions (2025), now confirmed through to the quarter-final '
                          '(v Kanturk) after finishing level on 4pts in Group 2 — stronger signal than '
                          'pre-season status alone, though Kanturk (also 4pts, +14 Group 1) are a live threat.',
                'confidence': 'medium — real group-stage form now factored in, still 3 rounds from the final',
            })
        elif g['key'] == 'PSFC':
            tips.append({
                'code': 'football', 'grade': 'Premier Senior', 'key': 'PSFC',
                'predicted_winner': None,
                'reason': 'Group stage not yet complete (Round 3 of 3 played 13 Sept) and no team has '
                          'separated enough from its group to justify a title pick — Carrigaline, Valley '
                          'Rovers, Clonakilty and Castlehaven all lead their groups but knockout draw '
                          'isn\'t set until Round 3 finishes.',
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
            'sport': 'gaa', 'data_key': 'RESULTS',
            'hurling': PSHC_RESULTS, 'football': PSFC_RESULTS,
            'updated_at': now_iso,
        }))
        sports_table.put_item(Item=_to_decimal({
            'sport': 'gaa', 'data_key': 'FIXTURES',
            'hurling': PSHC_FIXTURES, 'football': PSFC_FIXTURES,
            'updated_at': now_iso,
        }))
        sports_table.put_item(Item=_to_decimal({
            'sport': 'gaa', 'data_key': 'STANDINGS',
            'hurling': PSHC_STANDINGS, 'football': PSFC_STANDINGS,
            'updated_at': now_iso,
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

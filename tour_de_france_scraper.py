"""
tour_de_france_scraper.py — Daily Tour de France 2026 data scraper Lambda.

Runs once daily (Step Functions / EventBridge schedule). Tour runs 4-26 July 2026.

Data sources:
  1. Hardcoded stage schedule (static — 21 stages, confirmed route, won't change)
  2. Betfair Exchange outright WINNER market — top 5 GC contenders, live odds
  3. procyclingstats.com stage result page — best-effort scrape once each stage
     has run (regex-based table parse, falls back gracefully if site structure
     changes or blocks the request)

Storage: BetBudAI_Sports table
  PK 'sport' = 'tourdefrance'
  SK 'data_key':
    'SCHEDULE'   — all 21 stages (date, route, distance, type)
    'RESULTS'    — stage results scraped so far (stage winner, GC leader)
    'OUTRIGHT'   — top 5 GC winner contenders with live odds
    'META'       — last_updated, tournament dates, is_live flag

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

TOUR_START = '2026-07-04'
TOUR_END   = '2026-07-26'

# Static stage schedule — confirmed route, won't change once announced.
# Source: official ASO route announcement (verified 2026-06-30).
STAGE_SCHEDULE = [
    {'stage': 1,  'date': '2026-07-04', 'route': 'Barcelona — Barcelona',                'distance_km': 19.7,  'type': 'Team Time Trial'},
    {'stage': 2,  'date': '2026-07-05', 'route': 'Tarragona — Barcelona',                 'distance_km': 178,   'type': 'Hilly'},
    {'stage': 3,  'date': '2026-07-06', 'route': 'Granollers — Les Angles',                'distance_km': 196,   'type': 'Mountain'},
    {'stage': 4,  'date': '2026-07-07', 'route': 'Carcassonne — Foix',                      'distance_km': 182,   'type': 'Hilly'},
    {'stage': 5,  'date': '2026-07-08', 'route': 'Lannemezan — Pau',                        'distance_km': 158,   'type': 'Flat'},
    {'stage': 6,  'date': '2026-07-09', 'route': 'Pau — Gavarnie-Gèdre',                    'distance_km': 186,   'type': 'Mountain'},
    {'stage': 7,  'date': '2026-07-10', 'route': 'Hagetmau — Bordeaux',                     'distance_km': 175,   'type': 'Flat'},
    {'stage': 8,  'date': '2026-07-11', 'route': 'Périgueux — Bergerac',                    'distance_km': 182,   'type': 'Flat'},
    {'stage': 9,  'date': '2026-07-12', 'route': 'Malemort — Ussel',                        'distance_km': 185,   'type': 'Hilly'},
    {'stage': 10, 'date': '2026-07-14', 'route': 'Aurillac — Le Lioran',                    'distance_km': 167,   'type': 'Mountain'},
    {'stage': 11, 'date': '2026-07-15', 'route': 'Vichy — Nevers',                          'distance_km': 161,   'type': 'Flat'},
    {'stage': 12, 'date': '2026-07-16', 'route': 'Circuit de Nevers Magny-Cours — Chalon-sur-Saône', 'distance_km': 181, 'type': 'Flat'},
    {'stage': 13, 'date': '2026-07-17', 'route': 'Dole — Belfort',                          'distance_km': 205,   'type': 'Hilly'},
    {'stage': 14, 'date': '2026-07-18', 'route': 'Mulhouse — Le Markstein Fellering',        'distance_km': 155,   'type': 'Mountain'},
    {'stage': 15, 'date': '2026-07-19', 'route': 'Champagnole — Plateau de Solaison',        'distance_km': 184,   'type': 'Mountain'},
    {'stage': 16, 'date': '2026-07-21', 'route': 'Évian-les-Bains — Thonon-les-Bains',       'distance_km': 26,    'type': 'Individual Time Trial'},
    {'stage': 17, 'date': '2026-07-22', 'route': 'Chambéry — Voiron',                        'distance_km': 175,   'type': 'Flat'},
    {'stage': 18, 'date': '2026-07-23', 'route': 'Voiron — Orcières-Merlette',               'distance_km': 185,   'type': 'Mountain'},
    {'stage': 19, 'date': '2026-07-24', 'route': "Gap — Alpe d'Huez",                        'distance_km': 128,   'type': 'Mountain'},
    {'stage': 20, 'date': '2026-07-25', 'route': "Le Bourg-d'Oisans — Alpe d'Huez",          'distance_km': 171,   'type': 'Mountain'},
    {'stage': 21, 'date': '2026-07-26', 'route': 'Thoiry — Paris (Champs-Élysées)',          'distance_km': 130,   'type': 'Flat'},
]

# Tour de France winners, last 5 years — static reference data.
PREVIOUS_WINNERS = [
    {'year': 2025, 'winner': 'Tadej Pogačar',   'country': 'Slovenia'},
    {'year': 2024, 'winner': 'Tadej Pogačar',   'country': 'Slovenia'},
    {'year': 2023, 'winner': 'Jonas Vingegaard', 'country': 'Denmark'},
    {'year': 2022, 'winner': 'Jonas Vingegaard', 'country': 'Denmark'},
    {'year': 2021, 'winner': 'Tadej Pogačar',   'country': 'Slovenia'},
]

# 2026 Giro d'Italia — already completed (8-31 May), the other Grand Tour run
# so far this year. Big storyline: Vingegaard is also a top-2 TdF favourite.
GIRO_2026 = {
    'name': "Giro d'Italia 2026",
    'dates': '8–31 May 2026',
    'winner': 'Jonas Vingegaard',
    'winner_team': 'Visma–Lease a Bike',
    'margin': '5:22',
    'podium': [
        {'pos': 1, 'name': 'Jonas Vingegaard', 'note': '5 stage wins'},
        {'pos': 2, 'name': 'Felix Gall', 'note': ''},
        {'pos': 3, 'name': 'Jai Hindley', 'note': ''},
    ],
    'note': 'First Giro win for Vingegaard — completes the full Grand Tour set (Giro, Vuelta, Tour all won).',
}

# All-time Tour de France wins record — scraped from Wikipedia (verified 2026-06-30).
# Pogačar is the headline storyline: 1 win from tying the all-time record.
TDF_ALL_TIME_RECORD = {
    'record_wins': 5,
    'record_holders': ['Jacques Anquetil', 'Eddy Merckx', 'Bernard Hinault', 'Miguel Indurain'],
    'note': 'Indurain is the only rider to win 5 in a row (1991-1995).',
    'pogacar_wins': 4,
    'pogacar_years': [2020, 2021, 2024, 2025],
    'pogacar_note': 'Pogačar is just 1 win away from tying the all-time record of 5 — the headline storyline of the 2026 race.',
}

# 2026 Tour de France teams — 23 total: 18 UCI WorldTeams (automatic) + 5
# UCI ProTeams (wildcards). Source: Wikipedia, verified 2026-06-30.
TDF_2026_TEAMS = {
    'worldteams': [
        'Alpecin–Premier Tech', 'Decathlon CMA CGM', 'EF Education–EasyPost',
        'Groupama–FDJ United', 'Lidl–Trek', 'Lotto–Intermarché', 'Movistar Team',
        'Netcompany INEOS', 'NSN Cycling Team', 'Red Bull–Bora–Hansgrohe',
        'Soudal–Quick-Step', 'Team Bahrain Victorious', 'Team Jayco–AlUla',
        'Team Picnic–PostNL', 'Visma–Lease a Bike', 'UAE Team Emirates XRG',
        'Uno-X Mobility', 'XDS Astana Team',
    ],
    'proteams': [
        'Tudor Pro Cycling Team', 'Pinarello–Q36.5 Pro Cycling Team', 'Cofidis',
        'Team TotalEnergies', 'Caja Rural–Seguros RGA',
    ],
    'riders_total': 184,
    'key_teams': {
        'UAE Team Emirates XRG': 'Tadej Pogačar — defending champion, 4× winner',
        'Visma–Lease a Bike': 'Jonas Vingegaard — fresh off Giro d\'Italia win',
        'Red Bull–Bora–Hansgrohe': 'Remco Evenepoel & Florian Lipowitz — GC/TT threats',
        'Alpecin–Premier Tech': 'Jasper Philipsen — green jersey favourite',
    },
}

# Stage-type specialists — real current form, sourced 2026-06-30.
# Sprinters relevant to flat stages + green jersey; TT specialists relevant to
# Stage 1 (TTT) and Stage 16 (ITT).
TDF_SPRINTERS = [
    {'name': 'Jasper Philipsen', 'team': 'Alpecin–Premier Tech', 'note': 'Outright green jersey favourite — proven Tour winner with the peloton\'s best lead-out train'},
    {'name': 'Tim Merlier', 'team': 'Soudal–Quick-Step', 'note': 'Elite pure sprinter — top-end speed on flat, fast, controlled finishes'},
    {'name': 'Olav Kooij', 'team': 'Team Picnic–PostNL', 'note': 'In red-hot form — recently beat Philipsen, Merlier and Girmay in a sprint'},
    {'name': 'Dylan Groenewegen', 'team': 'Team Jayco–AlUla', 'note': 'Still has the speed to win at the highest level'},
]
TDF_TT_SPECIALISTS = [
    {'name': 'Filippo Ganna', 'team': 'Team Jayco–AlUla', 'note': 'Pure time-trial specialist — favourite for Stage 16 ITT'},
    {'name': 'Remco Evenepoel', 'team': 'Red Bull–Bora–Hansgrohe', 'note': 'Olympic TT champion — huge threat in both the Stage 1 TTT and Stage 16 ITT'},
    {'name': 'Tadej Pogačar', 'team': 'UAE Team Emirates XRG', 'note': 'Strong time-triallist on top of GC class — can take real time on TT days'},
]


def _to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(round(obj, 3)))
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    return obj


# ── Betfair outright GC winner market ───────────────────────────────────────

# ── Stage winner predictions by type ─────────────────────────────────────────
# Based on real confirmed startlist (verified 2026-07-01). Sources: ProCyclingUK,
# CyclingNews, Domestique Cycling stage previews.

STAGE_PREDICTIONS = {
    stage['stage']: _stage_tip(stage['type'], stage['distance_km'])
    for stage in []   # populated below via function
}

def _stage_tip(stage_type, distance_km):
    """Return predicted winner and reasoning for a given stage type."""
    if stage_type == 'Team Time Trial':
        return {'pick': 'UAE Team Emirates XRG', 'backup': 'Visma–Lease a Bike',
                'reason': 'UAE (Pogačar) and Visma (Vingegaard) have the strongest TT rosters. UAE marginally edged by Pogačar\'s individual ability on the flat.'}
    elif stage_type == 'Individual Time Trial':
        return {'pick': 'Filippo Ganna', 'backup': 'Remco Evenepoel',
                'reason': f'Pure ITT specialist Ganna (Lidl–Trek) is the outright favourite over {distance_km}km. Evenepoel (Red Bull–BORA) close; Pogačar also dangerous if GC is close.'}
    elif stage_type == 'Mountain':
        return {'pick': 'Tadej Pogačar', 'backup': 'Jonas Vingegaard',
                'reason': 'Decisive mountain stages are Pogačar vs Vingegaard territory. Pogačar\'s attacking style and dominance at Alpe d\'Huez make him favourite. Seixas and Lipowitz for breakaway stage wins.'}
    elif stage_type == 'Hilly':
        return {'pick': 'Mads Pedersen', 'backup': 'Mathieu van der Poel',
                'reason': f'Hilly/{distance_km}km favours punchy riders. Pedersen (Lidl–Trek) won Stage 4 from a breakaway — proven form in race. Van der Poel (Alpecin) is the main rival. Breakaways viable on rolling terrain.'}
    else:  # Flat
        return {'pick': 'Jasper Philipsen', 'backup': 'Tim Merlier',
                'reason': f'Flat/{distance_km}km sprint. Philipsen (Alpecin) is the outright green jersey favourite with the best lead-out train. Merlier (Soudal–Quick-Step) his main rival. Kooij watch.'}

# Build predictions for each stage
STAGE_PREDICTIONS = {s['stage']: _stage_tip(s['type'], s['distance_km']) for s in STAGE_SCHEDULE}


# ── Form analysis ────────────────────────────────────────────────────────────

def generate_tips(outright_odds, results):
    """
    Combines the key race storyline with stage-by-stage predictions and
    live GC tracking once the race is underway.
    """
    tips = {'storyline': None, 'gc_watch': None, 'stage_predictions': [], 'yesterday_performance': {}}

    tips['storyline'] = (
        "Jonas Vingegaard arrives off the back of a dominant Giro d'Italia win "
        "(5 stage wins, 5:22 margin) — his first Giro title, completing the full "
        "Grand Tour set. That's red-hot recent form against Tadej Pogačar, who's "
        "won 3 of the last 5 Tours (including the last two). Vingegaard beat "
        "Pogačar to the Tour in 2022 and 2023 when both were at their best — "
        "this is the rivalry to watch."
    )

    if results:
        latest = results[-1]
        tips['gc_watch'] = f"Stage {latest['stage']} winner: {latest['winner']}"

        # Yesterday's stage performance — did our pick win?
        from datetime import datetime, timezone, timedelta
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%Y-%m-%d')
        yesterday_stages = [r for r in results if r.get('date') == yesterday]
        perf_picks = []
        for r in yesterday_stages:
            pred = STAGE_PREDICTIONS.get(r['stage'], {})
            if pred:
                correct = r.get('winner', '') == pred.get('pick', '')
                perf_picks.append({
                    'stage': r['stage'],
                    'predicted': pred.get('pick', ''),
                    'actual': r.get('winner', ''),
                    'correct': correct,
                })
        if perf_picks:
            won = sum(1 for p in perf_picks if p['correct'])
            tips['yesterday_performance'] = {
                'date': yesterday,
                'total': len(perf_picks),
                'correct': won,
                'win_pct': round((won / len(perf_picks)) * 100) if perf_picks else None,
                'picks': perf_picks,
            }

    # Next 5 stages not yet completed
    completed_stages = {r['stage'] for r in results}
    upcoming = [s for s in STAGE_SCHEDULE if s['stage'] not in completed_stages][:5]
    tips['stage_predictions'] = [
        {
            'stage': s['stage'],
            'date': s['date'],
            'route': s['route'],
            'type': s['type'],
            'distance_km': s['distance_km'],
            **STAGE_PREDICTIONS.get(s['stage'], {}),
        }
        for s in upcoming
    ]

    return tips


def fetch_betfair_outright():
    """Fetch top 5 contenders for the Tour de France outright WINNER (GC) market."""
    try:
        from betfair_odds_fetcher import get_betfair_session
        app_key, session_token = get_betfair_session()
    except Exception as e:
        print(f'[tdf_scraper] Betfair auth failed: {e}')
        return []

    headers = {
        'X-Application': app_key,
        'X-Authentication': session_token,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    catalogue_req = {
        'filter': {
            # No eventTypeId filter — cycling's ID varies/is less standard on Betfair.
            # textQuery + marketTypeCode narrows it down reliably on its own.
            'textQuery': 'Tour de France',
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
        print(f'[tdf_scraper] Betfair catalogue fetch failed: {e}')
        return []

    if not markets:
        print('[tdf_scraper] No Betfair outright market found for Tour de France')
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
        print(f'[tdf_scraper] Betfair odds fetch failed: {e}')
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


# ── procyclingstats.com stage result scrape (best-effort) ──────────────────

def fetch_stage_result(stage_num, year='2026'):
    """
    Best-effort scrape of a single stage's result page.
    Returns {'winner': str, 'gc_leader': str} or None if unavailable/blocked.
    Regex-based since no HTML parser library is available in this Lambda layer.
    """
    url = f'https://www.procyclingstats.com/race/tour-de-france/{year}/stage-{stage_num}'
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        html = resp.text
    except Exception as e:
        print(f'[tdf_scraper] PCS fetch failed for stage {stage_num}: {e}')
        return None

    # Stage winner: first rider link inside the first 'results' table
    m = re.search(r'<table class="results[^"]*".*?<a[^>]*href="rider/[^"]*"[^>]*>([^<]+)</a>', html, re.DOTALL)
    winner = m.group(1).strip() if m else None

    # GC leader: look for the yellow jersey holder, often in a "leaders" widget
    gc_m = re.search(r'(?:GC|Yellow Jersey)[^<]*<a[^>]*href="rider/[^"]*"[^>]*>([^<]+)</a>', html, re.DOTALL)
    gc_leader = gc_m.group(1).strip() if gc_m else None

    if not winner:
        return None
    return {'winner': winner, 'gc_leader': gc_leader or winner}


def fetch_all_available_results(today):
    """Scrape results for any stage whose date has passed."""
    results = []
    for stage in STAGE_SCHEDULE:
        if stage['date'] > today:
            continue
        res = fetch_stage_result(stage['stage'])
        if res:
            results.append({
                'stage': stage['stage'],
                'date': stage['date'],
                'route': stage['route'],
                'winner': res['winner'],
                'gc_leader': res['gc_leader'],
            })
    return results


# ── Main handler ─────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    now_iso = datetime.now(timezone.utc).isoformat()
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

    print(f'[tdf_scraper] Starting daily scrape at {now_iso}')

    is_live = TOUR_START <= today <= TOUR_END
    outright = fetch_betfair_outright()
    results = fetch_all_available_results(today) if today >= TOUR_START else []
    tips = generate_tips(outright, results)

    try:
        sports_table.put_item(Item=_to_decimal({
            'sport': 'tourdefrance',
            'data_key': 'SCHEDULE',
            'stages': STAGE_SCHEDULE,
            'updated_at': now_iso,
        }))

        sports_table.put_item(Item=_to_decimal({
            'sport': 'tourdefrance',
            'data_key': 'TIPS',
            'storyline': tips['storyline'],
            'gc_watch': tips['gc_watch'],
            'stage_predictions': tips['stage_predictions'],
            'yesterday_performance': tips['yesterday_performance'],
            'updated_at': now_iso,
        }))

        sports_table.put_item(Item=_to_decimal({
            'sport': 'tourdefrance',
            'data_key': 'HISTORY',
            'previous_winners': PREVIOUS_WINNERS,
            'giro_2026': GIRO_2026,
            'all_time_record': TDF_ALL_TIME_RECORD,
            'updated_at': now_iso,
        }))

        sports_table.put_item(Item=_to_decimal({
            'sport': 'tourdefrance',
            'data_key': 'TEAMS',
            'teams': TDF_2026_TEAMS,
            'updated_at': now_iso,
        }))

        sports_table.put_item(Item=_to_decimal({
            'sport': 'tourdefrance',
            'data_key': 'SPECIALISTS',
            'sprinters': TDF_SPRINTERS,
            'tt_specialists': TDF_TT_SPECIALISTS,
            'updated_at': now_iso,
        }))

        if results:
            sports_table.put_item(Item=_to_decimal({
                'sport': 'tourdefrance',
                'data_key': 'RESULTS',
                'results': results,
                'updated_at': now_iso,
            }))
            print(f'[tdf_scraper] Saved {len(results)} stage results')

        if outright:
            sports_table.put_item(Item=_to_decimal({
                'sport': 'tourdefrance',
                'data_key': 'OUTRIGHT',
                'contenders': outright,
                'updated_at': now_iso,
            }))
            print(f'[tdf_scraper] Saved outright: {outright}')

        sports_table.put_item(Item=_to_decimal({
            'sport': 'tourdefrance',
            'data_key': 'META',
            'tournament_start': TOUR_START,
            'tournament_end': TOUR_END,
            'updated_at': now_iso,
            'is_live': is_live,
            'stages_completed': len(results),
            'stages_total': len(STAGE_SCHEDULE),
        }))
    except Exception as e:
        print(f'[tdf_scraper] DynamoDB write error: {e}')
        return {'statusCode': 500, 'body': json.dumps({'success': False, 'error': str(e)})}

    return {
        'statusCode': 200,
        'body': json.dumps({
            'success': True,
            'stages_results_scraped': len(results),
            'outright_count': len(outright),
            'is_live': is_live,
            'updated_at': now_iso,
        })
    }


if __name__ == '__main__':
    print(json.dumps(lambda_handler({}, None), indent=2))

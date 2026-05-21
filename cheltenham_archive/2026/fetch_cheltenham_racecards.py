"""
FETCH CHELTENHAM 2026 RACE CARDS FROM BETFAIR
=============================================
Fetches all 28 Cheltenham WIN markets including full runner metadata
(trainer, jockey, form, official rating, age, cloth, weight, days since last run)
and saves to DynamoDB CheltenhamRaceCards table.

Usage:
    python fetch_cheltenham_racecards.py           # fetch & save all 28 races
    python fetch_cheltenham_racecards.py --dry-run  # print only, no DB write
"""

import sys, os, json, time, argparse
import requests
import boto3
from datetime import datetime
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from barrys.barrys_config import FESTIVAL_RACES

BETFAIR_API  = "https://api.betfair.com/exchange/betting/rest/v1.0"
DYNAMODB_REGION = "eu-west-1"
TABLE_NAME   = "CheltenhamRaceCards"

# ── map Betfair market names to our FESTIVAL_RACES keys ───────────────────────
# Betfair uses short names like "2m Hrd", "3m Nov Chs" etc.
# We match on our race names → try fuzzy match by keywords
RACE_NAME_MAP = {
    "Supreme Novices' Hurdle":          "day1_race1",
    "Supreme Novices Hurdle":           "day1_race1",
    "Sky Bet Supreme":                  "day1_race1",
    "Arkle":                            "day1_race2",
    "Ultima":                           "day1_race3",
    "Champion Hurdle":                  "day1_race4",
    "Mares' Hurdle":                    "day1_race5",
    "Mares Hurdle":                     "day1_race5",
    "National Hunt Chase":              "day1_race6",
    "Challenge Cup":                    "day1_race7",
    "Ballymore":                        "day2_race1",
    "Brown Advisory":                   "day2_race2",
    "Coral Cup":                        "day2_race3",
    "Queen Mother":                     "day2_race4",
    "Glenfarclas":                      "day2_race5",
    "Cross Country":                    "day2_race5",
    "Dawn Run":                         "day2_race6",
    "FBD":                              "day2_race7",
    "NH Flat Race":                     "day2_race7",
    "Turners":                          "day3_race1",
    "Pertemps":                         "day3_race2",
    "Ryanair":                          "day3_race3",
    "Stayers":                          "day3_race4",
    "Paddy Power Stayers":              "day3_race4",
    "Plate":                            "day3_race5",
    "Boodles Juvenile":                 "day3_race6",
    "Martin Pipe":                      "day3_race7",
    "Ultima Handicap":                  "day1_race3",
    "Novices' Chase":                   "day2_race2",
    "Proactif":                         "day4_race1",   # County Hurdle / Triumph
    "County":                           "day4_race1",
    "Albert Bartlett":                  "day4_race2",   # or Triumph
    "Triumph Hurdle":                   "day4_race2",
    "JCB Triumph":                      "day4_race2",
    "Vincent O'Brien County":           "day4_race1",
    "Grand Annual":                     "day4_race3",
    "Gold Cup":                         "day4_race4",
    "Cheltenham Gold Cup":              "day4_race4",
    "Champion Bumper":                  "day4_race5",
    "Foxhunter":                        "day4_race6",
    "St James Place":                   "day4_race6",
    "Kim Muir":                         "day4_race7",
    "Conditional Jockeys":              "day1_race7",
}


def load_creds():
    path = os.path.join(ROOT, 'betfair-creds.json')
    with open(path) as f:
        return json.load(f)


def refresh_session(creds):
    """Re-login and update session token."""
    r = requests.post(
        'https://identitysso.betfair.com/api/login',
        headers={'X-Application': creds['app_key'],
                 'Content-Type': 'application/x-www-form-urlencoded'},
        data={'username': creds['username'], 'password': creds['password']},
        timeout=20
    )
    if r.status_code == 200:
        tok = r.json().get('sessionToken') or r.json().get('token')
        if tok:
            creds['session_token'] = tok
            path = os.path.join(ROOT, 'betfair-creds.json')
            with open(path, 'w') as f:
                json.dump(creds, f, indent=2)
            print("  Session refreshed OK")
            return tok
    print(f"  Session refresh failed: {r.status_code} {r.text[:200]}")
    return creds['session_token']


def bf_post(endpoint, payload, headers, timeout=30):
    url = f"{BETFAIR_API}/{endpoint}/"
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def match_race_key(market_name, race_name_in_cat):
    """Map a Betfair market/race name to our festival race key."""
    combined = (market_name + " " + race_name_in_cat).lower()
    best_key = None
    best_len = 0
    for keyword, race_key in RACE_NAME_MAP.items():
        if keyword.lower() in combined and len(keyword) > best_len:
            best_key = race_key
            best_len = len(keyword)
    return best_key


def decimal_to_fraction(dec):
    fracs = [
        (0.2,"1/5"),(0.25,"1/4"),(0.33,"1/3"),(0.4,"2/5"),(0.5,"1/2"),
        (0.6,"3/5"),(0.75,"3/4"),(0.8,"4/5"),(1.0,"Evs"),(1.25,"5/4"),
        (1.5,"6/4"),(1.75,"7/4"),(2.0,"2/1"),(2.25,"9/4"),(2.5,"5/2"),
        (2.75,"11/4"),(3.0,"3/1"),(3.5,"7/2"),(4.0,"4/1"),(4.5,"9/2"),
        (5.0,"5/1"),(6.0,"6/1"),(7.0,"7/1"),(8.0,"8/1"),(9.0,"9/1"),
        (10.0,"10/1"),(11.0,"11/1"),(12.0,"12/1"),(14.0,"14/1"),
        (16.0,"16/1"),(20.0,"20/1"),(25.0,"25/1"),(33.0,"33/1"),
        (40.0,"40/1"),(50.0,"50/1"),(66.0,"66/1"),(100.0,"100/1"),
    ]
    n = dec - 1.0
    if n <= 0: return "EVS"
    best = min(fracs, key=lambda x: abs(x[0] - n))
    return best[1]


def fetch_racecards(creds):
    """
    Returns dict: { race_key: { 'race_info': {...}, 'runners': [...] } }
    Each runner has: name, cloth, odds_dec, odds_frac, trainer, jockey,
                     official_rating, adjusted_rating, form, age, sex,
                     weight_lbs, days_since_last_run, selection_id, status
    """
    headers = {
        'X-Application':   creds['app_key'],
        'X-Authentication': creds['session_token'],
        'Content-Type':    'application/json',
    }

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  BETFAIR — CHELTENHAM 2026 FULL RACE CARDS")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # ── 1. Find 2026 Cheltenham event IDs ─────────────────────────────────────
    events = bf_post("listEvents", {
        "filter": {"eventTypeIds": ["7"], "textQuery": "Cheltenham"}
    }, headers)
    chelt_ids = []
    for ev in events:
        name = ev.get('event', {}).get('name', '')
        od   = ev.get('event', {}).get('openDate', '')
        if '2026' in od and 'Cheltenham' in name:
            chelt_ids.append(ev['event']['id'])
            print(f"  ✓ Event: {name}  ({od[:10]})")

    if not chelt_ids:
        print("  ✗ No 2026 Cheltenham events found on Exchange!")
        return {}

    # ── 2. Get WIN market catalogue with RUNNER_METADATA ─────────────────────
    catalogue = bf_post("listMarketCatalogue", {
        "filter": {
            "eventTypeIds":    ["7"],
            "eventIds":        chelt_ids,
            "marketTypeCodes": ["WIN"],
        },
        "sort":             "FIRST_TO_START",
        "maxResults":       50,
        "marketProjection": [
            "MARKET_NAME",
            "RUNNER_DESCRIPTION",
            "RUNNER_METADATA",
            "EVENT",
            "MARKET_START_TIME",
        ],
    }, headers)

    print(f"\n  Found {len(catalogue)} WIN markets\n")
    print(f"  {'MARKET':<50} {'START':<12} MARKET_ID")
    print("  " + "─" * 80)
    for m in catalogue:
        start = m.get('marketStartTime', '')[:16].replace('T', ' ')
        print(f"  {m.get('marketName', ''):<50} {start:<12} {m['marketId']}")

    # ── 3. Fetch prices for all markets ──────────────────────────────────────
    market_ids   = [m['marketId'] for m in catalogue]
    id_to_market = {m['marketId']: m for m in catalogue}
    id_to_runner = {}
    id_to_meta   = {}
    for m in catalogue:
        for r in m.get('runners', []):
            sid = r['selectionId']
            id_to_runner[sid] = r.get('runnerName', '')
            id_to_meta[sid]   = r.get('metadata', {})

    all_books = {}
    for i in range(0, len(market_ids), 10):
        batch = market_ids[i:i+10]
        books = bf_post("listMarketBook", {
            "marketIds": batch,
            "priceProjection": {
                "priceData":       ["EX_BEST_OFFERS"],
                "exBestOffersCnt": 1,
            },
        }, headers)
        for book in books:
            all_books[book['marketId']] = book
        time.sleep(0.3)

    # ── 4. Build race cards ───────────────────────────────────────────────────
    results = {}

    for m in catalogue:
        mid    = m['marketId']
        mname  = m.get('marketName', '')
        mstart = m.get('marketStartTime', '')
        event_name = m.get('event', {}).get('name', '')

        race_key = match_race_key(mname, event_name)
        if not race_key:
            print(f"\n  ⚠  Could not map: '{mname}' | '{event_name}' → skipping")
            continue

        festival_info = FESTIVAL_RACES.get(race_key, {})
        book = all_books.get(mid, {})

        # Build runner pricing lookup
        runner_prices = {}
        for r in book.get('runners', []):
            sid    = r['selectionId']
            status = r.get('status', '')
            backs  = r.get('ex', {}).get('availableToBack', [])
            price  = backs[0]['price'] if backs else None
            runner_prices[sid] = {'status': status, 'price': price}

        runners = []
        for r in m.get('runners', []):
            sid    = r['selectionId']
            name   = r.get('runnerName', '')
            meta   = r.get('metadata', {}) or {}
            price_info = runner_prices.get(sid, {})
            status = price_info.get('status', 'ACTIVE')
            price  = price_info.get('price')

            runner_rec = {
                'name':              name,
                'selection_id':      sid,
                'cloth':             meta.get('CLOTH_NUMBER_ALPHA') or meta.get('CLOTH_NUMBER', '?'),
                'status':            status,
                'odds_dec':          price,
                'odds_frac':         decimal_to_fraction(price) if price else '?',
                'trainer':           meta.get('TRAINER_NAME', '?'),
                'jockey':            meta.get('JOCKEY_NAME', '?'),
                'jockey_claim':      meta.get('JOCKEY_CLAIM', '0'),
                'official_rating':   meta.get('OFFICIAL_RATING'),
                'adjusted_rating':   meta.get('ADJUSTED_RATING'),
                'form':              meta.get('FORM', '?'),
                'age':               meta.get('AGE'),
                'sex':               meta.get('SEX_TYPE'),
                'weight_lbs':        meta.get('WEIGHT_VALUE'),
                'days_since_last_run': meta.get('DAYS_SINCE_LAST_RUN'),
                'sire':              meta.get('SIRE_NAME'),
                'dam':               meta.get('DAM_NAME'),
                'bred':              meta.get('SIRE_BRED'),
            }
            runners.append(runner_rec)

        # Sort by odds (favourites first)
        runners.sort(key=lambda x: (x['odds_dec'] or 9999, x['cloth']))

        results[race_key] = {
            'race_key':     race_key,
            'race_name':    festival_info.get('name', mname),
            'betfair_name': mname,
            'market_id':    mid,
            'day':          festival_info.get('day'),
            'time':         festival_info.get('time'),
            'grade':        festival_info.get('grade'),
            'market_start': mstart,
            'runner_count': len([r for r in runners if r['status'] != 'REMOVED']),
            'runners':      runners,
            'fetched_at':   datetime.utcnow().isoformat(),
        }

    return results


def save_to_dynamodb(racecards, dry_run=False):
    """Save race cards to CheltenhamRaceCards DynamoDB table."""
    if dry_run:
        print("\n  [DRY RUN] — not saving to DynamoDB")
        return

    dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION)

    # Create table if it doesn't exist
    existing = [t.name for t in dynamodb.tables.all()]
    if TABLE_NAME not in existing:
        print(f"\n  Creating DynamoDB table: {TABLE_NAME}")
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'race_key',    'KeyType': 'HASH'},
                {'AttributeName': 'fetched_date', 'KeyType': 'RANGE'},
            ],
            AttributeDefinitions=[
                {'AttributeName': 'race_key',    'AttributeType': 'S'},
                {'AttributeName': 'fetched_date', 'AttributeType': 'S'},
            ],
            BillingMode='PAY_PER_REQUEST',
        )
        table.meta.client.get_waiter('table_exists').wait(TableName=TABLE_NAME)
        print(f"  Table created OK")
    else:
        table = dynamodb.Table(TABLE_NAME)
        print(f"\n  Using existing table: {TABLE_NAME}")

    saved = 0
    fetch_date = datetime.utcnow().strftime('%Y-%m-%d')

    for race_key, card in racecards.items():
        # Convert floats to Decimal for DynamoDB
        item = _to_decimal(dict(card))
        item['race_key']    = race_key
        item['fetched_date'] = fetch_date
        table.put_item(Item=item)
        saved += 1
        print(f"  ✓ Saved: {race_key} — {card['race_name']} ({card['runner_count']} runners)")

    print(f"\n  ✅ {saved} race cards saved to {TABLE_NAME}")


def _to_decimal(obj):
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_to_decimal(v) for v in obj]
    elif isinstance(obj, float):
        return Decimal(str(round(obj, 4)))
    else:
        return obj


def print_summary(racecards):
    """Pretty-print the fetched race cards."""
    total_runners = 0
    print(f"\n\n{'═'*72}")
    print(f"  CHELTENHAM 2026 — BETFAIR RACE CARDS SUMMARY")
    print(f"{'═'*72}")
    for race_key in sorted(racecards.keys()):
        card = racecards[race_key]
        runners = [r for r in card['runners'] if r['status'] != 'REMOVED']
        total_runners += len(runners)
        print(f"\n  Day {card['day']}  {card['time']}  {card['race_name']}  [{card['grade']}]")
        print(f"  {card['market_id']}  |  {len(runners)} runners")
        print(f"  {'#':<4}{'HORSE':<30}{'ODDS':<10}{'TRAINER':<28}{'JOCKEY':<22}{'FORM':<12}{'RAT'}")
        print("  " + "─" * 110)
        for r in runners:
            cloth = str(r.get('cloth', '?'))
            odds  = r.get('odds_frac', '?')
            rat   = r.get('official_rating') or '-'
            form  = r.get('form', '?')
            print(f"  {cloth:<4}{r['name']:<30}{odds:<10}{r['trainer']:<28}{r['jockey']:<22}{form:<12}{rat}")

    print(f"\n  Total runners across all races: {total_runners}")


def main():
    parser = argparse.ArgumentParser(description="Fetch Cheltenham 2026 race cards from Betfair")
    parser.add_argument('--dry-run', action='store_true', help='Print only, do not save to DynamoDB')
    args = parser.parse_args()

    creds = load_creds()
    # Refresh session
    try:
        creds['session_token'] = refresh_session(creds)
    except Exception as e:
        print(f"  Session refresh error: {e} — using cached token")

    try:
        racecards = fetch_racecards(creds)
    except requests.HTTPError as e:
        if '401' in str(e):
            print("  Session expired — attempting re-login...")
            creds['session_token'] = refresh_session(creds)
            racecards = fetch_racecards(creds)
        else:
            raise

    if not racecards:
        print("\n  No race cards fetched. Exiting.")
        return

    print_summary(racecards)
    save_to_dynamodb(racecards, dry_run=args.dry_run)


if __name__ == '__main__':
    main()

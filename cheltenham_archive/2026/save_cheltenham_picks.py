"""
SAVE CHELTENHAM PICKS TO DYNAMODB
===================================
Runs daily to:
  1. Score ALL 28 2026 Festival races via the SureBet engine (surebet_intel.py)
  2. Compare with yesterday's pick for each race
  3. Detect any changes and record WHY the pick changed
  4. Save to CheltenhamPicks DynamoDB table with full history + per-horse scoring

Usage:
    python save_cheltenham_picks.py            # Save today's picks
    python save_cheltenham_picks.py --history  # Show pick change history
    python save_cheltenham_picks.py --today    # Print today's picks only (no save)
"""

import sys, os, json
import boto3
import requests
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

# ── path setup so barrys/ sub-package is importable ─────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# Import the full 28-race SureBet scoring engine
from barrys.surebet_intel import build_all_picks

# Festival day → DynamoDB day-key mapping
DAY_TO_DYNAMO = {
    1: "Tuesday_10_March",
    2: "Wednesday_11_March",
    3: "Thursday_12_March",
    4: "Friday_13_March",
}

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')

# Table: CheltenhamPicks
# PK: race_name   SK: pick_date
PICKS_TABLE = 'CheltenhamPicks'


# ─── Cheltenham Strategy: Race Classification ────────────────────────────────
# SKIP: Handicaps, amateur races, cross country — NO bets
SKIP_RACES = {
    "Ultima Handicap Chase",
    "Conditional Jockeys Handicap Hurdle",
    "National Hunt Chase",
    "Coral Cup Handicap Hurdle",
    "Glenfarclas Chase",
    "Glenfarclas Chase Cross Country",
    "Cross Country Chase",
    "Pertemps Final Handicap Hurdle",
    "Pertemps Network Final",
    "Festival Plate Handicap Chase",
    "Plate Handicap Chase",
    "TrustATrader Festival Plate Handicap Chase",
    "Boodles Juvenile Handicap Hurdle",
    "Fred Winter Juvenile Handicap Hurdle",
    "Martin Pipe Conditional Jockeys Hurdle",
    "Martin Pipe Conditional Jockeys Novices Hurdle",
    "County Handicap Hurdle",
    "Grand Annual Handicap Chase",
    "St James Place Foxhunter Chase",
    "Foxhunter Chase",
    "Hunters Chase",
}

# GRADE1 non-handicap championship races — eligible for BETTING_PICK
GRADE1_RACES = {
    "Sky Bet Supreme Novices Hurdle",
    "Supreme Novices Hurdle",
    "Supreme Novices' Hurdle",
    "Arkle Challenge Trophy Chase",
    "Arkle Chase",
    "Arkle Novices Chase",
    "Unibet Champion Hurdle",
    "Champion Hurdle",
    "Close Brothers Mares Hurdle",
    "Mares Hurdle",
    "Mares' Hurdle",
    "Ballymore Novices Hurdle",
    "Brown Advisory Novices Chase",
    "Queen Mother Champion Chase",
    "QMCC",
    "Dawn Run Mares Novices Hurdle",
    "Turners Novices Chase",
    "Ryanair Chase",
    "Paddy Power Stayers Hurdle",
    "Stayers Hurdle",
    "Stayers' Hurdle",
    "JCB Triumph Hurdle",
    "Triumph Hurdle",
    "Albert Bartlett Novices Hurdle",
    "Cheltenham Gold Cup",
    "Gold Cup",
    "Champion Standard Open NH Flat Race",
    "Champion Bumper",
    "NH Flat Race",
}


# ─── Live Racing Post odds scraped 2026-03-05 ────────────────────────────────
# Format: lowercase horse name → odds string
RP_LIVE_ODDS = {
    # Champion Hurdle (Day 1)
    "the new lion":           "2/1",
    "brighterdaysahead":      "7/2",
    "lossiemouth":            "2/1",   # Champion Hurdle favourite (updated 08/03/2026)
    "golden ace":             "7/1",
    "poniros":                "10/1",
    "alexei":                 "16/1",
    "anzadam":                "20/1",
    "workahead":              "100/1",

    # Cheltenham Gold Cup (Day 4)
    "gaelic warrior":         "7/2",  # Gold Cup favourite since Galopin withdrawal (updated 08/03/2026)
    "the jukebox man":        "6/1",
    "jango baie":             "6/1",
    "galopin des champs":     "7/1",
    "inothewayurthinkin":     "8/1",
    "grey dawning":           "14/1",
    "spillane's tower":       "16/1",
    "i am maximus":           "33/1",
    "grangeclare west":       "33/1",
    "affordale fury":         "33/1",
    "envoi allen":            "40/1",
    "fastorslow":             "40/1",
    "banbridge":              "40/1",
    "nick rockett":           "40/1",
    "monty's star":           "50/1",
    "firefox":                "50/1",
    "heart wood":             "66/1",
    "stellar story":          "66/1",
    "impaire et passe":       "66/1",
    "resplendent grey":       "66/1",
    "spindleberry":           "66/1",
    "three card brag":        "100/1",
    "lecky watson":           "100/1",
    "handstands":             "100/1",
    "myretown":               "150/1",
    "gold tweet":             "200/1",

    # Queen Mother Champion Chase / QMCC (Day 2)
    "majborough":             "6/4",
    "l'eau du sud":           "6/1",
    "il etait temps":         "7/1",
    "jonbon":                 "14/1",
    "quilixios":              "16/1",
    "thistle ask":            "16/1",
    "found a fifty":          "40/1",
    "solness":                "40/1",

    # Supreme Novices' Hurdle (Day 1) — confirmed 12 runners (Betfair 08/03/2026)
    "old park star":          "11/4",
    "talk the talk":          "4/1",
    "mighty park":            "10/3",
    "el cairos":              "11/2",
    "mydaddypaddy":           "13/2",
    "leader dallier":         "10/1",
    "sober glory":            "12/1",
    "baron noir":             "33/1",
    "koktail brut":           "66/1",
    "too bossy for us":       "40/1",
    "eachtotheirown":         "33/1",
    "sageborough":            "100/1",

    # Arkle Chase (Day 1) — confirmed 7 runners (Betfair 08/03/2026)
    "kopek des bordes":       "7/4",
    "lulamba":                "15/8",
    "kargese":                "6/1",
    "steel ally":             "14/1",
    "jax junior":             "20/1",
    "mambonumberfive":        "33/1",
    "hansard":                "100/1",

    # Ballymore / Baring Bingham Novices' Hurdle (Day 2)
    "no drama this end":      "4/1",
    "skylight hustle":        "6/1",
    "king rasko grey":        "8/1",
    "act of innocence":       "10/1",
    "i'll sort that":         "14/1",
    "doctor steinberg":       "3/1",   # Albert Bartlett FAVOURITE

    # Stayers' Hurdle (Day 3) — Betfair 11/03 morning prices
    "teahupoo":               "4/1",
    "kabral du mathan":       "9/2",
    "ballyburn":              "13/2",
    "bob olinger":            "7/1",
    "ma shantou":             "7/1",
    "honesty policy":         "10/1",
    "impose toi":             "10/1",
    "hewick":                 "59/1",
    "home by the lee":        "47/1",
    "doddiethegreat":         "33/1",

    # Ryanair Chase (Day 3) — 8 runners (Jagwar NOT running here, ran Day 1 Ultima)
    "fact to file":           "10/11",
    "panic attack":           "20/1",
    "protektorat":            "25/1",
    "energumene":             "40/1",
    "better days ahead":      "50/1",
    "edwardstone":            "100/1",
    "master chewy":           "100/1",
    "croke park":             "100/1",

    # Jack Richards Novices' Chase / Turners Chase (Day 3)
    "koktail divin":          "9/2",
    "regent's stroll":        "6/1",
    "meetmebythesea":         "6/1",
    "slade steel":            "9/1",
    "sixmilebridge":          "9/1",

    # Mares' Hurdle (Day 3) — Betfair 11/03 morning prices
    "wodhooh":                "10/11",  # FIT FAVOURITE — was listed wrong
    "jade de grugy":          "11/4",
    "feet of a dancer":       "12/1",
    "take no chances":        "13/1",
    "dream on baby":          "37/1",
    "jetara":                 "39/1",
    "sunset marquesa":        "119/1",

    # Brown Advisory Novices' Chase (Day 2)
    "final demand":           "7/2",
    "the big westerner":      "10/1",  # running in Mares Chase at 10/1
    "kaid d'authie":          "6/1",
    "wendigo":                "8/1",
    "western fold":           "8/1",
    "oscars brother":         "12/1",
    "kitzbuhel":              "12/1",
    "salver":                 "16/1",
    "kappa jy pyke":          "25/1",

    # JCB Triumph Hurdle (Day 4)
    "proactif":               "7/2",
    "selma de vary":          "9/2",
    "minella study":          "7/1",
    "maestro conti":          "15/2",
    "mange tout":             "8/1",
    "macho man":              "8/1",
    "winston junior":         "13/2",

    # Ryanair Mares' Novices' Hurdle 13:20 (Day 3) — Betfair 11/03 morning prices
    "bambino fever":          "5/4",
    "oldschool outlaw":       "5/1",
    "carrigmoornaspruce":     "12/1",
    "echoing silence":        "16/1",
    "la conquiere":           "21/1",

    # Champion Bumper (Day 2)
    "love sign d'aunou":      "9/2",
    "the irish avatar":       "8/1",
    "keep him company":       "9/1",
    "quiryn":                 "10/1",
    "bass hunter":            "14/1",

    # Mrs Paddy Power Mares Chase (Day 4) — Betfair 11/03
    "dinoblue":               "15/8",

    # Pertemps Handicap Hurdle (Day 3) — Betfair 11/03
    "supremely west":         "7/2",
    "cest different":         "17/2",
    "bold endeavour":         "9/1",
    "gowel road":             "59/1",

    # Kim Muir Handicap Chase (Day 3) — Betfair 11/03
    "jeriko du reponet":      "9/2",
    "waterford whispers":     "11/2",
    "herakles westwood":      "11/1",

    # Martin Pipe Conditional Jockeys' Hurdle (Day 4) — Betfair 11/03
    "kel histoire":           "11/2",
    "roc dino":               "9/1",
    "air of entitlement":     "9/1",
    "east india express":     "9/1",
    "nurse susan":            "13/1",  # was 40/1 in old RP data — massive correction
    "he cant dance":          "21/1",
    "sony bill":              "21/1",

    # Fred Winter Juvenile Handicap Hurdle (Day 1)
    "manlaga":                "7/1",

    # National Hunt Chase (Day 1)
    # "backmersackme":          "9/2",   # non-runner 08/03/2026

    # Jack Richards Novices' Chase (Day 3) - additional
    # "waterford whispers":     "12/1",  # non-runner 08/03/2026
}

# ── Module-level cache – populated once per Lambda invocation ────────────────
_BETFAIR_LIVE_ODDS: dict = {}

BETFAIR_API_URL = "https://api.betfair.com/exchange/betting/rest/v1.0/"

_BETFAIR_PRICE_MAP = {
    1.01: "1/100", 1.02: "1/50",  1.05: "1/20",  1.1:  "1/10",  1.2:  "1/5",
    1.25: "1/4",   1.33: "1/3",   1.4:  "2/5",   1.5:  "1/2",   1.57: "4/7",
    1.61: "4/6",   1.67: "8/13",  1.72: "8/11",  1.8:  "4/5",   1.83: "5/6",
    1.91: "10/11", 2.0:  "EVS",   2.1:  "11/10", 2.2:  "6/5",   2.25: "5/4",
    2.38: "11/8",  2.4:  "7/5",   2.5:  "6/4",   2.63: "13/8",  2.75: "7/4",
    2.88: "15/8",  3.0:  "2/1",   3.25: "9/4",   3.5:  "5/2",   3.75: "11/4",
    4.0:  "3/1",   4.5:  "7/2",   5.0:  "4/1",   5.5:  "9/2",   6.0:  "5/1",
    6.5:  "11/2",  7.0:  "6/1",   7.5:  "13/2",  8.0:  "7/1",   8.5:  "15/2",
    9.0:  "8/1",   9.5:  "17/2",  10.0: "9/1",   11.0: "10/1",  12.0: "11/1",
    13.0: "12/1",  14.0: "13/1",  15.0: "14/1",  16.0: "15/1",  17.0: "16/1",
    19.0: "18/1",  21.0: "20/1",  23.0: "22/1",  26.0: "25/1",  29.0: "28/1",
    31.0: "30/1",  34.0: "33/1",  36.0: "35/1",  41.0: "40/1",  51.0: "50/1",
    67.0: "66/1",  81.0: "80/1",  101.0: "100/1", 126.0: "125/1",
    151.0: "150/1", 201.0: "200/1", 251.0: "250/1",
}


def decimal_to_fractional(dec: float) -> str:
    """Convert a Betfair decimal price to a UK fractional string e.g. 4.0 → '3/1'."""
    if dec >= 990:
        return "NR"
    closest = min(_BETFAIR_PRICE_MAP.keys(), key=lambda k: abs(k - dec))
    if abs(closest - dec) < 0.6:
        return _BETFAIR_PRICE_MAP[closest]
    # Fallback for unlisted prices: simple integer fraction
    return f"{max(1, round(dec) - 1)}/1"


def get_betfair_live_odds() -> dict:
    """
    Fetch live WIN market prices for all Cheltenham races from Betfair Exchange.
    Reads the session token from Secrets Manager ('betfair-credentials').
    Returns {horse_name_lower: fractional_odds_string}.
    Returns {} on any failure — caller falls back to static RP_LIVE_ODDS.
    """
    try:
        # ── Credentials from Secrets Manager ────────────────────────────────
        sm = boto3.client('secretsmanager', region_name='eu-west-1')
        raw = sm.get_secret_value(SecretId='betfair-credentials')['SecretString']
        if raw.startswith('{\\'):
            raw = raw.replace('\\', '')
        creds = json.loads(raw)
        session_token = creds.get('session_token', '')
        app_key       = creds.get('app_key', '')
        if not session_token or not app_key:
            print("WARNING: Betfair credentials missing — using static RP odds")
            return {}

        headers = {
            'X-Application':   app_key,
            'X-Authentication': session_token,
            'Content-Type':    'application/json',
        }

        # ── Step 1: Discover all Cheltenham WIN markets ──────────────────────
        cat = requests.post(
            BETFAIR_API_URL + 'listMarketCatalogue/',
            headers=headers,
            json={
                'filter': {
                    'eventTypeIds':    ['7'],
                    'marketCountries': ['GB'],
                    'marketTypeCodes': ['WIN'],
                    'textQuery':       'Cheltenham',
                },
                'marketProjection': ['RUNNER_DESCRIPTION', 'EVENT'],
                'maxResults': 50,
            },
            timeout=20,
        )
        if cat.status_code != 200:
            print(f"WARNING: Betfair listMarketCatalogue HTTP {cat.status_code}")
            return {}
        markets = cat.json()
        if not markets:
            print("WARNING: No Cheltenham WIN markets returned by Betfair")
            return {}

        market_ids   = [m['marketId'] for m in markets]
        runner_names = {}   # selectionId (int) → horse name lowercase
        for m in markets:
            for r in m.get('runners', []):
                runner_names[r['selectionId']] = r['runnerName'].lower().strip()

        # ── Step 2: Fetch best available back prices ─────────────────────────
        book = requests.post(
            BETFAIR_API_URL + 'listMarketBook/',
            headers=headers,
            json={
                'marketIds':       market_ids,
                'priceProjection': {'priceData': ['EX_BEST_OFFERS']},
            },
            timeout=20,
        )
        if book.status_code != 200:
            print(f"WARNING: Betfair listMarketBook HTTP {book.status_code}")
            return {}

        live: dict = {}
        for mkt in book.json():
            # Skip already-settled markets (Day 1-2 completed races)
            mkt_status = mkt.get('status', '')
            if mkt_status in ('CLOSED',):
                continue
            for runner in mkt.get('runners', []):
                name = runner_names.get(runner['selectionId'])
                if not name:
                    continue
                runner_status = runner.get('status', '')
                # Skip settled or removed runners — their prices are BSP/settled garbage
                if runner_status in ('REMOVED', 'WINNER', 'LOSER'):
                    if runner_status == 'REMOVED':
                        live[name] = 'NR'
                    continue
                back_list = runner.get('ex', {}).get('availableToBack', [])
                if back_list:
                    price = back_list[0].get('price', 0)
                    # Guard: prices ≤ 1.10 are settled-market artefacts (BSP/winning margins)
                    if price < 1.1:
                        continue
                    live[name] = 'NR' if price >= 990 else decimal_to_fractional(price)

        print(f"\u2705 Betfair live odds fetched: {len(live)} horses across {len(market_ids)} markets")
        return live

    except Exception as exc:
        print(f"WARNING: Betfair live odds fetch failed ({exc}) — using static RP odds")
        return {}


def get_live_odds(horse_name: str) -> str:
    """Return live Betfair price if available, else fall back to static RP odds."""
    key = horse_name.lower().strip()
    return _BETFAIR_LIVE_ODDS.get(key) or RP_LIVE_ODDS.get(key, "?")


def _race_classification(race_name: str):
    """Return (is_grade1, is_skip) for a race name — partial substring match."""
    rn_lower = race_name.lower()
    is_skip = any(s.lower() in rn_lower or rn_lower in s.lower()
                  for s in SKIP_RACES)
    is_g1   = any(g.lower() in rn_lower or rn_lower in g.lower()
                  for g in GRADE1_RACES)
    return is_g1, is_skip

# Table: CheltenhamPicks
# PK: race_name   SK: pick_date
PICKS_TABLE = 'CheltenhamPicks'


def get_picks_table():
    return dynamodb.Table(PICKS_TABLE)


def ensure_table_exists():
    """Create CheltenhamPicks if it doesn't exist"""
    try:
        client = boto3.client('dynamodb', region_name='eu-west-1')
        existing = client.list_tables().get('TableNames', [])   # list of strings
        if PICKS_TABLE not in existing:
            print(f"Creating {PICKS_TABLE} table...")
            client.create_table(
                TableName=PICKS_TABLE,
                KeySchema=[
                    {'AttributeName': 'race_name', 'KeyType': 'HASH'},
                    {'AttributeName': 'pick_date', 'KeyType': 'RANGE'},
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'race_name', 'AttributeType': 'S'},
                    {'AttributeName': 'pick_date', 'AttributeType': 'S'},
                ],
                BillingMode='PAY_PER_REQUEST',
            )
            # Wait for table to be active
            waiter = client.get_waiter('table_exists')
            waiter.wait(TableName=PICKS_TABLE)
            print(f"Table {PICKS_TABLE} created.")
        else:
            print(f"Table {PICKS_TABLE} already exists.")
    except Exception as e:
        print(f"Warning: Could not check/create table: {e}")


def _tier(score):
    if score >= 155: return "A+  ELITE"
    if score >= 140: return "A   ELITE"
    if score >= 120: return "B   EXCELLENT"
    if score >= 100: return "C   STRONG"
    if score >= 80:  return "D   FAIR"
    return               "E   WEAK"


def score_all_races():
    """
    Score all 28 Cheltenham 2026 races using the SureBet engine.
    Returns a dict keyed by race_name with enriched pick data including
    the full ordered field (all_horses), tiered strategy classification,
    and live RP odds.
    """
    raw_picks = build_all_picks(verbose=True)   # verbose=True → full scored list

    picks = {}
    for race_key, r in raw_picks.items():
        scored = r.get("scored", [])
        if not scored:
            continue

        top = scored[0]
        second_score      = scored[1]["score"] if len(scored) > 1 else 0
        second_horse_name = scored[1]["name"]  if len(scored) > 1 else ""

        top_score = top["score"]
        race_name = r["race_name"]

        # ── Cheltenham Strategy Tier Classification ──────────────────────────
        is_grade1, is_skip = _race_classification(race_name)

        # BETTING_PICK: Grade 1, not a skip race, score >= 75
        # WATCH_LIST:   Not a skip race, score >= 60
        # OPINION_ONLY: Everything else (skip races, low scores)
        if (not is_skip) and is_grade1 and top_score >= 75:
            bet_tier        = "BETTING_PICK"
            bet_recommendation = True
        elif (not is_skip) and top_score >= 60:
            bet_tier        = "WATCH_LIST"
            bet_recommendation = False
        else:
            bet_tier        = "OPINION_ONLY"
            bet_recommendation = False

        # Legacy confidence field (kept for backwards compatibility)
        confidence = (
            'HIGH'   if top_score >= 140 else
            'MEDIUM' if top_score >= 100 else
            'LOW'
        )

        # ── Live odds from RP ────────────────────────────────────────────────
        live_odds = get_live_odds(top["name"])

        dynamo_day = DAY_TO_DYNAMO.get(r["day"], f"Day_{r['day']}")

        picks[race_name] = {
            'race_name':        race_name,
            'race_key':         race_key,
            'day':              dynamo_day,
            'race_time':        r.get("time", ""),
            'grade':            r["grade"],
            'distance':         '',
            'horse':            top["name"],
            'trainer':          top.get("trainer", ""),
            'jockey':           top.get("jockey", ""),
            'odds':             live_odds,
            'age':              '',
            'form':             '',
            'rating':           0,
            'score':            top_score,
            'tier':             _tier(top_score),
            'value_rating':     top.get("value_r", 0),
            'second_score':     second_score,
            'second_horse_name': second_horse_name,
            'score_gap':        top_score - second_score,
            'confidence':       confidence,
            # ── Strategy fields ─────────────────────────────────────────────
            'is_grade1':        is_grade1,
            'is_skip_race':     is_skip,
            'bet_tier':         bet_tier,
            'bet_recommendation': bet_recommendation,
            # ────────────────────────────────────────────────────────────────
            'reasons':          top.get("tips", [])[:6],
            'warnings':         top.get("warnings", []),
            # Full ordered horse list ─────────────────────────────────────────
            'all_horses':   [
                {
                    'name':             h["name"],
                    'trainer':          h.get("trainer", ""),
                    'jockey':           h.get("jockey", ""),
                    'score':            h["score"],
                    'tier':             _tier(h["score"]),
                    'value_rating':     h.get("value_r", 0),
                    'tips':             h.get("tips", []),
                    'warnings':         h.get("warnings", []),
                    'cheltenham_record': h.get("cheltenham_record", ""),
                    'is_surebet_pick':  h["name"] == top["name"],
                    'odds':             get_live_odds(h["name"]),
                }
                for h in scored
            ],
        }

    return picks


def get_yesterday_picks(table, today_str):
    """Fetch all picks saved for yesterday"""
    yesterday = (datetime.strptime(today_str, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
    try:
        response = table.scan(
            FilterExpression='pick_date = :d',
            ExpressionAttributeValues={':d': yesterday},
        )
        items = response.get('Items', [])
        return {item['race_name']: item for item in items}
    except Exception as e:
        print(f"Warning: could not fetch yesterday's picks: {e}")
        return {}


def detect_changes(today_pick, yesterday_pick):
    """Compare today vs yesterday pick for a race and return change info"""
    if not yesterday_pick:
        return False, None, None, 'First time pick recorded'

    prev_horse = yesterday_pick.get('horse', '')
    curr_horse = today_pick['horse']

    if prev_horse != curr_horse:
        prev_score = float(yesterday_pick.get('score', 0))
        curr_score  = today_pick['score']
        reason = (
            f"Pick changed from {prev_horse} (score {prev_score:.0f}) "
            f"to {curr_horse} (score {curr_score:.0f}) "
            f"+{curr_score - prev_score:.0f} pts difference"
        )
        return True, prev_horse, yesterday_pick.get('odds', ''), reason

    return False, None, None, 'Pick unchanged'


def save_picks(dry_run=False):
    """Main function: score races, detect changes, save to DynamoDB"""
    global _BETFAIR_LIVE_ODDS
    # Fetch live Betfair exchange prices once — used by all get_live_odds() calls
    print("Fetching live Betfair odds...")
    _BETFAIR_LIVE_ODDS = get_betfair_live_odds()
    if _BETFAIR_LIVE_ODDS:
        print(f"  ✅ Live prices loaded: {len(_BETFAIR_LIVE_ODDS)} horses")
    else:
        print("  ⚠️  No live prices — falling back to static RP odds dict")

    today = datetime.now().strftime('%Y-%m-%d')

    print(f"\n{'='*70}")
    print(f"  CHELTENHAM PICKS SAVE  -  {today}")
    print(f"{'='*70}\n")

    if not dry_run:
        ensure_table_exists()

    table = get_picks_table()
    today_picks = score_all_races()
    yesterday_picks = get_yesterday_picks(table, today) if not dry_run else {}

    # ── Load completed races (lock — never overwrite a pick once the race has run) ──
    completed_races = set()
    results_path = os.path.join(ROOT, 'barrys', 'race_results.json')
    try:
        with open(results_path) as _rf:
            _results = json.load(_rf).get('results', {})
        completed_races = {rn for rn, res in _results.items() if res.get('1st')}
    except Exception as _e:
        print(f"  ⚠️  Could not load race_results.json: {_e}")

    changes = []
    saved = 0
    unchanged = 0

    for race_name, pick in sorted(today_picks.items(), key=lambda x: x[1]['day']):
        is_completed = race_name in completed_races
        yesterday = yesterday_picks.get(race_name)
        changed, prev_horse, prev_odds, change_reason = detect_changes(pick, yesterday)

        # Completed races: never report as changed, lock the original pick
        if is_completed:
            changed = False
            change_reason = 'Race completed — pick locked'

        if changed:
            changes.append({
                'race': race_name,
                'from': prev_horse,
                'to':   pick['horse'],
                'reason': change_reason,
            })
            marker = '>> CHANGED <<'
        elif is_completed:
            marker = '   [LOCKED]  '
        else:
            marker = '             '

        print(f"  {marker}  [{pick['bet_tier']:<14}]  {race_name}")
        print(f"              -> {pick['horse']} @ {pick['odds']}  "
              f"[score {pick['score']}  |  {pick['tier']}  |  {pick['confidence']}]")
        if changed:
            print(f"              ** Was: {prev_horse} @ {prev_odds}")
        print()

        if not dry_run and not is_completed:
            item = {
                'race_name':         race_name,
                'pick_date':         today,
                'day':               pick['day'],
                'race_time':         pick['race_time'],
                'grade':             pick['grade'],
                'distance':          pick['distance'],
                'horse':             pick['horse'],
                'trainer':           pick['trainer'],
                'jockey':            pick['jockey'],
                'odds':              pick['odds'],
                'age':               str(pick['age']),
                'form':              pick['form'],
                'rating':            Decimal(str(pick['rating'])),
                'score':             Decimal(str(pick['score'])),
                'tier':              pick['tier'],
                'value_rating':      Decimal(str(round(pick['value_rating'], 1))),
                'second_score':      Decimal(str(pick['second_score'])),
                'second_horse_name': pick.get('second_horse_name', ''),
                'score_gap':         Decimal(str(pick['score_gap'])),
                'confidence':        pick['confidence'],
                # ── Strategy fields ──────────────────────────────────────────
                'is_grade1':         pick['is_grade1'],
                'is_skip_race':      pick['is_skip_race'],
                'bet_tier':          pick['bet_tier'],
                'bet_recommendation': pick['bet_recommendation'],
                # ─────────────────────────────────────────────────────────────
                'reasons':           pick['reasons'],
                'warnings':          pick['warnings'],
                'pick_changed':      changed,
                'previous_horse':    prev_horse or '',
                'previous_odds':     prev_odds or '',
                'change_reason':     change_reason,
                'updated_at':        datetime.now().isoformat(),
                # Full ordered field with scoring breakdown
                'all_horses':     [
                    {
                        'name':              h['name'],
                        'trainer':           h['trainer'],
                        'jockey':            h['jockey'],
                        'score':             Decimal(str(h['score'])),
                        'tier':              h['tier'],
                        'value_rating':      Decimal(str(round(h['value_rating'], 1))),
                        'tips':              h['tips'],
                        'warnings':          h['warnings'],
                        'cheltenham_record': h['cheltenham_record'],
                        'is_surebet_pick':   h['is_surebet_pick'],
                        'odds':              h.get('odds', '?'),
                    }
                    for h in pick['all_horses']
                ],
            }
            try:
                table.put_item(Item=item)
                saved += 1
            except Exception as e:
                print(f"  ERROR saving {race_name}: {e}")

    print(f"\n{'='*70}")
    print(f"  SUMMARY:")
    print(f"  Races processed: {len(today_picks)}")
    if not dry_run:
        print(f"  Saved to DynamoDB: {saved}")
    print(f"  Pick changes today: {len(changes)}")

    # Strategy tier breakdown
    tier_counts = {}
    for p in today_picks.values():
        t = p.get('bet_tier', 'OPINION_ONLY')
        tier_counts[t] = tier_counts.get(t, 0) + 1
    print(f"\n  STRATEGY TIERS:")
    for t in ['BETTING_PICK', 'WATCH_LIST', 'OPINION_ONLY']:
        print(f"    {t:<16}: {tier_counts.get(t, 0)}")

    if changes:
        print(f"\n  CHANGED PICKS:")
        for c in changes:
            print(f"    {c['race']}: {c['from']} -> {c['to']}")
            print(f"      Reason: {c['reason']}")
    else:
        print(f"\n  All picks unchanged from yesterday.")
    print(f"{'='*70}\n")

    return today_picks, changes


def show_history(race_name=None, days=14):
    """Show pick change history from DynamoDB"""
    table = get_picks_table()

    print(f"\n{'='*70}")
    print(f"  PICK HISTORY (last {days} days)")
    if race_name:
        print(f"  Race: {race_name}")
    print(f"{'='*70}\n")

    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    try:
        if race_name:
            response = table.query(
                KeyConditionExpression='race_name = :r AND pick_date >= :d',
                ExpressionAttributeValues={
                    ':r': race_name,
                    ':d': cutoff,
                },
                ScanIndexForward=False,   # newest first
            )
            items = response.get('Items', [])
        else:
            response = table.scan(
                FilterExpression='pick_date >= :d',
                ExpressionAttributeValues={':d': cutoff},
            )
            items = response.get('Items', [])

        if not items:
            print("  No history found.")
            return

        # Group by race
        by_race = defaultdict(list)
        for item in items:
            by_race[item['race_name']].append(item)

        for rname in sorted(by_race.keys()):
            entries = sorted(by_race[rname], key=lambda x: x['pick_date'], reverse=True)
            print(f"  {rname}")
            for e in entries:
                changed_marker = '>> CHANGED <<' if e.get('pick_changed') else '             '
                print(f"    {e['pick_date']}  {changed_marker}  "
                      f"{e['horse']} @ {e['odds']}  "
                      f"[{e['score']}/100  {e['confidence']}]")
                if e.get('pick_changed') and e.get('previous_horse'):
                    print(f"              Was: {e['previous_horse']} @ {e.get('previous_odds', '')}")
            print()

    except Exception as e:
        print(f"  Error reading history: {e}")


def lambda_handler(event, context):
    """
    AWS Lambda entry point for scheduled / on-demand execution.

    Schedule logic:
      - Pre-festival (before 10 Mar 2026): runs once per day.
        A rate(30 minutes) rule triggers this, but only the 06:00 UTC
        invocation actually saves; others are skipped.
      - Race days (10–13 Mar 2026, 11:00–18:30 UTC): saves every call
        so picks refresh every 30 minutes during live racing.
    """
    now_utc  = datetime.utcnow()
    today    = now_utc.date()

    festival_start = __import__('datetime').date(2026, 3, 10)
    festival_end   = __import__('datetime').date(2026, 3, 13)

    if today < festival_start:
        # Pre-festival: only run at the 06:xx trigger (hour == 6 or explicit call)
        source = event.get('source', '')
        if source == 'aws.events' and now_utc.hour != 6:
            return {
                'statusCode': 200,
                'body': f'Skipped — pre-festival non-6am trigger at {now_utc.strftime("%H:%M")} UTC'
            }
    elif festival_start <= today <= festival_end:
        # Race days: only run between 11:00 and 18:30 UTC
        if not (11 <= now_utc.hour < 19):
            return {
                'statusCode': 200,
                'body': f'Skipped — outside race hours at {now_utc.strftime("%H:%M")} UTC'
            }
    else:
        # Festival over
        return {
            'statusCode': 200,
            'body': 'Festival finished — no save needed'
        }

    try:
        picks, changes = save_picks(dry_run=False)
        return {
            'statusCode': 200,
            'body': f'Saved {len(picks)} picks. Changes: {len(changes)}'
        }
    except Exception as e:
        print(f'ERROR in lambda_handler: {e}')
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Save/view Cheltenham 2026 picks')
    parser.add_argument('--history', action='store_true', help='Show pick change history')
    parser.add_argument('--today',   action='store_true', help='Print today\'s picks without saving')
    parser.add_argument('--race',    type=str,  default=None, help='Filter history to a specific race')
    parser.add_argument('--days',    type=int,  default=14,   help='Days of history to show (default 14)')
    args = parser.parse_args()

    if args.history:
        show_history(race_name=args.race, days=args.days)
    elif args.today:
        save_picks(dry_run=True)
    else:
        save_picks(dry_run=False)

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

import sys, os
import json
import boto3
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
    "lossiemouth":            "7/2",
    "golden ace":             "7/1",
    "poniros":                "10/1",
    "alexei":                 "16/1",
    "anzadam":                "20/1",
    "workahead":              "100/1",

    # Cheltenham Gold Cup (Day 4)
    "gaelic warrior":         "6/1",
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

    # Ballymore / Baring Bingham Novices' Hurdle (Day 2)
    "no drama this end":      "4/1",
    "skylight hustle":        "6/1",
    "king rasko grey":        "8/1",
    "act of innocence":       "10/1",
    "i'll sort that":         "14/1",
    "doctor steinberg":       "3/1",   # Albert Bartlett FAVOURITE

    # Arkle Chase (Day 1) — confirmed 7 runners (Betfair 08/03/2026)
    "kopek des bordes":       "7/4",
    "lulamba":                "15/8",
    "kargese":                "6/1",
    "steel ally":             "14/1",
    "jax junior":             "20/1",
    "mambonumberfive":        "33/1",
    "hansard":                "100/1",

    # Stayers' Hurdle (Day 3)
    "teahupoo":               "9/4",
    "honesty policy":         "9/2",
    "kabral du mathan":       "5/1",
    "bob olinger":            "7/1",
    "ma shantou":             "8/1",
    "ballyburn":              "12/1",
    "impose toi":             "16/1",
    "wodhooh":                "16/1",
    "hewick":                 "33/1",
    "home by the lee":        "40/1",
    "flooring porter":        "40/1",
    "the yellow clay":        "40/1",
    "feet of a dancer":       "50/1",
    "potters charm":          "50/1",
    "doddiethegreat":         "66/1",
    "french ship":            "80/1",

    # Ryanair Chase (Day 3)
    "fact to file":           "4/5",
    "panic attack":           "20/1",
    "protektorat":            "25/1",
    "jagwar":                 "25/1",
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

    # Mares' Hurdle (Day 3)
    "jade de grugy":          "5/1",
    "take no chances":        "14/1",
    "murcia":                 "20/1",
    "jetara":                 "33/1",
    "dream on baby":          "33/1",
    "nurse susan":            "40/1",
    "park princess":          "50/1",
    "kateira":                "66/1",
    "lavida adiva":           "66/1",
    "listentoyourheart":      "66/1",
    "sunset marquesa":        "66/1",
    "that'll do moss":        "66/1",
    "siog geal":              "66/1",
    "baby kate":              "100/1",
    "la pinsonniere":         "100/1",
    "sotchi":                 "250/1",

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

    # Dawn Run Mares' Novices' Hurdle (Day 3)
    "bambino fever":          "4/5",
    "oldschool outlaw":       "4/1",
    "echoing silence":        "10/1",
    "la conquiere":           "14/1",

    # Champion Bumper (Day 2)
    "love sign d'aunou":      "9/2",
    "the irish avatar":       "8/1",
    "keep him company":       "9/1",
    "quiryn":                 "10/1",
    "bass hunter":            "14/1",

    # Mrs Paddy Power Mares Chase (Day 3)
    "dinoblue":               "6/4",

    # Fred Winter Juvenile Handicap Hurdle (Day 1)
    "manlaga":                "7/1",

    # National Hunt Chase (Day 1)
    "backmersackme":          "9/2",

    # Jack Richards Novices' Chase (Day 3) - additional
    "waterford whispers":     "12/1",
}


def get_live_odds(horse_name: str) -> str:
    """Look up live RP odds for a horse (case-insensitive).  Falls back to '?'."""
    return RP_LIVE_ODDS.get(horse_name.lower().strip(), "?")


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
    today = datetime.now().strftime('%Y-%m-%d')

    print(f"\n{'='*70}")
    print(f"  CHELTENHAM PICKS SAVE  -  {today}")
    print(f"{'='*70}\n")

    if not dry_run:
        ensure_table_exists()

    table = get_picks_table()
    today_picks = score_all_races()
    yesterday_picks = get_yesterday_picks(table, today) if not dry_run else {}

    changes = []
    saved = 0
    unchanged = 0

    for race_name, pick in sorted(today_picks.items(), key=lambda x: x[1]['day']):
        yesterday = yesterday_picks.get(race_name)
        changed, prev_horse, prev_odds, change_reason = detect_changes(pick, yesterday)

        if changed:
            changes.append({
                'race': race_name,
                'from': prev_horse,
                'to':   pick['horse'],
                'reason': change_reason,
            })
            marker = '>> CHANGED <<'
        else:
            marker = '             '

        print(f"  {marker}  [{pick['bet_tier']:<14}]  {race_name}")
        print(f"              -> {pick['horse']} @ {pick['odds']}  "
              f"[score {pick['score']}  |  {pick['tier']}  |  {pick['confidence']}]")
        if changed:
            print(f"              ** Was: {prev_horse} @ {prev_odds}")
        print()

        if not dry_run:
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
      - Race days (10–13 Mar 2026, 09:00–18:30 UTC): saves every call
        so picks refresh every 30 minutes during live racing.
    """
    # ── API Gateway GET: always serve current picks from DynamoDB ──────────
    # The time gate below is for the scheduled save; API reads bypass it.
    if event.get('httpMethod') == 'GET' or (
            'requestContext' in event and event.get('httpMethod') != 'POST'):
        try:
            table = get_picks_table()
            resp  = table.scan()
            items = resp.get('Items', [])
            # Paginate if necessary
            while 'LastEvaluatedKey' in resp:
                resp  = table.scan(ExclusiveStartKey=resp['LastEvaluatedKey'])
                items.extend(resp.get('Items', []))
            # Keep only the latest pick per race (highest pick_date then updated_at)
            latest = {}
            for item in items:
                rn = item.get('race_name', '')
                key = (item.get('pick_date', ''), item.get('updated_at', ''))
                if rn not in latest or key > (latest[rn].get('pick_date', ''), latest[rn].get('updated_at', '')):
                    latest[rn] = item

            # Group by festival day key — matches what the React frontend expects:
            # { success: true, days: { "Wednesday_11_March": [...] }, pick_date, total_changes }
            day_int_map = {
                1: 'Tuesday_10_March',
                2: 'Wednesday_11_March',
                3: 'Thursday_12_March',
                4: 'Friday_13_March',
            }
            # day_str_map handles items where 'day' was stored as the string key directly
            valid_day_keys = set(day_int_map.values())
            days = {}
            pick_date = None
            for item in latest.values():
                raw_day = item.get('day', 0)
                # 'day' may be an int (1-4) or already a string key like 'Wednesday_11_March'
                if isinstance(raw_day, str) and raw_day in valid_day_keys:
                    day_key = raw_day
                else:
                    try:
                        day_key = day_int_map.get(int(raw_day), f'Day_{raw_day}')
                    except (ValueError, TypeError):
                        day_key = f'Day_{raw_day}'
                if day_key not in days:
                    days[day_key] = []
                days[day_key].append(item)
                if not pick_date:
                    pick_date = item.get('pick_date', '')
            # Sort each day's picks by race_time
            for day_key in days:
                days[day_key].sort(key=lambda x: x.get('race_time', ''))

            payload = {
                'success': True,
                'days': days,
                'pick_date': pick_date or '',
                'total_changes': 0,
            }
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                },
                'body': json.dumps(payload, default=str),
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': str(e)}),
            }
    # ───────────────────────────────────────────────────────────────────────

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
        # Race days: only run between 09:00 and 18:30 UTC
        if not (9 <= now_utc.hour < 19):
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

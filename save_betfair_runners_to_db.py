"""
save_betfair_runners_to_db.py
Saves Betfair ANTEPOST runner lists for all 28 Cheltenham races to DynamoDB.
Table: CheltenhamRunnerValidation (PK=race_key, SK=scrape_date)
Table: CheltenhamHorseIntelligence (PK=horse_name, SK=race_key)
"""
import json, requests, boto3, sys, os
from datetime import date
from decimal import Decimal

ROOT = os.path.dirname(os.path.abspath(__file__))
TODAY = date.today().isoformat()
REGION = "eu-west-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)
client = boto3.client("dynamodb", region_name=REGION)

# ── Betfair config ────────────────────────────────────────────────────────
BETFAIR_EVENT_IDS = ["35129124", "35129125", "35129126", "35129127"]
with open(os.path.join(ROOT, "betfair-creds.json")) as f:
    CREDS = json.load(f)

BF_HEADERS = {
    "X-Application": CREDS["app_key"],
    "X-Authentication": CREDS["session_token"],
    "Content-Type": "application/json",
}

RACE_NAMES = {
    "day1_race1": "Supreme Novices Hurdle",
    "day1_race2": "Arkle Challenge Trophy",
    "day1_race3": "Ultima Handicap Chase",
    "day1_race4": "Unibet Champion Hurdle",
    "day1_race5": "Close Brothers Mares Hurdle",
    "day1_race6": "National Hunt Chase",
    "day1_race7": "Conditional Jockeys Hcap Hurdle",
    "day2_race1": "Ballymore Novices Hurdle",
    "day2_race2": "Brown Advisory Novices Chase",
    "day2_race3": "Coral Cup Handicap Hurdle",
    "day2_race4": "BetMGM Queen Mother Champion Chase",
    "day2_race5": "Glenfarclas Cross Country Chase",
    "day2_race6": "Dawn Run Mares Novices Hurdle",
    "day2_race7": "FBD NH Flat Race",
    "day3_race1": "Turners Novices Chase",
    "day3_race2": "Pertemps Final Handicap Hurdle",
    "day3_race3": "Ryanair Chase",
    "day3_race4": "Paddy Power Stayers Hurdle",
    "day3_race5": "Plate Handicap Chase",
    "day3_race6": "Boodles Juvenile Handicap Hurdle",
    "day3_race7": "Martin Pipe Conditional Jockeys Hurdle",
    "day4_race1": "JCB Triumph Hurdle",
    "day4_race2": "County Handicap Hurdle",
    "day4_race3": "Albert Bartlett Novices Hurdle",
    "day4_race4": "Cheltenham Gold Cup",
    "day4_race5": "Grand Annual Mares Chase",
    "day4_race6": "Champion Bumper",
    "day4_race7": "St James Place Foxhunter Chase",
}

MARKET_MAP = {
    "supreme novice hurdle": "day1_race1",
    "arkle chase": "day1_race2",
    "ultima handicap chase": "day1_race3",
    "champion hurdle": "day1_race4",
    "mares hurdle": "day1_race5",
    "national hunt challenge cup": "day1_race6",
    "turners novices hurdle": "day2_race1",
    "turners novice hurdle": "day2_race1",
    "betmgm cup handicap hurdle": "day2_race3",
    "brown advisory novice chase": "day2_race2",
    "queen mother champion chase": "day2_race4",
    "glenfarclas cross country": "day2_race5",
    "mares novice hurdle": "day2_race6",
    "champion bumper": "day4_race6",
    "jack richards novices": "day3_race1",
    "pertemps network final": "day3_race2",
    "ryanair chase": "day3_race3",
    "paddy power stayers hurdle": "day3_race4",
    "sun racing plate": "day3_race5",
    "mccoy contractors juvenile": "day3_race6",
    "martin pipe conditional": "day3_race7",
    "kim muir challenge cup": "day3_race7",
    "county handicap hurdle": "day4_race2",
    "triumph hurdle": "day4_race1",
    "albert bartlett": "day4_race3",
    "gold cup": "day4_race4",
    "johnny henderson grand annual": "day4_race5",
    "mrs paddy power mares chase": "day4_race5",
    "festival challenge cup": "day4_race7",
}


def map_market(name: str):
    n = name.lower()
    for kw, rk in MARKET_MAP.items():
        if kw in n:
            return rk
    return None


def ensure_table(tname, pk, sk=None):
    existing = client.list_tables()["TableNames"]
    if tname in existing:
        return dynamodb.Table(tname)
    ks = [{"AttributeName": pk, "KeyType": "HASH"}]
    ad = [{"AttributeName": pk, "AttributeType": "S"}]
    if sk:
        ks.append({"AttributeName": sk, "KeyType": "RANGE"})
        ad.append({"AttributeName": sk, "AttributeType": "S"})
    client.create_table(TableName=tname, KeySchema=ks, AttributeDefinitions=ad,
                        BillingMode="PAY_PER_REQUEST")
    client.get_waiter("table_exists").wait(TableName=tname)
    print(f"  Created table: {tname}")
    return dynamodb.Table(tname)


# ── Fetch markets ─────────────────────────────────────────────────────────
print(f"Fetching Betfair ANTEPOST markets for Cheltenham 2026 ...")
r = requests.post(
    "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/",
    headers=BF_HEADERS,
    json={"filter": {"eventIds": BETFAIR_EVENT_IDS, "marketTypeCodes": ["ANTEPOST_WIN"]},
          "marketProjection": ["RUNNER_DESCRIPTION", "EVENT", "MARKET_START_TIME"],
          "maxResults": "100"}, timeout=15)
markets = r.json()
print(f"  Got {len(markets)} markets")

# ── Organise runners by race_key ──────────────────────────────────────────
runners_by_race = {}
for m in markets:
    mname = m.get("marketName", "")
    rk = map_market(mname)
    if not rk or rk in runners_by_race:
        continue
    runners = [r.get("runnerName", "").strip()
               for r in m.get("runners", []) if r.get("status") != "REMOVED"]
    runners = [r for r in runners if r]
    runners_by_race[rk] = {"runners": runners, "market_name": mname,
                           "market_start": m.get("marketStartTime", "")[:10]}

print(f"  Mapped {len(runners_by_race)} races")

# ── Save to DynamoDB ──────────────────────────────────────────────────────
print("Saving to DynamoDB ...")
t_validation = ensure_table("CheltenhamRunnerValidation", "race_key", "scrape_date")
t_intel = ensure_table("CheltenhamHorseIntelligence", "horse_name", "race_key")

saved_races = 0
saved_horses = 0

for rk, data in sorted(runners_by_race.items()):
    runners = data["runners"]
    # Save race-level validation record
    t_validation.put_item(Item={
        "race_key": rk,
        "scrape_date": TODAY,
        "race_name": RACE_NAMES.get(rk, rk),
        "betfair_market": data["market_name"],
        "market_start": data["market_start"],
        "betfair_runners": runners,
        "betfair_runner_count": len(runners),
        "source": "betfair_antepost_win",
    })
    saved_races += 1

    # Save per-horse records
    for horse in runners:
        t_intel.put_item(Item={
            "horse_name": horse,
            "race_key": rk,
            "race_name": RACE_NAMES.get(rk, rk),
            "betfair_confirmed": True,
            "betfair_active": True,
            "scrape_date": TODAY,
            "source": "betfair_antepost_win",
        })
        saved_horses += 1

print(f"  Saved {saved_races} race validations")
print(f"  Saved {saved_horses} horse-race records")
print("Done.")

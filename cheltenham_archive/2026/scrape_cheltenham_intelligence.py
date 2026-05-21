"""
scrape_cheltenham_intelligence.py
══════════════════════════════════════════════════════════════════════════════
Scrapes GG.co.uk for Cheltenham 2026 horse intelligence + validates runners
against Betfair API declared entries. Stores results to DynamoDB.

Tables used:
  CheltenhamHorseIntelligence  (PK: horse_name, SK: race_key)
  CheltenhamRunnerValidation   (PK: race_key, SK: scrape_date)

Usage:
    python scrape_cheltenham_intelligence.py          # full run
    python scrape_cheltenham_intelligence.py --check  # print discrepancies only
    python scrape_cheltenham_intelligence.py --betfair # just Betfair runner check
"""

import sys, os, json, time, re, argparse
from datetime import datetime, date
from decimal import Decimal

import requests
from bs4 import BeautifulSoup
import boto3
from boto3.dynamodb.conditions import Key

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from cheltenham_full_fields_2026 import RACE_FULL_FIELDS

# ── Config ─────────────────────────────────────────────────────────────────
TODAY = date.today().isoformat()
REGION = "eu-west-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)

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

# GG.co.uk article URLs with key intelligence
GG_ARTICLES = [
    ("Supreme Novices Hurdle confirmations",
     "https://gg.co.uk/news/features/supreme-novices-hurdle-2026-runners-20-confirmed/"),
    ("Champion Hurdle confirmations",
     "https://gg.co.uk/news/features/champion-hurdle-2026-runners-nine-confirmed/"),
    ("Queen Mother Champion Chase",
     "https://gg.co.uk/news/features/13-remain-queen-mother-champion-chase-2026-runners/"),
    ("Turners Novices Hurdle (Mighty Park)",
     "https://gg.co.uk/news/features/mighty-park-not-among-turners-novices-hurdle-2026-runners/"),
    ("Ryanair Chase Jonbon",
     "https://gg.co.uk/news/ryanair-chase-2026-runners-fact-to-file-jonbon/"),
    ("Jonbon Aintree preference",
     "https://gg.co.uk/news/features/aintree-preferred-route-for-jonbon-over-ryanair/"),
    ("Day 1 confirmations roundup",
     "https://gg.co.uk/news/features/cheltenham-festival-day-one-runners-confirmations-roundup/"),
    ("Day 2 confirmations roundup",
     "https://gg.co.uk/news/cheltenham-festival-day-two-confirmations-round-up/"),
    ("Stayers Mares confirmations",
     "https://gg.co.uk/news/stayers-hurdle-mares-hurdle-confirmations-no-surprises-in-stayers-with-lossiemouth-still-in-mares/"),
    ("Gold Cup Envoi Allen",
     "https://gg.co.uk/news/features/envoi-allen-ready-for-career-swansong-in-cheltenham-gold-cup/"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://gg.co.uk/",
}


# ── GG.co.uk Scraper ────────────────────────────────────────────────────────

def scrape_gg_article(title: str, url: str) -> dict:
    """Fetch a GG.co.uk article and return structured intel."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if r.status_code != 200 or "doubleclick" in r.url:
            return {"title": title, "url": url, "status": f"blocked ({r.status_code})", "content": ""}
        soup = BeautifulSoup(r.text, "html.parser")
        # Extract article body
        body = soup.find("article") or soup.find("div", class_=re.compile(r"entry|post|content|article"))
        if body:
            text = body.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)
        # Trim and clean
        text = re.sub(r"\s+", " ", text)[:4000]
        # Extract horse names — look for capitalised word pairs
        horses = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b", text)
        # Filter noise words
        noise = {"The", "In", "At", "He", "She", "His", "Her", "Grand", "National", "Champion",
                 "Festival", "Horse", "Racing", "Gold", "Cup", "Hurdle", "Chase", "March"}
        horses = list(dict.fromkeys([h for h in horses if h.split()[0] not in noise]))[:30]
        return {
            "title": title,
            "url": url,
            "status": "ok",
            "scraped_at": datetime.utcnow().isoformat(),
            "content_snippet": text[:800],
            "horse_mentions": horses,
        }
    except Exception as e:
        return {"title": title, "url": url, "status": f"error: {e}", "content": ""}


def scrape_gg_race_page(race_key: str) -> list:
    """Try to get a GG.co.uk racecard page for the Cheltenham race."""
    # GG uses slug-based race pages — we try common patterns
    race_name = RACE_NAMES.get(race_key, "")
    slug = race_name.lower().replace(" ", "-").replace("'", "").replace("(", "").replace(")", "")
    urls_to_try = [
        f"https://gg.co.uk/horse-racing/cheltenham-festival/{slug}/",
        f"https://gg.co.uk/tips/cheltenham-festival/{slug}/",
        f"https://gg.co.uk/news/cheltenham-festival/{slug}-2026-runners/",
    ]
    for url in urls_to_try:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
            if r.status_code == 200 and "doubleclick" not in r.url:
                soup = BeautifulSoup(r.text, "html.parser")
                text = soup.get_text(separator=" ", strip=True)
                horses = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b", text)
                return list(dict.fromkeys(horses))[:40]
        except Exception:
            continue
    return []


# ── Betfair Runner Validation ───────────────────────────────────────────────

def load_betfair_creds() -> dict:
    creds_path = os.path.join(ROOT, "betfair-creds.json")
    with open(creds_path) as f:
        return json.load(f)


BETFAIR_EVENT_IDS = ["35129124", "35129125", "35129126", "35129127"]  # Cheltenham 10-13 Mar 2026


def betfair_get_cheltenham_markets(creds: dict) -> list:
    """Get Cheltenham 2026 festival ANTEPOST_WIN markets from Betfair."""
    headers = {
        "X-Application": creds["app_key"],
        "X-Authentication": creds["session_token"],
        "Content-Type": "application/json",
    }
    r = requests.post(
        "https://api.betfair.com/exchange/betting/rest/v1.0/listMarketCatalogue/",
        headers=headers,
        json={
            "filter": {
                "eventIds": BETFAIR_EVENT_IDS,
                "marketTypeCodes": ["ANTEPOST_WIN"],
            },
            "marketProjection": ["RUNNER_DESCRIPTION", "EVENT", "MARKET_START_TIME"],
            "maxResults": "100",
            "sort": "FIRST_TO_START",
        },
        timeout=15,
    )
    if r.status_code != 200:
        print(f"  Betfair market catalogue error: {r.status_code}")
        return []
    markets = r.json()
    print(f"  Found {len(markets)} ANTEPOST_WIN markets")
    return markets


def extract_runners_from_market(market: dict) -> list:
    """Extract active runner names directly from a market catalogue entry."""
    runners = market.get("runners", [])
    return [r.get("runnerName", "").strip() for r in runners if r.get("status") != "REMOVED"]


def match_market_to_race(market_name: str) -> str | None:
    """Try to map a Betfair market name to our race key."""
    name_lower = market_name.lower()
    mappings = [
        # Day 1
        ("supreme novice", "day1_race1"),
        ("arkle", "day1_race2"),
        ("ultima", "day1_race3"),
        ("champion hurdle", "day1_race4"),
        ("national hunt challenge", "day1_race6"),
        ("national hunt chase", "day1_race6"),
        # Day 2
        ("turners novices hurdle", "day2_race1"),
        ("turners novice hurdle", "day2_race1"),
        ("ballymore", "day2_race1"),
        ("brown advisory", "day2_race2"),
        ("jack richards", "day2_race2"),  # 2026 sponsor name for turners/brown advisory chase
        ("betmgm cup handicap hurdle", "day2_race3"),
        ("coral cup", "day2_race3"),
        ("queen mother", "day2_race4"),
        ("cross country", "day2_race5"),
        ("glenfarclas", "day2_race5"),
        ("mares novice", "day2_race6"),
        ("dawn run", "day2_race6"),
        ("fbd", "day2_race7"),
        ("champion bumper", "day4_race6"),
        # Day 3
        ("novices' limited handicap chase", "day3_race1"),
        ("novice limited handicap chase", "day3_race1"),
        ("pertemps", "day3_race2"),
        ("ryanair", "day3_race3"),
        ("stayers hurdle", "day3_race4"),
        ("paddy power stayers", "day3_race4"),
        ("sun racing plate", "day3_race5"),
        ("plate handicap chase", "day3_race5"),
        ("juvenile handicap hurdle", "day3_race6"),
        ("mccoy contractors", "day3_race6"),
        ("martin pipe", "day3_race7"),
        ("kim muir", "day3_race7"),  # Kim Muir = conditional/amateur  
        # Mares Hurdle — appears under both D1 and D3 in different forms
        ("mares hurdle", "day1_race5"),
        # Day 4
        ("triumph hurdle", "day4_race1"),
        ("county handicap hurdle", "day4_race2"),
        ("albert bartlett", "day4_race3"),
        ("gold cup", "day4_race4"),
        ("grand annual", "day4_race5"),
        ("mares chase", "day4_race5"),
        ("mrs paddy power", "day4_race5"),
        ("johnny henderson", "day4_race5"),
        ("foxhunter", "day4_race7"),
        ("festival challenge", "day4_race7"),
        ("hunters", "day4_race7"),
    ]
    for keyword, key in mappings:
        if keyword in name_lower:
            return key
    return None


# ── Cross-check Logic ───────────────────────────────────────────────────────

def cross_check_runners(betfair_runners: dict[str, list]) -> list:
    """Compare Betfair runners vs RACE_FULL_FIELDS. Return discrepancy report."""
    issues = []
    for race_key, bf_runners in sorted(betfair_runners.items()):
        our_runners = set(h.lower() for h in RACE_FULL_FIELDS.get(race_key, []))
        bf_set = set(h.lower() for h in bf_runners)

        # Horses in Betfair but NOT in our data
        missing_from_ours = [h for h in bf_runners if h.lower() not in our_runners]
        # Horses in our data but NOT on Betfair (possible scratching)
        not_on_betfair = [h for h in RACE_FULL_FIELDS.get(race_key, [])
                          if h.lower() not in bf_set]

        if missing_from_ours or not_on_betfair:
            issues.append({
                "race_key": race_key,
                "race_name": RACE_NAMES.get(race_key, race_key),
                "betfair_count": len(bf_runners),
                "our_count": len(RACE_FULL_FIELDS.get(race_key, [])),
                "missing_from_our_data": missing_from_ours,
                "possibly_scratched": not_on_betfair,
            })
    return issues


# ── DynamoDB Storage ────────────────────────────────────────────────────────

def ensure_table(table_name: str, pk: str, sk: str = None):
    """Ensure DynamoDB table exists, create if not."""
    client = boto3.client("dynamodb", region_name=REGION)
    existing = client.list_tables()["TableNames"]  # list of strings
    if table_name in existing:
        return dynamodb.Table(table_name)

    key_schema = [{"AttributeName": pk, "KeyType": "HASH"}]
    attr_defs = [{"AttributeName": pk, "AttributeType": "S"}]
    if sk:
        key_schema.append({"AttributeName": sk, "KeyType": "RANGE"})
        attr_defs.append({"AttributeName": sk, "AttributeType": "S"})

    client.create_table(
        TableName=table_name,
        KeySchema=key_schema,
        AttributeDefinitions=attr_defs,
        BillingMode="PAY_PER_REQUEST",
    )
    waiter = client.get_waiter("table_exists")
    waiter.wait(TableName=table_name)
    print(f"  Created DynamoDB table: {table_name}")
    return dynamodb.Table(table_name)


def save_horse_intelligence(horse_name: str, race_key: str, intel: dict):
    """Save per-horse intel to CheltenhamHorseIntelligence DynamoDB."""
    table = ensure_table("CheltenhamHorseIntelligence", "horse_name", "race_key")
    item = {
        "horse_name": horse_name,
        "race_key": race_key,
        "race_name": RACE_NAMES.get(race_key, race_key),
        "scrape_date": TODAY,
        "source": "gg.co.uk+betfair",
    }
    item.update({k: v for k, v in intel.items() if v is not None})
    # Convert floats for DynamoDB
    item = json.loads(json.dumps(item), parse_float=Decimal)
    table.put_item(Item=item)


def save_runner_validation(race_key: str, betfair_runners: list, issues: dict):
    """Save runner validation snapshot to CheltenhamRunnerValidation DynamoDB."""
    table = ensure_table("CheltenhamRunnerValidation", "race_key", "scrape_date")
    item = {
        "race_key": race_key,
        "scrape_date": TODAY,
        "race_name": RACE_NAMES.get(race_key, race_key),
        "betfair_runners": betfair_runners,
        "our_runners": RACE_FULL_FIELDS.get(race_key, []),
        "missing_from_our_data": issues.get("missing_from_our_data", []),
        "possibly_scratched": issues.get("possibly_scratched", []),
        "betfair_count": len(betfair_runners),
        "our_count": len(RACE_FULL_FIELDS.get(race_key, [])),
        "validated_at": datetime.utcnow().isoformat(),
    }
    table.put_item(Item=item)


def save_gg_intel(article: dict):
    """Save GG article intel to CheltenhamHorseIntelligence keyed by article."""
    table = ensure_table("CheltenhamHorseIntelligence", "horse_name", "race_key")
    # Save article-level intel; also save per-horse entries
    for horse in article.get("horse_mentions", []):
        item = {
            "horse_name": horse,
            "race_key": f"gg_article_{article['title'][:40].replace(' ', '_')}",
            "article_title": article["title"],
            "article_url": article["url"],
            "scrape_date": TODAY,
            "source": "gg.co.uk",
            "content_snippet": article.get("content_snippet", "")[:500],
        }
        item = json.loads(json.dumps(item), parse_float=Decimal)
        table.put_item(Item=item)


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Print discrepancies only, no DB write")
    parser.add_argument("--betfair", action="store_true", help="Only run Betfair validation")
    parser.add_argument("--gg-only", action="store_true", help="Only scrape GG.co.uk articles")
    args = parser.parse_args()

    print("=" * 70)
    print("  CHELTENHAM 2026 — INTELLIGENCE SCRAPER & RUNNER VALIDATOR")
    print(f"  {TODAY}")
    print("=" * 70)

    gg_results = []
    betfair_runners_by_race = {}
    all_discrepancies = []

    # ── Step 1: Scrape GG.co.uk intelligence articles ────────────────────
    if not args.betfair:
        print("\n[1] Scraping GG.co.uk intelligence articles ...")
        session = requests.Session()
        session.headers.update(HEADERS)

        # Also try the main cheltenham page which returns article snippets
        try:
            r = session.get("https://gg.co.uk/cheltenham-festival", timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                articles = soup.find_all(["h2", "h3", "p"])
                all_text = " ".join(a.get_text(separator=" ", strip=True) for a in articles)
                # Extract horse mentions from page
                horses = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b", all_text)
                noise = {"The", "In", "At", "He", "She", "His", "Her", "Grand", "National",
                         "Champion", "Festival", "Horse", "Racing", "Gold", "Cup", "Hurdle",
                         "Chase", "March", "Read", "Cheltenham", "Novices", "Bet", "Free"}
                horses = list(dict.fromkeys([h for h in horses if h.split()[0] not in noise]))[:50]
                # Save key text as intel
                gg_results.append({
                    "title": "GG.co.uk Cheltenham Hub",
                    "url": "https://gg.co.uk/cheltenham-festival",
                    "status": "ok",
                    "scraped_at": datetime.utcnow().isoformat(),
                    "content_snippet": all_text[:1500],
                    "horse_mentions": horses,
                })
                print(f"    GG cheltenham-festival hub          ✓  ({len(horses)} horse mentions)")
            else:
                print(f"    GG cheltenham-festival hub          ✗  {r.status_code}")
        except Exception as e:
            print(f"    GG cheltenham-festival hub          ✗  {e}")

        # Try individual articles
        for title, url in GG_ARTICLES:
            print(f"    {title[:50]:<50}", end=" ", flush=True)
            result = scrape_gg_article(title, url)
            status = result.get("status", "?")
            if status == "ok":
                nhorse = len(result.get("horse_mentions", []))
                print(f"✓  ({nhorse} horse mentions)")
            else:
                print(f"✗  {status}")
            gg_results.append(result)
            if not args.check:
                save_gg_intel(result)
            time.sleep(0.4)

        print(f"\n    Scraped {len(gg_results)} GG sources.")

    # ── Step 2: Betfair declared runners ─────────────────────────────────
    if not args.gg_only:
        print("\n[2] Checking Betfair ANTEPOST_WIN markets ...")
        try:
            creds = load_betfair_creds()
            markets = betfair_get_cheltenham_markets(creds)

            for market in markets:
                market_id = market.get("marketId")
                market_name = market.get("marketName", "")
                start_time = market.get("marketStartTime", "")[:10]

                race_key = match_market_to_race(market_name)
                if not race_key:
                    print(f"    [unmapped] {market_name}")
                    continue

                # Extract runners inline — no extra API call needed
                runners = extract_runners_from_market(market)
                # Only keep runners with "tidy" names (filter out empty)
                runners = [r for r in runners if r and len(r) > 2]

                if race_key not in betfair_runners_by_race:
                    betfair_runners_by_race[race_key] = runners
                    print(f"    {race_key} | {market_name[:45]:<45} | {len(runners)} runners")

        except FileNotFoundError:
            print("  betfair-creds.json not found — skipping Betfair validation")
        except Exception as e:
            print(f"  Betfair error: {e}")

    # ── Step 3: Cross-check & report ─────────────────────────────────────
    if betfair_runners_by_race:
        print("\n[3] Cross-checking runners vs our RACE_FULL_FIELDS ...")
        all_discrepancies = cross_check_runners(betfair_runners_by_race)

        if all_discrepancies:
            print(f"\n  ⚠  DISCREPANCIES FOUND in {len(all_discrepancies)} race(s):\n")
            for d in all_discrepancies:
                print(f"  {'─'*60}")
                print(f"  {d['race_key']} | {d['race_name']}")
                print(f"  Betfair: {d['betfair_count']} runners  |  Our data: {d['our_count']} runners")
                if d["missing_from_our_data"]:
                    print(f"  ▶ NOT in our data (add these): {', '.join(d['missing_from_our_data'])}")
                if d["possibly_scratched"]:
                    print(f"  ✗ Not on Betfair (possibly scratched): {', '.join(d['possibly_scratched'])}")
        else:
            print("  ✓ All races match Betfair declared runners!")

        # Save to DynamoDB (unless --check only)
        if not args.check:
            print("\n[4] Saving runner validation to DynamoDB ...")
            for race_key, runners in betfair_runners_by_race.items():
                issue = next((d for d in all_discrepancies if d["race_key"] == race_key), {})
                save_runner_validation(race_key, runners, issue)

                # Save each horse to CheltenhamHorseIntelligence
                for horse in runners:
                    save_horse_intelligence(horse, race_key, {
                        "betfair_confirmed": True,
                        "betfair_market_date": TODAY,
                    })

            print(f"  Saved {len(betfair_runners_by_race)} races to DynamoDB")

    # ── Step 4: GG article intel summary ─────────────────────────────────
    print("\n[5] GG.co.uk Key Intelligence Summary:")
    print("  " + "─" * 60)
    for r in gg_results:
        if r.get("status") == "ok" and r.get("content_snippet"):
            print(f"\n  [{r['title']}]")
            print(f"  {r['content_snippet'][:300]}")
            if r.get("horse_mentions"):
                print(f"  Horses: {', '.join(r['horse_mentions'][:12])}")

    # ── Step 5: Coverage check ────────────────────────────────────────────
    print("\n[6] Coverage: Races with Betfair data vs our 28 races:")
    all_keys = sorted(RACE_NAMES.keys())
    covered = set(betfair_runners_by_race.keys())
    for k in all_keys:
        status = "✓" if k in covered else "○"
        count = len(betfair_runners_by_race.get(k, []))
        our_count = len(RACE_FULL_FIELDS.get(k, []))
        label = RACE_NAMES.get(k, k)
        bf_str = f"{count} BF runners" if count else "no BF data"
        print(f"  {status} {k} | {label:<45} | {our_count} ours | {bf_str}")

    print("\n" + "=" * 70)
    print("  Done.")
    print("=" * 70)


if __name__ == "__main__":
    main()

"""
scrape_skysports_form.py
Scrapes Sky Sports Racing form profiles for all Cheltenham 2026 picks.

Pass 1: Discover horse IDs by scraping Cheltenham 2025 + key prep race results
Pass 2: Fetch each form profile page
Pass 3: Save structured form data to DynamoDB

Usage:
  python scrape_skysports_form.py             # full run
  python scrape_skysports_form.py --discover  # only find horse IDs, print dict
  python scrape_skysports_form.py --profiles  # assume IDs known, fetch profiles
"""
import re, json, os, sys, time, boto3, requests
from datetime import date, datetime
from bs4 import BeautifulSoup

ROOT   = os.path.dirname(os.path.abspath(__file__))
TODAY  = date.today().isoformat()
REGION = "eu-west-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)
ddb_client = boto3.client("dynamodb", region_name=REGION)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}

SKYSPORTS_PROFILE = "https://www.skysports.com/racing/form-profiles/horse/{id}/{slug}"
SKYSPORTS_RESULT  = "https://www.skysports.com/racing/results/full-result/{id}"

# ── Current picks (horse name -> race key + race name) ─────────────────────
CURRENT_PICKS = {}

# ── Source race result pages to search for horse IDs ──────────────────────
# Cheltenham 2025 Festival confirmed race IDs (from sidebar links)
# Day 2 (Mar 12): 1295281-1295287  — confirmed
# Day 1 (Mar 11): likely 1295274-1295280
# Day 3 (Mar 13): likely 1295288-1295294
# Day 4 (Mar 14): likely 1295295-1295301
CHELTENHAM_2025_RESULT_IDS = list(range(1295274, 1295302))

# Known Cheltenham Jan 24 2026 race result IDs (confirmed from sidebar)
CHELTENHAM_JAN26_RESULT_IDS = list(range(1352950, 1352958))

# Key prep race ranges — broad windows around known events
# Leopardstown Christmas Dec 26-29 2025: ~1349600-1350400
# Kempton Boxing Day Dec 26: ~1349700-1349800
# Haydock/Newbury Jan-Feb 2026: ~1353000-1356000
# Punchestown Dec 2025: ~1348000-1349000
PREP_RACE_RESULT_IDS = (
    list(range(1349600, 1350500)) +    # Leopardstown Christmas block
    list(range(1350500, 1351000, 3)) + # early Jan Irish
    list(range(1351000, 1353000, 5)) + # Jan UK/Irish
    list(range(1353000, 1356000, 3)) + # late Jan - Mar UK/Irish
    list(range(1348000, 1349600, 5))   # Dec 2025 UK
)

# ── ID map loaded from DB or file ──────────────────────────────────────────
HORSE_ID_MAP_FILE = os.path.join(ROOT, "_skysports_horse_ids.json")


def load_id_map():
    if os.path.exists(HORSE_ID_MAP_FILE):
        with open(HORSE_ID_MAP_FILE) as f:
            return json.load(f)
    return {}


def save_id_map(m):
    with open(HORSE_ID_MAP_FILE, "w") as f:
        json.dump(m, f, indent=2, ensure_ascii=False)


def name_to_slug(name: str) -> str:
    """Convert 'Some Horse (IRE)' → 'some-horse-ire'"""
    slug = re.sub(r"[^a-z0-9 ]", "", name.lower())
    return re.sub(r"\s+", "-", slug.strip())


# ── Pass 1: Discover horse IDs ─────────────────────────────────────────────

def extract_horse_ids_from_result_page(result_id: int) -> dict:
    """Fetch a Sky Sports race result page, return {display_name_lower: (id, slug)}"""
    url = f"https://www.skysports.com/racing/results/full-result/{result_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
        if resp.status_code != 200:
            return {}
        # Verify this is a race result page with horse links
        if 'form-profiles/horse' not in resp.text:
            return {}
        # Extract horse profile links: /racing/form-profiles/horse/(\d+)/([\w-]+)
        matches = re.findall(
            r'/racing/form-profiles/horse/(\d+)/([\w-]+)', resp.text)
        result = {}
        for horse_id, slug in set(matches):  # deduplicate
            display = re.sub(r'-+', ' ', slug).strip()
            result[display.lower()] = (int(horse_id), slug)
        return result
    except Exception:
        return {}


def discover_horse_ids(target_horses: list, existing_map: dict) -> dict:
    """
    Fetch race result pages to discover Sky Sports horse IDs.
    Returns updated id_map: {horse_name_lower: {"id": int, "slug": str}}
    """
    remaining = set(h.lower() for h in target_horses) - set(existing_map.keys())
    if not remaining:
        print("  All horse IDs already known.")
        return existing_map

    id_map = dict(existing_map)
    # Try Cheltenham 2025 first (highest hit rate), then Jan 2026, then prep races
    all_ids = CHELTENHAM_2025_RESULT_IDS + CHELTENHAM_JAN26_RESULT_IDS + PREP_RACE_RESULT_IDS
    found_count = 0
    total_fetched = 0
    total_pages_with_horses = 0

    print(f"  Searching for {len(remaining)} horse IDs ...")
    for rid in all_ids:
        if not remaining:
            break
        found = extract_horse_ids_from_result_page(rid)
        total_fetched += 1
        if found:
            total_pages_with_horses += 1
            for display_lower, (horse_id, slug) in found.items():
                for target in list(remaining):
                    # Clean both strings for comparison
                    t_clean = re.sub(r'[^a-z0-9 ]', '', target)
                    d_clean = re.sub(r'[^a-z0-9 ]', '', display_lower)
                    if t_clean == d_clean or t_clean in d_clean or d_clean in t_clean:
                        id_map[target] = {"id": horse_id, "slug": slug}
                        remaining.discard(target)
                        found_count += 1
                        print(f"    ✓ {target} → id={horse_id} (result {rid})")
        if total_fetched % 50 == 0:
            print(f"    ... {total_fetched} pages checked, {found_count} found, "
                  f"{len(remaining)} remaining")
        time.sleep(0.2)

    print(f"  Done: checked {total_fetched} pages, {total_pages_with_horses} had horse links")
    print(f"  Found {found_count} IDs | Still missing: {len(remaining)}")
    if remaining:
        print(f"  Missing: {sorted(remaining)}")
    return id_map


# ── Pass 2: Fetch form profiles ────────────────────────────────────────────

def parse_vital_stats(soup: BeautifulSoup) -> dict:
    """Extract vital stats table from profile page."""
    stats = {}
    table = soup.find("table")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            cells = [td.get_text(strip=True) for td in row.find_all("td")]
            if len(cells) >= 6:
                label = cells[0]
                if label in ("Season (Jump)", "Lifetime (Jump)", "Season (Flat)", "Lifetime (Flat)"):
                    stats[label] = {
                        "runs": cells[1], "wins": cells[2],
                        "places": cells[3], "unplaced": cells[4],
                        "win_pct": cells[5], "per_run": cells[6] if len(cells) > 6 else ""
                    }
    return stats


def parse_form_history(soup: BeautifulSoup) -> list:
    """Extract recent race history from profile page."""
    form_items = []
    # Form section contains date + position text
    form_section = soup.find("section", class_=re.compile("form", re.I))
    if not form_section:
        # Try to find form data differently
        for div in soup.find_all("div"):
            text = div.get_text()
            if "Weight:" in text and "Trainer:" in text:
                form_section = div
                break

    if not form_section:
        return form_items

    # Parse each race entry
    text = form_section.get_text(separator="\n")
    races = re.split(r'\n\d{1,2} \w{3}', text)
    for i, block in enumerate(races[1:], 1):
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        entry = {"raw": block[:200].strip()}
        for line in lines:
            if line.startswith("Weight:"):
                entry["weight"] = line.replace("Weight:", "").strip()
            elif line.startswith("Winner:"):
                entry["winner"] = line.replace("Winner:", "").strip()
            elif line.startswith("OR:"):
                try:
                    entry["or_rating"] = int(line.replace("OR:", "").strip())
                except ValueError:
                    pass
            elif line.startswith("Trainer:"):
                entry["trainer"] = line.replace("Trainer:", "").strip()
            elif line.startswith("Jockey:"):
                entry["jockey"] = line.replace("Jockey:", "").strip()
            elif "Cheltenham" in line or "Cheltenham" in block:
                entry["cheltenham"] = True
        form_items.append(entry)
        if len(form_items) >= 8:  # last 8 runs
            break
    return form_items


def fetch_form_profile(horse_name: str, horse_id: int, slug: str) -> dict | None:
    """Fetch Sky Sports form profile page and parse key data."""
    url = f"https://www.skysports.com/racing/form-profiles/horse/{horse_id}/{slug}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            print(f"    HTTP {resp.status_code} for {horse_name}")
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        profile_text = resp.text

        # Extract basic info via regex (more reliable than soup for this page)
        age_match = re.search(r'Age:\s*(\d+)', profile_text)
        sex_match = re.search(r'Sex:\s*([^\n<]+)', profile_text)
        breeding_match = re.search(r'Breeding:\s*([^\n<]+)', profile_text)
        trainer_match = re.search(r'Trainer:.*?>([\w\s\.]+)<', profile_text)
        owner_match = re.search(r'Owner:\s*([^\n<]+)', profile_text)

        # Vital stats from table
        vital_stats = parse_vital_stats(soup)

        # OR ratings - find all occurrences of "OR: {number}"
        or_ratings = [int(m) for m in re.findall(r'OR:\s*(\d+)', profile_text)]
        latest_or = or_ratings[0] if or_ratings else None

        # Win percentage from lifetime stats
        win_pct = ""
        per_run = ""
        if "Lifetime (Jump)" in vital_stats:
            win_pct = vital_stats["Lifetime (Jump)"].get("win_pct", "")
            per_run = vital_stats["Lifetime (Jump)"].get("per_run", "")

        # Cheltenham mentions
        cheltenham_wins = len(re.findall(r'Winner:\s*' + re.escape(horse_name), profile_text, re.I))
        cheltenham_mentions = profile_text.lower().count("cheltenham")

        # Form string - last 6 results (positions like 1, 2, 3, F, P, etc.)
        # Sky Sports shows results like "14 ran" or "1 ran" with position
        form_snippets = re.findall(
            r'(\d{1,2} \w{3})\s*(\d+) ran\s*\nWeight:', profile_text)

        # Recent racing destinations
        venues = re.findall(
            r'Race details:\s*\[([^\]]+)\]', profile_text)[:6]

        return {
            "horse_name": horse_name,
            "skysports_id": horse_id,
            "skysports_slug": slug,
            "skysports_url": url,
            "scrape_date": TODAY,
            "age": int(age_match.group(1)) if age_match else None,
            "sex": sex_match.group(1).strip() if sex_match else "",
            "breeding": breeding_match.group(1).strip() if breeding_match else "",
            "trainer": trainer_match.group(1).strip() if trainer_match else "",
            "owner": owner_match.group(1).strip() if owner_match else "",
            "latest_or": latest_or,
            "win_pct_lifetime": win_pct,
            "per_run_lifetime": per_run,
            "vital_stats": json.dumps(vital_stats),
            "festival_wins_on_page": cheltenham_wins,
            "cheltenham_mentions": cheltenham_mentions,
            "recent_venues": venues[:5],
            "or_history": or_ratings[:8],
        }
    except Exception as e:
        print(f"    Error fetching {horse_name}: {e}")
        return None


# ── Pass 3: Save to DynamoDB ───────────────────────────────────────────────

def ensure_table(table_name: str, pk: str, sk: str = None):
    existing = ddb_client.list_tables()["TableNames"]
    if table_name in existing:
        return dynamodb.Table(table_name)
    ks = [{"AttributeName": pk, "KeyType": "HASH"}]
    ad = [{"AttributeName": pk, "AttributeType": "S"}]
    if sk:
        ks.append({"AttributeName": sk, "KeyType": "RANGE"})
        ad.append({"AttributeName": sk, "AttributeType": "S"})
    ddb_client.create_table(
        TableName=table_name, KeySchema=ks, AttributeDefinitions=ad,
        BillingMode="PAY_PER_REQUEST")
    ddb_client.get_waiter("table_exists").wait(TableName=table_name)
    print(f"  Created DynamoDB table: {table_name}")
    return dynamodb.Table(table_name)


def save_form_profile(table, profile: dict):
    """Save form profile to DynamoDB, converting types correctly."""
    item = {}
    for k, v in profile.items():
        if v is None or v == "" or v == [] or v == {}:
            continue
        if isinstance(v, bool):
            item[k] = v
        elif isinstance(v, int):
            from decimal import Decimal
            item[k] = Decimal(str(v))
        elif isinstance(v, float):
            from decimal import Decimal
            item[k] = Decimal(str(round(v, 4)))
        elif isinstance(v, list):
            if all(isinstance(x, int) for x in v):
                from decimal import Decimal
                item[k] = [Decimal(str(x)) for x in v]
            else:
                item[k] = [str(x) for x in v]
        else:
            item[k] = str(v)
    table.put_item(Item=item)


# ── Load current picks from DynamoDB ──────────────────────────────────────

def load_current_picks() -> dict:
    """Returns {horse_name_lower: {race_name, horse, score}} from CheltenhamPicks."""
    try:
        t = dynamodb.Table("CheltenhamPicks")
        r = t.scan(ProjectionExpression="race_name, horse, score")
        picks = {}
        for item in r["Items"]:
            horse = item.get("horse", "").strip()
            if horse:
                picks[horse.lower()] = {
                    "horse": horse,
                    "race_name": item.get("race_name", ""),
                    "score": int(item.get("score", 0)),
                }
        # De-duplicate: keep highest score per horse
        deduped = {}
        for k, v in picks.items():
            if k not in deduped or v["score"] > deduped[k]["score"]:
                deduped[k] = v
        return deduped
    except Exception as e:
        print(f"  Warning: could not load picks from DynamoDB: {e}")
        return {}


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    mode_discover = "--discover" in sys.argv
    mode_profiles = "--profiles" in sys.argv

    print("=" * 68)
    print("  SKY SPORTS FORM PROFILE SCRAPER — Cheltenham 2026")
    print(f"  Date: {TODAY}")
    print("=" * 68)

    # Load picks
    print("\n[1] Loading current Cheltenham picks ...")
    picks = load_current_picks()
    if not picks:
        print("  No picks found — check DynamoDB CheltenhamPicks table!")
        return
    target_horses = [v["horse"] for v in picks.values()]
    print(f"  {len(target_horses)} unique horses to look up")
    for h in sorted(target_horses):
        print(f"    {h}")

    # Load existing ID map
    id_map = load_id_map()
    print(f"\n[2] Horse ID discovery (have {len(id_map)} cached IDs) ...")

    if not mode_profiles:
        id_map = discover_horse_ids(target_horses, id_map)
        save_id_map(id_map)
        print(f"\n  ID map saved: {len(id_map)} horses → {HORSE_ID_MAP_FILE}")

    if mode_discover:
        print("\n  Discovery mode complete. Exiting.")
        return

    # Fetch form profiles
    print("\n[3] Fetching Sky Sports form profiles ...")
    table = ensure_table("CheltenhamFormProfiles", "horse_name")
    fetched = 0
    missed = []

    for horse_lower, pick_info in sorted(picks.items()):
        horse = pick_info["horse"]
        if horse_lower not in id_map:
            print(f"  ✗ {horse} — no Sky Sports ID found, skipping")
            missed.append(horse)
            continue

        entry = id_map[horse_lower]
        horse_id = entry["id"]
        slug = entry["slug"]

        print(f"  Fetching: {horse} (id={horse_id}) ...")
        profile = fetch_form_profile(horse, horse_id, slug)
        if profile:
            # Merge race info
            profile["race_name"] = pick_info.get("race_name", "")
            profile["pick_score"] = pick_info.get("score", 0)
            save_form_profile(table, profile)
            fetched += 1
            print(f"    ✓ Saved: OR={profile.get('latest_or')}, "
                  f"Win%={profile.get('win_pct_lifetime')}, "
                  f"Cheltenham mentions={profile.get('cheltenham_mentions')}")
        else:
            missed.append(horse)
        time.sleep(0.5)  # polite delay

    print(f"\n[4] Summary")
    print(f"  Saved:   {fetched} form profiles to DynamoDB:CheltenhamFormProfiles")
    if missed:
        print(f"  Missed:  {len(missed)} horses")
        for h in missed:
            print(f"    - {h}")
    print(f"\nDone.")


if __name__ == "__main__":
    main()

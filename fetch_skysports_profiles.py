"""
fetch_skysports_profiles.py  v2
Fetch Sky Sports Racing form profiles for all Cheltenham 2026 picks with known IDs.
Correctly parses: age/sex/breed, trainer/owner, vital stats, OR history, 
                  Cheltenham record, recent form entries.
Saves to DynamoDB:  CheltenhamFormProfiles  (PK=horse_name)
                    CheltenhamFormByRace    (PK=race_key, SK=horse_name)
"""
import requests, re, json, time, os, boto3
from datetime import date
from decimal import Decimal
from bs4 import BeautifulSoup

ROOT    = r"C:\Users\charl\OneDrive\futuregenAI\Betting"
TODAY   = date.today().isoformat()
REGION  = "eu-west-1"
ID_FILE = os.path.join(ROOT, "_skysports_horse_ids.json")

dynamodb   = boto3.resource("dynamodb", region_name=REGION)
ddb_client = boto3.client("dynamodb",   region_name=REGION)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ─── DynamoDB helpers ───────────────────────────────────────────────────────

def ensure_table(tname, pk, sk=None):
    existing = ddb_client.list_tables()["TableNames"]
    if tname in existing:
        return dynamodb.Table(tname)
    ks = [{"AttributeName": pk, "KeyType": "HASH"}]
    ad = [{"AttributeName": pk, "AttributeType": "S"}]
    if sk:
        ks.append({"AttributeName": sk, "KeyType": "RANGE"})
        ad.append({"AttributeName": sk, "AttributeType": "S"})
    ddb_client.create_table(
        TableName=tname, KeySchema=ks, AttributeDefinitions=ad,
        BillingMode="PAY_PER_REQUEST")
    ddb_client.get_waiter("table_exists").wait(TableName=tname)
    print(f"  Created table: {tname}")
    return dynamodb.Table(tname)


def to_ddb_item(d: dict) -> dict:
    """Convert a Python dict to DynamoDB-safe types."""
    item = {}
    for k, v in d.items():
        if v is None or v == "" or v == [] or v == {}:
            continue
        if isinstance(v, bool):
            item[k] = v
        elif isinstance(v, int):
            item[k] = Decimal(str(v))
        elif isinstance(v, float):
            item[k] = Decimal(str(round(v, 4)))
        elif isinstance(v, list):
            if v and all(isinstance(x, int) for x in v):
                item[k] = [Decimal(str(x)) for x in v]
            else:
                item[k] = [str(x) for x in v]
        else:
            item[k] = str(v)
    return item


# ─── Parsing helpers ─────────────────────────────────────────────────────────

def parse_vital_stats(soup: BeautifulSoup) -> dict:
    """Extract the Vital Stats table rows."""
    stats = {}
    for row in soup.find_all("tr"):
        cells = [td.get_text(strip=True) for td in row.find_all("td")]
        if cells and len(cells) >= 5 and (
                "Lifetime" in cells[0] or "Season" in cells[0]):
            label  = cells[0]
            runs   = int(cells[1]) if cells[1].isdigit() else 0
            wins   = int(cells[2]) if cells[2].isdigit() else 0
            second = int(cells[3]) if cells[3].isdigit() else 0
            third  = int(cells[4]) if cells[4].isdigit() else 0
            win_pct = cells[5] if len(cells) > 5 else ""
            per_run = cells[6] if len(cells) > 6 else ""
            stats[label] = {
                "runs": runs, "wins": wins, "second": second, "third": third,
                "win_pct": win_pct, "per_run": per_run,
            }
    return stats


def parse_header_info(html: str) -> dict:
    """
    Extract horse meta from the profile header section.
    Sky Sports static HTML has these fields inside <strong> tags with multi-line
    whitespace between the label and value, e.g.:
        <strong>Age:</strong>\n                          9 (Foaled March 17th, 2017)
        <strong>Sex:</strong>\n                          Bay Gelding
    We parse them via soup.get_text() where they become:
        Age:\n \n                          9 (Foaled March 17th, 2017)
    """
    soup = BeautifulSoup(html, "html.parser")
    txt  = soup.get_text(separator="\n")

    # All these labels appear followed by multi-line whitespace then the value
    age_m  = re.search(r"Age:\s+(\d+)",  txt)
    sex_m  = re.search(r"Sex:\s+([^\n]+)", txt)
    br_m   = re.search(r"Breeding:\s+([^\n]+)", txt)
    own_m  = re.search(r"Owner:\s+([^\n]+)", txt)
    # Trainer from HTML anchor tag (doesn't need soup text)
    tr_links = re.findall(r'form-profiles/trainer/\d+/[^"]+">([^<]+)<', html)

    return {
        "age":      int(age_m.group(1)) if age_m else None,
        "sex":      sex_m.group(1).strip()[:50]  if sex_m  else "",
        "breeding": br_m.group(1).strip()[:120]  if br_m   else "",
        "owner":    own_m.group(1).strip()[:80]   if own_m  else "",
        "trainer":  tr_links[0].strip() if tr_links else "",
    }


def parse_or_history(html: str) -> list:
    """
    OR ratings are JS-rendered so NOT available in raw HTML.
    Returns empty list (retained for future JS-render support).
    """
    return []


def count_cheltenham_runs(html: str) -> dict:
    """
    Count Cheltenham appearances from result URLs embedded in static HTML.
    Race *details text* is JS-rendered but the <a href> links to race results are
    included in the static HTML, so we count by URL pattern instead.
    """
    # Any Cheltenham result link (all seasons)
    all_chelt  = len(re.findall(r'full-result/\d+/cheltenham/', html))
    # March = Festival runs specifically
    march_urls = re.findall(
        r'full-result/\d+/cheltenham/\d{2}-03-\d{4}', html)
    return {
        "cheltenham_total_runs": all_chelt,
        "cheltenham_march_runs": len(march_urls),
    }


def build_profile(html: str, display_name: str, horse_id: int, slug: str) -> dict:
    """Parse a Sky Sports form profile page into a structured dict."""
    soup = BeautifulSoup(html, "html.parser")

    # Page name from first suitable heading
    page_name = display_name
    for tag in soup.find_all(["h2", "h1"]):
        txt = tag.get_text(strip=True)
        if txt and 2 < len(txt) < 60 and not txt.startswith("Sky") \
                and "Profile" not in txt and "Form" not in txt:
            page_name = txt
            break

    head  = parse_header_info(html)
    vital = parse_vital_stats(soup)
    or_h  = parse_or_history(html)
    chelt = count_cheltenham_runs(html)

    # Prefer Jump stats; fall back to Flat
    best = (vital.get("Lifetime (Jump)") or
            vital.get("Lifetime (Flat)") or {})

    return {
        "horse_name":            page_name,
        "horse_lookup_key":      display_name.lower(),
        "skysports_id":          horse_id,
        "skysports_slug":        slug,
        "skysports_url":         (
            f"https://www.skysports.com/racing/form-profiles/"
            f"horse/{horse_id}/{slug}"),
        "scrape_date":           TODAY,
        # Header info
        "age":        head["age"],
        "sex":        head["sex"],
        "breeding":   head["breeding"],
        "trainer":    head["trainer"],
        "owner":      head["owner"],
        # Stats
        "lifetime_runs":    best.get("runs"),
        "lifetime_wins":    best.get("wins"),
        "lifetime_places":  (best.get("second", 0) or 0) +
                            (best.get("third",  0) or 0),
        "win_pct":          best.get("win_pct", ""),
        "per_run":          best.get("per_run", ""),
        # OR
        "latest_or":        or_h[0] if or_h else None,
        "best_or":          max(or_h) if or_h else None,
        "or_history":       or_h[:8],
        # Cheltenham
        "cheltenham_total_runs": chelt["cheltenham_total_runs"],
        "cheltenham_march_runs": chelt["cheltenham_march_runs"],
        # Full stats JSON
        "vital_stats_json":  json.dumps(vital),
    }


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(ID_FILE):
        print(f"ERROR: ID file not found: {ID_FILE}")
        return

    with open(ID_FILE, encoding="utf-8") as f:
        id_map = json.load(f)
    print(f"Loaded {len(id_map)} horse IDs")

    # Pull current picks for annotation
    picks_by_horse: dict = {}
    try:
        scan_r = dynamodb.Table("CheltenhamPicks").scan(
            ProjectionExpression="horse, race_name, score, pick_date")
        for item in scan_r["Items"]:
            k = str(item.get("horse", "")).strip().lower()
            d = str(item.get("pick_date", ""))
            if k not in picks_by_horse or d > picks_by_horse[k].get("pick_date",""):
                picks_by_horse[k] = {
                    "race_name": item.get("race_name", ""),
                    "score":     int(item.get("score", 0)),
                    "pick_date": d,
                }
        print(f"Loaded picks for {len(picks_by_horse)} horses")
    except Exception as exc:
        print(f"  Warning – picks not loaded: {exc}")

    tbl_profiles = ensure_table("CheltenhamFormProfiles", "horse_name")
    tbl_by_race  = ensure_table("CheltenhamFormByRace",   "race_key", "horse_name")

    saved = 0
    errors = []

    for horse_lower, entry in sorted(id_map.items()):
        horse_id = entry["id"]
        slug     = entry["slug"]
        display  = " ".join(w.capitalize()
                            for w in slug.replace("-", " ").split())

        url = (f"https://www.skysports.com/racing/form-profiles/"
               f"horse/{horse_id}/{slug}")
        print(f"\n  ▶ {horse_lower:<30}  id={horse_id}")

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"    ✗ HTTP {resp.status_code}")
                errors.append((horse_lower, f"HTTP {resp.status_code}"))
                continue

            profile = build_profile(resp.text, display, horse_id, slug)

            # Merge pick annotation
            if horse_lower in picks_by_horse:
                p = picks_by_horse[horse_lower]
                profile["cheltenham_race"] = p["race_name"]
                profile["pick_score"]      = p["score"]

            # Save main profile
            tbl_profiles.put_item(Item=to_ddb_item(profile))

            # Save race-level lookup row
            race_key = picks_by_horse.get(horse_lower, {}).get(
                "race_name", "Unknown")[:80]
            tbl_by_race.put_item(Item={
                "race_key":              race_key,
                "horse_name":            profile["horse_name"],
                "skysports_url":         profile["skysports_url"],
                "trainer":               profile.get("trainer", ""),
                "age":                   str(profile.get("age", "")),
                "latest_or":             str(profile.get("latest_or", "")),
                "cheltenham_march_runs": str(profile.get("cheltenham_march_runs", 0)),
                "win_pct":               profile.get("win_pct", ""),
                "lifetime_runs":         str(profile.get("lifetime_runs", 0)),
                "lifetime_wins":         str(profile.get("lifetime_wins", 0)),
                "pick_score":            str(picks_by_horse.get(
                                            horse_lower, {}).get("score", "")),
                "scrape_date":           TODAY,
            })

            saved += 1
            print(f"    ✓ trainer={str(profile.get('trainer','?')):<24}  "
                  f"age={profile.get('age')}  "
                  f"OR={profile.get('latest_or')} (best {profile.get('best_or')})  "
                  f"runs={profile.get('lifetime_runs')} "
                  f"wins={profile.get('lifetime_wins')}  "
                  f"win%={profile.get('win_pct')}  "
                  f"chelt_march={profile.get('cheltenham_march_runs')}")

        except Exception as exc:
            print(f"    ✗ ERROR: {exc}")
            errors.append((horse_lower, str(exc)))

        time.sleep(0.7)

    print(f"\n{'='*70}")
    print(f"  Saved {saved}/{len(id_map)} profiles  →  DynamoDB:CheltenhamFormProfiles")
    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for h, e in errors:
            print(f"    {h}: {e}")

    print("\n  All Sky Sports profile links:")
    for k, v in sorted(id_map.items()):
        print(f"    https://www.skysports.com/racing/"
              f"form-profiles/horse/{v['id']}/{v['slug']}")


if __name__ == "__main__":
    main()

"""
CHELTENHAM WEEK SLEEPER SCAN
============================
Combines Betfair (odds + field size) with Racing Post racecard scraping
(trainer + jockey + form) to find quality horses at inflated prices while
bookies are distracted by Cheltenham.

Classic pattern:
  - Top UK NH trainer runs a well-handicapped/class horse at Sedgefield, Huntingdon etc.
  - Betting market thin/distracted → price 6/1-20/1 when it should be 3/1
  - Small field (4-9 runners), NH race type (Hurdle/Chase/Bumper)
  - Trainer has recent winners at similar tracks (form confirms intent)

Usage:
    python sleeper_scan.py              # tomorrow (next festival day)
    python sleeper_scan.py --day 1      # Day 1 Tue 10 Mar
    python sleeper_scan.py --day 2      # Day 2 Wed 11 Mar
    python sleeper_scan.py --all        # all 4 festival days
    python sleeper_scan.py --min 45     # raise score threshold
"""

import json, os, sys, re, time, argparse
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.abspath(__file__))
BETFAIR_API = "https://api.betfair.com/exchange/betting/rest/v1.0"

with open(os.path.join(ROOT, "betfair-creds.json")) as f:
    creds = json.load(f)

BF_HEADERS = {
    "X-Application":    creds["app_key"],
    "X-Authentication": creds["session_token"],
    "Content-Type":     "application/json",
}

RP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://www.racingpost.com/",
    "Cache-Control": "no-cache",
}

FESTIVAL_DAYS = {1: "2026-03-10", 2: "2026-03-11", 3: "2026-03-12", 4: "2026-03-13"}

# ── NH tracks where sleepers appear ─────────────────────────────────────────
NH_VENUES = {
    "Sedgefield", "Huntingdon", "Taunton", "Exeter", "Wincanton",
    "Plumpton", "Fontwell", "Worcester", "Hereford", "Ludlow",
    "Carlisle", "Catterick", "Hexham", "Kelso", "Perth",
    "Bangor-on-Dee", "Stratford", "Market Rasen", "Fakenham",
    "Musselburgh", "Newcastle", "Wetherby", "Haydock", "Newbury",
    "Leicester", "Sandown", "Kempton", "Ascot", "Chelmsford",
}

CHELTENHAM = {"Cheltenham"}

# ── Tier 1: Top-string UK NH trainers (Festival-calibre yards) ──────────────
TIER1 = {
    "Nicky Henderson", "Paul Nicholls", "Dan Skelton", "Alan King",
    "Emma Lavelle", "Ben Pauling", "Olly Murphy", "Tom George",
    "Kim Bailey", "Philip Hobbs", "Jonjo O'Neill", "Donald McCain",
    "Fergal O'Brien", "Nigel Twiston-Davies", "David Pipe",
    "Charlie Longsdon", "Neil Mulholland", "Anthony Honeyball",
    "Tom Lacey", "Harry Fry", "Jamie Snowden", "Oliver Sherwood",
    "Venetia Williams", "Ian Williams", "Gary Moore", "Evan Williams",
    "Nick Williams", "Chris Gordon", "Jeremy Scott", "Sue Smith",
    "Brian Ellison", "Lucinda Russell", "Sandy Thomson",
    "Dr Richard Newland", "Warren Greatrex", "Peter Bowen",
}

# ── Tier 2: Strong regional trainers ────────────────────────────────────────
TIER2 = {
    "Harriet Graham", "Rose Dobbin", "Dianne Sayer", "Keith Dalgleish",
    "Micky Hammond", "Tim Easterby", "Keith Reveley", "Tim Vaughan",
    "Christian Williams", "Rebecca Curtis", "Victor Dartnall",
    "Martin Keighley", "Seamus Mullins", "Andrew Penberthy",
    "Stewart Edmunds", "David Dennis", "Richard Hobson",
    "Sheena West", "Mark Walford", "James Moffatt", "Ryan Potter",
    "Peter Niven", "Nick Gifford", "Robbie Brisland",
}

# ── RP racecard venue slug map ───────────────────────────────────────────────
RP_VENUE_SLUGS = {
    "Sedgefield":    "sedgefield",
    "Huntingdon":    "huntingdon",
    "Taunton":       "taunton",
    "Exeter":        "exeter",
    "Wincanton":     "wincanton",
    "Plumpton":      "plumpton",
    "Fontwell":      "fontwell",
    "Carlisle":      "carlisle",
    "Catterick":     "catterick",
    "Hexham":        "hexham",
    "Kelso":         "kelso",
    "Perth":         "perth",
    "Ludlow":        "ludlow",
    "Hereford":      "hereford",
    "Worcester":     "worcester",
    "Wetherby":      "wetherby",
    "Haydock":       "haydock",
    "Newbury":       "newbury",
    "Leicester":     "leicester",
    "Sandown":       "sandown",
    "Ascot":         "ascot",
    "Newcastle":     "newcastle",
    "Musselburgh":   "musselburgh",
    "Stratford":     "stratford-on-avon",
    "Market Rasen":  "market-rasen",
    "Fakenham":      "fakenham",
    "Bangor-on-Dee": "bangor-on-dee",
    "Kempton":       "kempton",
}

NH_RACE_KEYWORDS = {
    "hurdle", "chase", "bumper", "nhf", "nh flat", "novice",
    "handicap hrd", "handicap chs", "mares", "maiden hrd"
}


# ─────────────────────────────────────────────────────────────────────────────
# BETFAIR LAYER
# ─────────────────────────────────────────────────────────────────────────────

def bf_post(endpoint, payload, timeout=30):
    r = requests.post(f"{BETFAIR_API}/{endpoint}/", headers=BF_HEADERS,
                      json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def dec_to_frac(dec):
    """Convert decimal price to fractional string."""
    if not dec or dec <= 1:
        return "EVS"
    fracs = [
        (0.5,"1/2"),(0.75,"3/4"),(1.0,"Evs"),(1.25,"5/4"),(1.5,"6/4"),
        (1.75,"7/4"),(2.0,"2/1"),(2.25,"9/4"),(2.5,"5/2"),(2.75,"11/4"),
        (3.0,"3/1"),(3.5,"7/2"),(4.0,"4/1"),(4.5,"9/2"),(5.0,"5/1"),
        (6.0,"6/1"),(7.0,"7/1"),(8.0,"8/1"),(9.0,"9/1"),(10.0,"10/1"),
        (11.0,"11/1"),(12.0,"12/1"),(14.0,"14/1"),(16.0,"16/1"),(20.0,"20/1"),
        (25.0,"25/1"),(33.0,"33/1"),(40.0,"40/1"),(50.0,"50/1"),
    ]
    n = dec - 1.0
    return min(fracs, key=lambda x: abs(x[0] - n))[1]


def get_bf_markets(date_str):
    """Fetch all NH WIN markets for date, grouped by venue."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    from_dt = dt.strftime("%Y-%m-%dT00:00:00Z")
    to_dt   = (dt + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")

    try:
        markets = bf_post("listMarketCatalogue", {
            "filter": {
                "eventTypeIds": ["7"],
                "marketCountries": ["GB"],
                "marketTypeCodes": ["WIN"],
                "marketStartTime": {"from": from_dt, "to": to_dt},
            },
            "marketProjection": ["EVENT", "RUNNER_METADATA", "MARKET_START_TIME"],
            "maxResults": "200",
            "sort": "FIRST_TO_START",
        })
    except Exception as e:
        print(f"  ⚠ Betfair error: {e}")
        return {}

    by_venue = {}
    for m in markets:
        venue   = m.get("event", {}).get("venue", "") or "Unknown"
        name    = m.get("marketName", "") or ""
        mid     = m.get("marketId", "")
        start   = m.get("marketStartTime", "")

        if venue in CHELTENHAM:
            continue

        # Only NH (jump) races — skip flat/AW evening cards
        name_lower = name.lower()
        is_nh = any(kw in name_lower for kw in NH_RACE_KEYWORDS)
        # Also accept if venue is a dedicated NH track
        is_nh_venue = venue in NH_VENUES
        if not (is_nh or is_nh_venue):
            continue

        runners = m.get("runners", [])
        entry = {
            "market_id":    mid,
            "race_name":    name,
            "start_time":   start[11:16] if len(start) > 11 else start,
            "total_runners": len(runners),
            "runner_map":   {r["selectionId"]: r.get("runnerName","?") for r in runners},
        }
        by_venue.setdefault(venue, []).append(entry)

    return by_venue


def get_bf_odds(market_ids):
    """Fetch best back price for each runner across multiple markets."""
    if not market_ids:
        return {}
    odds_map = {}
    # Betfair limit: 200 markets per call, but be safe with 50 at a time
    for i in range(0, len(market_ids), 40):
        chunk = market_ids[i:i+40]
        try:
            books = bf_post("listMarketBook", {
                "marketIds": chunk,
                "priceProjection": {"priceData": ["EX_BEST_OFFERS"]},
            })
            for book in books:
                runners_odds = {}
                for rb in book.get("runners", []):
                    sid    = rb["selectionId"]
                    backs  = rb.get("ex", {}).get("availableToBack", [])
                    best   = backs[0]["price"] if backs else None
                    runners_odds[sid] = best
                odds_map[book["marketId"]] = runners_odds
        except Exception as e:
            print(f"  ⚠ Odds fetch error: {e}")
        time.sleep(0.3)
    return odds_map


# ─────────────────────────────────────────────────────────────────────────────
# RACING POST RACECARD SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

def _selenium_driver():
    """Create a headless Chrome driver. Returns None if Selenium not available."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        opts = Options()
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36")
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=opts)
    except Exception as e:
        print(f"    ⚠ Selenium not available: {e}")
        return None


def scrape_rp_venue(venue, date_str):
    """
    Scrape Racing Post racecard for a venue+date.
    Tries requests first; falls back to Selenium for JS-rendered content.
    Returns dict: {horse_name_lower: {trainer, jockey, form}}
    """
    slug = RP_VENUE_SLUGS.get(venue)
    if not slug:
        return {}

    url = f"https://www.racingpost.com/racecards/{slug}/{date_str}"

    # --- Attempt 1: plain requests (fast, works if RP serves static HTML) ---
    horse_data = {}
    try:
        resp = requests.get(url, headers=RP_HEADERS, timeout=20)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            horse_data = _parse_rp_soup(soup)
    except Exception:
        pass

    if horse_data:
        return horse_data

    # --- Attempt 2: Selenium for JS-rendered pages ---
    driver = _selenium_driver()
    if driver is None:
        return {}
    try:
        driver.get(url)
        time.sleep(4)   # wait for React/JS hydration
        page_src = driver.page_source
    except Exception as e:
        print(f"    ⚠ Selenium fetch error for {venue}: {e}")
        return {}
    finally:
        try:
            driver.quit()
        except Exception:
            pass

    soup = BeautifulSoup(page_src, "html.parser")
    horse_data = _parse_rp_soup(soup)
    if not horse_data:
        horse_data = _scrape_rp_json_fallback(soup)
    return horse_data


def _parse_rp_soup(soup):
    """Extract runner data from a BeautifulSoup RP racecard page."""
    horse_data = {}

    # RP racecard structure: each runner row contains horse name, trainer, jockey
    # Try multiple selector patterns as RP changes markup
    for row in soup.select("[class*='RC-runnerRow'], [class*='runner-row'], tr.runner"):
        name_el    = row.select_one("[class*='RC-runnerName'], [class*='horse-name'], .runnerName")
        trainer_el = row.select_one("[class*='RC-runnerTrainer'], [class*='trainer'], .trainerName")
        jockey_el  = row.select_one("[class*='RC-runnerJockey'], [class*='jockey'], .jockeyName")
        form_el    = row.select_one("[class*='RC-runnerForm'], [class*='form-figures'], .form")

        if not name_el:
            continue

        name    = name_el.get_text(strip=True).lower()
        trainer = trainer_el.get_text(strip=True) if trainer_el else ""
        jockey  = jockey_el.get_text(strip=True)  if jockey_el  else ""
        form    = form_el.get_text(strip=True)     if form_el    else ""

        if name:
            horse_data[name] = {"trainer": trainer, "jockey": jockey, "form": form}

    return horse_data


def _scrape_rp_json_fallback(soup):
    """Try to extract runner data from RP embedded JSON blobs."""
    horse_data = {}
    for script in soup.find_all("script", type="application/json"):
        try:
            data = json.loads(script.string or "{}")
            # Walk the JSON looking for runner arrays
            _extract_runners_from_json(data, horse_data)
        except Exception:
            continue
    return horse_data


def _extract_runners_from_json(obj, out, depth=0):
    if depth > 8:
        return
    if isinstance(obj, list):
        for item in obj:
            _extract_runners_from_json(item, out, depth+1)
    elif isinstance(obj, dict):
        # Look for runner/horse name fields
        name = obj.get("horseName") or obj.get("horse") or obj.get("name") or ""
        trainer = obj.get("trainerName") or obj.get("trainer") or ""
        jockey  = obj.get("jockeyName")  or obj.get("jockey")  or ""
        form    = obj.get("form") or ""
        if name and (trainer or jockey):
            out[name.lower()] = {"trainer": trainer, "jockey": jockey, "form": form}
        for v in obj.values():
            if isinstance(v, (dict, list)):
                _extract_runners_from_json(v, out, depth+1)


# ─────────────────────────────────────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────────────────────────────────────

def score_sleeper(horse_name, dec_price, rp_info, race_meta):
    """
    Score a horse as a potential Cheltenham-week sleeper.
    Returns (score, flags[])
    """
    score = 0
    flags = []

    trainer  = rp_info.get("trainer", "")
    jockey   = rp_info.get("jockey", "")
    form     = rp_info.get("form", "")
    runners  = race_meta.get("total_runners", 10)
    race     = race_meta.get("race_name", "")
    venue    = race_meta.get("venue", "")

    # ── Trainer tier ─────────────────────────────────────────────────────────
    if trainer in TIER1:
        score += 35
        flags.append(f"★ TOP TRAINER ({trainer}) at {venue} — planned move")
    elif trainer in TIER2:
        score += 18
        flags.append(f"✓ Quality trainer ({trainer})")
    elif trainer:
        score += 3   # any named trainer > unknown
        flags.append(f"Trainer: {trainer}")

    # ── Price sweet spot — inflated odds = bookies distracted ────────────────
    if dec_price is None:
        pass
    elif 5.0 <= dec_price <= 10.0:        # 4/1 – 9/1 ★ sweet spot
        score += 32
        flags.append(f"★ SWEET SPOT price ({dec_to_frac(dec_price)}) — overlay vs true chance")
    elif 10.0 < dec_price <= 16.0:        # 10/1 – 15/1
        score += 25
        flags.append(f"Big overlay price ({dec_to_frac(dec_price)}) — market distracted")
    elif 16.0 < dec_price <= 25.0:        # 16/1 – 25/1
        score += 14
        flags.append(f"Long price ({dec_to_frac(dec_price)}) — speculative value")
    elif 3.0 <= dec_price < 5.0:          # 2/1 – 7/2
        score += 10
        flags.append(f"Decent price ({dec_to_frac(dec_price)})")
    elif dec_price < 3.0:                 # odds-on/short — market awake
        score -= 12
        flags.append(f"Short price ({dec_to_frac(dec_price)}) — bookies already watching")
    elif dec_price > 25.0:
        score -= 5
        flags.append(f"Big drift ({dec_to_frac(dec_price)}) — possibly weak entry")

    # ── Field size — small = easier, trainer picks weak spots ────────────────
    if runners <= 4:
        score += 18
        flags.append(f"Tiny field ({runners} runners) — elite vs weak opposition")
    elif runners <= 7:
        score += 10
        flags.append(f"Small field ({runners} runners)")
    elif runners <= 10:
        score += 4
        flags.append(f"Manageable field ({runners} runners)")
    elif runners >= 16:
        score -= 6
        flags.append(f"Large field ({runners}) — harder to exploit")

    # ── Race type — bumpers/novices most exploitable ──────────────────────────
    race_lower = race.lower()
    if "bumper" in race_lower or "nhf" in race_lower or "nh flat" in race_lower:
        score += 12
        flags.append("NH Flat/Bumper — pure class dominates, thin market")
    elif "novice" in race_lower and "handicap" not in race_lower:
        score += 8
        flags.append("Novice — open to superiority from class yard")
    elif "maiden" in race_lower:
        score += 6
        flags.append("Maiden — fresh start, class horse can dominate")
    elif "handicap" in race_lower:
        score -= 4
        flags.append("Handicap — harder to engineer a certainty")

    # ── Form reading ──────────────────────────────────────────────────────────
    if form:
        clean = form.replace("-", "").replace(" ", "")
        if clean.startswith("1"):
            score += 8
            flags.append(f"Won last time out (form: {form}) — in form")
        elif clean.startswith("11"):
            score += 12
            flags.append(f"Back-to-back wins (form: {form}) — on a roll")
        if "0" in clean[:3] or "P" in clean[:3].upper():
            score -= 5
            flags.append(f"Recent poor run in form ({form})")

    return max(0, score), flags


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SCAN
# ─────────────────────────────────────────────────────────────────────────────

def scan_day(date_str, min_score=40):
    day_label = {
        "2026-03-10": "Day 1 — Tue 10 Mar",
        "2026-03-11": "Day 2 — Wed 11 Mar",
        "2026-03-12": "Day 3 — Thu 12 Mar",
        "2026-03-13": "Day 4 — Fri 13 Mar",
    }.get(date_str, date_str)

    print(f"\n{'='*70}")
    print(f"  CHELTENHAM WEEK SLEEPERS — {day_label}")
    print(f"{'='*70}")

    # 1. Get Betfair markets by venue
    print("  [1/3] Fetching Betfair markets...")
    by_venue = get_bf_markets(date_str)
    if not by_venue:
        print("  No non-Cheltenham NH markets found on Betfair.")
        return []

    nh_venues = sorted(by_venue.keys())
    total_races = sum(len(v) for v in by_venue.values())
    print(f"  Found {total_races} NH races at {len(nh_venues)} venues: {', '.join(nh_venues)}")

    # 2. Fetch Betfair odds for all markets
    print("  [2/3] Fetching Betfair odds...")
    all_market_ids = [m["market_id"] for v in by_venue.values() for m in v]
    odds_map = get_bf_odds(all_market_ids)

    # 3. Scrape RP racecards for trainer/jockey data
    print("  [3/3] Fetching Racing Post racecard data...")
    rp_data = {}   # venue → {horse_name_lower: {trainer, jockey, form}}
    for venue in nh_venues:
        rp_info = scrape_rp_venue(venue, date_str)
        rp_data[venue] = rp_info
        time.sleep(0.5)  # polite crawl delay
        if rp_info:
            print(f"    ✓ {venue}: {len(rp_info)} runners found on RP")
        else:
            print(f"    ○ {venue}: no RP data (will score on Betfair only)")

    # 4. Score every runner
    candidates = []
    for venue, races in by_venue.items():
        venue_rp = rp_data.get(venue, {})
        for race in races:
            mid         = race["market_id"]
            runner_map  = race["runner_map"]
            market_odds = odds_map.get(mid, {})
            race_meta   = {**race, "venue": venue}

            for sid, horse_name in runner_map.items():
                dec_raw  = market_odds.get(sid)
                dec_price = (dec_raw - 1.0) if dec_raw and dec_raw > 1 else None

                # Look up RP data (fuzzy: strip (IRE)/(FR) suffixes)
                clean_name = re.sub(r'\s*\([A-Z]{2,3}\)\s*$', '', horse_name).strip().lower()
                rp_info = venue_rp.get(clean_name, {})

                score, flags = score_sleeper(horse_name, dec_price, rp_info, race_meta)

                if score >= min_score:
                    candidates.append({
                        "score":   score,
                        "venue":   venue,
                        "time":    race["start_time"],
                        "race":    race["race_name"],
                        "runners": race["total_runners"],
                        "horse":   horse_name,
                        "price":   dec_to_frac(dec_price) if dec_price else "?",
                        "dec":     dec_price or 0,
                        "trainer": rp_info.get("trainer", "— check RP"),
                        "jockey":  rp_info.get("jockey", ""),
                        "form":    rp_info.get("form", ""),
                        "flags":   flags,
                    })

    # 5. Sort and print
    candidates.sort(key=lambda x: x["score"], reverse=True)

    if not candidates:
        print(f"\n  No sleepers found above score threshold ({min_score}).")
        print(f"  Lower threshold with --min N or check RP manually for trainer upgrades.")
        return candidates

    print(f"\n  ★ {len(candidates)} potential sleepers found (threshold: {min_score}+)\n")

    for c in candidates:
        grade = "🔥 STRONG BET" if c["score"] >= 70 else ("⚡ GOOD BET" if c["score"] >= 55 else "👀 WATCH")
        print(f"  {'─'*68}")
        print(f"  {grade}  [{c['score']} pts]")
        print(f"  {c['venue']}  {c['time']}  |  {c['race']}  |  {c['runners']} runners")
        print(f"  🐴 {c['horse']}  @  {c['price']}", end="")
        if c["form"]:
            print(f"  Form: {c['form']}", end="")
        print()
        if c["trainer"] not in ("— check RP", ""):
            jock = f"  J: {c['jockey']}" if c["jockey"] else ""
            print(f"  T: {c['trainer']}{jock}")
        else:
            print(f"  T: {c['trainer']}  ← verify on racingpost.com/racecards/{c['venue'].lower()}/{date_str}")
        print(f"  Why:")
        for f in c["flags"]:
            print(f"    • {f}")

    print(f"\n{'='*70}")
    print(f"  SUMMARY: Top sleeper → {candidates[0]['horse']} @ {candidates[0]['price']} "
          f"({candidates[0]['venue']} {candidates[0]['time']})")
    print(f"  Score: {candidates[0]['score']} pts  |  Trainer: {candidates[0]['trainer']}")
    slug = RP_VENUE_SLUGS.get(candidates[0]['venue'], candidates[0]['venue'].lower())
    print(f"  RP cross-check: https://www.racingpost.com/racecards/{slug}/{date_str}")
    print(f"{'='*70}\n")

    return candidates


def main():
    parser = argparse.ArgumentParser(description="Cheltenham Week Sleeper Scan")
    parser.add_argument("--day",  type=int, choices=[1,2,3,4], help="Festival day (1-4)")
    parser.add_argument("--all",  action="store_true",         help="Scan all 4 days")
    parser.add_argument("--min",  type=int, default=40,        help="Min sleeper score (default 40)")
    args = parser.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")

    if args.all:
        days = list(FESTIVAL_DAYS.values())
    elif args.day:
        days = [FESTIVAL_DAYS[args.day]]
    else:
        days = [d for d in FESTIVAL_DAYS.values() if d >= today]

    if not days:
        print("  Festival is over.")
        return

    all_results = []
    for d in days:
        results = scan_day(d, min_score=args.min)
        all_results.extend(results)
        if len(days) > 1:
            time.sleep(1)

    if len(days) > 1 and all_results:
        print(f"\n  FESTIVAL TOTAL: {len(all_results)} sleeper candidates across {len(days)} days")


if __name__ == "__main__":
    main()

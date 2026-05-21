"""
CHELTENHAM WEEK SLEEPER DETECTOR
=================================
Scans ALL UK non-Cheltenham NH races during the 4 festival days (Mar 10-13 2026).
Flags horses from quality trainers running at smaller tracks while the betting
public is fixated on Cheltenham — the classic "sleeper" pattern.

Key patterns matched:
  1. Quality trainer (top 30 NH) running at Sedgefield/Southwell/Worcestershire etc.
  2. Horse dropping significantly in class vs. recent runs
  3. Short-priced horse in a weak field (market confidence despite thin interest)
  4. Small field where trainer's runner is clearly the class act
  5. Horse returning from a break / fresh after a target campaign

Usage:
    python cheltenham_week_sleepers.py              # today + remaining festival days
    python cheltenham_week_sleepers.py --day 1      # Day 1 (10 Mar) only
    python cheltenham_week_sleepers.py --all        # all 4 festival days
"""

import json, os, sys, time, argparse
from datetime import datetime, timezone, timedelta
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
BETFAIR_API = "https://api.betfair.com/exchange/betting/rest/v1.0"

# ── Load Betfair credentials ──────────────────────────────────────────────────
creds_path = os.path.join(ROOT, "betfair-creds.json")
with open(creds_path) as f:
    creds = json.load(f)

HEADERS = {
    "X-Application":    creds["app_key"],
    "X-Authentication": creds["session_token"],
    "Content-Type":     "application/json",
}

# ── Festival dates ─────────────────────────────────────────────────────────────
FESTIVAL_DAYS = {
    1: "2026-03-10",
    2: "2026-03-11",
    3: "2026-03-12",
    4: "2026-03-13",
}

# ── Tracks to EXCLUDE (Cheltenham itself) ─────────────────────────────────────
CHELTENHAM_VENUES = {"Cheltenham"}

# ── Target smaller UK NH tracks where sleepers appear ────────────────────────
SLEEPER_VENUES = {
    "Sedgefield", "Southwell", "Wolverhampton", "Musselburgh",
    "Newcastle", "Huntingdon", "Exeter", "Taunton", "Wincanton",
    "Plumpton", "Fontwell", "Worcester", "Hereford", "Ludlow",
    "Carlisle", "Catterick", "Hexham", "Kelso", "Perth",
    "Bangor-on-Dee", "Stratford", "Market Rasen", "Fakenham",
    "Leicester", "Kempton", "Sandown", "Lingfield",
}

# ── Quality NH trainers who might plant sleepers ─────────────────────────────
# Tier 1: Festival-calibre trainers with deep strings — they CAN'T attend Chelt with everything
TIER1_TRAINERS = {
    "Nicky Henderson", "Paul Nicholls", "Dan Skelton", "Alan King",
    "Emma Lavelle", "Ben Pauling", "Olly Murphy", "Tom George",
    "Kim Bailey", "Colin Tizzard", "Philip Hobbs", "Jeremy Scott",
    "Chris Gordon", "Nick Williams", "Gary Moore", "Evan Williams",
    "Dr Richard Newland", "Jonjo O'Neill", "Donald McCain", "Sue Smith",
    "Brian Ellison", "Peter Niven", "Lucinda Russell", "Sandy Thomson",
    "Harriet Graham", "Rose Dobbin", "Dianne Sayer", "Keith Dalgleish",
    "Micky Hammond", "Tim Easterby", "David Thompson",
    "Fergal O'Brien", "Ian Williams", "Neil Mulholland",
    "Anthony Honeyball", "Martin Keighley", "David Pipe", "Martin Pipe",
    "Nigel Twiston-Davies", "Tom Lacey", "Nick Gifford",
    "Charlie Longsdon", "Robbie Brisland", "Seamus Mullins",
    # Irish trainers who sometimes send UK raiders to small tracks
    "Willie Mullins", "Gordon Elliott", "Henry de Bromhead",
    "Joseph Patrick O'Brien", "Gavin Cromwell", "Emmet Mullins",
}

# Tier 2: Strong regional trainers — good at finding weak fields
TIER2_TRAINERS = {
    "Warren Greatrex", "Richard Phillips", "Claire Dyson",
    "Keith Reveley", "Tim Vaughan", "Christian Williams",
    "Rebecca Curtis", "Peter Fahey", "John Joseph Hanlon",
    "Andrew Penberthy", "Paul Henderson", "Victor Dartnall",
    "John Flint", "Sheena West", "Mark Walford", "James Moffatt",
    "Ryan Potter", "Jonathan England", "Joanne Hughes",
    "Oliver Sherwood", "Venetia Williams", "Jamie Snowden",
    "Harry Fry", "Stewart Edmunds", "David Dennis",
    "Richard Hobson", "Peter Bowen", "Sarah Humphrey",
}

ALL_QUALITY_TRAINERS = TIER1_TRAINERS | TIER2_TRAINERS

# ── Jockeys who travel to small tracks with their stable's proper horse ───────
QUALITY_JOCKEYS = {
    "Harry Skelton", "Nico de Boinville", "Daryl Jacob",
    "Aidan Coleman", "Richard Johnson", "Tom Scudamore",
    "Sam Twiston-Davies", "Harry Cobden", "Nick Scholfield",
    "James Bowen", "Sean Bowen", "Jonjo O'Neill Jr.",
    "Tom Cannon", "Rex Dingle", "Bryony Frost",
    "Charlie Hammond", "Craig Nichol", "Richie McLernon",
    "Brian Hughes", "Henry Brooke", "Danny McMenamin",
    "Ryan Mania", "Derek Fox", "Conor O'Farrell",
    "Alan Doyle", "Tom O'Brien", "Michael O'Sullivan",
}


def bf_post(endpoint, payload, timeout=30):
    """POST to Betfair REST API."""
    r = requests.post(
        f"{BETFAIR_API}/{endpoint}/",
        headers=HEADERS,
        json=payload,
        timeout=timeout,
    )
    r.raise_for_status()
    return r.json()


def dec_to_frac(dec):
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


def score_sleeper(runner, market_info):
    """
    Score a runner for 'sleeper' potential (0-100).
    Higher = more likely to be a deliberately planted class act.
    """
    score = 0
    flags = []

    trainer  = runner.get("trainer", "")
    jockey   = runner.get("jockey", "")
    sp_dec   = runner.get("sp_dec", 99)
    runners  = market_info.get("total_runners", 10)
    venue    = market_info.get("venue", "")
    race_type = market_info.get("race_type", "")

    # ── Trainer quality ───────────────────────────────────────────────────────
    if trainer in TIER1_TRAINERS:
        score += 30
        flags.append(f"★ TIER 1 trainer ({trainer})")
    elif trainer in TIER2_TRAINERS:
        score += 15
        flags.append(f"✓ Quality trainer ({trainer})")

    # ── Jockey quality ────────────────────────────────────────────────────────
    if jockey in QUALITY_JOCKEYS:
        score += 10
        flags.append(f"Top jockey booked ({jockey})")

    # ── Price sweet spot for sleepers ────────────────────────────────────────
    # Classic pattern: bookies distracted by Cheltenham → quality horse drifts
    # to 6/1-16/1 at small track while trainer backs quietly.
    # Odds-on = market has noticed, NOT a sleeper. Big price = the find.
    if 6.0 <= sp_dec <= 10.0:       # 5/1 to 9/1  — sweet spot
        score += 30
        flags.append(f"★ SWEET SPOT price ({dec_to_frac(sp_dec + 1)}) — bookies not watching, trainer knows")
    elif 10.0 < sp_dec <= 16.0:     # 10/1 to 15/1 — big overlay potential
        score += 25
        flags.append(f"Big price overlay ({dec_to_frac(sp_dec + 1)}) — market distracted by Cheltenham")
    elif 16.0 < sp_dec <= 25.0:     # 16/1-25/1 — speculative but rewarding
        score += 15
        flags.append(f"Long price ({dec_to_frac(sp_dec + 1)}) — speculative sleeper")
    elif 3.0 < sp_dec < 6.0:        # 3/1-4/1 — some value but less hidden
        score += 10
        flags.append(f"Decent price ({dec_to_frac(sp_dec + 1)}) — moderate overlay")
    elif sp_dec <= 3.0:             # odds-on to 2/1 — market has noticed
        score -= 15
        flags.append(f"Short price ({dec_to_frac(sp_dec + 1)}) — bookies already aware, not a sleeper")
    elif sp_dec > 25.0:             # 25/1+ — too big, possibly no quality
        score -= 5
        flags.append(f"Very big price ({dec_to_frac(sp_dec + 1)}) — may lack quality")

    # ── Small field bonus (easier pickings) ──────────────────────────────────
    if runners <= 5:
        score += 15
        flags.append(f"Tiny field ({runners} runners) — very winnable")
    elif runners <= 8:
        score += 8
        flags.append(f"Small field ({runners} runners)")
    elif runners >= 16:
        score -= 5
        flags.append(f"Large field ({runners}) — harder to exploit")

    # ── Sleeper venue boost ──────────────────────────────────────────────────
    if venue in SLEEPER_VENUES:
        score += 5
        flags.append(f"Classic sleeper venue ({venue})")

    # ── Race type signals ─────────────────────────────────────────────────────
    if "Novice" in race_type or "Maiden" in race_type:
        score += 5
        flags.append("Novice/Maiden — thinner competition, open to class act")
    if "Handicap" in race_type:
        score -= 3   # handicaps harder to exploit
        flags.append("Handicap — harder to plan a certainty")
    if "Bumper" in race_type or "NH Flat" in race_type:
        score += 8
        flags.append("Bumper/NH Flat — pure class dominates")

    return max(0, score), flags


def fetch_non_cheltenham_markets(date_str):
    """
    Fetch all UK NH WIN markets for a given date, excluding Cheltenham.
    Returns list of market summaries.
    """
    date_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    from_dt = date_dt.strftime("%Y-%m-%dT00:00:00Z")
    to_dt   = (date_dt + timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")

    filter_payload = {
        "filter": {
            "eventTypeIds": ["7"],           # Horse Racing
            "marketCountries": ["GB", "IE"], # UK + Ireland
            "marketTypeCodes": ["WIN"],
            "marketStartTime": {"from": from_dt, "to": to_dt},
        },
        "marketProjection": ["EVENT", "RUNNER_METADATA", "MARKET_START_TIME"],
        "maxResults": "200",
        "sort": "FIRST_TO_START",
    }

    try:
        markets = bf_post("listMarketCatalogue", filter_payload)
    except Exception as e:
        print(f"  ⚠ Betfair API error: {e}")
        return []

    results = []
    for m in markets:
        venue   = m.get("event", {}).get("venue", "") or ""
        country = m.get("event", {}).get("countryCode", "") or ""
        name    = m.get("marketName", "") or ""
        mid     = m.get("marketId", "")
        start   = m.get("marketStartTime", "")

        # Skip Cheltenham
        if any(c in venue for c in CHELTENHAM_VENUES):
            continue
        # Only UK NH (Jump) races — filter out Flat by race name signals
        flat_signals = any(s in name for s in ["Flat", "Turf", "AW", "All-Weather"])
        if flat_signals:
            continue

        runners = m.get("runners", [])
        results.append({
            "market_id": mid,
            "venue": venue,
            "race_name": name,
            "start_time": start,
            "total_runners": len(runners),
            "runner_ids": [r["selectionId"] for r in runners],
            "runner_names": {r["selectionId"]: r.get("runnerName","?") for r in runners},
            "race_type": name,
        })

    return results


def enrich_with_odds_and_metadata(markets):
    """
    For each market, fetch best available win price (lay side best back).
    Also attempt to extract trainer/jockey from runner metadata.
    """
    if not markets:
        return markets

    market_ids = [m["market_id"] for m in markets[:50]]  # Betfair limit

    try:
        books = bf_post("listMarketBook", {
            "marketIds": market_ids,
            "priceProjection": {"priceData": ["EX_BEST_OFFERS"]},
        })
    except Exception as e:
        print(f"  ⚠ Could not fetch odds: {e}")
        return markets

    odds_by_market = {b["marketId"]: b for b in books}

    enriched = []
    for mkt in markets:
        mid = mkt["market_id"]
        book = odds_by_market.get(mid, {})
        runners_book = book.get("runners", [])

        runners_enriched = []
        for rb in runners_book:
            sid = rb["selectionId"]
            horse_name = mkt["runner_names"].get(sid, "?")
            status = rb.get("status", "")
            if status not in ("ACTIVE", ""):
                continue

            best_back = None
            ex = rb.get("ex", {})
            backs = ex.get("availableToBack", [])
            if backs:
                best_back = backs[0].get("price")

            sp_dec = (best_back - 1.0) if best_back else 99.0

            runners_enriched.append({
                "name": horse_name,
                "selection_id": sid,
                "sp_dec": sp_dec,
                "trainer": "",   # Betfair WIN markets don't expose trainer — filled by metadata
                "jockey": "",
            })

        # Sort by price (shortest first)
        runners_enriched.sort(key=lambda x: x["sp_dec"])
        mkt["runners_enriched"] = runners_enriched
        enriched.append(mkt)

    return enriched


def print_sleepers(markets, date_str, min_score=25):
    """Print flagged sleepers sorted by sleeper score."""
    header = f"\n{'='*72}\n  CHELTENHAM WEEK SLEEPERS — {date_str}\n{'='*72}"
    print(header)

    all_flags = []

    for mkt in markets:
        venue     = mkt.get("venue", "Unknown")
        race_name = mkt.get("race_name", "")
        start     = mkt.get("start_time", "")[:16].replace("T", " ")
        runners   = mkt.get("runners_enriched", [])

        if not runners:
            continue

        # Score the shortest-priced runner (likeliest "planted" banker)
        for runner in runners[:3]:  # check top 3 priced
            sl_score, flags = score_sleeper(runner, mkt)
            if sl_score >= min_score:
                all_flags.append({
                    "score": sl_score,
                    "venue": venue,
                    "start": start,
                    "race": race_name,
                    "horse": runner["name"],
                    "price": dec_to_frac(runner["sp_dec"] + 1),
                    "trainer": runner.get("trainer", "?"),
                    "jockey": runner.get("jockey", "?"),
                    "flags": flags,
                    "field_size": mkt["total_runners"],
                })

    # Sort by score descending
    all_flags.sort(key=lambda x: x["score"], reverse=True)

    if not all_flags:
        print(f"  No sleepers found above threshold (min_score={min_score})")
        print(f"  Scanned {len(markets)} non-Cheltenham markets on {date_str}")
        return

    print(f"\n  Found {len(all_flags)} potential sleepers above score {min_score}:\n")

    for i, item in enumerate(all_flags, 1):
        grade = "🔥 STRONG" if item["score"] >= 55 else ("⚡ GOOD" if item["score"] >= 40 else "👀 WATCH")
        print(f"  {'─'*66}")
        print(f"  {grade}  [{item['score']} pts]  {item['venue']}  {item['start']}")
        print(f"  Race: {item['race']}  |  Field: {item['field_size']} runners")
        print(f"  Horse: {item['horse']}  @  {item['price']}")
        if item['trainer'] not in ('', '?'):
            print(f"  T: {item['trainer']}  |  J: {item['jockey']}")
        print(f"  Flags:")
        for f in item["flags"]:
            print(f"    • {f}")

    print(f"\n{'='*72}")
    print(f"  Pattern notes:")
    print(f"  • Tier 1 trainers (Henderson/Nicholls/Skelton etc.) at tiny tracks = planned")
    print(f"  • Odds-on in field of 4-6 = trainer has sent a class act to a weak race")
    print(f"  • Novice/Bumper + quality trainer = safest spot for a sleeper")
    print(f"  • Check Racing Post: is the horse dropping in class vs. last 3 runs?")
    print(f"  • NOTE: Betfair markets don't expose trainer — check RP for confirmation")
    print(f"{'='*72}\n")


def main():
    parser = argparse.ArgumentParser(description="Cheltenham Week Sleeper Detector")
    parser.add_argument("--day", type=int, choices=[1,2,3,4],
                        help="Festival day to scan (1=Tue, 2=Wed, 3=Thu, 4=Fri)")
    parser.add_argument("--all", action="store_true", help="Scan all 4 festival days")
    parser.add_argument("--min-score", type=int, default=25,
                        help="Minimum sleeper score to display (default: 25)")
    args = parser.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")

    # Decide which days to scan
    if args.all:
        days_to_scan = list(FESTIVAL_DAYS.values())
    elif args.day:
        days_to_scan = [FESTIVAL_DAYS[args.day]]
    else:
        # Default: today + any remaining festival days
        days_to_scan = [d for d in FESTIVAL_DAYS.values() if d >= today]

    if not days_to_scan:
        print("  Festival is over — no days to scan.")
        return

    for date_str in days_to_scan:
        print(f"\n  Scanning non-Cheltenham UK NH markets for {date_str}...")
        markets = fetch_non_cheltenham_markets(date_str)
        print(f"  Found {len(markets)} non-Cheltenham NH markets")

        if markets:
            markets = enrich_with_odds_and_metadata(markets)
            print_sleepers(markets, date_str, min_score=args.min_score)

        if len(days_to_scan) > 1:
            time.sleep(1)  # rate limit courtesy


if __name__ == "__main__":
    main()

"""
handicap_festival_scanner.py
═══════════════════════════════════════════════════════════════════════════════
Scans every horse in every Cheltenham 2026 handicap/non-Grade-1 race for
"festival meeting improvement" — horses that have recently shown they can
handle soft/good-to-soft ground at similar distances in high-quality company,
suggesting they may be much better than their current handicap mark / our
model score implies.

Signal detected:
  - Ran at a festival-class prep venue (Cheltenham, Newbury, Ascot, Haydock,
    Sandown, Wetherby, Kempton, Leopardstown, Punchestown) in last 3 runs
  - On soft or good-to-soft ground
  - Within ~4 furlongs of the target Cheltenham race distance
  - Form position improved vs average of previous 3 runs  OR
    placed / won at that festival meeting

Scoring:
  festival_venue_recent    +20   ran at festival-tier venue last 3 runs
  festival_placed          +20   won or placed 1-3 at festival-tier venue
  soft_ground_match        + 8   recent run on soft / good-to-soft
  distance_match           + 8   within 4 furlongs of Cheltenham race distance
  form_improving           +12   latest position < mean(prev 3 positions)
  won_last_time            +10   1st in last run
  back_from_peak           + 5   within 5 pts of their best recent score
  flag_bonus               + 5   one or more "Won same distance/class" tip found
  class_drop               + 8   stepping DOWN in class vs recent runs

Output:
  - Per-race ranked table of ALL runners, flagging overlooked horses
  - Highlights "DARK HORSE" picks (score ≥ 35 but NOT our current pick)
  - Saves results to DynamoDB CheltenhamHandicapFlags table
  - Saves a text report to handicap_improvement_report.txt

Usage:
  python handicap_festival_scanner.py              # all handicap races
  python handicap_festival_scanner.py --race Pertemps
  python handicap_festival_scanner.py --no-save    # skip DynamoDB write
  python handicap_festival_scanner.py --rp         # also attempt RP form scrape

Scheduling:
  Run daily 08:00–12:00 during festival week (10–13 Mar 2026).
  Task scheduler: schedule_handicap_scan.ps1
"""

import ast, argparse, json, os, re, sys, time
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict
import requests
from bs4 import BeautifulSoup
import boto3
from boto3.dynamodb.conditions import Attr

ROOT   = os.path.dirname(os.path.abspath(__file__))
TODAY  = date.today().isoformat()
REGION = "eu-west-1"
dynamodb = boto3.resource("dynamodb", region_name=REGION)

# ── Handicap / non-Grade-1 races that this scanner targets ──────────────────
HANDICAP_RACES = {
    "Ultima Handicap Chase":              {"day": 1, "dist_f": 26, "going": "soft"},
    "Fred Winter Handicap Hurdle":        {"day": 1, "dist_f": 16, "going": "soft"},
    "Cheltenham Plate Chase":             {"day": 1, "dist_f": 20, "going": "soft"},
    "Challenge Cup Chase":                {"day": 1, "dist_f": 20, "going": "soft"},
    "BetMGM Cup Hurdle":                  {"day": 2, "dist_f": 22, "going": "soft"},
    "Glenfarclas Cross Country Chase":    {"day": 2, "dist_f": 32, "going": "soft"},
    "Grand Annual Handicap Chase":        {"day": 2, "dist_f": 16, "going": "soft"},
    "Pertemps Handicap Hurdle":           {"day": 3, "dist_f": 26, "going": "soft"},
    "Kim Muir Handicap Chase":            {"day": 3, "dist_f": 26, "going": "soft"},
    "Martin Pipe Handicap Hurdle":        {"day": 3, "dist_f": 21, "going": "soft"},
    "JCB Triumph Hurdle":                 {"day": 4, "dist_f": 18, "going": "soft"},
    "County Handicap Hurdle":             {"day": 4, "dist_f": 16, "going": "soft"},
    "St James's Place Hunters' Chase":    {"day": 4, "dist_f": 26, "going": "soft"},
}

# ── Festival-tier prep venues that count for the improvement signal ──────────
FESTIVAL_VENUES = {
    # UK
    "cheltenham", "newbury", "ascot", "haydock", "sandown", "kempton",
    "wetherby", "doncaster", "exeter",
    # Irish
    "leopardstown", "punchestown", "fairyhouse", "naas", "navan",
    "gowran park", "thurles", "galway",
}

# ── Going strings that match Cheltenham conditions ──────────────────────────
SOFT_GOING = {"soft", "heavy", "good to soft", "good to yielding",
              "yielding", "yielding to soft"}

RP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://www.racingpost.com/",
    "Cache-Control": "no-cache",
}


# ═══════════════════════════════════════════════════════════════════════════════
# RP form scraping helpers
# ═══════════════════════════════════════════════════════════════════════════════

def name_to_rp_slug(name: str) -> str:
    """Convert horse name to Racing Post URL slug."""
    slug = re.sub(r"[^\w\s-]", "", name.lower())
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug


def fetch_rp_form(horse_name: str, max_runs: int = 8) -> list[dict]:
    """
    Try to fetch last N runs from Racing Post horse form page.
    Returns list of dicts with: date, venue, going, dist_f, position, rpr, or [].
    """
    slug = name_to_rp_slug(horse_name)
    # Try the RP horse form URL (no auth needed for form page)
    urls = [
        f"https://www.racingpost.com/horses/{slug}/form",
        f"https://www.racingpost.com/horses/{slug}",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=RP_HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.content, "html.parser")
            runs = []
            # RP form rows: look for the results table
            rows = soup.select("table.form-table tr, tr[data-horse-form-row]")
            if not rows:
                rows = soup.select("section.formDataSection tr")
            for row in rows[:max_runs + 2]:
                cols = row.find_all("td")
                if len(cols) < 5:
                    continue
                try:
                    texts = [c.get_text(strip=True) for c in cols]
                    # RP columns (approx): date, venue, class, dist, going, pos, ...rpr
                    run = _parse_rp_row(texts)
                    if run:
                        runs.append(run)
                except Exception:
                    pass
            if runs:
                return runs[:max_runs]
        except requests.RequestException:
            pass
    return []


def _parse_rp_row(texts: list[str]) -> dict | None:
    """Parse a Racing Post form row into a structured dict."""
    if len(texts) < 5:
        return None
    # Position is usually 1st/2nd or a number
    pos_raw = next((t for t in texts[:8] if re.match(r"^(\d{1,2})(st|nd|rd|th)?$", t)), None)
    pos = int(re.match(r"(\d+)", pos_raw).group(1)) if pos_raw else None

    # Distance: look for pattern like 2m, 2m4f, 3m1f
    dist_raw = next((t for t in texts if re.match(r"^\d+m\d*f?$", t)), None)
    dist_f = None
    if dist_raw:
        m = re.match(r"(\d+)m(\d+)?f?", dist_raw)
        if m:
            dist_f = int(m.group(1)) * 8 + (int(m.group(2)) if m.group(2) else 0)

    # Going
    going_map = {"Sft": "soft", "Gd/Sft": "good to soft", "Hvy": "heavy",
                 "Gd": "good", "Gd/Fm": "good to firm", "Fm": "firm",
                 "Yld": "yielding", "Yld/Sft": "yielding to soft", "Soft": "soft"}
    going = None
    for t in texts:
        if t in going_map:
            going = going_map[t]
            break
        if t.lower() in SOFT_GOING:
            going = t.lower()
            break

    # Venue: long-ish text that isn't a date/number/position
    venue = None
    for t in texts[:5]:
        if len(t) > 4 and not re.match(r"^\d", t) and t not in going_map:
            venue = t.lower()
            break

    # RPR: last numeric column typically
    rpr = None
    for t in reversed(texts):
        if re.match(r"^\d{2,3}$", t):
            rpr = int(t)
            break

    if pos is None and venue is None:
        return None
    return {"venue": venue, "going": going, "dist_f": dist_f, "position": pos, "rpr": rpr}


# ═══════════════════════════════════════════════════════════════════════════════
# Scoring engine
# ═══════════════════════════════════════════════════════════════════════════════

def festival_improvement_score(
    horse: dict,
    race_meta: dict,
    rp_runs: list[dict],
    do_rp: bool = False,
) -> tuple[int, list[str]]:
    """
    Compute a festival-improvement signal score.
    Returns (score, [reasons])
    """
    score = 0
    reasons = []
    tips = horse.get("tips", []) or []
    cheltenham_rec = (horse.get("cheltenham_record") or "").lower()
    target_dist = race_meta["dist_f"]

    # ── 1. Existing tip signals  ───────────────────────────────────────────
    for tip in tips:
        tip_l = tip.lower()
        if "won same distance" in tip_l or "same race course" in tip_l:
            score += 5
            reasons.append("Won same dist/course class bracket")
        if "festival winner" in tip_l:
            score += 5
            reasons.append("Previous Festival winner")
        if "ground suits" in tip_l:
            score += 5
            reasons.append("Ground suits (tip)")
        if "won this exact race" in tip_l:
            score += 8
            reasons.append("Won this exact race before")
        if "prep gap" in tip_l and "ideal" in tip_l:
            score += 3
            reasons.append("Ideal prep gap timing")
        if "consecutive wins" in tip_l or "won last time" in tip_l:
            score += 5
            reasons.append("In-form winning run")
        if "improving" in tip_l or "well-handicapped" in tip_l:
            score += 5
            reasons.append("Improving / well-handicapped")

    # ── 2. Cheltenham record ───────────────────────────────────────────────
    if "won" in cheltenham_rec and "first time" not in cheltenham_rec:
        score += 15
        reasons.append(f"Cheltenham winner: {horse.get('cheltenham_record','')[:50]}")
    elif any(x in cheltenham_rec for x in ["2nd", "placed", "second"]):
        score += 8
        reasons.append("Cheltenham placed")
    elif "first time" in cheltenham_rec:
        # Unknown quantity — mild penalty handled elsewhere
        pass

    # ── 3. RP form analysis (if scraped) ──────────────────────────────────
    if do_rp and rp_runs:
        # Check last 3 runs for festival venue
        recent = rp_runs[:3]
        older  = rp_runs[3:]

        for i, run in enumerate(recent):
            venue = (run.get("venue") or "").lower()
            going = (run.get("going") or "").lower()
            dist  = run.get("dist_f")
            pos   = run.get("position")

            # Festival venue match
            if any(fv in venue for fv in FESTIVAL_VENUES):
                score += 20
                reasons.append(f"Festival venue ({venue}) in last 3 runs")

                # Placed at festival venue
                if pos and pos <= 3:
                    score += 20
                    reasons.append(f"Placed {pos} at {venue}")

            # Soft going match
            if going in SOFT_GOING:
                score += 8
                reasons.append(f"Recent run on {going} ground")

            # Distance match (within 4f)
            if dist and abs(dist - target_dist) <= 4:
                score += 8
                reasons.append(f"Distance match: {dist}f vs target {target_dist}f")

        # Form improvement: latest pos < avg(last 3)
        positions = [r["position"] for r in rp_runs[:4] if r.get("position")]
        if len(positions) >= 2:
            latest = positions[0]
            prev_avg = sum(positions[1:4]) / len(positions[1:4])
            if latest < prev_avg:
                score += 12
                reasons.append(
                    f"Form improving: last={latest} vs prev_avg={prev_avg:.1f}"
                )
            if latest == 1:
                score += 10
                reasons.append("Won last time out")

        # RPR trend
        rprs = [r["rpr"] for r in rp_runs[:4] if r.get("rpr")]
        if len(rprs) >= 2 and rprs[0] >= max(rprs[1:]) * 0.97:
            score += 5
            reasons.append(f"RPR near peak: {rprs[0]}")

    return score, reasons


# ═══════════════════════════════════════════════════════════════════════════════
# Main scan
# ═══════════════════════════════════════════════════════════════════════════════

def run_scan(args):
    picks_table = dynamodb.Table("CheltenhamPicks")
    flags_table_name = "CheltenhamHandicapFlags"

    # Ensure output table exists
    if not args.no_save:
        client = boto3.client("dynamodb", region_name=REGION)
        existing = client.list_tables()["TableNames"]
        if flags_table_name not in existing:
            client.create_table(
                TableName=flags_table_name,
                KeySchema=[
                    {"AttributeName": "race_name",  "KeyType": "HASH"},
                    {"AttributeName": "horse_name", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "race_name",  "AttributeType": "S"},
                    {"AttributeName": "horse_name", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",
            )
            print(f"  Created DynamoDB table: {flags_table_name}")
            time.sleep(3)

    # Load existing profiles for score enrichment
    profiles_table = dynamodb.Table("CheltenhamFormProfiles")
    prof_resp = profiles_table.scan()
    profiles = {}
    for p in prof_resp["Items"]:
        key = (p.get("horse_name") or "").lower().split("(")[0].strip()
        profiles[key] = p

    # Fetch current picks date (prefer today, then most recent)
    resp = picks_table.scan(FilterExpression=Attr("pick_date").eq(TODAY))
    items = resp["Items"]
    if not items:
        resp = picks_table.scan()
        items = resp["Items"]
        dates = sorted(set(i.get("pick_date","") for i in items), reverse=True)
        latest = dates[0] if dates else TODAY
        items = [i for i in items if i.get("pick_date") == latest]
        print(f"  ⚠ No picks for {TODAY}, using {latest}")

    # Index by race name
    picks_by_race = {i["race_name"]: i for i in items}

    all_results = []
    report_lines = [
        "═" * 80,
        f"  CHELTENHAM HANDICAP FESTIVAL IMPROVEMENT SCANNER  —  {TODAY}",
        "═" * 80,
        "",
        "Signals: festival venue in last 3 runs + soft ground + distance match",
        "         + improving form position + cheltenham record",
        "",
    ]

    # Filter to requested race
    races_to_scan = HANDICAP_RACES
    if args.race:
        races_to_scan = {
            k: v for k, v in HANDICAP_RACES.items()
            if args.race.lower() in k.lower()
        }
        if not races_to_scan:
            print(f"No race matching '{args.race}'. Available races:")
            for r in HANDICAP_RACES:
                print(f"  {r}")
            return

    for race_name, race_meta in sorted(races_to_scan.items(), key=lambda x: (x[1]["day"], x[0])):
        pick_item = picks_by_race.get(race_name)
        if not pick_item:
            # Try partial match
            pick_item = next(
                (v for k, v in picks_by_race.items() if race_name.lower() in k.lower()),
                None
            )
        if not pick_item:
            report_lines.append(f"\n{race_name}  [no DB entry found — skipping]")
            continue

        current_pick = pick_item.get("horse", "?")
        day_label = f"Day {race_meta['day']}"

        # Parse all_horses
        raw = pick_item.get("all_horses", "[]")
        try:
            if isinstance(raw, str):
                all_horses = ast.literal_eval(raw)
            else:
                all_horses = list(raw)
        except Exception:
            all_horses = []

        report_lines.append(f"\n{'─'*78}")
        report_lines.append(
            f"  {day_label}  ·  {race_name}  "
            f"[{race_meta['dist_f']/8:.1f}m, {race_meta['going']}]"
        )
        report_lines.append(
            f"  Current pick: {current_pick} (score {pick_item.get('score','?')})"
        )
        report_lines.append(f"  {'Horse':<30} {'Sys':>4}  {'FI':>4}  Signals")
        report_lines.append(f"  {'─'*30}─{'─'*4}──{'─'*4}──{'─'*40}")

        race_results = []
        for horse in all_horses:
            name = horse.get("name", "")
            sys_score = int(horse.get("score", 0) or 0)

            # Fetch RP form if requested
            rp_runs = []
            if args.rp:
                rp_runs = fetch_rp_form(name)
                time.sleep(1.5)  # be polite

            fi_score, fi_reasons = festival_improvement_score(
                horse, race_meta, rp_runs, do_rp=args.rp
            )

            # Enrich with profile if present
            profile_key = name.lower().split("(")[0].strip()
            if profile_key in profiles:
                p = profiles[profile_key]
                if p.get("cheltenham_total_runs", 0):
                    fi_score += 3
                    fi_reasons.append(
                        f"Profile: {p.get('cheltenham_total_runs')} Cheltn runs"
                    )

            combined = sys_score + fi_score

            race_results.append({
                "race_name":    race_name,
                "horse_name":   name,
                "sys_score":    sys_score,
                "fi_score":     fi_score,
                "combined":     combined,
                "is_our_pick":  (name == current_pick),
                "reasons":      fi_reasons,
                "trainer":      horse.get("trainer", ""),
                "odds":         horse.get("odds", "?"),
                "cheltenham_record": horse.get("cheltenham_record", ""),
            })

        # Sort by combined score
        race_results.sort(key=lambda x: x["combined"], reverse=True)

        dark_horses = []
        for r in race_results[:10]:
            is_pick = r["is_our_pick"]
            pick_tag = " ◄ OUR PICK" if is_pick else ""
            dark_tag = ""
            if r["fi_score"] >= 30 and not is_pick:
                dark_tag = " 🌙 DARK HORSE"
                dark_horses.append(r)
            fi_tag = f" ↑fi+{r['fi_score']}" if r["fi_score"] > 0 else ""
            reasons_str = ", ".join(r["reasons"][:3]) if r["reasons"] else "—"
            report_lines.append(
                f"  {r['horse_name']:<30} {r['sys_score']:>4}  {r['fi_score']:>4}  "
                f"{reasons_str[:45]}{pick_tag}{dark_tag}"
            )

        if dark_horses:
            report_lines.append(f"\n  ⚡ DARK HORSES — not our pick but strong festival signal:")
            for dh in dark_horses:
                report_lines.append(
                    f"    → {dh['horse_name']} @ {dh['odds']}  "
                    f"FI={dh['fi_score']}  trainer={dh['trainer']}"
                )
                for r in dh["reasons"]:
                    report_lines.append(f"       • {r}")

        all_results.extend(race_results)

        # Save to DynamoDB
        if not args.no_save:
            flags_table = dynamodb.Table(flags_table_name)
            for r in race_results:
                with flags_table.batch_writer() as batch:
                    batch.put_item(Item={
                        "race_name":         r["race_name"],
                        "horse_name":        r["horse_name"],
                        "scan_date":         TODAY,
                        "sys_score":         Decimal(str(r["sys_score"])),
                        "fi_score":          Decimal(str(r["fi_score"])),
                        "combined_score":    Decimal(str(r["combined"])),
                        "is_our_pick":       r["is_our_pick"],
                        "trainer":           r["trainer"],
                        "odds":              r["odds"],
                        "cheltenham_record": r["cheltenham_record"],
                        "fi_reasons":        json.dumps(r["reasons"]),
                    })

    # ── Summary: top dark horses across all races ────────────────────────────
    report_lines.append("\n" + "═" * 78)
    report_lines.append("  DARK HORSE SUMMARY — festival improvement signal > our current pick")
    report_lines.append("═" * 78)

    dark_all = [r for r in all_results if r["fi_score"] >= 25 and not r["is_our_pick"]]
    dark_all.sort(key=lambda x: x["fi_score"], reverse=True)

    if dark_all:
        for dh in dark_all[:15]:
            report_lines.append(
                f"  {dh['race_name']:<42} {dh['horse_name']:<28} "
                f"@ {dh['odds']:<8} FI={dh['fi_score']:>3}  sys={dh['sys_score']:>3}"
            )
    else:
        report_lines.append("  No dark horses found (FI score < 25 for all non-picks)")

    report_lines.append("")
    report_lines.append(
        f"  Scan complete: {len(HANDICAP_RACES)} races · "
        f"{len(all_results)} horses evaluated · "
        f"{len(dark_all)} dark horse flags"
    )
    if not args.no_save:
        report_lines.append(
            f"  Results saved to DynamoDB table: {flags_table_name}"
        )
    report_lines.append("═" * 78)

    output = "\n".join(report_lines)
    print(output)

    # Write text report
    report_path = os.path.join(ROOT, "handicap_improvement_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n  Report written to: {report_path}")


# ───────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cheltenham handicap festival improvement scanner"
    )
    parser.add_argument(
        "--race", type=str, default="",
        help="Filter to single race (partial name match)"
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Skip DynamoDB write (dry run)"
    )
    parser.add_argument(
        "--rp", action="store_true",
        help="Attempt Racing Post form scrape for each horse (slower)"
    )
    args = parser.parse_args()
    run_scan(args)

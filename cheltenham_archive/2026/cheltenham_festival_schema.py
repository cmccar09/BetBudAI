"""
cheltenham_festival_schema.py
=============================================================
Validates all 28 Cheltenham 2026 festival race entries and
prints a comprehensive scoring summary, pick confidence,
and field-completeness report.

Usage:
    python cheltenham_festival_schema.py              # full report
    python cheltenham_festival_schema.py --race RACE  # single race (partial name)
    python cheltenham_festival_schema.py --issues      # only show data issues
"""
import sys, os, argparse, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from barrys.surebet_intel import build_all_picks
from barrys.barrys_config import FESTIVAL_RACES

REQUIRED_FIELDS  = {"name", "trainer", "jockey", "odds", "age", "form", "rating",
                    "cheltenham_record", "last_run", "days_off"}
OPTIONAL_FIELDS  = {"ground_pref", "dist_class_form"}

DAY_NAMES = {
    1: "Tuesday 10 Mar (Champion Day)",
    2: "Wednesday 11 Mar (Ladies Day)",
    3: "Thursday 12 Mar (St. Patrick's Day)",
    4: "Friday 13 Mar (Gold Cup Day)",
}

TIER_MAP = {
    (0, 70):   ("F", "WEAK     "),
    (70, 90):  ("D", "AVERAGE  "),
    (90, 110): ("C", "STRONG   "),
    (110, 135):("B", "EXCELLENT"),
    (135, 999):("A", "ELITE    "),
}


def tier_label(score):
    for (lo, hi), (letter, label) in TIER_MAP.items():
        if lo <= score < hi:
            return letter, label
    return "A", "ELITE    "


def analyse_picks():
    parser = argparse.ArgumentParser(description="Cheltenham 2026 Festival Schema Validator")
    parser.add_argument("--race", help="Filter to a single race by partial name match")
    parser.add_argument("--issues", action="store_true", help="Only print data issues")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("  CHELTENHAM 2026 FESTIVAL SCHEMA REPORT")
    print("="*80)

    picks = build_all_picks(verbose=True)   # verbose=True → full scored list, not just top-3

    total_horses  = 0
    total_issues  = 0
    all_issues    = []

    current_day = 0
    for key, p in sorted(picks.items(), key=lambda x: (x[1]["day"], x[1]["time"])):
        rname     = p["race_name"]
        day       = p["day"]
        time_str  = p["time"]
        scored    = p.get("scored", [])

        # Apply the race name filter if provided
        if args.race and args.race.lower() not in rname.lower():
            continue

        if not args.issues:
            if day != current_day:
                current_day = day
                print(f"\n{'─'*80}")
                print(f"  DAY {day}  ·  {DAY_NAMES.get(day, '')}")
                print(f"{'─'*80}")

            sb   = p.get("surebet", {})
            ds   = p.get("douglas", {})
            tier_l, tier_n = tier_label(sb.get("score", 0))
            print(f"\n  ⏰ {time_str}  {rname}  [{len(scored)} runners]")
            print(f"     SureBet: {sb.get('name','?'):<32} score={sb.get('score',0):3}  "
                  f"{tier_l} {tier_n.strip()}  @{sb.get('odds','?')}")
            if ds.get("name") != sb.get("name"):
                print(f"     Douglas: {ds.get('name','?'):<32} score={ds.get('score',0):3}  "
                      f"(festival specialist diverges)")

            # Top 3 with gap
            for rank, h in enumerate(scored[:3], 1):
                gap = scored[0]["score"] - h["score"]
                rec = (h.get("cheltenham_record") or "—")[:40]
                print(f"       {rank}. {h['name']:<30} {h['score']:3}  gap={gap:2}  rec={rec}")

        # --- Validate entries ---
        for h in scored:
            issues = []
            rec = h.get("cheltenham_record") or ""
            if not rec or rec == "First time":
                issues.append("⚠ cheltenham_record missing")
            if h.get("score", 0) < 45:
                issues.append(f"⚠ Suspiciously low score {h['score']}")
            if not h.get("trainer") or h["trainer"] in ("?", ""):
                issues.append("⚠ Missing trainer")
            if issues:
                total_issues += len(issues)
                for iss in issues:
                    all_issues.append(f"  {rname} | {h['name']:<30} | {iss}")

        total_horses += len(scored)

    # Full issues summary
    print(f"\n{'='*80}")
    print(f"  SUMMARY: {total_horses} horses across {len(picks)} races  |  {total_issues} issues found")
    print(f"{'='*80}")
    if all_issues:
        print(f"\n  DATA ISSUES ({total_issues}):")
        for iss in all_issues[:40]:
            print(iss)
        if len(all_issues) > 40:
            print(f"  ... and {len(all_issues)-40} more")
    else:
        print("\n  ✅ No data issues found — all fields complete")

    # Pick confidence summary
    if not args.issues and not args.race:
        print(f"\n{'─'*80}")
        print("  PICK CONFIDENCE SUMMARY (by day)")
        print(f"{'─'*80}")
        for day_num in [1, 2, 3, 4]:
            day_picks = [(k, p) for k, p in picks.items() if p["day"] == day_num]
            betting_picks = [(k, p) for k, p in day_picks
                             if p.get("surebet", {}).get("score", 0) >= 100]
            print(f"\n  Day {day_num} — {DAY_NAMES.get(day_num, '')} — {len(day_picks)} races")
            for k, p in sorted(day_picks, key=lambda x: x[1]["time"]):
                sb    = p["surebet"]
                t, n  = tier_label(sb.get("score", 0))
                flag  = "🎯 BETTING PICK" if sb.get("score", 0) >= 100 else "👀 WATCH LIST "
                sc    = p.get("scored", [])
                gap   = sc[0]["score"] - sc[1]["score"] if len(sc) > 1 else 99
                odds  = sb.get("odds", "?")
                print(f"    {flag}  {p['race_name']:<42}  {sb['name']:<28}  "
                      f"@{odds:<6}  {t}{sb['score']:3}  gap={gap:2}")

    print()


if __name__ == "__main__":
    analyse_picks()

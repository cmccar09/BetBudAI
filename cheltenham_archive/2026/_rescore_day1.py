"""
_rescore_day1.py
Full scoring breakdown for all Day 1 (Champion Day) races — 10 March 2026
"""
import sys
sys.path.insert(0, r'c:\Users\charl\OneDrive\futuregenAI\Betting')

from barrys.surebet_intel import EXTRA_RACES, RACES_2026_MAP, _score_tier
from cheltenham_deep_analysis_2026 import RACES_2026, score_horse_2026
from cheltenham_full_fields_2026 import extend_race_entries
from barrys.barrys_config import FESTIVAL_RACES

# Build the combined race data
all_race_data = {}
for r2026_name, entries_data in RACES_2026.items():
    fkey = RACES_2026_MAP.get(r2026_name)
    if fkey:
        all_race_data[fkey] = entries_data["entries"]
for fkey, data in EXTRA_RACES.items():
    all_race_data[fkey] = data["entries"]

day1_keys = sorted(
    [k for k, v in FESTIVAL_RACES.items() if v["day"] == 1],
    key=lambda x: FESTIVAL_RACES[x]["time"]
)

print("=" * 105)
print("  DAY 1 — CHAMPION DAY — FULL SCORE BREAKDOWN  (Tuesday 10 March 2026)")
print("=" * 105)

for rkey in day1_keys:
    rinfo = FESTIVAL_RACES[rkey]
    base_entries = all_race_data.get(rkey, [])
    entries = extend_race_entries(rkey, base_entries)
    if not entries:
        print(f"\n  NO ENTRIES: {rinfo['time']} {rinfo['name']}")
        continue

    scored = []
    for h in entries:
        s, tips, warnings, val = score_horse_2026(h, rinfo["name"])
        scored.append({**h, "score": s, "tips": tips, "warnings": warnings, "value": val})
    scored.sort(key=lambda x: x["score"], reverse=True)

    top = scored[0]
    second = scored[1] if len(scored) > 1 else None
    gap = top["score"] - second["score"] if second else 0
    tier = _score_tier(top["score"])

    print(f"\n{'─' * 105}")
    print(f"  {rinfo['time']}  {rinfo['name'].upper()}  |  {rinfo['grade']}  |  {len(entries)} runners")
    print(f"  *** PICK:  {top['name']}  [{top['trainer']} / {top['jockey']}]")
    print(f"       Score={top['score']}  Tier={tier}  Gap=+{gap:.0f} over 2nd  Odds={top.get('odds','?')}")
    print(f"       Cheltenham record: {top.get('cheltenham_record') or 'None recorded'}")
    print(f"       Last run: {top.get('last_run','?')}  ({top.get('days_off','?')} days ago)")
    print(f"       Form (recent-first): {top.get('form','?')}  RPR: {top.get('rating','?')}")
    tips_str = " | ".join(top["tips"][:7])
    print(f"       Scoring: {tips_str}")
    if top["warnings"]:
        print(f"       Warnings: {' | '.join(top['warnings'])}")

    print(f"\n  {'#':<3} {'HORSE':<26} {'TRAINER':<26} {'JOCKEY':<22} {'ODDS':<8} {'RPR':<5} {'SCORE':<7} {'TIER':<16} CHELTENHAM")
    print(f"  {'-'*103}")
    for i, h in enumerate(scored[:8], 1):
        cht  = (h.get("cheltenham_record") or "")[:22]
        flag = "  <<< PICK" if i == 1 else ""
        print(f"  {i:<3} {h['name'][:25]:<26} {h['trainer'][:25]:<26} {h['jockey'][:21]:<22} "
              f"{h.get('odds','sp'):<8} {h.get('rating',0):<5} {h['score']:<7.0f} "
              f"{_score_tier(h['score']):<16} {cht}{flag}")

print(f"\n{'=' * 105}")
print("  SUMMARY — DAY 1 PICKS")
print(f"{'=' * 105}")
print(f"  {'TIME':<7} {'RACE':<42} {'PICK':<26} {'ODDS':<8} {'SCORE':<7} {'TIER':<16} GAP")
print(f"  {'-'*105}")

for rkey in day1_keys:
    rinfo = FESTIVAL_RACES[rkey]
    base_entries = all_race_data.get(rkey, [])
    entries = extend_race_entries(rkey, base_entries)
    if not entries:
        continue
    scored = []
    for h in entries:
        s, tips, warnings, val = score_horse_2026(h, rinfo["name"])
        scored.append({**h, "score": s})
    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[0]
    gap = top["score"] - scored[1]["score"] if len(scored) > 1 else 0
    print(f"  {rinfo['time']:<7} {rinfo['name'][:41]:<42} {top['name'][:25]:<26} "
          f"{top.get('odds','?'):<8} {top['score']:<7.0f} {_score_tier(top['score']):<16} +{gap:.0f}")

print()

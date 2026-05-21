import sys; sys.path.insert(0,"."); sys.path.insert(0,"barrys")
from barrys.surebet_intel import EXTRA_RACES
from cheltenham_deep_analysis_2026 import score_horse_2026

print("=== Gold Cup (day4_race6) field ===")
entries = EXTRA_RACES.get("day4_race6", {}).get("entries", [])
results = sorted([(score_horse_2026(h, "Cheltenham Gold Cup")[0], h["name"], h.get("odds","?"), h.get("jockey","?"), h.get("rating","?")) for h in entries], reverse=True)
for sc, nm, od, jk, rt in results:
    print(f"  {sc}  {nm}  {od}  OR:{rt}  {jk}")

print()
print("=== Stayers (day3_race4) ===")
for h in EXTRA_RACES.get("day3_race4", {}).get("entries", []):
    print(f"  {h['name']}  {h.get('jockey','?')}")

print()
print("=== All keys in EXTRA_RACES ===")
print(list(EXTRA_RACES.keys()))

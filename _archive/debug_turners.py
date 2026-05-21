import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from barrys.surebet_intel import build_all_picks

raw = build_all_picks(verbose=True)
race = raw.get('day2_race1', {})
scored = race.get('scored', [])
print("Turner's Novices' Hurdle — Full Scoring Breakdown")
print("=" * 70)
for h in scored[:6]:
    print(f"\n  {h['name']:<30} score={h['score']}")
    for tip in h.get('tips', []):
        print(f"    + {tip}")
    for w in h.get('warnings', []):
        print(f"    ! {w}")

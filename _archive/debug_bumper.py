"""Debug Champion Bumper scoring"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from barrys.surebet_intel import build_all_picks

picks = build_all_picks(verbose=True)

for key, p in picks.items():
    if "bumper" in p["race_name"].lower():
        print(f"\n{'='*70}")
        print(f"  {p['race_name']}")
        print(f"{'='*70}")
        for i, h in enumerate(p["scored"][:10]):
            print(f"  {i+1:2}. {h['name']:<32} score={h['score']:3}  odds={h.get('odds','?')}")
            for t in h["tips"]:
                print(f"       + {t}")
            for w in h["warnings"]:
                print(f"       ! {w}")
        break

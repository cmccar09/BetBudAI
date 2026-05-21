"""Debug  Queen Mother Champion Chase scoring"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from barrys.surebet_intel import build_all_picks

picks = build_all_picks(verbose=False)

for key, p in picks.items():
    name = p["race_name"]
    if "queen mother" in name.lower() or ("champion" in name.lower() and "chase" in name.lower()):
        print(f"\n{'='*70}")
        print(f"  {name}")
        print(f"{'='*70}")
        sb = p["surebet"]
        print(f"  SureBet pick : {sb['name']}  score={sb['score']}")
        print()
        for i, h in enumerate(p["scored"][:10]):
            print(f"  {i+1:2}. {h['name']:<32} score={h['score']:3}  rec={h['cheltenham_record'][:40] if h['cheltenham_record'] else 'None'}")
            for t in h["tips"]:
                print(f"       + {t}")
            for w in h["warnings"]:
                print(f"       ! {w}")
        break

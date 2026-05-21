import sys; sys.path.insert(0, '.')
from save_cheltenham_picks import get_betfair_live_odds
from barrys.surebet_intel import build_all_picks

odds = get_betfair_live_odds()
picks = build_all_picks(verbose=False)

for day_num in [1]:
    for k, r in sorted(picks.items(), key=lambda x: x[1]['time']):
        if r['day'] != day_num:
            continue
        top  = r['surebet']
        s    = r['scored']
        top2 = s[1] if len(s) > 1 else {}
        top3 = s[2] if len(s) > 2 else {}
        live  = odds.get(top['name'].lower(), '?')
        live2 = odds.get(top2.get('name','').lower(), '?') if top2 else '?'
        live3 = odds.get(top3.get('name','').lower(), '?') if top3 else '?'
        print(f"{r['time']}  {r['race_name']}")
        print(f"  #1  {top['name']:<30} [{live:<8}]  score={top.get('score',0):.0f}  T:{top.get('trainer','?')}  J:{top.get('jockey','?')}")
        print(f"  #2  {top2.get('name','?'):<30} [{live2:<8}]  score={top2.get('score',0):.0f}")
        print(f"  #3  {top3.get('name','?'):<30} [{live3:<8}]  score={top3.get('score',0):.0f}")
        print()

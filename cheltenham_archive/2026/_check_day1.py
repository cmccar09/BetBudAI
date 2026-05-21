from barrys.surebet_intel import build_all_picks
picks = build_all_picks(verbose=False)
for key in ['day1_race6', 'day1_race7']:
    r = picks.get(key, {})
    print(f"\n{key}: {r.get('race_name')} @ {r.get('time')}")
    sb = r.get('surebet', {})
    ds = r.get('douglas', {})
    print(f"  SureBet pick : {sb.get('name')}  score={sb.get('score')}")
    print(f"  MacFitz pick : {ds.get('name')}  score={ds.get('score')}")
    print("  Top 3 scored:")
    for h in r.get('scored', [])[:3]:
        print(f"    {h.get('name')}  total={h.get('total_score')}  tier={h.get('tier')}")

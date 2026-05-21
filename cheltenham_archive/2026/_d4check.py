import sys; sys.path.insert(0,"."); sys.path.insert(0,"barrys")
from barrys.surebet_intel import EXTRA_RACES
from barrys.barrys_config import FESTIVAL_RACES
from cheltenham_deep_analysis_2026 import score_horse_2026

day4 = {k:v for k,v in FESTIVAL_RACES.items() if v["day"]==4}
for key in sorted(day4, key=lambda x: day4[x]["time"]):
    info = day4[key]
    entries = EXTRA_RACES.get(key, {}).get("entries", [])
    name = info["name"]
    time = info["time"]
    if entries:
        results = sorted([(score_horse_2026(h, name)[0], h["name"], h.get("odds","?"), h.get("jockey","?")) for h in entries], reverse=True)
        top = results[0]
        tbds = sum(1 for _,_,_,j in results if j in ("TBD",""))
        print(time + "  " + key + "  " + name + "  [" + str(len(entries)) + " runners]")
        print("  TOP: " + top[1] + " (" + str(top[0]) + "pts @ " + str(top[2]) + ") - J:" + str(top[3]))
        if tbds:
            print("  *** " + str(tbds) + " jockeys TBD - NEEDS LIVE CARD ***")
    else:
        print(time + "  " + key + "  " + name)
        print("  *** NO DATA - NEEDS CARD ***")
    print()

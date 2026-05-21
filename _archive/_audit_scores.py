import sys, json
sys.path.insert(0, '.')
from barrys.update_barrys_html import load_results, compute_competition_scores, load_overrides, apply_macfitz, fetch_latest_picks, RACES

overrides = load_overrides()
db_picks = fetch_latest_picks()
assembled = []
for race in RACES:
    db_name = race[2]
    sb_pick = db_picks.get(db_name)
    if not sb_pick:
        for key in db_picks:
            if db_name.lower() in key.lower() or key.lower() in db_name.lower():
                sb_pick = db_picks[key]
                break
    if not sb_pick:
        sb_pick = {"horse": "TBC", "score": 0, "tier": "?", "race_name": db_name, "second_horse_name": "", "second_score": 0, "score_gap": 999}
    mf_pick = apply_macfitz(sb_pick, overrides)
    assembled.append((race, sb_pick, mf_pick))
results = load_results()
scores = compute_competition_scores(assembled, results)

sb_total = scores["sb_total"]
mf_total = scores["mf_total"]
races_run = scores["races_run"]
print(f"SB: {sb_total}  MF: {mf_total}  Races: {races_run}")
print()
print(f"{'Race':<45} {'SB Horse':<22} {'SP':>4}  {'MF Horse':<22} {'MP':>4}   Result")
print('-' * 120)
for row in scores["per_race"]:
    db_name, sb, mf, sp, mp, p1, p2, p3 = row
    if sp == -1:
        continue
    print(f"{db_name:<45} {sb:<22} {sp:>4}  {mf:<22} {mp:>4}   [{p1} / {p2} / {p3}]")

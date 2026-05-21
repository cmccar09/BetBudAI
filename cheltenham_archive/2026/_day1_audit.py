"""Day 1 model audit — run after all results are in."""
from barrys.surebet_intel import build_all_picks

picks = build_all_picks(verbose=False)

results = {
    "Sky Bet Supreme Novices' Hurdle":  ("Old Park Star",   "Sober Glory",    "Mydaddypaddy"),
    "Arkle Challenge Trophy Chase":     ("Kargese",         "Kopek Des Bordes","Lulamba"),
    "Fred Winter Handicap Hurdle":      ("Saratoga",        "Winston Junior",  "Madness Delle"),
    "Ultima Handicap Chase":            ("Johnnywho",       "Jagwar",          "Quebecois"),
    "Unibet Champion Hurdle":           ("Lossiemouth",     "Brighterdaysahead","The New Lion"),
    "Cheltenham Plate Chase":           ("Madara",          "Will The Wise",   "Moon D'orange"),
    "Challenge Cup Chase":              ("Holloway Queen",  "King Of Answers", "One Big Bang"),
}

POINTS = {1: 10, 2: 5, 3: 3}

print("=" * 80)
print("DAY 1 MODEL AUDIT — Challenge Day (10 March 2026)")
print("=" * 80)

day1 = {k: v for k, v in picks.items() if v.get("day") == 1}
total_sb = 0
insights = []

for k, r in sorted(day1.items()):
    rname = r.get("race_name", "")
    res = results.get(rname)
    if not res:
        continue
    winner, second, third = res
    sc = r.get("scored", [])
    if not sc:
        continue
    top = sc[0]
    pick = top.get("name", "?")
    pick_score = top.get("score", 0)

    # Outcome
    p = pick.lower()
    if p == winner.lower():
        pts = 10; outcome = "WIN  ✅"
    elif p == second.lower():
        pts = 5;  outcome = "2nd  ✅"
    elif p == third.lower():
        pts = 3;  outcome = "3rd  ✅"
    else:
        pts = 0;  outcome = "MISS ❌"
    total_sb += pts

    # Where was the winner in our ranking?
    w_rank = next((i+1 for i, h in enumerate(sc) if h.get("name","").lower() == winner.lower()), None)
    w_score = next((h.get("score",0) for h in sc if h.get("name","").lower() == winner.lower()), 0)
    gap_to_winner = pick_score - w_score

    print(f"\n  {rname}")
    print(f"    Pick : {pick:<25} score={pick_score:3d}  result={outcome}  (+{pts}pts)")
    print(f"    Winner: {winner:<24} score={w_score:3d}  ranked #{w_rank} in our model")
    if pts == 0 and w_rank:
        print(f"    GAP  : our pick was +{gap_to_winner} over winner in model score — LEARNING OPPORTUNITY")
        tag = ""
        if w_rank == 1:
            tag = "Model was RIGHT but pick logic diverged"
        elif w_rank <= 3:
            tag = f"Winner was in our top-3 (#{w_rank}) — CLOSE"
        elif w_rank <= 6:
            tag = f"Winner was #{w_rank} — missed but in top half"
        else:
            tag = f"Winner was #{w_rank} — model missed badly"
        print(f"    NOTE : {tag}")
        insights.append((rname, pick, winner, w_rank, gap_to_winner))

print()
print(f"  Total Surebet points: {total_sb}")
print()
print("=" * 80)
print("EDGE LEARNINGS")
print("=" * 80)
for rname, pick, winner, w_rank, gap in insights:
    print(f"\n  {rname}")
    if w_rank <= 3:
        print(f"    ✅ Winner ({winner}) was in our top 3 (#{w_rank}) — model had the horse,")
        print(f"       but scored {gap} pts below our pick. Consider:")
        print(f"       → If gap <= 15, soft-line race (handicap/large field) — top-2 coverage strategy?")
    else:
        print(f"    ❌ Winner ({winner}) was #{w_rank} — model didn't have it near the top.")
        print(f"       → BLIND SPOT: research what our model is missing for this horse type")

# Challenge Cup specific
print()
print("  Challenge Cup (last race):")
r7 = picks.get("day1_race7", {})
sc7 = r7.get("scored", [])
hw_rank = next((i+1 for i,h in enumerate(sc7) if "holloway" in h.get("name","").lower()), None)
hw_score = next((h.get("score",0) for h in sc7 if "holloway" in h.get("name","").lower()), 0)
top_score = sc7[0].get("score",0) if sc7 else 0
print(f"    Holloway Queen (winner 12/1): ranked #{hw_rank} in model, score={hw_score}")
print(f"    Our pick Backmersackme: score={top_score}, gap over winner = {top_score - hw_score}")
print(f"    Nicky Henderson / James Bowen — typical Day 1 closer for Henderson")
print(f"    LEARNING: Henderson late-day handicap chasers at big prices need explicit bonus")

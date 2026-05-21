import boto3
from boto3.dynamodb.conditions import Attr
from collections import defaultdict

dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
table = dynamodb.Table("SureBetBets")
all_items = []
resp = table.scan(FilterExpression=Attr("comprehensive_score").exists())
all_items.extend(resp["Items"])
while "LastEvaluatedKey" in resp:
    resp = table.scan(FilterExpression=Attr("comprehensive_score").exists(), ExclusiveStartKey=resp["LastEvaluatedKey"])
    all_items.extend(resp["Items"])

races = defaultdict(list)
for item in all_items:
    date = item.get("bet_date", "")
    course = item.get("course", "")
    rt = str(item.get("race_time", ""))[:16]
    if date and course and rt:
        races[(date, course, rt)].append(item)

gap_results = []
for race_key, horses in races.items():
    scored = sorted(horses, key=lambda h: float(h.get("comprehensive_score",0) or 0), reverse=True)
    best = scored[0]
    best_score = float(best.get("comprehensive_score",0) or 0)
    if best_score < 85:
        continue
    outcome = best.get("outcome","")
    if outcome not in ("won","lost","placed"):
        continue
    second_score = float(scored[1].get("comprehensive_score",0) or 0) if len(scored) >= 2 else 0
    gap = best_score - second_score
    gap_results.append({"horse": best.get("horse"), "score": best_score,
                        "second": second_score, "gap": gap, "outcome": outcome,
                        "pl": float(best.get("profit_loss",0) or 0)})

print("85+ score picks with settled results:", len(gap_results))
print()
big  = [r for r in gap_results if r["gap"] > 15]
med  = [r for r in gap_results if 5 <= r["gap"] <= 15]
sml  = [r for r in gap_results if 0 <= r["gap"] < 5]

print()
print("SCORE GAP vs ROI VERDICT (85+ picks only)")
print("-" * 65)
for name, b in [("Big gap >15", big), ("Gap 5-15", med), ("Gap 0-5", sml)]:
    if not b:
        continue
    w = sum(1 for r in b if r["outcome"] == "won")
    p = sum(1 for r in b if r["outcome"] == "placed")
    pl = sum(r["pl"] for r in b)
    sr = (w + p) / len(b) * 100
    roi = pl / (len(b) * 6) * 100
    print(f"{name:<20} n={len(b):>3}  W={w} P={p}  SR={sr:>5.1f}%  P/L={pl:+.2f}  ROI={roi:+.1f}%")

print()
print("All 85+ picks sorted by gap (largest gap first):")
for r in sorted(gap_results, key=lambda x: x["gap"], reverse=True):
    sym = "W" if r["outcome"] == "won" else "P" if r["outcome"] == "placed" else "L"
    horse = r["horse"] if r["horse"] else "?"
    print(f"  [{sym}] {horse:<28} score={r['score']:>5.0f}  next={r['second']:>5.0f}  gap=+{r['gap']:>4.0f}  pl={r['pl']:+.2f}")

print()
print("=" * 65)
print("SHOULD WE ADD SCORE GAP AS A SCORING FACTOR?")
print("=" * 65)
if big and sml:
    big_roi = sum(r["pl"] for r in big) / (len(big) * 6) * 100
    sml_roi = sum(r["pl"] for r in sml) / (len(sml) * 6) * 100
    if big_roi > sml_roi + 10:
        print(f"YES - Large gap ROI {big_roi:+.1f}% is significantly better than small gap ROI {sml_roi:+.1f}%")
        print("RECOMMENDATION: Add +5 bonus pts when score_gap > 15")
    elif big_roi < sml_roi:
        print(f"NO - Large gap ROI {big_roi:+.1f}% is WORSE than small gap ROI {sml_roi:+.1f}%")
        print("RECOMMENDATION: Do not add gap as bonus factor - it does not predict wins")
    else:
        print(f"INCONCLUSIVE - Large gap ROI {big_roi:+.1f}% vs small gap ROI {sml_roi:+.1f}%")
        print("RECOMMENDATION: Need more data - do not change scoring yet")
else:
    print("Not enough data to draw conclusions - need at least 3+ races per bucket")

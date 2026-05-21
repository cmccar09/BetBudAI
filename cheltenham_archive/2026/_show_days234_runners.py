"""Print full fields for Days 2, 3, 4 from DynamoDB CheltenhamPicks."""
import boto3, json
from collections import defaultdict
from decimal import Decimal

DAY_LABELS = {
    "Wednesday_11_March": "Day 2 — Wednesday 11 March",
    "Thursday_12_March":  "Day 3 — Thursday 12 March",
    "Friday_13_March":    "Day 4 — Friday 13 March",
}
TARGET_DAYS = set(DAY_LABELS.keys())

ddb = boto3.resource("dynamodb", region_name="eu-west-1")
table = ddb.Table("CheltenhamPicks")

resp = table.scan()
items = list(resp["Items"])
while resp.get("LastEvaluatedKey"):
    resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
    items += list(resp["Items"])

# Most recent date only
dates = sorted({i.get("pick_date", "") for i in items}, reverse=True)
latest = dates[0] if dates else "2026-03-08"

today_items = [i for i in items if i.get("pick_date") == latest and i.get("day") in TARGET_DAYS]
print(f"Using date: {latest}  |  {len(today_items)} races for Days 2-4\n")

by_day = defaultdict(list)
for item in today_items:
    by_day[item.get("day", "?")].append(item)

day_order = ["Wednesday_11_March", "Thursday_12_March", "Friday_13_March"]

total_runners = 0
for day_key in day_order:
    races = by_day.get(day_key, [])
    if not races:
        continue
    print()
    print("=" * 88)
    print(f"  {DAY_LABELS[day_key]}")
    print("=" * 88)
    races_sorted = sorted(races, key=lambda x: x.get("race_time", ""))
    for race in races_sorted:
        rname = race.get("race_name", "?")
        rtime = race.get("race_time", "?")
        tier  = race.get("bet_tier", race.get("tier", "?"))
        top   = race.get("horse", "?")
        tscore = float(race.get("score", 0) or 0)
        top_odds = race.get("odds", "?")
        all_h = race.get("all_horses", [])
        active = [h for h in all_h if str(h.get("status", "ACTIVE")).upper() != "REMOVED"]
        total_runners += len(active)

        print(f"\n  {rtime}  {rname}  [{tier}]")
        print(f"  TOP PICK: {top} @ {top_odds}  (score {tscore})")
        if active:
            print(f"  {'#':<4}{'HORSE':<32}{'SCORE':<8}{'GRADE':<16}{'ODDS':<10}TIER")
            print(f"  {'':-<78}")
            sorted_h = sorted(active, key=lambda x: float(x.get("score", 0) or 0), reverse=True)
            for h in sorted_h:
                name  = h.get("name", "?")
                score = h.get("score", "-")
                grade = h.get("grade", "-")
                odds  = h.get("odds", "?")
                cloth = str(h.get("cloth", "?"))
                htier = h.get("tier", "-")
                print(f"  {cloth:<4}{name:<32}{str(score):<8}{str(grade):<16}{str(odds):<10}{htier}")
        else:
            print("  (no runner data)")

print()
print(f"Total active runners Days 2-4: {total_runners}")

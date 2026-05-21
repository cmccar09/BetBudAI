"""Verify all 28 races in DynamoDB and HTML are correct for Cheltenham 2026."""
import boto3
import re
from collections import defaultdict
from datetime import date

EXPECTED = {
    "Day 1": [
        "Sky Bet Supreme Novices' Hurdle",
        "Arkle Challenge Trophy Chase",
        "Fred Winter Handicap Hurdle",
        "Ultima Handicap Chase",
        "Unibet Champion Hurdle",
        "Cheltenham Plate Chase",
        "Challenge Cup Chase",
    ],
    "Day 2": [
        "Turner's Novices' Hurdle",
        "Brown Advisory Novices' Chase",
        "BetMGM Cup Hurdle",
        "Glenfarclas Cross Country Chase",
        "Queen Mother Champion Chase",
        "Grand Annual Handicap Chase",
        "Champion Bumper",
    ],
    "Day 3": [
        "Ryanair Mares' Novices' Hurdle",
        "Jack Richards Novices' Chase",
        "Close Brothers Mares' Hurdle",
        "Paddy Power Stayers' Hurdle",
        "Ryanair Chase",
        "Pertemps Handicap Hurdle",
        "Kim Muir Handicap Chase",
    ],
    "Day 4": [
        "JCB Triumph Hurdle",
        "County Handicap Hurdle",
        "Albert Bartlett Novices' Hurdle",
        "Mrs Paddy Power Mares' Chase",
        "Cheltenham Gold Cup",
        "St James's Place Hunters' Chase",
        "Martin Pipe Handicap Hurdle",
    ],
}
ALL_EXPECTED = [n for names in EXPECTED.values() for n in names]

# ── DynamoDB check ────────────────────────────────────────────────────────────
print("=" * 72)
print("DYNAMODB CHECK")
print("=" * 72)

dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
table = dynamodb.Table("CheltenhamPicks")

resp = table.scan()
items = resp["Items"]
while resp.get("LastEvaluatedKey"):
    resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
    items += resp["Items"]

today = str(date.today())
print(f"Total records in table: {len(items)}   today={today}\n")

by_date = defaultdict(list)
for it in items:
    by_date[it.get("pick_date", "?")].append(it)

def _day_sort_key(x):
    d = x.get("day", 0)
    try:
        return (int(d), x.get("race_time", "00:00"))
    except (ValueError, TypeError):
        return (str(d), x.get("race_time", "00:00"))

today_items = sorted(by_date.get(today, []), key=_day_sort_key)
print(f"TODAY ({today}) — {len(today_items)} records:\n")
print(f"  {'Day':>4}  {'Time':<6}  {'Race Name':<45}  {'Pick':<26}  {'Score':>5}  {'Runners':>7}  Status")
print(f"  {'-'*4}  {'-'*6}  {'-'*45}  {'-'*26}  {'-'*5}  {'-'*7}  {'-'*10}")

db_names = set(it["race_name"] for it in today_items)
all_ok = True
for it in today_items:
    d = it.get("day", "?")
    t = it.get("race_time", "?")
    rn = it["race_name"]
    horse = it.get("horse", "?")
    score = it.get("score", "?")
    n_runners = len(it.get("all_horses", []))
    status = "OK" if rn in ALL_EXPECTED else "!! WRONG !!"
    if status != "OK":
        all_ok = False
    print(f"  {str(d):>4}  {t:<6}  {rn[:45]:<45}  {horse[:26]:<26}  {str(score):>5}  {n_runners:>7}  {status}")

print()
missing = [n for n in ALL_EXPECTED if n not in db_names]
unexpected = [n for n in db_names if n not in ALL_EXPECTED]

if missing:
    print(f"MISSING ({len(missing)}):")
    for n in missing:
        print(f"  MISSING: {n}")
else:
    print("MISSING: none")

if unexpected:
    print(f"\nUNEXPECTED ({len(unexpected)}):")
    for n in unexpected:
        print(f"  UNEXPECTED: {n}")
else:
    print("UNEXPECTED: none")

print()
print("All dates in table:")
for d in sorted(by_date.keys()):
    print(f"  {d}: {len(by_date[d])} records")

# ── HTML check ────────────────────────────────────────────────────────────────
print()
print("=" * 72)
print("HTML CHECK  (barrys/barrys_cheltenham_2026.html)")
print("=" * 72)

html_path = r"barrys\barrys_cheltenham_2026.html"
try:
    with open(html_path, encoding="utf-8") as f:
        html = f.read()
    html_names_found = []
    for name in ALL_EXPECTED:
        if name in html:
            html_names_found.append(name)

    print(f"HTML file size: {len(html):,} bytes\n")
    html_ok = True
    for day_label, races in EXPECTED.items():
        print(f"  {day_label}:")
        for rn in races:
            present = rn in html
            status = "OK" if present else "MISSING"
            if not present:
                html_ok = False
            print(f"    {'✓' if present else '✗'}  {rn}  [{status}]")
    print()
    if html_ok:
        print("HTML: all 28 race names present  OK")
    else:
        print("HTML: SOME RACES MISSING — see above")
except FileNotFoundError:
    print("ERROR: HTML file not found")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 72)
print("SUMMARY")
print("=" * 72)
db_status = "ALL 28 CORRECT" if (len(today_items) == 28 and not missing and not unexpected and all_ok) else f"ISSUES FOUND — {len(today_items)}/28 present, {len(missing)} missing, {len(unexpected)} unexpected"
print(f"  DB  : {db_status}")
print(f"  HTML: {'ALL 28 CORRECT' if html_ok else 'ISSUES FOUND'}")

"""Delete DynamoDB CheltenhamPicks records with non-2026 race names."""
import boto3

OFFICIAL_NAMES = {
    # Day 1
    "Sky Bet Supreme Novices' Hurdle",
    "Arkle Challenge Trophy Chase",
    "Fred Winter Handicap Hurdle",
    "Ultima Handicap Chase",
    "Unibet Champion Hurdle",
    "Cheltenham Plate Chase",
    "Challenge Cup Chase",
    # Day 2
    "Turner's Novices' Hurdle",
    "Brown Advisory Novices' Chase",
    "BetMGM Cup Hurdle",
    "Glenfarclas Cross Country Chase",
    "Queen Mother Champion Chase",
    "Grand Annual Handicap Chase",
    "Champion Bumper",
    # Day 3
    "Ryanair Mares' Novices' Hurdle",
    "Jack Richards Novices' Chase",
    "Close Brothers Mares' Hurdle",
    "Paddy Power Stayers' Hurdle",
    "Ryanair Chase",
    "Pertemps Handicap Hurdle",
    "Kim Muir Handicap Chase",
    # Day 4
    "JCB Triumph Hurdle",
    "County Handicap Hurdle",
    "Albert Bartlett Novices' Hurdle",
    "Mrs Paddy Power Mares' Chase",
    "Cheltenham Gold Cup",
    "St James's Place Hunters' Chase",
    "Martin Pipe Handicap Hurdle",
}

ddb = boto3.resource("dynamodb", region_name="eu-west-1")
table = ddb.Table("CheltenhamPicks")

# Full scan
resp = table.scan()
items = list(resp["Items"])
while resp.get("LastEvaluatedKey"):
    resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
    items += list(resp["Items"])

print(f"Total records in DB: {len(items)}")

stale = [i for i in items if i.get("race_name") not in OFFICIAL_NAMES]
keep  = [i for i in items if i.get("race_name") in OFFICIAL_NAMES]

print(f"Official records to keep : {len(keep)}")
print(f"Stale records to delete  : {len(stale)}")
print()

for s in sorted(stale, key=lambda x: (x.get("pick_date",""), x.get("race_name",""))):
    rn = s.get("race_name", "?")
    pd = s.get("pick_date", "?")
    print(f"  DELETE  {pd}  |  {rn}")

if not stale:
    print("Nothing to delete — DB is clean.")
else:
    print()
    with table.batch_writer() as batch:
        for s in stale:
            batch.delete_item(Key={"race_name": s["race_name"], "pick_date": s["pick_date"]})
    print(f"Deleted {len(stale)} stale records. Done.")

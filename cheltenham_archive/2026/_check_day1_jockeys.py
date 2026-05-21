"""Check all Day 1 jockeys from DynamoDB against known correct data."""
import boto3
from datetime import date

dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
table = dynamodb.Table("CheltenhamPicks")

today = str(date.today())
resp = table.scan(
    FilterExpression=(
        boto3.dynamodb.conditions.Attr("pick_date").eq(today) &
        boto3.dynamodb.conditions.Attr("day").eq("Tuesday_10_March")
    )
)
items = sorted(resp["Items"], key=lambda x: x.get("race_time", ""))

for race in items:
    print(f"\n{'='*70}")
    print(f"{race['race_time']}  {race['race_name']}")
    print(f"  TOP PICK: {race.get('horse')}  J:{race.get('jockey','?')}  T:{race.get('trainer','?')}")
    horses = race.get("all_horses", [])
    print(f"  {'#':<3} {'Horse':<30} {'Jockey':<26} {'Trainer':<30} Odds   Score")
    print(f"  {'-'*3} {'-'*30} {'-'*26} {'-'*30} {'-'*6} {'-'*5}")
    for i, h in enumerate(sorted(horses, key=lambda x: -float(x.get("score") or 0)), 1):
        name  = h.get("name", "?")
        jock  = h.get("jockey", "?")
        train = h.get("trainer", "?")
        odds  = h.get("odds", "?")
        score = h.get("score", "?")
        print(f"  {i:<3} {name:<30} {jock:<26} {train:<30} {str(odds):<7}{score}")

"""One-shot: restore correct picks for completed races in DynamoDB."""
import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime

dynamo = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamo.Table('CheltenhamPicks')

# Authoritative Surebet picks as they stood when each race actually ran on Day 1
# (These are the MODEL picks at race-time, not necessarily the winners)
correct_picks = {
    "Unibet Champion Hurdle":              "Lossiemouth",      # won ✅ +10
    "Sky Bet Supreme Novices' Hurdle":     "Old Park Star",    # won ✅ +10
    "Arkle Challenge Trophy Chase":        "Kopek Des Bordes", # 2nd → +5 pts
    "Fred Winter Handicap Hurdle":         "Manlaga",          # unplaced → 0 pts
    "Ultima Handicap Chase":               "Jagwar",           # 2nd → +5 pts
}

today = "2026-03-10"
for race, horse in correct_picks.items():
    resp = table.query(
        KeyConditionExpression=Key("race_name").eq(race) & Key("pick_date").eq(today)
    )
    if resp["Items"]:
        item = resp["Items"][0]
        current = item.get("horse", "")
        if current != horse:
            table.update_item(
                Key={"race_name": race, "pick_date": today},
                UpdateExpression="SET horse = :h, updated_at = :u, change_reason = :r",
                ExpressionAttributeValues={
                    ":h": horse,
                    ":u": datetime.now().isoformat(),
                    ":r": "Restored: completed race lock — original pick reinstated",
                },
            )
            print(f"  FIXED  {race}: {current!r} -> {horse!r}")
        else:
            print(f"  OK     {race}: {horse!r} already correct")
    else:
        print(f"  MISS   {race}: no DynamoDB entry for {today}")

import sys, boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Key

sys.stdout.reconfigure(encoding="utf-8")

dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
table = dynamodb.Table("SureBetBets")
TODAY = "2026-03-29"

def frac_to_dec(frac):
    n, d = frac.split("/")
    return Decimal(str(round(int(n) / int(d) + 1, 4)))

TARGETS = {
    "Jimmy Speaking": {"outcome": "win", "finish": 1, "sp": frac_to_dec("10/3"), "winner_name": "Jimmy Speaking"},
    "Fine Interview":  {"outcome": "win", "finish": 1, "sp": frac_to_dec("15/8"), "winner_name": "Fine Interview"},
    "Say What You See":{"outcome": "placed", "finish": 3, "sp": frac_to_dec("10/3"), "winner_name": "Harvey"},
}
PLACE_TERMS = Decimal("4")

response = table.query(KeyConditionExpression=Key("bet_date").eq(TODAY))
all_items = response.get("Items", [])
print(f"Total items today: {len(all_items)}")

updated = 0
for pick in all_items:
    horse = pick.get("horse", "")
    if horse not in TARGETS:
        continue
    target = TARGETS[horse]
    outcome = target["outcome"]
    sp = target["sp"]
    finish = target["finish"]
    if outcome == "win":
        ret = float(sp); profit = float(sp) - 1
    else:
        place_dec = Decimal("1") + (sp - 1) / PLACE_TERMS
        ret = float(place_dec); profit = float(place_dec) - 1
    table.update_item(
        Key={"bet_id": pick["bet_id"], "bet_date": pick["bet_date"]},
        UpdateExpression=(
            "SET result_won = :w, outcome = :oc, result_settled = :s, "
            "finish_position = :fp, result_winner_name = :wn, "
            "result_return = :ret, profit_units = :pu, sp_decimal = :sp, show_in_ui = :ui"
        ),
        ExpressionAttributeValues={
            ":w": outcome == "win", ":oc": outcome, ":s": True,
            ":fp": finish, ":wn": target["winner_name"],
            ":ret": Decimal(str(round(ret, 4))), ":pu": Decimal(str(round(profit, 4))),
            ":sp": sp, ":ui": True,
        }
    )
    tag = "WIN  " if outcome == "win" else "PLACE"
    print(f"[{tag}] {horse:30}  SP {float(sp):.2f}  profit={profit:+.2f}u")
    updated += 1

print(f"\nDone. Updated {updated} picks.")

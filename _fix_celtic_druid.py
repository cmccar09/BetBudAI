import boto3
from decimal import Decimal

ddb = boto3.resource("dynamodb", region_name="eu-west-1")
table = ddb.Table("SureBetBets")

# Full paginated scan to find Celtic Druid
resp = table.scan()
items = resp["Items"]
while "LastEvaluatedKey" in resp:
    resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
    items += resp["Items"]

celtics = [i for i in items if "Celtic Druid" in str(i.get("horse", "")) and "Dundalk" in str(i.get("course", "")) and str(i.get("race_time","")).startswith("2026-04-10")]
items = celtics
print(f"Found {len(items)} Celtic Druid Dundalk Apr10 records")

for i in items:
    bid = i.get("bet_id")
    print(f"  bet_id: {bid}")
    print(f"  odds: {i.get('odds')}")
    print(f"  result: {i.get('result', 'NONE')}")
    print(f"  race_time: {i.get('race_time')}")

    # Update to WIN — Celtic Druid won at 5/1 (decimal 6.0)
    # Profit = (odds - 1) * stake. At 6.0 decimal on 1pt stake = +5.0 profit
    odds = float(i.get("odds", 6.0))
    profit = round(odds - 1, 4)

    table.update_item(
        Key={"bet_date": "2026-04-10", "bet_id": bid},
        UpdateExpression="SET #r = :r, profit_loss = :p, result_position = :pos",
        ExpressionAttributeNames={"#r": "result"},
        ExpressionAttributeValues={
            ":r": "WIN",
            ":p": Decimal(str(profit)),
            ":pos": "1",
        }
    )
    print(f"  -> Updated to WIN, profit={profit}")

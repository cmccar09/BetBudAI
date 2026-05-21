"""audit_dynamo.py — print summary of all CheltenhamXxx DynamoDB tables."""
import boto3
from decimal import Decimal

ddb = boto3.client("dynamodb", region_name="eu-west-1")
resource = boto3.resource("dynamodb", region_name="eu-west-1")

tables_r = ddb.list_tables()["TableNames"]
chelt = sorted(t for t in tables_r if t.startswith("Cheltenham"))
print(f"Found {len(chelt)} Cheltenham tables:\n")

for tname in chelt:
    tbl = resource.Table(tname)
    desc = ddb.describe_table(TableName=tname)["Table"]
    count = desc.get("ItemCount", "?")
    keys  = [k["AttributeName"] for k in desc["KeySchema"]]
    print(f"  {tname}")
    print(f"    Keys  : {keys}")
    print(f"    Items : {count}")
    # Sample 1 item
    scan = tbl.scan(Limit=1)
    if scan["Items"]:
        sample = scan["Items"][0]
        field_names = list(sample.keys())
        print(f"    Fields: {sorted(field_names)}")
    print()

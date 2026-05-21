#!/usr/bin/env python3
"""Delete subscriber records for a username from BetBudAI_Subscribers."""

import argparse
import sys

import boto3
from boto3.dynamodb.conditions import Attr


def main() -> int:
    parser = argparse.ArgumentParser(description="Drop subscriber by username")
    parser.add_argument("username")
    parser.add_argument("--region", default="eu-west-1")
    parser.add_argument("--table", default="BetBudAI_Subscribers")
    args = parser.parse_args()

    username = args.username.strip().lower()
    if not username:
        print("[ERROR] username is required")
        return 2

    ddb = boto3.resource("dynamodb", region_name=args.region)
    table = ddb.Table(args.table)

    deleted_keys = []

    # Delete username reservation row if present.
    alias_key = f"u#{username}"
    table.delete_item(Key={"email": alias_key})
    deleted_keys.append(alias_key)

    # Scan for user rows with this username and delete each by PK.
    resp = table.scan(FilterExpression=Attr("username").eq(username), ProjectionExpression="#e", ExpressionAttributeNames={"#e": "email"})
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = table.scan(
            FilterExpression=Attr("username").eq(username),
            ProjectionExpression="#e",
            ExpressionAttributeNames={"#e": "email"},
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))

    for item in items:
        email = item.get("email")
        if email:
            table.delete_item(Key={"email": email})
            deleted_keys.append(email)

    # Deduplicate while preserving order.
    final = []
    seen = set()
    for k in deleted_keys:
        if k not in seen:
            seen.add(k)
            final.append(k)

    print("[DONE] Drop user request completed")
    print(f"  Username: {username}")
    print("  Deleted keys:")
    for key in final:
        print(f"    - {key}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

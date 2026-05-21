"""
Create DynamoDB table 'CheltenhamResults' and load verified 2024/2025 data.

Table design:
  PK (partition key): year_race   e.g. "2024#Cheltenham Gold Cup"
  SK (sort key):      position    e.g. 1, 2, 3
  Attributes: horse, jockey, trainer, sp, day, year, race_name
"""

import boto3
import csv
import time
from botocore.exceptions import ClientError

REGION = "eu-west-1"
TABLE_NAME = "CheltenhamResults"
CSV_PATH = r"c:\Users\charl\OneDrive\futuregenAI\Betting\last year.csv"


def create_table(dynamodb):
    try:
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "year_race", "KeyType": "HASH"},
                {"AttributeName": "position", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "year_race", "AttributeType": "S"},
                {"AttributeName": "position", "AttributeType": "N"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"Creating table {TABLE_NAME}...")
        table.wait_until_exists()
        print(f"Table {TABLE_NAME} created successfully.")
        return table
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"Table {TABLE_NAME} already exists.")
            return dynamodb.Table(TABLE_NAME)
        raise


def load_data(table):
    loaded = 0
    skipped = 0

    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = row["Year"].strip()
            race_name = row["Race Name"].strip()
            position = int(row["Position"].strip())
            horse = row["Horse"].strip()
            jockey = row["Jockey"].strip()
            trainer = row["Trainer"].strip()
            sp = row["SP Fractional"].strip()
            day = row["Day"].strip()

            # Only load 2024 and 2025 (verified)
            if year not in ("2024", "2025"):
                skipped += 1
                continue

            item = {
                "year_race": f"{year}#{race_name}",
                "position": position,
                "year": int(year),
                "race_name": race_name,
                "day": day,
                "horse": horse,
                "jockey": jockey,
                "sp": sp,
            }
            if trainer:
                item["trainer"] = trainer

            table.put_item(Item=item)
            loaded += 1
            print(f"  Loaded: {year} {race_name} pos {position} → {horse} ({sp})")

    print(f"\nDone. Loaded: {loaded} items. Skipped: {skipped} items.")
    return loaded


def verify_sample(table):
    """Spot-check a few key records."""
    print("\n--- Verification spot-checks ---")
    checks = [
        ("2025#Unibet Champion Hurdle", 1, "Golden Ace"),
        ("2025#Unibet Champion Hurdle", 2, "Burdett Road"),
        ("2025#Close Brothers Mares' Hurdle", 2, "Jade De Grugy"),
        ("2024#Cheltenham Gold Cup", 2, "Gerri Colombe"),
        ("2024#Triumph Hurdle", 1, "Majborough"),
        ("2024#Kim Muir Challenge Cup", 1, "Inothewayurthinkin"),
        ("2024#Ryanair Mares' Novices' Hurdle", 1, "Golden Ace"),
    ]
    all_ok = True
    for year_race, pos, expected_horse in checks:
        resp = table.get_item(Key={"year_race": year_race, "position": pos})
        item = resp.get("Item")
        if item and item["horse"] == expected_horse:
            print(f"  ✅ {year_race} pos {pos}: {item['horse']}")
        else:
            actual = item["horse"] if item else "NOT FOUND"
            print(f"  ❌ {year_race} pos {pos}: expected {expected_horse}, got {actual}")
            all_ok = False
    return all_ok


def main():
    dynamodb = boto3.resource("dynamodb", region_name=REGION)

    print(f"Connecting to DynamoDB in {REGION}...")
    table = create_table(dynamodb)

    print(f"\nLoading data from CSV...")
    loaded = load_data(table)

    print(f"\nRunning verification...")
    ok = verify_sample(table)

    if ok:
        print(f"\n✅ All {loaded} records loaded and verified successfully!")
    else:
        print(f"\n⚠️  Some verification checks failed - review above.")


if __name__ == "__main__":
    main()

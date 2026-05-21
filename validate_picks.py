"""
validate_picks.py
-----------------
Post-analysis health check — runs immediately after complete_daily_analysis.py in the
pipeline before anything is displayed to the user.

Checks every today's UI pick in DynamoDB and asserts:
  1. all_horses list is present and has ≥ 2 runners
  2. Score is not zero
  3. Odds are present

Exits with code 1 if any pick fails. The pipeline in auto_refresh_betfair.py
will log the failure and the UI will show "Analysis in Progress" instead of broken picks.
"""

import sys
from datetime import datetime, timezone
from decimal import Decimal

import boto3

TABLE_NAME = "SureBetBets"
REGION     = "eu-west-1"
MIN_RUNNERS = 2  # minimum all_horses entries before we flag a problem

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table    = dynamodb.Table(TABLE_NAME)


def _float(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Fetch all today's UI picks
    resp = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("bet_date").eq(today)
    )
    items = resp.get("Items", [])
    while "LastEvaluatedKey" in resp:
        resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("bet_date").eq(today),
            ExclusiveStartKey=resp["LastEvaluatedKey"],
        )
        items.extend(resp.get("Items", []))

    ui_picks = [i for i in items if i.get("show_in_ui") is True]

    if not ui_picks:
        print("[VALIDATE] ⚠  No UI picks found for today — analysis may not have run yet")
        sys.exit(1)

    failures = []
    for pick in ui_picks:
        horse       = pick.get("horse", "?")
        course      = pick.get("course", "?")
        race_time   = pick.get("race_time", "?")
        score       = _float(pick.get("comprehensive_score", 0))
        odds        = _float(pick.get("odds", 0))
        all_horses  = pick.get("all_horses", [])
        n_runners   = len(all_horses)

        issues = []

        if n_runners < MIN_RUNNERS:
            issues.append(f"all_horses has only {n_runners} runner(s) — expected ≥ {MIN_RUNNERS}")

        if score == 0:
            issues.append("score is 0")

        if odds == 0:
            issues.append("odds are 0")

        label = f"{horse} @ {course} {race_time}"
        if issues:
            print(f"[VALIDATE] ❌  {label}  —  {'; '.join(issues)}")
            failures.append(label)
        else:
            print(f"[VALIDATE] ✅  {label}  —  {n_runners} runners, score={score:.0f}, odds={odds:.2f}")

    print()
    if failures:
        print(f"[VALIDATE] FAILED: {len(failures)} pick(s) have data issues — check analysis output")
        sys.exit(1)
    else:
        print(f"[VALIDATE] PASSED: all {len(ui_picks)} pick(s) have valid data")
        sys.exit(0)


if __name__ == "__main__":
    main()

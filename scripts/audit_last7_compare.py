#!/usr/bin/env python3
"""Run a fresh 7-day post-race audit and compare against baseline JSON."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key


CAUSE_WINNER_MISSING = "winner_missing_from_modeled_field"
CAUSE_IMPROVER_NOISE = "potential_improver_flag_noise"
CAUSE_OTHER_MISS = "other_model_miss"
CAUSE_WINNER_RANKED_6PLUS = "winner_ranked_6plus"
CAUSE_WINNER_DOUBLE_DIGIT = "winner_double_digit_odds"
CAUSE_3PLUS_NR = "race_had_3plus_nonrunners"
CAUSE_NARROW_GAP = "narrow_gap_10_or_less"
CAUSE_IMPROVER_HIT = "potential_improver_flagged_actual_winner"


def decimal_to_python(value):
    if isinstance(value, list):
        return [decimal_to_python(v) for v in value]
    if isinstance(value, dict):
        return {k: decimal_to_python(v) for k, v in value.items()}
    if isinstance(value, Decimal):
        return float(value)
    return value


def to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except Exception:
        return float(default)


def normalize_name(value):
    return str(value or "").strip().lower()


def score_of(row):
    return to_float(
        row.get("comprehensive_score_adjusted")
        or row.get("comprehensive_score")
        or row.get("analysis_score"),
        0.0,
    )


def odds_of(row):
    return to_float(row.get("odds"), 0.0)


def is_horse_row(row):
    return str(row.get("sport") or "horses").strip().lower() in ("horses", "horse racing")


def is_winner_row(row):
    outcome = str(row.get("outcome") or row.get("result") or "").strip().lower()
    if outcome in ("win", "won"):
        return True
    finish_position = str(row.get("finish_position") or "").strip()
    return finish_position == "1"


def race_key(row):
    return (
        str(row.get("bet_date") or "")[:10],
        str(row.get("course") or row.get("race_course") or "").strip().lower(),
        str(row.get("race_time") or "").strip(),
    )


def load_rows_for_date(table, date_str):
    response = table.query(KeyConditionExpression=Key("bet_date").eq(date_str))
    rows = [decimal_to_python(item) for item in response.get("Items", [])]
    while response.get("LastEvaluatedKey"):
        response = table.query(
            KeyConditionExpression=Key("bet_date").eq(date_str),
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        rows.extend(decimal_to_python(item) for item in response.get("Items", []))
    return rows


def extract_modeled_card(rows, winner_name):
    name_to_score = {}
    name_to_odds = {}

    for row in rows:
        all_horses = row.get("all_horses") or []
        if isinstance(all_horses, list):
            for horse in all_horses:
                name = normalize_name(horse.get("horse"))
                if not name:
                    continue
                score = to_float(horse.get("score"), 0.0)
                if name not in name_to_score or score > name_to_score[name]:
                    name_to_score[name] = score
                    name_to_odds[name] = to_float(horse.get("odds"), 0.0)

    if not name_to_score:
        for row in rows:
            name = normalize_name(row.get("horse"))
            if not name:
                continue
            score = score_of(row)
            if score <= 0:
                continue
            if name not in name_to_score or score > name_to_score[name]:
                name_to_score[name] = score
                name_to_odds[name] = odds_of(row)

    sorted_names = sorted(name_to_score.items(), key=lambda kv: kv[1], reverse=True)
    winner_key = normalize_name(winner_name)

    winner_score = 0.0
    winner_rank = None
    winner_odds = 0.0
    for idx, (name, score) in enumerate(sorted_names, start=1):
        if name == winner_key:
            winner_score = score
            winner_rank = idx
            winner_odds = name_to_odds.get(name, 0.0)
            break

    modeled_names = {name for name, _ in sorted_names}
    return sorted_names, modeled_names, winner_score, winner_rank, winner_odds


def audit_rows(rows):
    races = defaultdict(list)
    for row in rows:
        if not is_horse_row(row):
            continue
        key = race_key(row)
        if key[1] and key[2]:
            races[key].append(row)

    race_reports = []
    cause_counts = Counter()
    hits = 0

    for key, race_rows in sorted(races.items(), key=lambda kv: (kv[0][0], kv[0][2], kv[0][1])):
        winner_row = next((r for r in race_rows if is_winner_row(r)), None)
        if not winner_row:
            continue

        winner_name = str(winner_row.get("winner_horse") or winner_row.get("result_winner_name") or winner_row.get("horse") or "").strip()
        if not winner_name:
            continue

        scored_rows = [r for r in race_rows if score_of(r) != 0]
        if not scored_rows:
            continue

        top_pick_row = max(scored_rows, key=score_of)
        top_pick = str(top_pick_row.get("horse") or "").strip()
        top_score = score_of(top_pick_row)

        sorted_card, modeled_names, winner_score, winner_rank, winner_odds = extract_modeled_card(scored_rows, winner_name)
        hit = normalize_name(top_pick) == normalize_name(winner_name)
        if hit:
            hits += 1

        reasons = []
        winner_key = normalize_name(winner_name)
        if winner_key not in modeled_names:
            reasons.append(CAUSE_WINNER_MISSING)
        else:
            if winner_rank is not None and winner_rank >= 6:
                reasons.append(CAUSE_WINNER_RANKED_6PLUS)

        non_runners_count = int(to_float(top_pick_row.get("non_runners_count"), 0.0))
        if non_runners_count >= 3:
            reasons.append(CAUSE_3PLUS_NR)

        if winner_odds >= 10.0:
            reasons.append(CAUSE_WINNER_DOUBLE_DIGIT)

        potential_improver = normalize_name(top_pick_row.get("potential_improver_horse"))
        if potential_improver and non_runners_count >= 3 and not hit:
            reasons.append(CAUSE_IMPROVER_NOISE)
        if potential_improver and potential_improver == winner_key:
            reasons.append(CAUSE_IMPROVER_HIT)

        if not hit and winner_key in modeled_names:
            gap = abs(top_score - winner_score)
            if gap <= 10:
                reasons.append(CAUSE_NARROW_GAP)

        if not hit and not reasons:
            reasons.append(CAUSE_OTHER_MISS)

        if not hit:
            for reason in reasons:
                cause_counts[reason] += 1

        race_reports.append(
            {
                "race_time": key[2],
                "course": key[1],
                "winner": winner_name,
                "top_pick": top_pick,
                "hit": hit,
                "top_score": round(top_score, 2),
                "winner_score": round(winner_score, 2),
                "winner_rank": winner_rank,
                "winner_odds": round(winner_odds, 2),
                "reasons": reasons if not hit else [],
            }
        )

    misses = len(race_reports) - hits
    hit_rate = round((hits / len(race_reports) * 100.0), 2) if race_reports else 0.0
    return race_reports, cause_counts, hits, misses, hit_rate


def parse_baseline_causes(summary):
    causes = summary.get("cause_counts") or {}
    if isinstance(causes, dict):
        return {str(k): int(v) for k, v in causes.items()}
    parsed = {}
    if isinstance(causes, list):
        for row in causes:
            if isinstance(row, (list, tuple)) and len(row) == 2:
                parsed[str(row[0])] = int(row[1])
    return parsed


def main():
    parser = argparse.ArgumentParser(description="Run fresh 7-day race audit and compare with baseline")
    parser.add_argument("--region", default="eu-west-1")
    parser.add_argument("--table", default="SureBetBets")
    parser.add_argument("--end-date", default=None, help="Window end date (YYYY-MM-DD). Default: yesterday UTC")
    parser.add_argument("--baseline", default="last7_race_deep_analysis.json")
    parser.add_argument("--output", default="last7_race_deep_analysis_fresh.json")
    args = parser.parse_args()

    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    else:
        end_date = (datetime.now(timezone.utc) - timedelta(days=1)).date()

    start_date = end_date - timedelta(days=6)
    dates = [(start_date + timedelta(days=idx)).isoformat() for idx in range(7)]

    ddb = boto3.resource("dynamodb", region_name=args.region)
    table = ddb.Table(args.table)

    rows = []
    for date_str in dates:
        rows.extend(load_rows_for_date(table, date_str))

    races, cause_counts, hits, misses, hit_rate = audit_rows(rows)
    cause_list = sorted(cause_counts.items(), key=lambda kv: kv[1], reverse=True)

    fresh_report = {
        "summary": {
            "date_range": [dates[0], dates[-1]],
            "races_analyzed": len(races),
            "hits": hits,
            "misses": misses,
            "hit_rate_pct": hit_rate,
            "cause_counts": [[k, v] for k, v in cause_list],
        },
        "races": races,
    }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(fresh_report, indent=2), encoding="utf-8")

    baseline_path = Path(args.baseline)
    if not baseline_path.exists():
        print(json.dumps({"error": f"Baseline file not found: {baseline_path}"}, indent=2))
        return

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_summary = baseline.get("summary") or {}
    baseline_causes = parse_baseline_causes(baseline_summary)
    fresh_causes = {k: v for k, v in cause_list}

    all_causes = sorted(set(baseline_causes) | set(fresh_causes))
    cause_delta = []
    for cause in all_causes:
        before = int(baseline_causes.get(cause, 0))
        after = int(fresh_causes.get(cause, 0))
        cause_delta.append({"cause": cause, "baseline": before, "fresh": after, "delta": after - before})

    comparison = {
        "baseline_file": str(baseline_path),
        "fresh_file": str(output_path),
        "baseline_window": baseline_summary.get("date_range"),
        "fresh_window": fresh_report["summary"]["date_range"],
        "baseline_hit_rate_pct": baseline_summary.get("hit_rate_pct"),
        "fresh_hit_rate_pct": fresh_report["summary"]["hit_rate_pct"],
        "hit_rate_delta_pct": round(
            to_float(fresh_report["summary"]["hit_rate_pct"]) - to_float(baseline_summary.get("hit_rate_pct"), 0.0),
            2,
        ),
        "baseline_races": int(baseline_summary.get("races_analyzed", 0) or 0),
        "fresh_races": int(fresh_report["summary"].get("races_analyzed", 0) or 0),
        "cause_mix_delta": cause_delta,
    }

    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()

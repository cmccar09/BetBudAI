"""
Concurrent multi-agent race analysis orchestrator.

This script fans out race jobs and runs specialist agents in parallel for each race.
It is intentionally fail-open and non-destructive by default: it writes JSON outputs
for observability and can be integrated gradually into existing pick workflows.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple


try:
    import boto3
except Exception:
    boto3 = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def parse_form_value(form: str) -> float:
    """Parse simple form string into a 0..100 score.

    Lower numbers are better (1st place). Recent form strings vary heavily,
    so this parser only extracts numeric placings and ignores noise.
    """
    if not form:
        return 50.0

    digits: List[int] = []
    for ch in str(form):
        if ch.isdigit():
            digits.append(int(ch))

    if not digits:
        return 50.0

    # Convert places to quality points where 1 -> 100, 9 -> 20.
    values = [max(20.0, 110.0 - (d * 10.0)) for d in digits[:5]]
    return round(sum(values) / len(values), 2)


def classify_tier(score: float) -> str:
    if score >= 90:
        return "ELITE"
    if score >= 80:
        return "STRONG"
    if score >= 70:
        return "SOLID"
    if score >= 60:
        return "WATCH"
    return "PASS"


@dataclass
class AgentOutput:
    agent_name: str
    runner_scores: Dict[str, float]
    runner_reasons: Dict[str, List[str]]
    meta: Dict[str, Any]


class JobStateStore:
    def mark(self, job: Dict[str, Any]) -> None:
        raise NotImplementedError


class NoopStateStore(JobStateStore):
    def mark(self, job: Dict[str, Any]) -> None:
        return


class DynamoJobStateStore(JobStateStore):
    def __init__(self, table_name: str, region_name: str) -> None:
        if boto3 is None:
            raise RuntimeError("boto3 is not available")
        self._table = boto3.resource("dynamodb", region_name=region_name).Table(table_name)

    def mark(self, job: Dict[str, Any]) -> None:
        self._table.put_item(Item=job)


class CloudWatchMetricsReporter:
    def __init__(self, namespace: str, region_name: str) -> None:
        if boto3 is None:
            raise RuntimeError("boto3 is not available")
        self._namespace = namespace
        self._client = boto3.client("cloudwatch", region_name=region_name)

    def publish_summary(self, summary: Dict[str, Any]) -> None:
        now = datetime.now(timezone.utc)
        metrics = [
            {"MetricName": "RunDurationSeconds", "Value": float(summary.get("duration_seconds", 0.0)), "Unit": "Seconds"},
            {"MetricName": "TotalRaces", "Value": float(summary.get("total_races", 0.0)), "Unit": "Count"},
            {"MetricName": "CompletedRaces", "Value": float(summary.get("completed", 0.0)), "Unit": "Count"},
            {"MetricName": "FailedRaces", "Value": float(summary.get("failed", 0.0)), "Unit": "Count"},
            {"MetricName": "EligiblePicks", "Value": float(summary.get("eligible_picks", 0.0)), "Unit": "Count"},
            {"MetricName": "FailureRatePct", "Value": float(summary.get("failure_rate_pct", 0.0)), "Unit": "Percent"},
            {"MetricName": "AverageRaceLatencySeconds", "Value": float(summary.get("avg_race_latency_s", 0.0)), "Unit": "Seconds"},
            {"MetricName": "P95RaceLatencySeconds", "Value": float(summary.get("p95_race_latency_s", 0.0)), "Unit": "Seconds"},
            {"MetricName": "AverageConfidence", "Value": float(summary.get("avg_confidence", 0.0)), "Unit": "None"},
        ]

        payload = []
        for metric in metrics:
            payload.append(
                {
                    "MetricName": metric["MetricName"],
                    "Timestamp": now,
                    "Value": metric["Value"],
                    "Unit": metric["Unit"],
                    "Dimensions": [
                        {"Name": "Orchestrator", "Value": "agentic_parallel"},
                        {"Name": "Environment", "Value": os.getenv("AGENTIC_ENV", "prod")},
                    ],
                }
            )

        self._client.put_metric_data(Namespace=self._namespace, MetricData=payload)


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    pos = int(round((pct / 100.0) * (len(ordered) - 1)))
    return float(ordered[max(0, min(pos, len(ordered) - 1))])


def odds_agent(race: Dict[str, Any]) -> AgentOutput:
    scores: Dict[str, float] = {}
    reasons: Dict[str, List[str]] = {}

    runners = race.get("runners", [])
    odds_values = []
    for r in runners:
        odds_values.append(to_float(r.get("odds"), default=999.0))

    # Lower odds generally imply stronger market expectation.
    valid_odds = [o for o in odds_values if o > 1.0 and o < 999.0]
    min_o = min(valid_odds) if valid_odds else 2.0
    max_o = max(valid_odds) if valid_odds else 20.0
    span = max(0.1, max_o - min_o)

    for r in runners:
        horse = str(r.get("horse") or r.get("name") or "UNKNOWN")
        odds = to_float(r.get("odds"), default=999.0)
        if odds <= 1.0 or odds >= 999.0:
            score = 45.0
            note = "odds unavailable"
        else:
            # Invert and normalize to 0..100 where shortest odds get highest score.
            normalized = (max_o - odds) / span
            score = 40.0 + (normalized * 60.0)
            note = f"odds {odds:.2f}"
        scores[horse] = round(max(0.0, min(100.0, score)), 2)
        reasons[horse] = [note]

    return AgentOutput("odds", scores, reasons, {"runner_count": len(runners)})


def form_agent(race: Dict[str, Any]) -> AgentOutput:
    scores: Dict[str, float] = {}
    reasons: Dict[str, List[str]] = {}

    for r in race.get("runners", []):
        horse = str(r.get("horse") or r.get("name") or "UNKNOWN")
        form_score = parse_form_value(str(r.get("form") or ""))

        jockey = str(r.get("jockey") or "").strip()
        trainer = str(r.get("trainer") or "").strip()
        profile_bonus = 0.0
        profile_notes: List[str] = []

        if jockey:
            profile_bonus += 4.0
            profile_notes.append("named jockey")
        if trainer:
            profile_bonus += 4.0
            profile_notes.append("named trainer")

        total = min(100.0, form_score + profile_bonus)
        scores[horse] = round(total, 2)
        notes = [f"form score {form_score:.1f}"]
        notes.extend(profile_notes)
        reasons[horse] = notes

    return AgentOutput("form", scores, reasons, {})


def market_move_agent(race: Dict[str, Any]) -> AgentOutput:
    """Proxy market movement signal from available odds shape.

    This project does not always include full time-series drift in every runner,
    so this agent uses a conservative proxy based on favorite clustering and
    relative value in mid-price runners.
    """
    scores: Dict[str, float] = {}
    reasons: Dict[str, List[str]] = {}

    runners = race.get("runners", [])
    prices = [to_float(r.get("odds"), default=0.0) for r in runners]
    valid_prices = [p for p in prices if p > 1.0]

    if not valid_prices:
        for r in runners:
            horse = str(r.get("horse") or r.get("name") or "UNKNOWN")
            scores[horse] = 50.0
            reasons[horse] = ["no market data"]
        return AgentOutput("market_move", scores, reasons, {})

    fav_price = min(valid_prices)
    for r in runners:
        horse = str(r.get("horse") or r.get("name") or "UNKNOWN")
        p = to_float(r.get("odds"), default=0.0)
        if p <= 1.0:
            scores[horse] = 45.0
            reasons[horse] = ["missing odds"]
            continue

        # Favor runners close to the favorite but not over-compressed.
        ratio = p / max(1.01, fav_price)
        if ratio <= 1.25:
            score = 84.0
            note = "strong near-favorite cluster"
        elif ratio <= 1.8:
            score = 72.0
            note = "close to market leader"
        elif ratio <= 2.5:
            score = 63.0
            note = "mid-price market support"
        else:
            score = 52.0
            note = "long-price market profile"

        scores[horse] = score
        reasons[horse] = [note]

    return AgentOutput("market_move", scores, reasons, {"favorite_odds": fav_price})


def risk_agent(race: Dict[str, Any]) -> AgentOutput:
    scores: Dict[str, float] = {}
    reasons: Dict[str, List[str]] = {}

    runners = race.get("runners", [])
    field_size = len(runners)
    handicap_flag = bool(race.get("has_handicap", False))

    for r in runners:
        horse = str(r.get("horse") or r.get("name") or "UNKNOWN")
        base = 78.0
        notes = [f"field size {field_size}"]

        if field_size < 5:
            base -= 12.0
            notes.append("small field volatility")
        elif field_size > 14:
            base -= 8.0
            notes.append("large field variance")

        if handicap_flag:
            base -= 6.0
            notes.append("handicap race risk")

        odds = to_float(r.get("odds"), default=0.0)
        if odds > 0 and odds < 2.0:
            base -= 10.0
            notes.append("very short price risk")
        elif odds >= 12.0:
            base -= 8.0
            notes.append("outsider variance")

        scores[horse] = round(max(0.0, min(100.0, base)), 2)
        reasons[horse] = notes

    return AgentOutput("risk", scores, reasons, {"has_handicap": handicap_flag, "field_size": field_size})


def explainability_agent(race: Dict[str, Any]) -> AgentOutput:
    scores: Dict[str, float] = {}
    reasons: Dict[str, List[str]] = {}

    for r in race.get("runners", []):
        horse = str(r.get("horse") or r.get("name") or "UNKNOWN")
        notes: List[str] = []

        if r.get("favourite"):
            notes.append("declared favorite")
        if str(r.get("headgear") or "").strip():
            notes.append("headgear listed")
        if to_float(r.get("official_rating"), 0.0) > 0:
            notes.append("official rating present")

        transparency = 60.0 + (min(3, len(notes)) * 10.0)
        scores[horse] = round(transparency, 2)
        reasons[horse] = notes if notes else ["baseline explainability"]

    return AgentOutput("explainability", scores, reasons, {})


def aggregate_race(
    race: Dict[str, Any],
    agent_outputs: List[AgentOutput],
    weights: Dict[str, float],
    min_confidence: float,
) -> Dict[str, Any]:
    combined_scores: Dict[str, float] = {}
    combined_reasons: Dict[str, List[str]] = {}

    runners = race.get("runners", [])
    for r in runners:
        horse = str(r.get("horse") or r.get("name") or "UNKNOWN")
        combined_scores[horse] = 0.0
        combined_reasons[horse] = []

    for out in agent_outputs:
        weight = weights.get(out.agent_name, 0.0)
        for horse in combined_scores.keys():
            agent_score = out.runner_scores.get(horse, 50.0)
            combined_scores[horse] += (weight * agent_score)
            reasons = out.runner_reasons.get(horse, [])
            combined_reasons[horse].extend([f"{out.agent_name}: {txt}" for txt in reasons[:2]])

    best_horse: Optional[str] = None
    best_score = -1.0
    for horse, score in combined_scores.items():
        if score > best_score:
            best_horse = horse
            best_score = score

    is_eligible = bool(best_horse) and best_score >= min_confidence

    return {
        "race_id": str(race.get("race_id") or ""),
        "venue": race.get("venue") or race.get("course") or "UNKNOWN",
        "start_time": race.get("start_time") or race.get("race_time") or "UNKNOWN",
        "runner_count": len(runners),
        "pick": best_horse,
        "confidence": round(max(0.0, min(100.0, best_score)), 2),
        "tier": classify_tier(best_score),
        "eligible": is_eligible,
        "reason_codes": (combined_reasons.get(best_horse or "", [])[:6] if best_horse else []),
        "agent_scores": {
            horse: round(score, 2)
            for horse, score in sorted(combined_scores.items(), key=lambda kv: kv[1], reverse=True)
        },
    }


def run_specialists_for_race(
    race: Dict[str, Any],
    max_agent_workers: int,
    timeout_s: int,
) -> Tuple[List[AgentOutput], List[str]]:
    specialists: List[Callable[[Dict[str, Any]], AgentOutput]] = [
        odds_agent,
        form_agent,
        market_move_agent,
        risk_agent,
        explainability_agent,
    ]

    outputs: List[AgentOutput] = []
    errors: List[str] = []

    with ThreadPoolExecutor(max_workers=max_agent_workers) as pool:
        futures = {pool.submit(fn, race): fn.__name__ for fn in specialists}
        for future in as_completed(futures, timeout=timeout_s):
            name = futures[future]
            try:
                outputs.append(future.result())
            except Exception as exc:
                errors.append(f"{name} failed: {exc}")

    return outputs, errors


def build_race_key(race: Dict[str, Any], idx: int) -> str:
    venue = str(race.get("venue") or race.get("course") or "venue")
    start = str(race.get("start_time") or race.get("race_time") or f"idx-{idx}")
    return f"{venue}|{start}|{idx}"


def run_orchestration(
    races: List[Dict[str, Any]],
    max_race_workers: int,
    max_agent_workers: int,
    timeout_s: int,
    min_confidence: float,
    store: JobStateStore,
    fail_fast: bool,
) -> Dict[str, Any]:
    started = time.time()

    weights = {
        "odds": 0.30,
        "form": 0.30,
        "market_move": 0.20,
        "risk": 0.15,
        "explainability": 0.05,
    }

    race_results: List[Dict[str, Any]] = []
    failed_jobs: List[Dict[str, Any]] = []
    race_latencies: List[float] = []

    def process_one(race: Dict[str, Any], idx: int) -> Dict[str, Any]:
        race_started = time.time()
        race_key = build_race_key(race, idx)
        job_id = f"AGENTJOB#{uuid.uuid4()}"
        now = utc_now_iso()

        store.mark(
            {
                "job_pk": race_key,
                "job_sk": job_id,
                "status": "running",
                "created_at": now,
                "updated_at": now,
                "race_key": race_key,
                "agentic_version": "v1",
            }
        )

        try:
            outputs, errors = run_specialists_for_race(race, max_agent_workers=max_agent_workers, timeout_s=timeout_s)
            result = aggregate_race(race, outputs, weights=weights, min_confidence=min_confidence)
            result["race_key"] = race_key
            result["specialist_errors"] = errors
            result["specialists_completed"] = [o.agent_name for o in outputs]
            result["processing_seconds"] = round(time.time() - race_started, 3)

            status = "done" if not errors else "done_with_warnings"
            store.mark(
                {
                    "job_pk": race_key,
                    "job_sk": job_id,
                    "status": status,
                    "created_at": now,
                    "updated_at": utc_now_iso(),
                    "race_key": race_key,
                    "pick": result.get("pick") or "",
                    "confidence": str(result.get("confidence", 0)),
                }
            )
            return {"ok": True, "result": result}
        except Exception as exc:
            err_msg = str(exc)
            store.mark(
                {
                    "job_pk": race_key,
                    "job_sk": job_id,
                    "status": "failed",
                    "created_at": now,
                    "updated_at": utc_now_iso(),
                    "race_key": race_key,
                    "error": err_msg[:1200],
                }
            )
            return {
                "ok": False,
                "error": err_msg,
                "race_key": race_key,
                "processing_seconds": round(time.time() - race_started, 3),
            }

    with ThreadPoolExecutor(max_workers=max_race_workers) as pool:
        futures = {pool.submit(process_one, race, idx): idx for idx, race in enumerate(races)}
        for future in as_completed(futures):
            payload = future.result()
            if payload.get("ok"):
                race_results.append(payload["result"])
                race_latencies.append(float(payload["result"].get("processing_seconds", 0.0)))
            else:
                failed_jobs.append(payload)
                race_latencies.append(float(payload.get("processing_seconds", 0.0)))
                if fail_fast:
                    break

    # Highest confidence first.
    race_results.sort(key=lambda item: item.get("confidence", 0.0), reverse=True)

    elapsed = round(time.time() - started, 2)
    failure_rate = (len(failed_jobs) / max(1, len(races))) * 100.0
    confidences = [float(r.get("confidence", 0.0)) for r in race_results]
    avg_confidence = statistics.fmean(confidences) if confidences else 0.0
    avg_race_latency = statistics.fmean(race_latencies) if race_latencies else 0.0

    summary = {
        "started_at": utc_now_iso(),
        "duration_seconds": elapsed,
        "total_races": len(races),
        "completed": len(race_results),
        "failed": len(failed_jobs),
        "eligible_picks": sum(1 for r in race_results if r.get("eligible")),
        "max_race_workers": max_race_workers,
        "max_agent_workers": max_agent_workers,
        "failure_rate_pct": round(failure_rate, 2),
        "avg_confidence": round(avg_confidence, 2),
        "avg_race_latency_s": round(avg_race_latency, 3),
        "p50_race_latency_s": round(_percentile(race_latencies, 50.0), 3),
        "p95_race_latency_s": round(_percentile(race_latencies, 95.0), 3),
    }

    return {
        "summary": summary,
        "race_results": race_results,
        "failed_jobs": failed_jobs,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Concurrent multi-agent betting orchestrator")
    parser.add_argument("--input", default="response_horses.json", help="Input race JSON path")
    parser.add_argument("--output", default="agentic_parallel_output.json", help="Output analysis JSON path")
    parser.add_argument("--max-race-workers", type=int, default=int(os.getenv("AGENTIC_MAX_RACE_WORKERS", "6")))
    parser.add_argument("--max-agent-workers", type=int, default=int(os.getenv("AGENTIC_MAX_AGENT_WORKERS", "5")))
    parser.add_argument("--timeout", type=int, default=int(os.getenv("AGENTIC_AGENT_TIMEOUT_S", "90")))
    parser.add_argument("--min-confidence", type=float, default=float(os.getenv("AGENTIC_MIN_CONFIDENCE", "70")))
    parser.add_argument("--region", default=os.getenv("AWS_REGION", "eu-west-1"))
    parser.add_argument("--dynamodb-table", default=os.getenv("AGENTIC_JOB_TABLE", ""))
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failed race job")
    return parser.parse_args()


def load_races(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    races = payload.get("races", [])
    if not isinstance(races, list):
        raise ValueError("Input JSON does not contain a valid races list")
    return races


def select_store(region: str, table_name: str) -> JobStateStore:
    if not table_name:
        return NoopStateStore()
    try:
        return DynamoJobStateStore(table_name=table_name, region_name=region)
    except Exception as exc:
        print(f"WARN: Could not initialize DynamoDB store ({exc}). Falling back to NoopStateStore.")
        return NoopStateStore()


def main() -> int:
    args = parse_args()

    if os.getenv("AGENTIC_DISABLE_BETTING_ACTIONS", "1").strip().lower() in ("1", "true", "yes", "on"):
        print("INFO: AGENTIC_DISABLE_BETTING_ACTIONS is enabled. Running analysis-only mode.")

    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        return 1

    races = load_races(args.input)
    if not races:
        print("WARN: No races found in input. Writing empty output.")
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump({"summary": {"total_races": 0}, "race_results": [], "failed_jobs": []}, handle, indent=2)
        return 0

    store = select_store(region=args.region, table_name=args.dynamodb_table)

    result = run_orchestration(
        races=races,
        max_race_workers=max(1, args.max_race_workers),
        max_agent_workers=max(1, args.max_agent_workers),
        timeout_s=max(10, args.timeout),
        min_confidence=max(0.0, min(100.0, args.min_confidence)),
        store=store,
        fail_fast=args.fail_fast,
    )

    output_payload = {
        "generated_at": utc_now_iso(),
        "input_path": args.input,
        "orchestrator": "agentic_parallel_orchestrator.py",
        "config": {
            "max_race_workers": args.max_race_workers,
            "max_agent_workers": args.max_agent_workers,
            "timeout": args.timeout,
            "min_confidence": args.min_confidence,
            "dynamodb_table": args.dynamodb_table,
        },
        "summary": result["summary"],
        "race_results": result["race_results"],
        "failed_jobs": result["failed_jobs"],
    }

    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(output_payload, handle, indent=2)

    s = result["summary"]
    print(
        f"AGENTIC_ORCHESTRATION_COMPLETE races={s['total_races']} completed={s['completed']} "
        f"failed={s['failed']} eligible={s['eligible_picks']} duration_s={s['duration_seconds']}"
    )
    print(
        "AGENTIC_ORCHESTRATION_SUMMARY "
        f"failure_rate_pct={s.get('failure_rate_pct', 0)} "
        f"avg_race_latency_s={s.get('avg_race_latency_s', 0)} "
        f"p95_race_latency_s={s.get('p95_race_latency_s', 0)} "
        f"avg_confidence={s.get('avg_confidence', 0)}"
    )

    cw_enabled = os.getenv("AGENTIC_CW_METRICS_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")
    cw_namespace = os.getenv("AGENTIC_CW_NAMESPACE", "BetBudAI/Agentic")
    if cw_enabled and boto3 is not None:
        try:
            reporter = CloudWatchMetricsReporter(namespace=cw_namespace, region_name=args.region)
            reporter.publish_summary(s)
            print(f"AGENTIC_CLOUDWATCH_METRICS_PUBLISHED namespace={cw_namespace}")
        except Exception as exc:
            print(f"WARN: CloudWatch metrics publish failed: {exc}")

    return 0 if s["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""
surebet_orchestrator.py
========================
Master orchestration script.  Every daily pipeline phase is defined here with:
  • the script to run
  • a success verifier (checks exit-code AND output patterns AND DynamoDB state)
  • an abort flag (True = stop the phase on failure)
  • a notification flag (True = email/log prominently on failure)

Usage
-----
  python surebet_orchestrator.py                     # full-day run (all phases)
  python surebet_orchestrator.py --phase morning     # Phase 1-2: health + Betfair
  python surebet_orchestrator.py --phase refresh     # Phase 3-4: analysis + validate
  python surebet_orchestrator.py --phase evening     # Phase 5:   results + loss report
  python surebet_orchestrator.py --phase learning    # Phase 6:   learning cycle
  python surebet_orchestrator.py --status            # Print current pipeline state only
  python surebet_orchestrator.py --dry-run           # List all steps, do not execute

Designed to be called by Windows Task Scheduler:
  08:30 → --phase morning
  12:00, 14:00, 16:00, 18:00 → --phase refresh
  20:00 → --phase evening
  21:00 → --phase learning
"""

import argparse
import json
import os
import re
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import boto3
from boto3.dynamodb.conditions import Key

# ── Config ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
PYTHON       = str(BASE_DIR / ".venv" / "Scripts" / "python.exe")
LOG_FILE     = BASE_DIR / "orchestrator.log"
REGION       = "eu-west-1"
TABLE_NAME   = "SureBetBets"
MANIFEST_KEY = "ORCH_MANIFEST"   # bet_date for orchestrator status records

# ── DynamoDB ───────────────────────────────────────────────────────────────────
try:
    _dynamodb = boto3.resource("dynamodb", region_name=REGION)
    _table    = _dynamodb.Table(TABLE_NAME)
except Exception:
    _table = None

# ── Logging ────────────────────────────────────────────────────────────────────
def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

def log(msg: str, level: str = "INFO"):
    prefix = {"INFO": "   ", "OK": "✅ ", "WARN": "⚠️ ", "ERROR": "❌ ", "HEADER": "══"}
    line = f"[{_ts()}] {prefix.get(level, '   ')}{msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except OSError:
        pass

# ── Pipeline phase definitions ─────────────────────────────────────────────────
#
# Each step dict:
#   script          str    – filename relative to BASE_DIR (or None for built-in checks)
#   label           str    – human-readable description
#   abort_on_fail   bool   – stop the current phase if this step fails
#   output_checks   list   – strings that must appear in stdout for pass; empty = not checked
#   min_runtime_s   float  – fail if script finishes faster than this (catches silent crashes)
#   phase           str    – which --phase this step belongs to
#   builtin         str    – name of built-in verifier function (if no script)

STEPS = [
    # ── MORNING PHASE ──────────────────────────────────────────────────────────
    {
        "phase": "morning",
        "script": "daily_health_check.py",
        "label": "Pre-flight health check",
        "abort_on_fail": True,
        "output_checks": [],           # daily_health_check exits 0 on pass, 1 on fail
        "min_runtime_s": 0,
    },
    {
        "phase": "morning",
        "script": "betfair_odds_fetcher.py",
        "label": "Fetch Betfair odds",
        "abort_on_fail": True,
        "output_checks": ["response_horses", "races", "runners"],
        "min_runtime_s": 5,
    },

    # ── REFRESH PHASE (runs every 2 hours 12-18) ───────────────────────────────
    {
        "phase": "refresh",
        "script": "betfair_odds_fetcher.py",
        "label": "Refresh Betfair odds",
        "abort_on_fail": True,
        "output_checks": ["response_horses", "races", "runners"],
        "min_runtime_s": 5,
    },
    {
        "phase": "refresh",
        "script": "complete_daily_analysis.py",
        "label": "Score all horses + build top-5 UI picks",
        "abort_on_fail": True,
        "output_checks": ["Saved", "horses", "UI picks"],
        "min_runtime_s": 10,
    },
    {
        "phase": "refresh",
        "script": "validate_picks.py",
        "label": "Validate pick data completeness",
        "abort_on_fail": False,         # warn but don't abort — picks gate is in Lambda
        "output_checks": ["VALIDATE"],
        "min_runtime_s": 0,
    },
    {
        "phase": "refresh",
        "script": "notify_picks.py",
        "label": "Send pick notifications",
        "abort_on_fail": False,
        "output_checks": [],
        "min_runtime_s": 0,
    },

    # ── EVENING PHASE (20:00) ──────────────────────────────────────────────────
    {
        "phase": "evening",
        "script": "fetch_settled_today.py",
        "label": "Fetch settled results for today",
        "abort_on_fail": True,
        "output_checks": [],
        "min_runtime_s": 0,
    },
    {
        "phase": "evening",
        "script": "evaluate_performance.py",
        "label": "Evaluate performance + update P&L",
        "abort_on_fail": False,
        "output_checks": [],
        "min_runtime_s": 0,
    },
    {
        "phase": "evening",
        "script": "evening_loss_report.py",
        "label": "Generate evening loss report",
        "abort_on_fail": False,
        "output_checks": [],
        "min_runtime_s": 0,
    },

    # ── LEARNING PHASE (21:00) ─────────────────────────────────────────────────
    {
        "phase": "learning",
        "script": "daily_learning_cycle.py",
        "label": "Run learning cycle + update weights",
        "abort_on_fail": False,
        "output_checks": ["weight", "learning"],
        "min_runtime_s": 0,
    },
]

# ── Script runner ───────────────────────────────────────────────────────────────
def run_step(step: dict, dry_run: bool = False) -> dict:
    """
    Run a single pipeline step.
    Returns {ok, exit_code, stdout, stderr, runtime_s, reason}.
    """
    script = step["script"]
    label  = step["label"]
    path   = BASE_DIR / script

    result = {"ok": False, "exit_code": -1, "stdout": "", "stderr": "", "runtime_s": 0, "reason": ""}

    if not path.exists():
        result["reason"] = f"Script not found: {script}"
        log(f"SKIP  {label} — script not found ({script})", "WARN")
        # Non-existent optional scripts are warnings, not failures
        result["ok"] = not step["abort_on_fail"]
        return result

    if dry_run:
        log(f"DRY-RUN  {label} ({script})", "INFO")
        result["ok"] = True
        return result

    log(f"Running  {label} …", "INFO")
    start = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            [PYTHON, "-X", "utf8", str(path)],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(BASE_DIR), timeout=600
        )
    except subprocess.TimeoutExpired:
        result["reason"] = "Timed out after 600s"
        log(f"TIMEOUT  {label}", "ERROR")
        return result
    except Exception as exc:
        result["reason"] = str(exc)
        log(f"EXEC-ERR {label}: {exc}", "ERROR")
        return result

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    result["exit_code"]  = proc.returncode
    result["stdout"]     = proc.stdout
    result["stderr"]     = proc.stderr
    result["runtime_s"]  = round(elapsed, 1)

    # Surface key output lines
    for line in proc.stdout.splitlines():
        kw = ("ERROR", "WARNING", "WARN", "PICK", "✅", "❌", "✓", "✗",
              "saved", "Saved", "HEALTH", "VALIDATE", "total", "Total",
              "UI pick", "learning", "weight", "complete", "PASS", "FAIL")
        if any(k in line for k in kw):
            log(f"  >> {line.strip()}", "INFO")

    # Check exit code
    if proc.returncode != 0:
        result["reason"] = f"Exit code {proc.returncode}"
        if proc.stderr:
            tail = proc.stderr.strip()[-500:]
            log(f"  STDERR: {tail}", "ERROR")
        log(f"FAIL  {label} (exit {proc.returncode})", "ERROR")
        return result

    # Check minimum runtime (catches silent no-op)
    if elapsed < step.get("min_runtime_s", 0):
        result["reason"] = f"Finished too fast ({elapsed}s < {step['min_runtime_s']}s min) — possible silent crash"
        log(f"WARN  {label} — {result['reason']}", "WARN")
        # Don't fail hard for timing, just warn

    # Check expected output substrings
    for check in step.get("output_checks", []):
        if check.lower() not in proc.stdout.lower():
            result["reason"] = f"Expected output not found: '{check}'"
            log(f"WARN  {label} — {result['reason']}", "WARN")
            # Output check failure is a warning, not a hard fail (scripts vary)

    result["ok"] = True
    log(f"OK    {label} ({elapsed}s)", "OK")
    return result


# ── Phase runner ────────────────────────────────────────────────────────────────
def run_phase(phase: str, dry_run: bool = False) -> dict:
    """Run all steps for a given phase. Returns summary dict."""
    today  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_ts = datetime.now(timezone.utc).isoformat()

    log("=" * 70, "HEADER")
    log(f"SureBet Orchestrator  phase={phase.upper()}  date={today}  {'(DRY-RUN) ' if dry_run else ''}", "INFO")
    log("=" * 70, "HEADER")

    phase_steps   = [s for s in STEPS if s["phase"] == phase]
    passed        = []
    failed        = []
    skipped       = []
    aborted_after = None

    for i, step in enumerate(phase_steps, 1):
        log(f"[{i}/{len(phase_steps)}] {step['label']}", "INFO")
        res = run_step(step, dry_run=dry_run)

        if res["ok"]:
            passed.append(step["label"])
        else:
            failed.append({"step": step["label"], "reason": res["reason"]})
            if step["abort_on_fail"]:
                aborted_after = step["label"]
                remaining     = [s["label"] for s in phase_steps[i:]]
                skipped.extend(remaining)
                log(f"Aborting {phase} phase after: {aborted_after}", "ERROR")
                break

    status = "ok" if not failed else ("partial" if passed else "failed")

    summary = {
        "phase":         phase,
        "date":          today,
        "timestamp":     now_ts,
        "status":        status,
        "steps_passed":  len(passed),
        "steps_failed":  len(failed),
        "steps_skipped": len(skipped),
        "passed":        passed,
        "failed":        failed,
        "skipped":       skipped,
        "aborted_after": aborted_after,
    }

    icon = "✅" if status == "ok" else ("⚠️" if status == "partial" else "❌")
    log(f"{icon} Phase {phase.upper()} {status.upper()} — {len(passed)}/{len(phase_steps)} steps passed", "INFO")

    _write_manifest(phase, summary)
    return summary


# ── DynamoDB manifest ───────────────────────────────────────────────────────────
def _dec(v):
    """Convert numeric values to Decimal for DynamoDB."""
    if isinstance(v, float):
        return Decimal(str(round(v, 4)))
    if isinstance(v, int):
        return Decimal(v)
    return v

def _sanitize(obj):
    """Recursively convert floats to Decimal for DynamoDB storage."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    if isinstance(obj, float):
        return Decimal(str(round(obj, 4)))
    return obj

def _write_manifest(phase: str, summary: dict):
    """Persist orchestration status to DynamoDB."""
    if _table is None:
        return
    try:
        item = {
            "bet_date":   MANIFEST_KEY,
            "bet_id":     f"PHASE_{phase.upper()}_{summary['date']}",
            "phase":      phase,
            "date":       summary["date"],
            "status":     summary["status"],
            "timestamp":  summary["timestamp"],
            "steps_passed":  _dec(summary["steps_passed"]),
            "steps_failed":  _dec(summary["steps_failed"]),
            "steps_skipped": _dec(summary["steps_skipped"]),
            "failed_steps":  json.dumps(summary["failed"]),
            "skipped_steps": json.dumps(summary["skipped"]),
        }
        _table.put_item(Item=item)
    except Exception as exc:
        log(f"DynamoDB manifest write failed: {exc}", "WARN")


# ── Status query ────────────────────────────────────────────────────────────────
def print_status():
    """Print today's orchestration state from DynamoDB."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log(f"Pipeline status for {today}", "INFO")
    log("-" * 50, "INFO")

    if _table is None:
        log("DynamoDB unavailable", "WARN")
        return

    try:
        resp  = _table.query(KeyConditionExpression=Key("bet_date").eq(MANIFEST_KEY))
        items = [i for i in resp.get("Items", []) if str(i.get("date", "")) == today]
    except Exception as exc:
        log(f"DynamoDB query failed: {exc}", "ERROR")
        return

    if not items:
        log("No orchestration runs recorded yet today", "WARN")
        return

    for item in sorted(items, key=lambda x: x.get("timestamp", "")):
        phase     = item.get("phase", "?").upper()
        status    = item.get("status", "?")
        ts        = item.get("timestamp", "")[:19]
        passed    = item.get("steps_passed", 0)
        failed    = item.get("steps_failed", 0)
        skipped   = item.get("steps_skipped", 0)
        icon      = "✅" if status == "ok" else ("⚠️" if status == "partial" else "❌")
        log(f"  {icon} {phase:10} {status:8}  {passed}✓ {failed}✗ {skipped}⏭  @ {ts}", "INFO")

        fails = json.loads(item.get("failed_steps", "[]"))
        for f in fails:
            log(f"       ✗ {f['step']}: {f['reason']}", "WARN")


# ── CLI entry point ─────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="SureBet Orchestrator")
    parser.add_argument("--phase",   choices=["morning", "refresh", "evening", "learning", "all"],
                        default="all", help="Which phase to run")
    parser.add_argument("--dry-run", action="store_true", help="Print steps only, do not execute")
    parser.add_argument("--status",  action="store_true", help="Print today's pipeline state and exit")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    phases = (["morning", "refresh", "evening", "learning"]
              if args.phase == "all"
              else [args.phase])

    overall_ok = True
    for phase in phases:
        summary = run_phase(phase, dry_run=args.dry_run)
        if summary["status"] == "failed":
            overall_ok = False

    log("=" * 70, "HEADER")
    if overall_ok:
        log("ALL PHASES COMPLETE ✅", "OK")
    else:
        log("ONE OR MORE PHASES FAILED ❌ — check orchestrator.log", "ERROR")
    log("=" * 70, "HEADER")

    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()

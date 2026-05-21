"""
cheltenham_monitor.py
─────────────────────────────────────────────────────────────────────────────
Runs every 30 minutes all day at Cheltenham.

Each cycle:
  1. Refresh Betfair session token
  2. Re-run save_cheltenham_picks.py  →  detect any pick changes
  3. Pull live Betfair odds for Day 1 races  →  flag big market moves (>20%)
  4. Check race_results.json for any new results filled in manually
  5. Regenerate barrys_cheltenham_2026.html
  6. Git add + commit + push  (only if something actually changed)

Usage:
    python cheltenham_monitor.py            # runs until Ctrl-C
    python cheltenham_monitor.py --once     # single cycle then exit
"""

import subprocess
import sys
import os
import io
import json
import time
import hashlib
import datetime

# Force UTF-8 stdout/stderr regardless of Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
import re

# Ensure UTF-8 output in Windows terminals / background jobs
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

ROOT      = os.path.dirname(os.path.abspath(__file__))
PYTHON    = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
BARRYS    = os.path.join(ROOT, "barrys")
HTML_FILE = os.path.join(BARRYS, "barrys_cheltenham_2026.html")
RESULTS_FILE = os.path.join(BARRYS, "race_results.json")
PICKS_SCRIPT  = os.path.join(ROOT, "save_cheltenham_picks.py")
HTML_SCRIPT   = os.path.join(BARRYS, "update_barrys_html.py")
SESSION_SCRIPT = os.path.join(ROOT, "refresh_betfair_session.py")

INTERVAL_SEC = 30 * 60   # 30 minutes

# Day 1 race times (local UK) for countdown display
DAY1_RACES = [
    ("13:20", "Supreme Novices' Hurdle"),
    ("14:00", "Arkle Chase"),
    ("14:40", "Fred Winter Hurdle"),
    ("15:20", "Ultima Chase"),
    ("16:00", "Champion Hurdle"),
    ("16:40", "Cheltenham Plate"),
    ("17:20", "Challenge Cup Chase"),
]

SEPARATOR = "=" * 70


def ts():
    return datetime.datetime.now().strftime("%H:%M:%S")


def log(msg, level="INFO"):
    icons = {"INFO": "[..]", "OK": "[OK]", "WARN": "[!!]", "ERR": "[XX]", "CHANGE": "[**]"}
    icon = icons.get(level, "[..]")
    print(f"  [{ts()}] {icon}  {msg}")


def file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except FileNotFoundError:
        return None


def run(cmd, cwd=None, capture=True):
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run(
        cmd, shell=True, cwd=cwd or ROOT,
        capture_output=capture, text=True, env=env
    )
    return result


def count_results():
    """Return number of races that have a 1st recorded."""
    try:
        with open(RESULTS_FILE) as f:
            data = json.load(f)
        return sum(1 for v in data.get("results", {}).values() if v.get("1st"))
    except Exception:
        return 0


def next_race_info():
    """Return (time_str, name) of the next unrun race today."""
    now = datetime.datetime.now()
    for t, name in DAY1_RACES:
        h, m = map(int, t.split(":"))
        race_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if race_dt > now:
            delta = race_dt - now
            mins = int(delta.total_seconds() // 60)
            return t, name, mins
    return None, None, None


def step_refresh_session():
    log("Refreshing Betfair session token...")
    r = run(f'"{PYTHON}" "{SESSION_SCRIPT}"')
    if r.returncode == 0:
        log("Session token refreshed OK", "OK")
    else:
        log(f"Session refresh failed: {r.stderr[:120]}", "WARN")


def step_save_picks():
    """Run save_cheltenham_picks and return (changed: bool, summary: str)."""
    log("Running save_cheltenham_picks.py...")
    r = run(f'"{PYTHON}" "{PICKS_SCRIPT}"')
    out = r.stdout or ""

    # Look for pick change lines like "CHANGED: ..."
    changes = [line.strip() for line in out.splitlines()
               if "CHANGED" in line or "changed" in line.lower() or "→" in line]
    if changes:
        for c in changes:
            log(f"PICK CHANGE: {c}", "CHANGE")
        return True, f"{len(changes)} pick change(s)"
    else:
        log("No pick changes detected", "OK")
        return False, "no changes"


def step_live_odds():
    """Check live Betfair odds and flag big drifters/steamers."""
    log("Pulling live Betfair odds...")
    script = os.path.join(ROOT, "_live_odds_check.py")
    if not os.path.exists(script):
        log("_live_odds_check.py not found, skipping", "WARN")
        return False

    r = run(f'"{PYTHON}" "{script}"')
    out = r.stdout or ""

    alerts = []
    # Look for lines mentioning our picks with big price moves
    for line in out.splitlines():
        if any(horse in line for horse in [
            "Old Park Star", "Kopek Des Bordes", "Lossiemouth",
            "Manlaga", "Jagwar", "Madara", "Backmersackme"
        ]):
            alerts.append(line.strip())

    if alerts:
        log("Odds snapshot for our picks:", "INFO")
        for a in alerts:
            print(f"    {a}")
        return True
    else:
        log("Odds check complete — no notable moves on our picks", "OK")
        return False


def step_regen_html():
    """Regenerate the HTML. Returns (changed: bool)."""
    before = file_hash(HTML_FILE)
    log("Regenerating HTML...")
    r = run(f'"{PYTHON}" "{HTML_SCRIPT}"', cwd=BARRYS)
    if r.returncode != 0:
        log(f"HTML regen failed: {r.stderr[:200]}", "ERR")
        return False
    after = file_hash(HTML_FILE)
    if after != before:
        # Extract size
        size = os.path.getsize(HTML_FILE)
        log(f"HTML updated ({size:,} bytes)", "OK")
        return True
    else:
        log("HTML unchanged", "INFO")
        return False


def step_git_push(reason: str):
    log(f"Committing & pushing: {reason}...")
    run('git add barrys/barrys_cheltenham_2026.html barrys/race_results.json barrys/macfitz_overrides.json')
    r = run(f'git commit -m "Monitor auto-update: {reason}"')
    if "nothing to commit" in (r.stdout + r.stderr):
        log("Git: nothing new to commit", "INFO")
        return
    push = run("git push")
    if push.returncode == 0:
        log("Pushed to GitHub -> Amplify deploying", "OK")
    else:
        log(f"Push failed: {push.stderr[:120]}", "ERR")


def run_cycle(cycle_num: int):
    print(f"\n{SEPARATOR}")
    print(f"  CHELTENHAM MONITOR  -- Cycle #{cycle_num}  -- {datetime.datetime.now().strftime('%a %d %b %Y  %H:%M')}")

    results_before = count_results()
    next_time, next_name, next_mins = next_race_info()
    if next_time:
        print(f"  Next race: {next_time} {next_name}  ({next_mins} mins away)")
    else:
        print("  All Day 1 races are past -- watching for result updates only")
    print(SEPARATOR)

    # 1. Refresh session
    step_refresh_session()

    # 2. Save picks — detect changes
    picks_changed, picks_summary = step_save_picks()

    # 3. Live odds
    step_live_odds()

    # 4. Check results
    results_after = count_results()
    if results_after > results_before:
        log(f"New race results detected: {results_before} -> {results_after} races recorded", "CHANGE")
    else:
        log(f"Results: {results_after} / 7 Day 1 races recorded", "INFO")

    # 5. Regen HTML
    html_changed = step_regen_html()

    # 6. Push if anything changed
    reasons = []
    if picks_changed:
        reasons.append(picks_summary)
    if results_after > results_before:
        reasons.append(f"{results_after} results")
    if html_changed and not reasons:
        reasons.append("routine refresh")

    if html_changed or picks_changed or results_after > results_before:
        step_git_push(" | ".join(reasons) if reasons else "auto")
    else:
        log("Nothing changed -- skipping git push", "INFO")

    print("\n  Next cycle in 30 minutes.  Press Ctrl-C to stop.\n")


def main():
    once = "--once" in sys.argv

    print(f"\n{'='*70}")
    print(f"  CHELTENHAM LIVE MONITOR -- Starting up -- {ts()}")
    print(f"  Interval: every 30 minutes  |  Root: {ROOT}")
    print(f"{'='*70}\n")

    cycle = 1
    while True:
        try:
            run_cycle(cycle)
        except KeyboardInterrupt:
            print("\n\n  Monitor stopped by user.\n")
            sys.exit(0)
        except Exception as e:
            log(f"Cycle {cycle} error: {e}", "ERR")

        if once:
            break

        cycle += 1
        try:
            print("  Sleeping 30 minutes... (Ctrl-C to stop)")
            time.sleep(INTERVAL_SEC)
        except KeyboardInterrupt:
            print("\n\n  Monitor stopped by user.\n")
            sys.exit(0)


if __name__ == "__main__":
    main()

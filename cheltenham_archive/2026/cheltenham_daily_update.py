"""
cheltenham_daily_update.py
==========================
Master orchestrator for Cheltenham 2026 Festival automation.

Schedule:
  - Daily 10am   (Mar 7–13):  full picks refresh + HTML update
  - Every 30min  (Mar 10–13, 09:00–18:00):  picks + live Betfair odds

Usage:
    python cheltenham_daily_update.py               # standard run
    python cheltenham_daily_update.py --race-day    # force race-day mode (30-min)
    python cheltenham_daily_update.py --odds-only   # only refresh Betfair odds
"""

import sys, os, subprocess, argparse, logging
from datetime import datetime, date

# ── paths ──────────────────────────────────────────────────────────────────
ROOT      = os.path.dirname(os.path.abspath(__file__))
VENV_PY   = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
PYTHON    = VENV_PY if os.path.exists(VENV_PY) else sys.executable
LOG_FILE  = os.path.join(ROOT, "cheltenham_auto.log")

BARR_HTML = os.path.join(ROOT, "barrys", "barrys_cheltenham_2026.html")
STRAT_HTML = os.path.join(ROOT, "cheltenham_strategy_2026.html")

FESTIVAL_START = date(2026, 3, 10)
FESTIVAL_END   = date(2026, 3, 13)

# ── logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger("cheltenham_update")


def run(cmd: list[str], label: str) -> bool:
    """Run a subprocess and return True if it succeeded."""
    log.info(f"▶ Running: {label}")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True, encoding="utf-8")
    if result.returncode == 0:
        log.info(f"  ✓ {label} completed OK")
        if result.stdout.strip():
            # Print last 15 lines of stdout for useful context
            lines = result.stdout.strip().splitlines()
            for line in lines[-15:]:
                log.info(f"  | {line}")
    else:
        log.error(f"  ✗ {label} FAILED (exit {result.returncode})")
        for line in (result.stderr or result.stdout or "").strip().splitlines()[-10:]:
            log.error(f"  ! {line}")
    return result.returncode == 0


def update_html_dates(today_str: str):
    """
    Patch both HTML files to show today's date.
    Handles the date tags in cheltenham_strategy_2026.html and barrys HTML.
    """
    import re

    # ── Strategy HTML ──────────────────────────────────────────────────────
    if os.path.exists(STRAT_HTML):
        with open(STRAT_HTML, encoding="utf-8") as f:
            html = f.read()

        # Badge: "Updated: D Month YYYY — Master Combined"
        html = re.sub(
            r"Updated: \d{1,2} \w+ 2026 \u2014 Master Combined",
            f"Updated: {today_str} \u2014 Master Combined",
            html,
        )
        # Section title: "Today's Ranked Picks — D Month YYYY ..."
        html = re.sub(
            r"Today's Ranked Picks \u2014 \d{1,2} \w+ 2026[^<]*",
            f"Today\u2019s Ranked Picks \u2014 {today_str} (Pre-Festival)",
            html,
        )

        with open(STRAT_HTML, "w", encoding="utf-8") as f:
            f.write(html)
        log.info(f"  ✓ cheltenham_strategy_2026.html date → {today_str}")
    else:
        log.warning(f"  ⚠ Strategy HTML not found: {STRAT_HTML}")

    # ── Barry's HTML ───────────────────────────────────────────────────────
    if os.path.exists(BARR_HTML):
        with open(BARR_HTML, encoding="utf-8") as f:
            html = f.read()

        # "Live scores — DD Mon YYYY" style tag
        html = re.sub(
            r"Live scores \u2014 \d{2} \w+ 2026",
            f"Live scores \u2014 {today_str}",
            html,
        )
        # Footer "... 07 Mar 2026 · Prize: £2,500"
        html = re.sub(
            r"\d{2} \w{3} 2026 &middot; Prize",
            lambda m: f"{datetime.now().strftime('%d %b %Y')} &middot; Prize",
            html,
        )

        with open(BARR_HTML, "w", encoding="utf-8") as f:
            f.write(html)
        log.info(f"  ✓ barrys_cheltenham_2026.html date → {today_str}")
    else:
        log.warning(f"  ⚠ Barry's HTML not found: {BARR_HTML}")


def is_race_day(today: date = None) -> bool:
    today = today or date.today()
    return FESTIVAL_START <= today <= FESTIVAL_END


def main():
    parser = argparse.ArgumentParser(description="Cheltenham 2026 daily update")
    parser.add_argument("--race-day",   action="store_true", help="Force race-day mode (Betfair odds + picks)")
    parser.add_argument("--odds-only",  action="store_true", help="Only refresh Betfair odds (no full picks run)")
    args = parser.parse_args()

    today      = date.today()
    today_str  = today.strftime("%-d %B %Y") if sys.platform != "win32" else today.strftime("%#d %B %Y")
    race_day   = args.race_day or is_race_day(today)

    log.info("=" * 70)
    log.info(f"  CHELTENHAM DAILY UPDATE  —  {today_str}")
    log.info(f"  Race day mode: {race_day}")
    log.info("=" * 70)

    success = True

    # ── Step 1: Refresh Betfair odds (race days + odds-only mode) ──────────
    if race_day or args.odds_only:
        ok = run(
            [PYTHON, "cheltenham_2026_intelligence.py", "--update-picks"],
            "Betfair odds refresh",
        )
        success = success and ok
        if args.odds_only:
            log.info("  --odds-only: stopping after Betfair refresh.")
            return 0 if success else 1

    # ── Step 2: Full picks scoring ─────────────────────────────────────────
    ok = run(
        [PYTHON, "save_cheltenham_picks.py", "--today"],
        "save_cheltenham_picks (score all 28 races)",
    )
    success = success and ok

    # ── Step 3: Update HTML date stamps ───────────────────────────────────
    update_html_dates(today_str)

    log.info("=" * 70)
    log.info(f"  {'✓ All done' if success else '⚠ Completed with errors'}  —  {today_str}")
    log.info("=" * 70)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

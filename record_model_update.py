"""
record_model_update.py
----------------------
CLI tool to record a new model update to DynamoDB so that the Results UI
banner is always driven by live data rather than hardcoded values.

Usage
-----
  python record_model_update.py \\
    --date 2026-04-03 \\
    --title "Threshold raised 85→90 + losing odds band block" \\
    --summary "Scores 85-89 were producing -21.8% ROI. Hard filter added for 3.0-4.9 decimal odds." \\
    --type threshold

  python record_model_update.py --list         # Show all stored updates
  python record_model_update.py --seed         # Seed historical updates (run once)

Update types: threshold | signal_fix | scoring | pipeline | bug_fix
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME   = "SureBetBets"
REGION       = "eu-west-1"
PARTITION_KEY = "MODEL_UPDATES"   # All model updates live under this bet_date

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table    = dynamodb.Table(TABLE_NAME)


# ── Historical updates to seed ─────────────────────────────────────────────────
# These encode the updates that were previously hardcoded in App.js
HISTORICAL_UPDATES = [
    {
        "date":    "2026-03-30",
        "title":   "Deep Form Score Recalibration",
        "summary": "Two scoring bugs identified and fixed. Applied to all future picks.",
        "type":    "signal_fix",
        "bugs": [
            {
                "name":  "AW Going Non-Selectivity (+16pts phantom signal)",
                "detail": ("The Deep Form scorer awarded up to +16 pts for 'Won on Standard ground' on "
                           "All-Weather races. But every All-Weather race runs on Standard going — so this "
                           "signal fired for virtually every AW horse regardless of whether their going "
                           "preference was actually being matched. Equivalent to awarding points for "
                           "'racing during daylight'. Completely non-selective."),
                "fix":   "going_win_match suppressed entirely for AW/Standard surfaces. "
                         "Going Suitability (signal 1) already accounts for this correctly.",
            },
            {
                "name":  "OR Trajectory on Long Layoff (+10pts invalid signal)",
                "detail": ("The model awarded +10 pts when a horse's Official Rating was higher than "
                           "3 runs ago — intended to identify improving horses. But this also fired after "
                           "300-400 day layoffs, where a higher OR after a long absence likely reflects a "
                           "handicapper's reassessment, not genuine improvement. A horse returning from "
                           "13 months off is an unknown quantity, not a 'rising' horse."),
                "fix":   "OR trajectory signal only counts when days since last run ≤ 90.",
            },
        ],
        "impact": {
            "horses_affected": [
                {
                    "horse":   "Layla Liz",
                    "course":  "Wolverhampton",
                    "old":     112,
                    "new":     86,
                    "delta":   -26,
                    "changes": "AW going -16 · OR trajectory -10",
                    "outcome": "Unplaced",
                    "outcome_color": "#f87171",
                    "note":    "Would have been ranked lower — correctly STRONG not ELITE",
                },
                {
                    "horse":   "Scarlet Moon",
                    "course":  "Ludlow",
                    "old":     100,
                    "new":     90,
                    "delta":   -10,
                    "changes": "OR trajectory -10 (406-day layoff)",
                    "outcome": "Placed (3rd)",
                    "outcome_color": "#60a5fa",
                    "note":    "Still selected; score more accurate",
                },
            ],
            "unchanged": "Shazani, Say What You See, Galileo Dame, Kool One and Al Durry were unaffected.",
            "conclusion": "The same 5 picks would still have been selected today with the fix applied; "
                          "Layla Liz's tier correctly downgrades from ELITE (112) to STRONG (86). "
                          "This fix is now live for all future picks.",
        },
    },
    {
        "date":    "2026-04-03",
        "title":   "Score Threshold Raised 85 → 90 + Losing Odds Band Block",
        "summary": ("Scores 85–89 were producing −21.8% ROI — a losing band. Hard filter added: "
                    "3.0–4.9 decimal (2/1–4/1) odds picks blocked unless score ≥ 95 (historically "
                    "that range lost £11.95 per cycle). Race-skip threshold also raised 85 → 90."),
        "type":    "threshold",
        "bugs": [
            {
                "name":  "Threshold too low (85 → 90)",
                "detail": ("Scores 85–89 were being shown on the UI but had a −21.8% ROI. "
                           "Raising to 90 removes this losing band entirely."),
                "fix":   "show_in_ui threshold raised from 85 to 90. Race-skip floor also raised.",
            },
            {
                "name":  "3.0–4.9 decimal odds losing band",
                "detail": ("Historical P&L: 3.0–4.9 decimal odds picks produced £−11.95 per cycle "
                           "— statistically the worst-performing band. The signal strength was "
                           "insufficient to overcome the short-odds market accuracy in this range."),
                "fix":   "Picks with 3.0–4.9 decimal odds now blocked unless score ≥ 95.",
            },
        ],
        "impact": {
            "horses_affected": [
                {
                    "horse":   "Hundred Caps (4.5 dec, AW evening)",
                    "course":  "",
                    "old":     92,
                    "new":     80,
                    "delta":   -12,
                    "changes": "sweet spot penalty applied",
                    "outcome": "Would not show",
                    "outcome_color": "#f87171",
                    "note":    "below 90",
                },
                {
                    "horse":   "Always A Reason (4.5 dec, unkn. trainer)",
                    "course":  "",
                    "old":     100,
                    "new":     88,
                    "delta":   -12,
                    "changes": "losing band",
                    "outcome": "Would not show",
                    "outcome_color": "#f87171",
                    "note":    "losing band",
                },
                {
                    "horse":   "So You Know (4.5 dec, K Bailey)",
                    "course":  "",
                    "old":     88,
                    "new":     76,
                    "delta":   -12,
                    "changes": "sweet spot penalty applied",
                    "outcome": "Would not show",
                    "outcome_color": "#f87171",
                    "note":    "below 90",
                },
                {
                    "horse":   "Jaipaletemps (8.0 dec, D Pipe)",
                    "course":  "",
                    "old":     88,
                    "new":     88,
                    "delta":   0,
                    "changes": "unchanged",
                    "outcome": "Would not show",
                    "outcome_color": "#f87171",
                    "note":    "below 90",
                },
            ],
            "unchanged": "",
            "conclusion": "All 4 yesterday's losses would have been filtered out under the new rules.",
        },
    },
]


def seed_historical():
    """Write all HISTORICAL_UPDATES to DynamoDB."""
    for upd in HISTORICAL_UPDATES:
        write_update(
            date    = upd["date"],
            title   = upd["title"],
            summary = upd["summary"],
            upd_type = upd["type"],
            payload  = upd,
        )
    print(f"Seeded {len(HISTORICAL_UPDATES)} historical updates.")


def write_update(date: str, title: str, summary: str, upd_type: str, payload: dict = None):
    """Persist a model update record to DynamoDB."""
    item = {
        "bet_date":      PARTITION_KEY,
        "bet_id":        f"UPDATE_{date}",
        "date":          date,
        "title":         title,
        "summary":       summary,
        "type":          upd_type,
        "created_at":    datetime.now(timezone.utc).isoformat(),
        "payload":       json.dumps(payload or {}),
    }
    table.put_item(Item=item)
    print(f"✅  Recorded model update {date}: {title}")


def list_updates():
    """Print all model updates stored in DynamoDB."""
    resp  = table.query(KeyConditionExpression=Key("bet_date").eq(PARTITION_KEY))
    items = sorted(resp.get("Items", []), key=lambda x: x.get("date", ""), reverse=True)
    if not items:
        print("No model updates found.")
        return
    print(f"\n{'Date':<14} {'Type':<12} Title")
    print("-" * 70)
    for it in items:
        print(f"{it.get('date',''):<14} {it.get('type',''):<12} {it.get('title','')}")


def main():
    parser = argparse.ArgumentParser(description="Record a model update")
    parser.add_argument("--date",    help="Update date YYYY-MM-DD (defaults to today)")
    parser.add_argument("--title",   help="Short title for the update")
    parser.add_argument("--summary", help="Longer explanation paragraph")
    parser.add_argument("--type",    default="scoring",
                        choices=["threshold", "signal_fix", "scoring", "pipeline", "bug_fix"],
                        help="Category of update")
    parser.add_argument("--list",    action="store_true", help="List all stored updates")
    parser.add_argument("--seed",    action="store_true", help="Seed historical updates")
    args = parser.parse_args()

    if args.seed:
        seed_historical()
        return

    if args.list:
        list_updates()
        return

    if not args.title or not args.summary:
        parser.error("--title and --summary are required when recording a new update")

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    write_update(date, args.title, args.summary, args.type)


if __name__ == "__main__":
    main()

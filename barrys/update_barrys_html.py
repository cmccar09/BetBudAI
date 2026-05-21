"""
BARRY'S CHELTENHAM 2026 — DAILY HTML REGENERATOR
=================================================
Pulls latest picks from CheltenhamPicks DynamoDB, applies MacFitz override
logic from macfitz_overrides.json, flags new close calls, and writes
barrys_cheltenham_2026.html.

Schedule: runs automatically inside daily_automated_workflow.py during the
Cheltenham window (05–13 Mar 2026).

Usage:
    python barrys/update_barrys_html.py               # full update
    python barrys/update_barrys_html.py --dry-run      # print diff, no write
    python barrys/update_barrys_html.py --check-splits # show close-call report only
"""

import sys, os, json, re, pathlib, argparse
from datetime import datetime
from decimal import Decimal

# ── path setup ────────────────────────────────────────────────────────────────
ROOT = pathlib.Path(__file__).resolve().parent.parent   # Betting/
sys.path.insert(0, str(ROOT))
import boto3

# ── file paths ────────────────────────────────────────────────────────────────
HERE              = pathlib.Path(__file__).resolve().parent
OVERRIDES_FILE    = HERE / "macfitz_overrides.json"
RESULTS_FILE      = HERE / "race_results.json"
PERSONAL_BETS_FILE = HERE / "personal_bets.json"
HTML_OUT          = HERE / "barrys_cheltenham_2026.html"
PICKS_TABLE       = "CheltenhamPicks"
REGION            = "eu-west-1"

# ── scoring ──────────────────────────────────────────────────────────────────
POINTS = {1: 10, 2: 5, 3: 3}  # position → points

# ── race catalogue (defines display order + metadata) ─────────────────────────
# Each entry: (day_num, time, db_name, display_name, grade_css, grade_label, day_label, day_date)
RACES = [
    # Day 1 — Champion Day (Tuesday 10 March 2026)
    (1, "13:20", "Sky Bet Supreme Novices' Hurdle",    "Sky Bet Supreme Novices' Hurdle",  "g1",   "G1",     "Champion Day",          "Tuesday 10 March 2026"),
    (1, "14:00", "Arkle Challenge Trophy Chase",       "Arkle Challenge Trophy Chase",     "g1",   "G1",     "Champion Day",          "Tuesday 10 March 2026"),
    (1, "14:40", "Fred Winter Handicap Hurdle",        "Fred Winter Handicap Hurdle",      "hcap", "Hcap",   "Champion Day",          "Tuesday 10 March 2026"),
    (1, "15:20", "Ultima Handicap Chase",              "Ultima Handicap Chase",            "hcap", "Hcap",   "Champion Day",          "Tuesday 10 March 2026"),
    (1, "16:00", "Unibet Champion Hurdle",             "Unibet Champion Hurdle",           "g1",   "G1",     "Champion Day",          "Tuesday 10 March 2026"),
    (1, "16:40", "Cheltenham Plate Chase",             "Cheltenham Plate Chase",           "hcap", "Hcap",   "Champion Day",          "Tuesday 10 March 2026"),
    (1, "17:20", "Challenge Cup Chase",                "Challenge Cup Chase",              "hcap", "Hcap",   "Champion Day",          "Tuesday 10 March 2026"),
    # Day 2 — Ladies Day (Wednesday 11 March 2026)
    (2, "13:20", "Turner's Novices' Hurdle",           "Turner's Novices' Hurdle",         "g1",   "G1",     "Ladies Day",            "Wednesday 11 March 2026"),
    (2, "14:00", "Brown Advisory Novices' Chase",      "Brown Advisory Novices' Chase",    "g1",   "G1",     "Ladies Day",            "Wednesday 11 March 2026"),
    (2, "14:40", "BetMGM Cup Hurdle",                  "BetMGM Cup Hurdle",                "hcap", "Hcap",   "Ladies Day",            "Wednesday 11 March 2026"),
    (2, "15:20", "Glenfarclas Cross Country Chase",    "Glenfarclas Cross Country Chase",  "g2",   "G2",     "Ladies Day",            "Wednesday 11 March 2026"),
    (2, "16:00", "Queen Mother Champion Chase",        "Queen Mother Champion Chase",      "g1",   "G1",     "Ladies Day",            "Wednesday 11 March 2026"),
    (2, "16:40", "Grand Annual Handicap Chase",        "Grand Annual Handicap Chase",      "hcap", "Hcap",   "Ladies Day",            "Wednesday 11 March 2026"),
    (2, "17:20", "Champion Bumper",                    "Champion Bumper",                  "flat", "Flat",   "Ladies Day",            "Wednesday 11 March 2026"),
    # Day 3 — St Patrick's Thursday (Thursday 12 March 2026)
    (3, "13:20", "Ryanair Mares' Novices' Hurdle",     "Ryanair Mares' Novices' Hurdle",   "g1",   "G1",     "St Patrick's Thursday", "Thursday 12 March 2026"),
    (3, "14:00", "Jack Richards Novices' Chase",       "Jack Richards Novices' Chase",     "g1",   "G1",     "St Patrick's Thursday", "Thursday 12 March 2026"),
    (3, "14:40", "Close Brothers Mares' Hurdle",       "Close Brothers Mares' Hurdle",     "g1",   "G1",     "St Patrick's Thursday", "Thursday 12 March 2026"),
    (3, "15:20", "Paddy Power Stayers' Hurdle",        "Paddy Power Stayers' Hurdle",      "g1",   "G1",     "St Patrick's Thursday", "Thursday 12 March 2026"),
    (3, "16:00", "Ryanair Chase",                      "Ryanair Chase",                    "g1",   "G1",     "St Patrick's Thursday", "Thursday 12 March 2026"),
    (3, "16:40", "Pertemps Handicap Hurdle",           "Pertemps Handicap Hurdle",         "hcap", "Hcap",   "St Patrick's Thursday", "Thursday 12 March 2026"),
    (3, "17:20", "Kim Muir Handicap Chase",            "Kim Muir Handicap Chase",          "hcap", "Hcap",   "St Patrick's Thursday", "Thursday 12 March 2026"),
    # Day 4 — Gold Cup Day (Friday 13 March 2026)
    (4, "13:20", "JCB Triumph Hurdle",                 "JCB Triumph Hurdle",               "g1",   "G1",     "Gold Cup Day",          "Friday 13 March 2026"),
    (4, "14:00", "County Handicap Hurdle",             "County Handicap Hurdle",           "hcap", "Hcap",   "Gold Cup Day",          "Friday 13 March 2026"),
    (4, "14:40", "Mrs Paddy Power Mares' Chase",       "Mrs Paddy Power Mares' Chase",     "g2",   "G2",     "Gold Cup Day",          "Friday 13 March 2026"),
    (4, "15:20", "Albert Bartlett Novices' Hurdle",    "Albert Bartlett Novices' Hurdle",  "g1",   "G1",     "Gold Cup Day",          "Friday 13 March 2026"),
    (4, "16:00", "Cheltenham Gold Cup",                "Cheltenham Gold Cup",              "g1",   "G1",     "Gold Cup Day",          "Friday 13 March 2026"),
    (4, "16:40", "St James's Place Hunters' Chase",    "St James's Place Hunters' Chase",  "hunt", "Hunter", "Gold Cup Day",          "Friday 13 March 2026"),
    (4, "17:20", "Martin Pipe Handicap Hurdle",        "Martin Pipe Handicap Hurdle",      "hcap", "Hcap",   "Gold Cup Day",          "Friday 13 March 2026"),
]

# Known Cheltenham course winners (shown as notes in MacFitz entry)
COURSE_WINNERS = {
    "Kopek Des Bordes":   "Cheltenham course winner",
    "Lossiemouth":        "Cheltenham course winner",
    "Majborough":         "Cheltenham course winner",
    "Favori De Champdou": "Won 2024 Cross Country",
    "Fact To File":       "Won 2024 & 2025 Ryanair — reigning champion",
    "Gaelic Warrior":     "Cheltenham course winner",
    "Dinoblue":           "Won 2025 Mares Chase",
}

# ── bumper submission config ──────────────────────────────────────────────────
SUREBET_GROUP_ID = 34
FITZMAC_GROUP_ID = 38

# Cloth / race-card numbers per horse at the Festival.
# Updated each morning before racing. '?' = not yet confirmed (Days 2-4).
RUNNER_NUMBERS: dict[str, int | str] = {
    # Day 1 — Champion Day (10 Mar)
    "Old Park Star":      8,
    "Talk The Talk":      6,
    "Kopek Des Bordes":   3,   # Surebet Arkle pick
    "Lulamba":            4,   # FitzMac Arkle pick (SPLIT)
    "Manlaga":            8,
    "Winston Junior":     10,
    "Jagwar":             4,
    "Iroko":              14,
    "Lossiemouth":        9,
    "The New Lion":       4,
    "Madara":             9,   # Surebet Plate pick
    "Zurich":             15,   # MacFitz Plate pick (SPLIT)
    "McLaurey":           2,
    "Backmersackme":      9,
    "Newton Tornado":     11,
    "Iceberg Theory":     6,
    # Day 2 — Ladies' Day (11 Mar)
    "No Drama This End":  12,   # Turner's 13:20 — 11/4
    "Final Demand":         2,   # Brown Advisory 14:00 — FitzMac split (alphabetical: A=1,F=2,J=3,K=4)
    "Kaid D'Authie":       4,   # Brown Advisory 14:00 — 6/1
    "Iberico Lord":        11,  # BetMGM Cup 14:40 — 9/1
    "Stumptown":            1,  # Cross Country 15:20 — 3/1
    "Favori De Champdou":   2,  # Cross Country 15:20 — FitzMac split
    "Majborough":           8,  # QMCC 16:00 — 10/11
    "Inthepocket":          5,  # Grand Annual 16:40 — 9/1 Surebet
    "Jazzy Matty":          8,  # Grand Annual 16:40 — 7/1 (NOT selected)
    "Be Aware":              4,  # Grand Annual 16:40 — 5/1 fav FitzMac split
    "Keep Him Company":     8,  # Champion Bumper 17:20 — Surebet
    "Quiryn":              21,  # Champion Bumper 17:20 — FitzMac split (Mullins/Townend, 4yo)
    # Day 3 — St Patrick's Thursday (12 Mar) — confirmed from Betfair declared runners
    "Bambino Fever":        3,    # Mares Novices Hurdle 13:20 — SB banker (11/10 fav, cloth #3)
    "Oldschool Outlaw":     15,   # Mares Novices Hurdle 13:20 — cloth #15 (beat Bambino Fever Dec 25)
    "Sixmilebridge":        "NR",  # Jack Richards Novices' Chase 14:00 — NR (confirmed 12/03/2026)
    "Jordans Cross":        10,   # Jack Richards Novices' Chase 14:00 — NEW SB pick (CD winner, 6/1, cloth #10)
    "Regents Stroll":        4,    # Jack Richards Novices' Chase 14:00 — MF SWITCH (9/2, Cobden/Nicholls, D symbol)
    "Meetmebythesea":       11,   # Jack Richards Novices' Chase 14:00 — cloth #11 (9/2 big market mover)
    "Jade De Grugy":        3,    # Close Brothers Mares' Hurdle 14:40 — SB SPLIT (5/2, cloth #3)
    "Wodhooh":              7,    # Close Brothers Mares' Hurdle 14:40 — MF SPLIT (EVS fav, cloth #7)
    "Kabral Du Mathan":     9,    # Paddy Power Stayers' Hurdle 15:20 — SB SPLIT (5/1, cloth #9)
    "Teahupoo":             11,   # Paddy Power Stayers' Hurdle 15:20 — MF SPLIT (7/2, cloth #11)
    "Impose Toi":           8,    # Paddy Power Stayers' Hurdle 15:20 — cloth #8 (17/2)
    "Fact To File":         3,    # Ryanair Chase 16:00 — SB banker (6/5 fav, cloth #3)
    "Jonbon":               6,    # Ryanair Chase 16:00 — cloth #6 (4/1)
    "Impaire Et Passe":     5,    # Ryanair Chase 16:00 — cloth #5 (11/2)
    "Banbridge":            1,    # Ryanair Chase 16:00 — cloth #1 (8/1)
    "Supremely West":       7,    # Pertemps Handicap Hurdle 16:40 — market fav (3/1, cloth #7)
    "Ace Of Spades":        4,    # Pertemps Handicap Hurdle 16:40 — BOTH picks (10/1, cloth #4)
    "Gowel Road":           2,    # Pertemps Handicap Hurdle 16:40 — cloth #2 (old MF split)
    "Staffordshire Knot":   1,    # Pertemps Handicap Hurdle 16:40 — cloth #1 (original model pick)
    "Herakles Westwood":    8,    # Kim Muir Handicap Chase 17:20 — SB SPLIT (11/1, cloth #8)
    "Jeriko Du Reponet":    1,    # Kim Muir Handicap Chase 17:20 — MF SPLIT (9/2 fav, cloth #1)
    # Day 4 — Gold Cup Day (13 Mar) — confirmed from Betfair declared runners
    "Minella Study":        11,   # JCB Triumph Hurdle 13:20 — SB banker (13/2, cloth #11)
    "Proactif":             15,   # JCB Triumph Hurdle 13:20 — cloth #15 (9/2 fav)
    "Highland Crystal":     17,   # JCB Triumph Hurdle 13:20 — MF SPLIT (15/2, cloth #17)
    "Absurde":              2,    # County Hurdle 14:00 — SB banker (22/1, cloth #2)
    "Ndaawi":               1,    # County Hurdle 14:00 — MF SPLIT (28/1, cloth #1)
    "Dinoblue":             2,    # Mares' Chase 14:40 — SB banker (21/10 fav, cloth #2)
    "Panic Attack":         7,    # Mares' Chase 14:40 — MF SPLIT (11/4, cloth #7)
    "Doctor Steinberg":     2,    # Albert Bartlett 15:20 — BOTH banker (3/1 fav, cloth #2)
    "Gaelic Warrior":       3,    # Gold Cup 16:00 — MF SPLIT (7/2 fav, cloth #3)
    "Jango Baie":           8,    # Gold Cup 16:00 — SB SPLIT (4/1, cloth #8)
    "Wonderwall":          23,    # Hunters' Chase 16:40 — SB SPLIT (17/2, cloth #23)
    "Its On The Line":      7,    # Hunters' Chase 16:40 — MF SPLIT (5/1 fav, cloth #7)
    "Nurse Susan":          2,    # Martin Pipe 17:20 — SB SPLIT (25/1, cloth #2)
    "Sony Bill":            "NR", # Martin Pipe 17:20 — NR (not declared 13/03/2026)
    "Kel Histoire":         11,   # Martin Pipe 17:20 — MF SPLIT (4/1 fav, cloth #11 by entry)
}

# ── tier cosmetics ─────────────────────────────────────────────────────────────
TIER_CSS = {
    "A+": ("elite",  "var(--gold)",   "A+ ELITE"),
    "A":  ("elite",  "var(--gold)",   "A ELITE"),
    "B":  ("strong", "var(--blue)",   "B EXCELLENT"),
    "C":  ("",       "var(--green)",  "C STRONG"),
    "D":  ("fair",   "var(--muted)",  "D FAIR"),
    "E":  ("fair",   "var(--muted)",  "E WEAK"),
}

def _tier_css(tier_str: str):
    """Map raw tier string from DB (e.g. 'A+ ELITE', 'B   EXCELLENT') → (css_class, color, label)."""
    t = tier_str.strip().upper()
    for key, val in TIER_CSS.items():
        if t.startswith(key):
            return val
    return ("", "var(--muted)", tier_str.strip())


# ── DynamoDB fetch ─────────────────────────────────────────────────────────────
def fetch_latest_picks() -> dict:
    """Return dict[race_name → latest item] from CheltenhamPicks."""
    dynamo = boto3.resource("dynamodb", region_name=REGION)
    table  = dynamo.Table(PICKS_TABLE)
    resp   = table.scan()
    items  = resp["Items"]
    while "LastEvaluatedKey" in resp:
        resp  = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items += resp["Items"]

    latest = {}
    for item in items:
        rn = item.get("race_name", "?")
        ua = item.get("updated_at", "")
        if rn not in latest or ua > latest[rn].get("updated_at", ""):
            latest[rn] = item
    return latest


# ── MacFitz override logic ─────────────────────────────────────────────────────
def load_overrides() -> dict:
    if OVERRIDES_FILE.exists():
        return json.loads(OVERRIDES_FILE.read_text(encoding="utf-8"))
    return {"overrides": {}}


def load_results() -> dict:
    """Load race_results.json. Returns dict[race_name → {1st, 2nd, 3rd}]."""
    if RESULTS_FILE.exists():
        data = json.loads(RESULTS_FILE.read_text(encoding="utf-8"))
        return data.get("results", {})
    return {}


def compute_competition_scores(assembled: list, results: dict) -> dict:
    """
    For each race compute how many points Surebet and MacFitz scored.
    Returns:
      {
        "per_race": [(race_db_name, sb_horse, mf_horse, sb_pts, mf_pts, placed_1, placed_2, placed_3), ...],
        "sb_total": int,
        "mf_total": int,
        "races_run": int,
      }
    """
    per_race = []
    sb_total = 0
    mf_total = 0
    races_run = 0

    for race, sb_pick, mf_pick in assembled:
        db_name  = race[2]
        # For split races use the override's declared surebet_horse, not the raw DB pick
        # (the override intentionally assigns a different horse to SureBet for scoring)
        if mf_pick.get("is_split"):
            sb_horse = mf_pick.get("surebet_horse", sb_pick.get("horse", "?"))
        else:
            sb_horse = sb_pick.get("horse", "?")
        mf_horse = mf_pick["horse"]
        res      = results.get(db_name, {})

        p1 = (res.get("1st") or "").strip()
        p2 = (res.get("2nd") or "").strip()
        p3 = (res.get("3rd") or "").strip()

        finished = bool(p1)  # race is complete if 1st is set
        if finished:
            races_run += 1

        def pts_for(horse: str) -> int:
            if not finished:
                return -1  # sentinel = not run yet
            h = horse.strip().lower()
            if h and h == p1.lower():
                return POINTS[1]
            if h and h == p2.lower():
                return POINTS[2]
            if h and h == p3.lower():
                return POINTS[3]
            return 0

        sb_pts = pts_for(sb_horse)
        mf_pts = pts_for(mf_horse)
        if finished:
            sb_total += sb_pts
            mf_total += mf_pts

        per_race.append((db_name, sb_horse, mf_horse, sb_pts, mf_pts, p1, p2, p3))

    return {
        "per_race":  per_race,
        "sb_total":  sb_total,
        "mf_total":  mf_total,
        "races_run": races_run,
    }


# ── MacFitz override logic ─────────────────────────────────────────────────────
def apply_macfitz(pick: dict, overrides: dict) -> dict:
    """
    Given a CheltenhamPicks item, return a MacFitz pick dict:
      { horse, score, is_split, override_reason, new_close_call }
    """
    surebet_horse = pick.get("horse", "?")
    score         = int(pick.get("score", 0) or 0)
    second_horse  = pick.get("second_horse_name", "")
    second_score  = int(pick.get("second_score", 0) or 0)
    gap           = int(pick.get("score_gap", score - second_score) or (score - second_score))
    race_name     = pick.get("race_name", "")

    # Check for a manual override
    ovr = overrides.get("overrides", {}).get(race_name)
    if ovr and ovr.get("active", True):
        # Validate the override horse is still in the field (score > 0)
        # If scores have changed significantly, warn but still apply
        return {
            "horse":          ovr["macfitz_horse"],
            "score":          ovr.get("macfitz_score", second_score),
            "is_split":       True,
            "override_reason": ovr["reason"],
            "new_close_call": False,
            "gap":            gap,
            "surebet_horse":  ovr.get("surebet_horse", surebet_horse),
            "surebet_score":  score,
        }

    # Auto-detect dead ties not yet in overrides
    threshold = overrides.get("_auto_split_threshold", 3)
    new_close = (gap <= threshold and second_horse)

    return {
        "horse":          surebet_horse,
        "score":          score,
        "is_split":       False,
        "override_reason": None,
        "new_close_call": new_close,
        "gap":            gap,
        "surebet_horse":  surebet_horse,
        "surebet_score":  score,
    }


def _pts_class(pts: int) -> str:
    if pts == 10: return "pts-win"
    if pts == 5:  return "pts-place"
    if pts == 3:  return "pts-show"
    if pts == 0:  return "pts-zero"
    return "pts-pending"


def _pts_label(pts: int) -> str:
    if pts == -1: return "&mdash;"
    if pts == 10: return "10 &#127949;"
    if pts == 5:  return "5 &#127948;"
    if pts == 3:  return "3 &#127947;"
    return "0"


def _build_scorecard_html(assembled: list, score_data: dict | None) -> str:
    if not score_data:
        score_data = {"per_race": [], "sb_total": 0, "mf_total": 0, "races_run": 0}

    sb_total   = score_data["sb_total"]
    mf_total   = score_data["mf_total"]
    races_run  = score_data["races_run"]
    per_race   = score_data["per_race"]
    max_pts    = races_run * 10 if races_run else 28 * 10
    pct        = round(sb_total / max_pts * 100) if max_pts else 0

    if races_run == 0:
        status_msg = '<span style="color:var(--muted);font-style:italic;">Festival starts tomorrow &mdash; check back after each race!</span>'
        leader_badge = ""
    elif sb_total > mf_total:
        gap = sb_total - mf_total
        status_msg = f'<span style="color:var(--green);font-weight:700;">&#128309; SUREBET leads by {gap} point{"s" if gap!=1 else ""}</span>'
        leader_badge = f'<span style="background:var(--green);color:#0d1117;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:10px;margin-left:10px;">LEADING</span>'
    elif mf_total > sb_total:
        gap = mf_total - sb_total
        status_msg = f'<span style="color:var(--orange);font-weight:700;">&#128992; FITZMAC leads by {gap} point{"s" if gap!=1 else ""}</span>'
        leader_badge = f'<span style="background:var(--orange);color:#0d1117;font-size:.72rem;font-weight:700;padding:3px 10px;border-radius:10px;margin-left:10px;">LEADING</span>'
    else:
        status_msg = '<span style="color:var(--gold);font-weight:700;">&#9889; All Square</span>'
        leader_badge = ""

    # Build per-race rows (only if any races run)
    race_rows = ""
    race_order = {r[2]: i for i, (r, _, _) in enumerate(assembled)}
    if races_run > 0:
        for db_name, sb_horse, mf_horse, sb_pts, mf_pts, p1, p2, p3 in per_race:
            if sb_pts == -1:
                continue  # race not yet run
            placed_str = ""
            if p1:
                placed_str = f'<span style="color:var(--green);font-weight:600">{p1}</span>'
                if p2: placed_str += f' &middot; <span style="color:var(--blue)">{p2}</span>'
                if p3: placed_str += f' &middot; <span style="color:var(--gold)">{p3}</span>'
            same = (sb_horse.lower() == mf_horse.lower())
            mf_cell = "&mdash; (same)" if same else f'<span style="color:var(--orange)">{mf_horse}</span>'
            race_display = db_name[:45]
            race_rows += (
                f'<tr>'
                f'<td style="color:var(--muted);font-size:.78rem">{race_display}</td>'
                f'<td style="color:var(--green)">{sb_horse}</td>'
                f'<td class="{_pts_class(sb_pts)}">{_pts_label(sb_pts)}</td>'
                f'<td>{mf_cell}</td>'
                f'<td class="{_pts_class(mf_pts)}">{_pts_label(mf_pts)}</td>'
                f'<td style="color:var(--muted);font-size:.78rem">{placed_str}</td>'
                f'</tr>\n'
            )

    results_table = ""
    if race_rows:
        results_table = f"""
  <table class="results-table">
    <thead><tr>
      <th>Race</th>
      <th style="color:var(--blue)">&#128309; Surebet Pick</th>
      <th style="color:var(--green)">Pts</th>
      <th style="color:var(--orange)">&#128992; FitzMac Pick</th>
      <th style="color:var(--orange)">Pts</th>
      <th>Placed 1st / 2nd / 3rd</th>
    </tr></thead>
    <tbody>{race_rows}</tbody>
  </table>"""

    festival_started = races_run == 0
    fill_tip = (
        '<div style="font-size:.78rem;color:var(--muted);margin-top:8px;">'
        '&#9432; Add results to <code>barrys/race_results.json</code> after each race to update the scorecard.</div>'
    ) if festival_started else ""

    return f"""
<div class="scorecard">
  <div class="score-header">
    <div class="score-big">
      <div class="pts" style="color:var(--blue)">{sb_total}</div>
      <div class="lbl">&#128309; Surebet</div>
    </div>
    <div class="score-vs">vs</div>
    <div class="score-big">
      <div class="pts" style="color:var(--orange)">{mf_total}</div>
      <div class="lbl">&#128992; FitzMac</div>
    </div>
    <div class="score-meta">
      <div style="font-size:.85rem;color:var(--text);font-weight:600;">{status_msg}{leader_badge}</div>
      <div style="font-size:.75rem;color:var(--muted);margin-top:4px;">{races_run} of 28 races complete &middot; Max: 280 pts &middot; &euro;3,000 1st &middot; &euro;1,250 2nd &middot; &euro;500 3rd &middot; &euro;250 4th</div>
      <div class="progress"><div class="bar" style="width:{pct}%"></div></div>
    </div>
  </div>
  {results_table}
  {fill_tip}
</div>"""


# ── HTML generation ────────────────────────────────────────────────────────────
CSS = r"""
  :root {
    --bg:#0d1117;--surface:#161b22;--border:#30363d;--gold:#c9a84c;--gold2:#e8c96d;
    --green:#3fb950;--blue:#58a6ff;--purple:#bc8cff;--red:#f85149;--orange:#d29922;
    --muted:#8b949e;--text:#e6edf3;
  }
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:14px;line-height:1.5;}
  .masthead{background:linear-gradient(135deg,#1a1200 0%,#2a1f00 40%,#1a1200 100%);border-bottom:2px solid var(--gold);padding:28px 32px;text-align:center;}
  .masthead::before{content:"🏆";font-size:48px;display:block;margin-bottom:8px;}
  .masthead h1{font-size:2.2rem;color:var(--gold2);letter-spacing:2px;text-transform:uppercase;text-shadow:0 0 20px rgba(201,168,76,.5);}
  .masthead .subtitle{font-size:1rem;color:var(--muted);margin-top:6px;letter-spacing:1px;}
  .prize-badge{display:inline-block;margin-top:14px;background:var(--gold);color:#0d1117;font-weight:700;font-size:1.2rem;padding:6px 22px;border-radius:20px;letter-spacing:1px;}
  .updated-tag{display:inline-block;margin-top:10px;margin-left:12px;background:rgba(63,185,80,.2);border:1px solid var(--green);color:var(--green);font-size:.8rem;font-weight:600;padding:4px 14px;border-radius:20px;}
  .rules-bar{display:flex;justify-content:center;gap:24px;padding:14px 32px;background:var(--surface);border-bottom:1px solid var(--border);flex-wrap:wrap;}
  .score-pill{display:flex;align-items:center;gap:8px;padding:5px 16px;border-radius:6px;font-weight:600;font-size:.9rem;}
  .score-pill.win  {background:rgba(63,185,80,.15);border:1px solid var(--green);color:var(--green);}
  .score-pill.place{background:rgba(88,166,255,.15);border:1px solid var(--blue);color:var(--blue);}
  .score-pill.show {background:rgba(201,168,76,.15);border:1px solid var(--gold);color:var(--gold);}
  .score-pill.zero {background:rgba(139,148,158,.1);border:1px solid var(--muted);color:var(--muted);}
  .strategy-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;padding:20px 32px;max-width:1100px;margin:0 auto;}
  .strategy-card{padding:18px 22px;border-radius:10px;border:1px solid var(--border);}
  .strategy-card.surebet {background:linear-gradient(135deg,#0d1117 0%,#0a1a2a 100%);border-left:4px solid var(--blue);}
  .strategy-card.macfitz {background:linear-gradient(135deg,#0d1117 0%,#1a0d0a 100%);border-left:4px solid var(--orange);}
  .strategy-card h3{font-size:1.1rem;margin-bottom:6px;}
  .strategy-card.surebet h3{color:var(--blue);}
  .strategy-card.macfitz h3{color:var(--orange);}
  .strategy-card p{color:var(--muted);font-size:.88rem;line-height:1.6;}
  .notice-wrapper{max-width:1100px;margin:0 auto 0;padding:0 32px 16px;}
  .notice-box{background:rgba(63,185,80,.08);border:1px solid rgba(63,185,80,.4);border-radius:8px;padding:12px 18px;font-size:.88rem;color:var(--green);}
  .notice-box.has-splits{background:rgba(210,153,34,.08);border-color:rgba(210,153,34,.4);color:var(--text);}
  .content{max-width:1200px;margin:0 auto;padding:0 24px 40px;}
  .day-section{margin-bottom:32px;}
  .day-header{display:flex;align-items:center;gap:16px;padding:14px 20px;background:linear-gradient(90deg,#1a1200 0%,#161b22 100%);border-radius:10px 10px 0 0;border:1px solid var(--gold);border-bottom:none;}
  .day-number{background:var(--gold);color:#0d1117;font-weight:800;font-size:.85rem;padding:4px 10px;border-radius:4px;letter-spacing:1px;}
  .day-title{font-size:1.15rem;font-weight:700;color:var(--gold2);}
  .day-date{font-size:.85rem;color:var(--muted);margin-left:auto;}
  .picks-table{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--border);border-radius:0 0 10px 10px;overflow:hidden;}
  .picks-table thead tr{background:#1c2128;}
  .picks-table th{padding:10px 14px;text-align:left;font-size:.78rem;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);border-bottom:1px solid var(--border);white-space:nowrap;}
  .picks-table td{padding:12px 14px;border-bottom:1px solid rgba(48,54,61,.6);vertical-align:middle;}
  .picks-table tr:last-child td{border-bottom:none;}
  .picks-table tr:hover td{background:rgba(255,255,255,.02);}
  .picks-table tr.banker-row td{background:rgba(63,185,80,.04);}
  .picks-table tr.split-row td{background:rgba(210,153,34,.04);}
  .time-cell{color:var(--gold);font-weight:600;font-size:.85rem;white-space:nowrap;}
  .grade-badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.75rem;font-weight:700;letter-spacing:.5px;white-space:nowrap;}
  .g1  {background:rgba(201,168,76,.2); color:var(--gold2); border:1px solid rgba(201,168,76,.4);}
  .g2  {background:rgba(88,166,255,.15);color:var(--blue);  border:1px solid rgba(88,166,255,.3);}
  .hcap{background:rgba(188,140,255,.15);color:var(--purple);border:1px solid rgba(188,140,255,.3);}
  .flat{background:rgba(63,185,80,.15); color:var(--green); border:1px solid rgba(63,185,80,.3);}
  .hunt{background:rgba(139,148,158,.15);color:var(--muted); border:1px solid rgba(139,148,158,.3);}
  .race-name{font-weight:600;color:var(--text);}
  .horse-pick{font-weight:700;font-size:.95rem;color:var(--green);}
  .banker-tag{display:inline-block;margin-left:8px;background:rgba(63,185,80,.2);border:1px solid rgba(63,185,80,.5);color:var(--green);font-size:.7rem;font-weight:700;padding:1px 7px;border-radius:10px;letter-spacing:.5px;vertical-align:middle;}
  .split-tag{display:inline-block;margin-left:6px;background:rgba(210,153,34,.25);border:1px solid rgba(210,153,34,.6);color:var(--orange);font-size:.7rem;font-weight:700;padding:1px 7px;border-radius:10px;letter-spacing:.5px;vertical-align:middle;}
  .score-tag{display:inline-block;margin-left:8px;background:rgba(88,166,255,.1);border:1px solid rgba(88,166,255,.3);color:var(--blue);font-size:.7rem;font-weight:600;padding:1px 7px;border-radius:10px;vertical-align:middle;}
  .score-tag.elite{background:rgba(201,168,76,.15);border-color:rgba(201,168,76,.4);color:var(--gold);}
  .score-tag.strong{background:rgba(63,185,80,.12);border-color:rgba(63,185,80,.3);color:var(--green);}
  .score-tag.fair{background:rgba(139,148,158,.1);border-color:rgba(139,148,158,.3);color:var(--muted);}
  .both-agree{font-size:.75rem;color:var(--muted);margin-top:2px;}
  .summary-section{margin-bottom:32px;padding:24px;background:var(--surface);border:1px solid var(--border);border-radius:10px;}
  .summary-section h2{font-size:1.2rem;color:var(--gold2);border-bottom:1px solid var(--border);padding-bottom:10px;margin-bottom:16px;}
  .summary-grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;}
  .solo-list h3{font-size:1rem;padding:8px 14px;border-radius:6px;margin-bottom:10px;font-weight:700;letter-spacing:.5px;}
  .surebet-header {background:rgba(88,166,255,.15);color:var(--blue);  border-left:3px solid var(--blue);}
  .macfitz-header  {background:rgba(210,153,34,.15); color:var(--orange);border-left:3px solid var(--orange);}
  .pick-item{display:flex;align-items:flex-start;gap:10px;padding:7px 0;border-bottom:1px solid rgba(48,54,61,.5);}
  .pick-item:last-child{border-bottom:none;}
  .pick-num{font-size:.72rem;color:var(--muted);min-width:20px;text-align:right;padding-top:1px;}
  .pick-body{flex:1;}
  .day-divider{font-size:.72rem;color:var(--muted);padding:10px 0 8px;border-bottom:1px solid var(--border);margin:6px 0;}
  .footer{text-align:center;padding:20px;border-top:1px solid var(--border);color:var(--muted);font-size:.8rem;}
  /* ── Personal Bets Panel ── */
  .pb-panel{max-width:1100px;margin:0 auto 28px;padding:0 32px;}
  .pb-box{background:linear-gradient(135deg,#0a0d14 0%,#0d1117 100%);border:2px solid #c9a84c;border-radius:12px;padding:20px 24px;}
  .pb-box h2{font-size:1.05rem;color:var(--gold2);font-weight:700;letter-spacing:.5px;margin-bottom:18px;display:flex;align-items:center;gap:10px;border-bottom:1px solid rgba(201,168,76,.25);padding-bottom:10px;}
  .pb-race-block{margin-bottom:18px;}
  .pb-race-header{display:flex;align-items:baseline;gap:10px;margin-bottom:8px;}
  .pb-time{background:var(--gold);color:#0d1117;font-size:.72rem;font-weight:800;padding:2px 8px;border-radius:4px;letter-spacing:.5px;white-space:nowrap;}
  .pb-race-name{font-size:.88rem;font-weight:600;color:var(--text);}
  .pb-bets{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:6px;}
  .pb-bet{display:flex;flex-direction:column;gap:3px;background:rgba(255,255,255,.04);border:1px solid var(--border);border-radius:8px;padding:8px 12px;min-width:180px;max-width:340px;flex:1;}
  .pb-bet.win-bet{border-color:rgba(63,185,80,.5);background:rgba(63,185,80,.06);}
  .pb-bet.ew-bet{border-color:rgba(88,166,255,.4);background:rgba(88,166,255,.05);}
  .pb-bet.outsider-bet{border-color:rgba(188,140,255,.4);background:rgba(188,140,255,.04);}
  .pb-horse{font-size:.9rem;font-weight:700;color:var(--text);}
  .pb-odds{font-size:.82rem;font-weight:700;margin-left:4px;}
  .pb-odds.win-odds{color:var(--green);}
  .pb-odds.ew-odds{color:var(--blue);}
  .pb-type{display:inline-block;font-size:.65rem;font-weight:700;padding:1px 6px;border-radius:4px;letter-spacing:.5px;white-space:nowrap;}
  .pb-type.win-type{background:rgba(63,185,80,.2);color:var(--green);border:1px solid rgba(63,185,80,.4);}
  .pb-type.ew-type{background:rgba(88,166,255,.15);color:var(--blue);border:1px solid rgba(88,166,255,.3);}
  .pb-reason{font-size:.72rem;color:var(--muted);line-height:1.45;margin-top:2px;}
  .pb-outsider-tag{display:inline-block;font-size:.63rem;background:rgba(188,140,255,.15);color:var(--purple);border:1px solid rgba(188,140,255,.3);border-radius:4px;padding:1px 6px;font-weight:700;margin-right:4px;letter-spacing:.3px;vertical-align:middle;}
  .pb-arc{font-size:.7rem;color:var(--purple);font-style:italic;margin-top:2px;}
  .pb-exch{display:inline-block;font-size:.65rem;font-weight:600;padding:1px 6px;border-radius:4px;background:rgba(139,148,158,.12);color:var(--muted);border:1px solid rgba(139,148,158,.25);margin-left:4px;white-space:nowrap;}
  .pb-exch-value{display:inline-block;font-size:.65rem;font-weight:700;padding:1px 6px;border-radius:4px;background:rgba(63,185,80,.18);color:var(--green);border:1px solid rgba(63,185,80,.45);margin-left:4px;white-space:nowrap;}
  .pb-exch-signal{display:inline-block;font-size:.65rem;font-weight:700;padding:1px 6px;border-radius:4px;background:rgba(210,153,34,.18);color:var(--orange);border:1px solid rgba(210,153,34,.45);margin-left:4px;white-space:nowrap;}
  .pb-exch-suspended{display:inline-block;font-size:.65rem;padding:1px 6px;border-radius:4px;background:rgba(139,148,158,.08);color:rgba(139,148,158,.5);border:1px dashed rgba(139,148,158,.2);margin-left:4px;white-space:nowrap;}
  /* ── SureBet Best Picks panel ── */
  .sbp-panel{max-width:1100px;margin:0 auto 24px;padding:0 32px;}
  .sbp-box{background:linear-gradient(135deg,#0d1a2a 0%,#0d1117 100%);border:2px solid var(--gold);border-radius:12px;padding:20px 24px;}
  .sbp-box h2{font-size:1.05rem;color:var(--gold);font-weight:700;letter-spacing:.5px;margin:0 0 16px;display:flex;align-items:center;gap:8px;}
  .sbp-grid{display:grid;grid-template-columns:55px 1fr 1fr 1fr;gap:0;border-radius:8px;overflow:hidden;border:1px solid rgba(139,148,158,.15);}
  .sbp-header{background:rgba(139,148,158,.1);font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--muted);padding:6px 10px;}
  .sbp-cell{font-size:.8rem;padding:7px 10px;border-top:1px solid rgba(139,148,158,.08);color:var(--fg);}
  .sbp-cell.time{color:var(--gold);font-weight:700;font-size:.78rem;}
  .sbp-cell.horse{font-weight:700;color:#e6edf3;}
  .sbp-cell.odds{color:var(--green);font-weight:600;}
  .sbp-cell.note{color:var(--muted);font-size:.72rem;}
  .sbp-badge{display:inline-block;font-size:.6rem;padding:1px 5px;border-radius:3px;font-weight:700;margin-right:3px;vertical-align:middle;}
  .sbp-badge.banker{background:rgba(63,185,80,.2);color:var(--green);border:1px solid rgba(63,185,80,.4);}
  .sbp-badge.cd{background:rgba(88,166,255,.15);color:var(--blue);border:1px solid rgba(88,166,255,.3);}
  .sbp-badge.value{background:rgba(210,153,34,.2);color:var(--orange);border:1px solid rgba(210,153,34,.4);}
  .sbp-badge.signal{background:rgba(236,105,65,.2);color:#f0876a;border:1px solid rgba(236,105,65,.4);}
  /* ── Submission Numbers panel ── */
  .submission-panel{max-width:1100px;margin:0 auto 24px;padding:0 32px;}
  .submission-box{background:linear-gradient(135deg,#0a1a0a 0%,#0d1117 100%);border:2px solid var(--green);border-radius:12px;padding:20px 24px;}
  .submission-box h3{font-size:1rem;color:var(--green);font-weight:700;letter-spacing:.5px;margin-bottom:14px;display:flex;align-items:center;gap:8px;}
  .sub-group-row{display:flex;gap:20px;margin-bottom:16px;flex-wrap:wrap;}
  .sub-group-badge{padding:6px 16px;border-radius:8px;font-weight:700;font-size:.95rem;letter-spacing:.5px;}
  .sub-group-badge.sb{background:rgba(88,166,255,.2);border:1px solid var(--blue);color:var(--blue);}
  .sub-group-badge.mf{background:rgba(210,153,34,.2);border:1px solid var(--orange);color:var(--orange);}
  .sub-day-grid{display:grid;grid-template-columns:auto 1fr 1fr;gap:8px 16px;align-items:start;}
  .sub-day-label{font-size:.78rem;font-weight:700;color:var(--gold);text-transform:uppercase;letter-spacing:.5px;padding-top:6px;}
  .sub-num-col{background:rgba(139,148,158,.06);border-radius:8px;padding:8px 12px;}
  .sub-num-col .col-head{font-size:.68rem;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;font-weight:700;}
  .sub-num-col .col-head.sb{color:var(--blue);}
  .sub-num-col .col-head.mf{color:var(--orange);}
  .sub-num-list{display:flex;flex-wrap:wrap;gap:6px;}
  .sub-horse-chip{display:inline-flex;flex-direction:column;align-items:center;background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:6px;padding:4px 8px;font-size:.72rem;min-width:38px;}
  .sub-horse-chip .chip-num{font-size:1.05rem;font-weight:900;line-height:1.1;}
  .sub-horse-chip .chip-name{font-size:.6rem;color:var(--muted);text-align:center;max-width:58px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .sub-horse-chip.split-sb{border-color:var(--blue);background:rgba(88,166,255,.1);}
  .sub-horse-chip.split-mf{border-color:var(--orange);background:rgba(210,153,34,.1);}
  .sub-horse-chip .chip-num.split-sb{color:var(--blue);}
  .sub-horse-chip .chip-num.split-mf{color:var(--orange);}
  .sub-nums-flat{font-size:.85rem;font-weight:600;color:var(--text);letter-spacing:.5px;}
  /* ── Scorecard / Leaderboard ── */
  .scorecard{max-width:1100px;margin:0 auto 24px;padding:0 32px;}
  .score-header{background:linear-gradient(135deg,#1a1200 0%,#0d1117 100%);border:2px solid var(--gold);border-radius:12px;padding:20px 28px;display:flex;align-items:center;gap:20px;flex-wrap:wrap;}
  .score-big{display:flex;flex-direction:column;align-items:center;min-width:120px;}
  .score-big .pts{font-size:2.4rem;font-weight:900;line-height:1;}
  .score-big .lbl{font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-top:4px;}
  .score-vs{font-size:1.5rem;font-weight:700;color:var(--muted);padding:0 8px;}
  .score-meta{flex:1;min-width:180px;}
  .score-meta .progress{background:rgba(139,148,158,.15);border-radius:4px;height:6px;margin-top:8px;overflow:hidden;}
  .score-meta .bar{height:100%;border-radius:4px;background:linear-gradient(90deg,var(--gold) 0%,var(--green) 100%);}
  .results-table{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-top:16px;}
  .results-table thead tr{background:#1c2128;}
  .results-table th{padding:9px 12px;text-align:left;font-size:.75rem;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);border-bottom:1px solid var(--border);}
  .results-table td{padding:10px 12px;border-bottom:1px solid rgba(48,54,61,.5);font-size:.82rem;vertical-align:middle;}
  .results-table tr:last-child td{border-bottom:none;}
  .pts-win{color:var(--green);font-weight:700;}
  .pts-place{color:var(--blue);font-weight:700;}
  .pts-show{color:var(--gold);font-weight:700;}
  .pts-zero{color:var(--muted);}
  .pts-pending{color:rgba(139,148,158,.45);font-style:italic;}
  @media(max-width:768px){.strategy-grid,.summary-grid{grid-template-columns:1fr;}.score-header{flex-direction:column;text-align:center;}}
"""


def _build_personal_bets_html() -> str:
    """Build the personal bets / improving outsiders panel from personal_bets.json."""
    if not PERSONAL_BETS_FILE.exists():
        return ""
    try:
        data = json.loads(PERSONAL_BETS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return ""

    races = data.get("races", [])
    if not races:
        return ""

    race_blocks = []
    for r in races:
        time_str  = r.get("time", "")
        race_name = r.get("race", "")
        bets      = r.get("bets", [])
        if not bets:
            continue

        bet_cards = []
        for b in bets:
            horse    = b.get("horse", "")
            odds     = b.get("odds", "")
            btype    = b.get("type", "EW").upper()
            reason   = b.get("reason", "")
            is_outsider = "IMPROVING OUTSIDER" in reason or "PEAKING" in reason.upper() or "arc" in b

            css_bet   = "win-bet"      if btype == "WIN" else ("outsider-bet" if is_outsider else "ew-bet")
            css_odds  = "win-odds"     if btype == "WIN" else "ew-odds"
            css_type  = "win-type"     if btype == "WIN" else "ew-type"
            outsider_tag = '<span class="pb-outsider-tag">&#8599; OUTSIDER</span>' if is_outsider and btype == "EW" else ""

            # Truncate reason to reasonable length
            reason_short = reason[:220] + "..." if len(reason) > 220 else reason

            # Betfair exchange price display
            exch_dec  = b.get("betfair_exchange")
            exch_note = b.get("betfair_note", "")
            if exch_dec is not None:
                exch_frac  = f"{exch_dec - 1:.1f}/1".rstrip("0").rstrip(".")
                value_flag = "VALUE" in exch_note.upper()
                signal_flag = "SIGNAL" in exch_note.upper() or "FAVOURITE" in exch_note.upper()
                exch_cls   = "pb-exch-value" if value_flag else ("pb-exch-signal" if signal_flag else "pb-exch")
                exch_html  = (f' <span class="{exch_cls}" title="{exch_note}">'
                              f'&#128260; BF {exch_dec}</span>')
            else:
                exch_html = ' <span class="pb-exch-suspended">BF susp.</span>'

            bet_cards.append(
                f'<div class="pb-bet {css_bet}">'
                f'<div><span class="pb-horse">{horse}</span>'
                f' <span class="pb-odds {css_odds}">{odds}</span>'
                f' <span class="pb-type {css_type}">{btype}</span>'
                f'{exch_html}'
                f'</div>'
                f'<div>{outsider_tag}<span class="pb-reason">{reason_short}</span></div>'
                f'</div>'
            )

        race_blocks.append(
            f'<div class="pb-race-block">'
            f'<div class="pb-race-header">'
            f'<span class="pb-time">{time_str}</span>'
            f'<span class="pb-race-name">{race_name}</span>'
            f'</div>'
            f'<div class="pb-bets">{" ".join(bet_cards)}</div>'
            f'</div>'
        )

    day_label  = data.get("day", "Gold Cup Day")
    last_upd   = data.get("last_updated", "")
    total_bets = sum(len(r.get("bets", [])) for r in races)
    outsider_count = sum(
        1 for r in races for b in r.get("bets", [])
        if "IMPROVING OUTSIDER" in b.get("reason", "") or "PEAKING" in b.get("reason", "").upper()
    )

    return f"""<div class="pb-panel">
  <div class="pb-box">
    <h2>&#127922; Personal Bets &mdash; {day_label}
      <span style="font-size:.75rem;font-weight:400;color:var(--muted);margin-left:8px;">{total_bets} bets incl. {outsider_count} improving outsiders &middot; Updated {last_upd}</span>
    </h2>
    {chr(10).join(race_blocks)}
  </div>
</div>"""


def _build_surebet_picks_html() -> str:
    """Build the SureBet Best Picks for today panel — Gold Cup Day 2026."""
    # Static data for Day 4 Gold Cup Day — SureBet's selections per race
    # Betfair exchange decimal prices (live 10:08 UTC 13 Mar 2026)
    picks = [
        {
            "time": "13:20",
            "race": "JCB Triumph Hurdle",
            "horse": "Minella Study",
            "cloth": 11,
            "bf_dec": 7.8,
            "reason": "C+D winner Dec 2025 (only such form). Timeform #1 &#9733;&#9733;&#9733;&#9733;&#9733;",
            "badges": ["cd"],
        },
        {
            "time": "14:00",
            "race": "County Handicap Hurdle",
            "horse": "Absurde",
            "cloth": 2,
            "bf_dec": 30.0,
            "reason": "2024 County winner. Sussex Champ Hurdle Apr 25. C+D course specialist",
            "badges": ["cd"],
        },
        {
            "time": "14:40",
            "race": "Mares&#x27; Chase",
            "horse": "Dinoblue",
            "cloth": 2,
            "bf_dec": 3.15,
            "reason": "9&#215; C+D course winner. Exchange favourite 2/1. Timeform #2 &#9733;&#9733;&#9733;&#9733;&#9733;",
            "badges": ["cd"],
        },
        {
            "time": "15:20",
            "race": "Albert Bartlett",
            "horse": "Doctor Steinberg",
            "cloth": 1,
            "bf_dec": 3.9,
            "reason": "BANKER &#8212; DB gap 27pts (largest of Festival). 3/3 hurdles. Townend. Timeform #2 &#9733;&#9733;&#9733;&#9733;&#9733;",
            "badges": ["banker"],
        },
        {
            "time": "16:00",
            "race": "Cheltenham Gold Cup",
            "horse": "Jango Baie",
            "cloth": 8,
            "bf_dec": 4.6,
            "reason": "SureBet #1. Timeform #1 &#9733;&#9733;&#9733;&#9733;&#9733;. BF 4.6 (3.6/1). King George 4th. Gap=1 vs Gaelic Warrior",
            "badges": ["signal"],
        },
        {
            "time": "16:40",
            "race": "Hunters&#x27; Chase",
            "horse": "Wonderwall",
            "cloth": 7,
            "bf_dec": 10.5,
            "reason": "Defending champion. Won point Nov 2025 (fresh+first). Patrick Mullins rides",
            "badges": ["cd"],
        },
        {
            "time": "17:20",
            "race": "Martin Pipe Handicap",
            "horse": "Nurse Susan",
            "cloth": 2,
            "bf_dec": None,
            "reason": "C+D advantage. Cloth #2 (historically powerful). Market suspended pre-race",
            "badges": ["cd"],
        },
    ]

    badge_map = {
        "banker": '<span class="sbp-badge banker">BANKER</span>',
        "cd":     '<span class="sbp-badge cd">C+D</span>',
        "value":  '<span class="sbp-badge value">VALUE</span>',
        "signal": '<span class="sbp-badge signal">&#9650; SIGNAL</span>',
    }

    rows = [
        '<div class="sbp-header">Time</div>'
        '<div class="sbp-header">SureBet Pick</div>'
        '<div class="sbp-header">BF Exchange</div>'
        '<div class="sbp-header">Notes</div>'
    ]
    for p in picks:
        # Betfair odds string
        if p["bf_dec"] is not None:
            frac = f"{p['bf_dec'] - 1:.1f}/1"
            bf_str = f"{p['bf_dec']} ({frac})"
        else:
            bf_str = "Susp."

        badge_html = "".join(badge_map.get(b, "") for b in p["badges"])
        rows.append(
            f'<div class="sbp-cell time">{p["time"]}</div>'
            f'<div class="sbp-cell horse">{badge_html}#{p["cloth"]} {p["horse"]}</div>'
            f'<div class="sbp-cell odds">{bf_str}</div>'
            f'<div class="sbp-cell note">{p["reason"]}</div>'
        )

    grid_html = "\n".join(rows)
    return f"""<div class="sbp-panel">
  <div class="sbp-box">
    <h2>&#127919; SureBet Best Picks &mdash; Gold Cup Day
      <span style="font-size:.75rem;font-weight:400;color:var(--muted);margin-left:8px;">7 races &middot; Betfair Exchange prices live 10:08 UTC</span>
    </h2>
    <div class="sbp-grid">
{grid_html}
    </div>
  </div>
</div>"""


def _build_submission_html(assembled: list) -> str:
    """
    Build the 'Bumper Submission Numbers' panel.
    Shows group IDs + per-day cloth numbers for Surebet and MacFitz.
    """
    # Group races by day
    days: dict[int, list] = {}
    for race, sb, mf in assembled:
        d = race[0]
        if d not in days:
            days[d] = []
        days[d].append((race, sb, mf))

    day_label_map = {
        1: "DAY 1 — TUE",
        2: "DAY 2 — WED",
        3: "DAY 3 — THU",
        4: "DAY 4 — FRI",
    }

    def _chip(horse: str, is_split: bool, side: str) -> str:
        """Return a chip <div> for one horse with its cloth number."""
        num = RUNNER_NUMBERS.get(horse)
        num_str = str(num) if num is not None else "?"
        short_name = (horse[:9] + "…") if len(horse) > 9 else horse
        if is_split:
            cls = f"sub-horse-chip split-{side}"
            num_cls = f"chip-num split-{side}"
        else:
            cls = "sub-horse-chip"
            num_cls = "chip-num"
        return (
            f'<div class="{cls}" title="{horse}">'
            f'<span class="{num_cls}">{num_str}</span>'
            f'<span class="chip-name">{short_name}</span>'
            f'</div>'
        )

    def _flat_nums(entries: list[tuple[str, bool, str]]) -> str:
        """Comma-separated numbers string, with splits marked."""
        parts = []
        for horse, is_split, side in entries:
            num = RUNNER_NUMBERS.get(horse)
            parts.append(str(num) if num is not None else "?")
        return ", ".join(parts)

    day_rows = ""
    for d in sorted(days.keys()):
        races_today = days[d][:6]  # only first 6 races per day are required
        sb_entries = [(mf.get("surebet_horse", sb.get("horse", "?")) if mf["is_split"] else sb.get("horse", "?"), mf["is_split"], "sb") for _, sb, mf in races_today]
        mf_entries = [(mf["horse"], mf["is_split"], "mf") for _, sb, mf in races_today]

        sb_chips = "".join(_chip(horse, split, "sb") for horse, split, _ in sb_entries)
        mf_chips = "".join(_chip(horse, split, "mf") for horse, split, _ in mf_entries)
        sb_flat = _flat_nums(sb_entries)
        mf_flat = _flat_nums(mf_entries)

        day_rows += f"""
      <div class="sub-day-label">{day_label_map[d]}</div>
      <div class="sub-num-col">
        <div class="col-head sb">&#128309; Surebet &nbsp;<span class="sub-nums-flat">[ {sb_flat} ]</span></div>
        <div class="sub-num-list">{sb_chips}</div>
      </div>
      <div class="sub-num-col">
        <div class="col-head mf">&#128992; FitzMac &nbsp;<span class="sub-nums-flat">[ {mf_flat} ]</span></div>
        <div class="sub-num-list">{mf_chips}</div>
      </div>"""

    return f"""
<div class="submission-panel">
  <div class="submission-box">
    <h3>&#128203; Bumper Submission Numbers &nbsp;
      <span style="font-size:.72rem;color:var(--muted);font-weight:400;">First 6 races each day &middot; cloth numbers in race order &middot; deadline 12 noon daily</span>
    </h3>
    <div class="sub-group-row">
      <div class="sub-group-badge sb">&#128309; Surebet Group ID: {SUREBET_GROUP_ID}</div>
      <div class="sub-group-badge mf">&#128992; FitzMac Group ID: {FITZMAC_GROUP_ID}</div>
      <div style="font-size:.78rem;color:var(--muted);align-self:center;">Coloured chips = splits &nbsp;| &nbsp;<span style="color:var(--muted);">? = racecard not yet published</span></div>
    </div>
    <div class="sub-day-grid">{day_rows}
    </div>
  </div>
</div>"""


def _score_tag(score: int, css_class: str) -> str:
    cls = f'score-tag {css_class}'.strip()
    return f'<span class="{cls}">{score}</span>'


def _row_race(race, sb_pick, mf_pick, race_num: int) -> str:
    day, time, db_name, display_name, grade_css, grade_label, day_label, day_date = race
    sb_horse = sb_pick.get("horse", "?")
    sb_score = int(sb_pick.get("score", 0) or 0)
    tier_str = sb_pick.get("tier", "")
    tier_css_class, tier_color, tier_label = _tier_css(tier_str)

    is_split = mf_pick["is_split"]
    mf_horse = mf_pick["horse"]
    gap      = mf_pick["gap"]
    reason   = mf_pick.get("override_reason", "")

    # When a split override specifies a different SureBet horse, use that — not the raw DynamoDB pick
    if is_split:
        sb_horse = mf_pick.get("surebet_horse", sb_horse)
        sb_score = mf_pick.get("surebet_score", sb_score)

    score_html = _score_tag(sb_score, tier_css_class)

    tier_span = f'<span style="color:{tier_color};font-size:.8rem">{tier_label}</span>'
    grade_span = f'<span class="grade-badge {grade_css}">{grade_label}</span>'

    def _cloth(horse: str) -> str:
        """Return a small cloth-number badge if known, else empty string."""
        num = RUNNER_NUMBERS.get(horse)
        if num is None:
            return ""
        return f' <span style="display:inline-block;background:rgba(88,166,255,.18);border:1px solid rgba(88,166,255,.4);color:var(--blue);font-size:.65rem;font-weight:700;padding:0 5px;border-radius:4px;vertical-align:middle;">#{num}</span>'

    if not is_split:
        cw_note = COURSE_WINNERS.get(sb_horse, "")
        agree_text = f"Both entries agree{' &middot; ' + cw_note if cw_note else ''}"
        pick_cell = (
            f'<div class="horse-pick">{sb_horse}{_cloth(sb_horse)} '
            f'<span class="banker-tag">&#9733; BANKER</span></div>'
            f'<div class="both-agree">{agree_text}</div>'
        )
        row_class = "banker-row"
    else:
        cw_sb = COURSE_WINNERS.get(sb_horse, "")
        cw_mf = COURSE_WINNERS.get(mf_horse, "")
        sb_note = f' <span style="font-size:.7rem;color:var(--muted)">({cw_sb})</span>' if cw_sb else ""
        mf_note = f' &middot; {cw_mf}' if cw_mf else ""
        pick_cell = (
            f'<div style="display:flex;flex-direction:column;gap:4px">'
            f'<div><span style="color:var(--blue);font-size:.72rem;font-weight:700">&#128309; SUREBET:</span> '
            f'<span style="font-weight:700;color:var(--green)">{sb_horse}</span>{_cloth(sb_horse)}{sb_note}</div>'
            f'<div><span style="color:var(--orange);font-size:.72rem;font-weight:700">&#128992; FITZMAC:</span> '
            f'<span style="font-weight:700;color:var(--orange)">{mf_horse}</span>{_cloth(mf_horse)}{mf_note} '
            f'<span class="split-tag">&#9889; SPLIT</span></div>'
            f'<div style="font-size:.7rem;color:var(--muted)">{reason}</div>'
            f'</div>'
        )
        row_class = "split-row"

    return (
        f'      <tr class="{row_class}">'
        f'<td class="time-cell">{time}</td>'
        f'<td>{grade_span}</td>'
        f'<td class="race-name">{display_name}</td>'
        f'<td>{pick_cell}</td>'
        f'<td>{score_html}</td>'
        f'<td>{tier_span}</td>'
        f'</tr>\n'
    )


def _pick_list_item(num: int, horse: str, race_display: str, time: str, score: int,
                    tier_str: str, color: str, is_split: bool = False,
                    split_note: str = "") -> str:
    _, tier_color, _ = _tier_css(tier_str)
    score_color = tier_color
    split_html  = f' <span class="split-tag">&#9889; SPLIT</span>' if is_split else ""
    note_html   = f'<br><span style="font-size:.72rem;font-style:italic;color:var(--muted)">{split_note}</span>' if split_note else ""
    return (
        f'      <div class="pick-item">'
        f'<div class="pick-num">{num}</div>'
        f'<div class="pick-body">'
        f'<div style="font-weight:600;color:{color}">{horse}{split_html}</div>'
        f'<div style="font-size:.75rem;color:var(--muted)">{time} {race_display}'
        f'<span style="font-size:.7rem;font-weight:600;color:{score_color}"> &middot; {score}</span>'
        f'{note_html}</div>'
        f'</div></div>\n'
    )


def build_html(assembled: list, run_date: str, n_splits: int, new_close_calls: list,
               score_data: dict | None = None) -> str:
    # assembled: list of (race_info, sb_pick, mf_pick) in order

    # Detect day boundaries
    days_seen = []
    rows_by_day = {}
    for race, sb, mf in assembled:
        d = race[0]
        if d not in rows_by_day:
            rows_by_day[d] = []
            days_seen.append(d)
        rows_by_day[d].append((race, sb, mf))

    # Build day sections
    day_htmls = []
    for d in days_seen:
        items = rows_by_day[d]
        _, _, _, _, _, _, day_label, day_date = items[0][0]
        day_names_map = {1: "DAY 1", 2: "DAY 2", 3: "DAY 3", 4: "DAY 4"}
        header = (
            f'  <div class="day-header">'
            f'<span class="day-number">{day_names_map[d]}</span>'
            f'<span class="day-title">{day_label}</span>'
            f'<span class="day-date">{day_date}</span>'
            f'</div>\n'
        )
        thead = (
            f'  <table class="picks-table">\n'
            f'    <thead><tr><th>Time</th><th>Grade</th><th>Race</th>'
            f'<th>&#128309; Surebet &amp; &#128992; FitzMac</th>'
            f'<th>Score</th><th>Tier</th></tr></thead>\n'
            f'    <tbody>\n'
        )
        race_rows = ""
        for i, (race, sb, mf) in enumerate(items, 1):
            race_rows += _row_race(race, sb, mf, i)
        tfoot = f'    </tbody>\n  </table>\n'
        day_htmls.append(
            f'<div class="day-section">\n{header}{thead}{race_rows}{tfoot}</div>\n'
        )

    day_sections = "\n".join(day_htmls)

    # Build pick lists
    surebet_items = ""
    macfitz_items = ""
    current_day = None
    day_label_map = {1: "DAY 1 &mdash; CHAMPION DAY", 2: "DAY 2 &mdash; LADIES DAY",
                     3: "DAY 3 &mdash; ST PATRICK'S THURSDAY", 4: "DAY 4 &mdash; GOLD CUP DAY"}
    pick_num = 0
    for race, sb, mf in assembled:
        d = race[0]
        if d != current_day:
            current_day = d
            divider = f'      <div class="day-divider">{day_label_map[d]}</div>\n'
            surebet_items += divider
            macfitz_items += divider
        pick_num += 1
        time, race_display = race[1], race[3]
        sb_horse = sb.get("horse", "?")
        sb_score = int(sb.get("score", 0) or 0)
        tier_str = sb.get("tier", "")
        mf_horse = mf["horse"]
        mf_score = mf["score"]
        is_split = mf["is_split"]

        # Use override-specified SureBet horse for split rows
        if is_split:
            sb_horse = mf.get("surebet_horse", sb_horse)
            sb_score = mf.get("surebet_score", sb_score)

        surebet_items += _pick_list_item(pick_num, sb_horse, race_display, time, sb_score,
                                         tier_str, "var(--green)")
        if is_split:
            macfitz_items += _pick_list_item(pick_num, mf_horse, race_display, time, mf_score,
                                              tier_str, "var(--orange)", is_split=True,
                                              split_note=f"Surebet: {sb_horse}")
        else:
            cw = COURSE_WINNERS.get(mf_horse, "")
            note = f"&#127942; {cw}" if cw else ""
            macfitz_items += _pick_list_item(pick_num, mf_horse, race_display, time, sb_score,
                                              tier_str, "var(--orange)",
                                              split_note=note)

    n_bankers = 28 - n_splits
    if n_splits == 0:
        notice_content = (
            f'<strong>&#9733; All 28 races are BANKERS this cycle</strong> &mdash; '
            f'both Surebet and FitzMac agree on every race.'
        )
        notice_class = "notice-box"
    else:
        split_race_names = ", ".join(
            f'<em>{race[3]}</em>' for race, sb, mf in assembled if mf["is_split"]
        )
        split_details = " | ".join(
            f'{race[3]}: FitzMac &rarr; <strong>{mf["horse"]}</strong> (gap={mf["gap"]})'
            for race, sb, mf in assembled if mf["is_split"]
        )
        notice_content = (
            f'<strong>&#9733; {n_bankers} BANKERS</strong> &mdash; both entries agree. '
            f'&nbsp;<strong style="color:var(--orange)">&#9889; {n_splits} SPLIT{"S" if n_splits>1 else ""}</strong>: '
            f'{split_details}'
        )
        notice_class = "notice-box has-splits"

    new_cc_html = ""
    if new_close_calls:
        new_cc_html = (
            f'<div style="margin-top:8px;padding:8px 12px;background:rgba(248,81,73,.1);'
            f'border:1px solid rgba(248,81,73,.4);border-radius:6px;font-size:.8rem;color:#f85149;">'
            f'<strong>&#9888; NEW CLOSE CALLS (not yet in overrides):</strong> '
            + " | ".join(
                f'{r}: {h1}({s1}) vs {h2}({s2}) gap={g}'
                for r, h1, s1, h2, s2, g in new_close_calls
            ) + '</div>'
        )

    sb_footer = (
        f'      <div style="margin-top:12px;padding:8px 12px;background:rgba(88,166,255,.08);'
        f'border-radius:6px;font-size:.8rem;color:var(--muted);">'
        f'{n_bankers} bankers &middot; {n_splits} split{"s" if n_splits!=1 else ""} (see FitzMac list) '
        f'&middot; Scores from live SureBet engine {run_date}</div>\n'
    )
    mf_footer = (
        f'      <div style="margin-top:12px;padding:8px 12px;background:rgba(210,153,34,.08);'
        f'border-radius:6px;font-size:.8rem;color:var(--muted);">'
        f'{n_bankers} bankers &middot; <strong style="color:var(--orange)">{n_splits} split{"s" if n_splits!=1 else ""}</strong> '
        f'(races apply macfitz_overrides.json) &middot; &#127942; = Cheltenham course winner</div>\n'
    )

    # ── Scorecard / Leaderboard HTML ──────────────────────────────────────────
    scorecard_html = _build_scorecard_html(assembled, score_data)

    # ── Submission Numbers panel ───────────────────────────────────────────────
    submission_html = _build_submission_html(assembled)

    # ── Personal Bets + SureBet Best Picks panels ─────────────────────────────
    personal_bets_html = _build_personal_bets_html()
    surebet_picks_html = _build_surebet_picks_html()

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Barry's Cheltenham 2026 &mdash; Competition Picks</title>
<style>
{CSS}
</style>
</head>
<body>

<div class="masthead">
  <h1>Barry's Cheltenham 2026</h1>
  <div class="subtitle">Cheltenham Festival &middot; 10&ndash;13 March 2026 &middot; 28 Races &middot; Two Entries</div>
  <div>
    <span class="prize-badge">&euro;3,000 / &euro;1,250 / &euro;500 / &euro;250 Prize</span>
    <span class="updated-tag">&#10003; Live scores &mdash; {run_date}</span>
  </div>
</div>

<div class="rules-bar">
  <div class="score-pill win">&#127949; 1st = 10 pts</div>
  <div class="score-pill place">&#127948; 2nd = 5 pts</div>
  <div class="score-pill show">&#127947; 3rd = 3 pts</div>
  <div class="score-pill zero">&#10060; Unplaced = 0</div>
  <div class="score-pill zero">Max: 280 pts (28 &times; 10)</div>
  <div class="score-pill zero">6 races&nbsp;/&nbsp;day</div>
  <div class="score-pill zero">&#128344; Deadline: 12 noon daily</div>
  <div class="score-pill zero">&euro;100 entry &middot; Max 50 entries</div>
</div>

{scorecard_html}

{submission_html}

<div class="strategy-grid">
  <div class="strategy-card surebet">
    <h3>&#128309; Surebet</h3>
    <p><strong>Form-first strategy.</strong> Highest live SureBet score &mdash; best recent form, top trainer/jockey combo, class performer, course &amp; distance winner. Scores auto-refreshed <strong>every 30 mins from 9:00am UTC</strong> via Betfair Exchange (live odds).</p>
  </div>
  <div class="strategy-card macfitz">
    <h3>&#128992; FitzMac</h3>
    <p><strong>Festival specialist strategy.</strong> Follows Surebet EXCEPT in dead-heat / near-tie races where a festival specialist or course winner is within striking distance. Splits governed by <code>macfitz_overrides.json</code>.</p>
  </div>
</div>

<div class="notice-wrapper">
  <div class="{notice_class}">
    {notice_content}
  </div>
  {new_cc_html}
</div>

<div class="content">

{day_sections}

<div class="summary-section">
  <h2>&#128203; Complete Entry Lists</h2>
  <div class="summary-grid">

    <div class="solo-list">
      <h3 class="surebet-header">&#128309; SUREBET &mdash; 28 Picks</h3>
{surebet_items}
{sb_footer}
    </div>

    <div class="solo-list">
      <h3 class="macfitz-header">&#128992; FITZMAC &mdash; 28 Picks</h3>
{macfitz_items}
{mf_footer}
    </div>

  </div>
</div>

</div>

{surebet_picks_html}

{personal_bets_html}

<div class="footer">
  Barry's Cheltenham 2026 &middot; Live Betfair odds refreshed every 30 mins from 9:00am UTC &middot; {run_date} &middot; 1st: &euro;3,000 &middot; 2nd: &euro;1,250 &middot; 3rd: &euro;500 &middot; 4th: &euro;250
</div>

</body>
</html>"""
    return html


# ── main ──────────────────────────────────────────────────────────────────────
def run(dry_run: bool = False, check_only: bool = False):
    run_date = datetime.now().strftime("%d %b %Y")
    print(f"\n{'='*70}")
    print(f"  BARRY'S HTML REGEN  --  {run_date}")
    print(f"{'='*70}\n")

    print("  [1] Loading MacFitz overrides ...")
    overrides = load_overrides()
    active_overrides = {k: v for k, v in overrides.get("overrides", {}).items() if v.get("active", True)}
    print(f"      {len(active_overrides)} active manual splits loaded")

    print("  [1b] Loading race results ...")
    results = load_results()
    races_with_results = sum(1 for v in results.values() if v.get("1st", "").strip())
    print(f"       {races_with_results} races with results recorded")

    print("  [2] Fetching latest picks from CheltenhamPicks DynamoDB ...")
    db_picks = fetch_latest_picks()
    print(f"      {len(db_picks)} races found in DB")

    # Assemble in RACES order
    assembled = []
    new_close_calls = []
    n_splits = 0
    missing = []

    for race in RACES:
        db_name = race[2]
        sb_pick = db_picks.get(db_name)
        if not sb_pick:
            # Try partial match
            for key in db_picks:
                if db_name.lower() in key.lower() or key.lower() in db_name.lower():
                    sb_pick = db_picks[key]
                    break
        if not sb_pick:
            missing.append(db_name)
            sb_pick = {"horse": "TBC", "score": 0, "tier": "? UNKNOWN",
                       "race_name": db_name, "second_horse_name": "", "second_score": 0, "score_gap": 999}

        mf_pick = apply_macfitz(sb_pick, overrides)
        if mf_pick["is_split"]:
            n_splits += 1
        if mf_pick["new_close_call"]:
            h2 = sb_pick.get("second_horse_name", "?")
            s1 = int(sb_pick.get("score", 0) or 0)
            s2 = int(sb_pick.get("second_score", 0) or 0)
            new_close_calls.append((db_name, sb_pick.get("horse", "?"), s1, h2, s2, mf_pick["gap"]))

        assembled.append((race, sb_pick, mf_pick))

    if missing:
        print(f"\n  [WARN] {len(missing)} races not found in DB: {missing}")

    # Report
    n_bankers = 28 - n_splits
    print(f"\n  RESULT:  {n_bankers} bankers  |  {n_splits} splits")
    for race, sb, mf in assembled:
        if mf["is_split"]:
            print(f"    !! SPLIT  {race[1]} {race[3]:45}  Surebet={mf['surebet_horse']}  MacFitz={mf['horse']}  gap={mf['gap']}")
    if new_close_calls:
        print(f"\n  !! NEW CLOSE CALLS (not yet in overrides -- consider updating macfitz_overrides.json):")
        for r, h1, s1, h2, s2, g in new_close_calls:
            print(f"    {r}: {h1}({s1}) vs {h2}({s2}) gap={g}")

    if check_only:
        print("\n  [--check-splits]: no HTML written.")
        return

    print("\n  [3] Computing competition scores ...")
    score_data = compute_competition_scores(assembled, results)
    print(f"      Surebet: {score_data['sb_total']} pts  |  MacFitz: {score_data['mf_total']} pts  |  {score_data['races_run']} races run")

    print("\n  [4] Generating HTML ...")
    html = build_html(assembled, run_date, n_splits, new_close_calls, score_data=score_data)

    if dry_run:
        print(f"\n  [DRY RUN] Would write {len(html):,} bytes to {HTML_OUT}")
        print("  (Use without --dry-run to write the file)")
        return

    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"\n  [5] Written {len(html):,} bytes -> {HTML_OUT}")
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Regenerate Barry's Cheltenham 2026 HTML from live DynamoDB data")
    parser.add_argument("--dry-run",      action="store_true", help="Print what would change but don't write file")
    parser.add_argument("--check-splits", action="store_true", help="Show close-call report only, no HTML write")
    args = parser.parse_args()
    run(dry_run=args.dry_run, check_only=args.check_splits)

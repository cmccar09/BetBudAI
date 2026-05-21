"""
CHELTENHAM 2026 — COMPREHENSIVE WINNER PREDICTIONS
====================================================
Full cross-horse analysis for all 28 races.
Uses:
  - 10-year historical patterns (WINNERS / GOING_BY_YEAR from cheltenham_deep_analysis_2026.py)
  - Full 2026 declarations (RACES_2026 + ADDITIONAL_RUNNERS from cheltenham_full_fields_2026.py)
  - RP live odds (save_cheltenham_picks.py RP_LIVE_ODDS)
  - DynamoDB saved picks (CheltenhamPicks table)
  - Ground conditions forecast (Soft → Heavy Day 4)

Scores each horse using a layered model:
  BASE 40 + trainer + jockey + combo + festival record + form + rating +
  ground-going bonus + age + race type congruence

Run:
    python cheltenham_winner_predictions_2026.py
    python cheltenham_winner_predictions_2026.py --html          (export to HTML)
    python cheltenham_winner_predictions_2026.py --race "Gold Cup"
    python cheltenham_winner_predictions_2026.py --dynamo        (pull live from DynamoDB)
"""

import sys, os, json, argparse
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS FROM EXISTING MODULES
# ─────────────────────────────────────────────────────────────────────────────
from cheltenham_deep_analysis_2026 import WINNERS, RACES_2026, GOING_BY_YEAR, score_horse_2026
from cheltenham_full_fields_2026   import ADDITIONAL_RUNNERS

# RP_LIVE_ODDS
try:
    from save_cheltenham_picks import RP_LIVE_ODDS
except ImportError:
    RP_LIVE_ODDS = {}

# ─────────────────────────────────────────────────────────────────────────────
# GOING CORRECTION FOR 2026 (Soft / Soft-Heavy from Day 2 onwards)
# ─────────────────────────────────────────────────────────────────────────────
GOING_2026 = {
    "Day 1 (10 Mar)": "Good to Soft",
    "Day 2 (11 Mar)": "Good to Soft / Soft",
    "Day 3 (12 Mar)": "Soft",
    "Day 4 (13 Mar)": "Soft / Soft-Heavy (patches)",
}

# Trainers whose horses historically thrive on soft ground
SOFT_GROUND_BONUS_TRAINERS = {
    "Willie Mullins":    8,   # trains on soft Irish ground year-round
    "Gordon Elliott":    7,
    "Henry de Bromhead": 7,
    "Gavin Cromwell":    5,
    "Nicky Henderson":   2,
}
# Trainers whose horses may underperform on soft
SOFT_GROUND_PENALTY_TRAINERS = {
    "Dan Skelton":    -3,
    "Ben Pauling":    -2,
    "Paul Nicholls":  -2,
}
# French trainers: typically prefer faster ground
FRENCH_TRAINERS = {"Andre Fabre", "Francois Nicolle", "Thomas Fourcy", "Arnaud Chaille-Chaille"}

# ─────────────────────────────────────────────────────────────────────────────
# FULL 28 RACE SCHEDULE
# ─────────────────────────────────────────────────────────────────────────────
RACE_SCHEDULE = [
    # Day 1 — Champion Day (Tuesday 10 March)
    {"key": "d1r1",  "name": "Supreme Novices Hurdle",               "day": 1, "grade": "G1",  "type": "Novice Hurdle",      "dist": "2m",    "is_skip": False},
    {"key": "d1r2",  "name": "Arkle Challenge Trophy",               "day": 1, "grade": "G1",  "type": "Novice Chase",       "dist": "2m",    "is_skip": False},
    {"key": "d1r3",  "name": "Ultima Handicap Chase",                "day": 1, "grade": "H",   "type": "Handicap Chase",     "dist": "3m 1f", "is_skip": True},
    {"key": "d1r4",  "name": "Champion Hurdle",                      "day": 1, "grade": "G1",  "type": "Championship Hurdle","dist": "2m",    "is_skip": False},
    {"key": "d1r5",  "name": "Close Brothers Mares Hurdle",          "day": 1, "grade": "G1",  "type": "Mares Hurdle",       "dist": "2m 4f", "is_skip": False},
    {"key": "d1r6",  "name": "National Hunt Chase",                  "day": 1, "grade": "G4",  "type": "Am Chase",           "dist": "3m 6f", "is_skip": True},
    {"key": "d1r7",  "name": "Conditional Jockeys Handicap Hurdle", "day": 1, "grade": "H",   "type": "Handicap Hurdle",    "dist": "2m 4f", "is_skip": True},
    # Day 2 — Ladies Day (Wednesday 11 March)
    {"key": "d2r1",  "name": "Ballymore Novices Hurdle",             "day": 2, "grade": "G1",  "type": "Novice Hurdle",      "dist": "2m 5f", "is_skip": False},
    {"key": "d2r2",  "name": "Brown Advisory Novices Chase",         "day": 2, "grade": "G1",  "type": "Novice Chase",       "dist": "3m 1f", "is_skip": False},
    {"key": "d2r3",  "name": "Coral Cup Handicap Hurdle",            "day": 2, "grade": "H",   "type": "Handicap Hurdle",    "dist": "2m 5f", "is_skip": True},
    {"key": "d2r4",  "name": "Queen Mother Champion Chase",          "day": 2, "grade": "G1",  "type": "Championship Chase", "dist": "2m",    "is_skip": False},
    {"key": "d2r5",  "name": "Glenfarclas Cross Country Chase",      "day": 2, "grade": "spec","type": "Cross Country",      "dist": "3m 6f", "is_skip": True},
    {"key": "d2r6",  "name": "Dawn Run Mares Novices Hurdle",        "day": 2, "grade": "G2",  "type": "Mares Novice",       "dist": "2m 1f", "is_skip": False},
    {"key": "d2r7",  "name": "Champion Bumper",                      "day": 2, "grade": "G1",  "type": "NH Flat",            "dist": "2m",    "is_skip": False},
    # Day 3 — St Patrick's Eve (Thursday 12 March)
    {"key": "d3r1",  "name": "Turners Novices Chase",                "day": 3, "grade": "G1",  "type": "Novice Chase",       "dist": "2m 4f", "is_skip": False},
    {"key": "d3r2",  "name": "Pertemps Final Handicap Hurdle",       "day": 3, "grade": "H",   "type": "Handicap Hurdle",    "dist": "3m",    "is_skip": True},
    {"key": "d3r3",  "name": "Ryanair Chase",                        "day": 3, "grade": "G1",  "type": "Championship Chase", "dist": "2m 5f", "is_skip": False},
    {"key": "d3r4",  "name": "Stayers Hurdle",                       "day": 3, "grade": "G1",  "type": "Championship Hurdle","dist": "3m",    "is_skip": False},
    {"key": "d3r5",  "name": "Plate Handicap Chase",                 "day": 3, "grade": "H",   "type": "Handicap Chase",     "dist": "2m 5f", "is_skip": True},
    {"key": "d3r6",  "name": "Boodles Juvenile Handicap Hurdle",     "day": 3, "grade": "H",   "type": "Handicap Hurdle",    "dist": "2m 1f", "is_skip": True},
    {"key": "d3r7",  "name": "Martin Pipe Handicap Hurdle",          "day": 3, "grade": "H",   "type": "Handicap Hurdle",    "dist": "2m 4f", "is_skip": True},
    # Day 4 — Gold Cup Day (Friday 13 March)
    {"key": "d4r1",  "name": "JCB Triumph Hurdle",                   "day": 4, "grade": "G1",  "type": "Juvenile Hurdle",    "dist": "2m 1f", "is_skip": False},
    {"key": "d4r2",  "name": "County Handicap Hurdle",               "day": 4, "grade": "H",   "type": "Handicap Hurdle",    "dist": "2m 1f", "is_skip": True},
    {"key": "d4r3",  "name": "Albert Bartlett Novices Hurdle",       "day": 4, "grade": "G1",  "type": "Novice Hurdle",      "dist": "3m 1f", "is_skip": False},
    {"key": "d4r4",  "name": "Cheltenham Gold Cup",                  "day": 4, "grade": "G1",  "type": "Championship Chase", "dist": "3m 2f", "is_skip": False},
    {"key": "d4r5",  "name": "Grand Annual / Mares Chase",           "day": 4, "grade": "H",   "type": "Handicap Chase",     "dist": "2m",    "is_skip": True},
    {"key": "d4r6",  "name": "Foxhunter Chase",                      "day": 4, "grade": "Hunt","type": "Hunter Chase",       "dist": "3m 2f", "is_skip": True},
    {"key": "d4r7",  "name": "Champion Bumper (NH Flat)",            "day": 4, "grade": "G1",  "type": "NH Flat",            "dist": "2m",    "is_skip": False},
]

# ─────────────────────────────────────────────────────────────────────────────
# SUPPLEMENTARY RACE DATA: horses not in RACES_2026 (main module)
# Built from save_cheltenham_picks RP_LIVE_ODDS + cheltenham_full_fields_2026
# ─────────────────────────────────────────────────────────────────────────────
SUPPLEMENTARY_RACES = {
    "Ballymore Novices Hurdle": {
        "grade": "G1", "day": "Wednesday 11 March",
        "entries": [
            {"name": "No Drama This End",  "trainer": "Nicky Henderson",    "jockey": "Nico de Boinville",
             "odds": "4/1",  "age": 6, "form": "1-1-2-1",  "rating": 157, "cheltenham_record": None},
            {"name": "Skylight Hustle",    "trainer": "Willie Mullins",     "jockey": "Paul Townend",
             "odds": "6/1",  "age": 5, "form": "1-1-1",    "rating": 152, "cheltenham_record": None},
            {"name": "Doctor Steinberg",   "trainer": "Gordon Elliott",     "jockey": "Jack Kennedy",
             "odds": "3/1",  "age": 5, "form": "1-1-1",    "rating": 160, "cheltenham_record": None},
            {"name": "King Rasko Grey",    "trainer": "Paul Nicholls",      "jockey": "Harry Cobden",
             "odds": "8/1",  "age": 5, "form": "1-2-1-1",  "rating": 148, "cheltenham_record": None},
            {"name": "Act Of Innocence",   "trainer": "Joseph O'Brien",     "jockey": "Mark Walsh",
             "odds": "10/1", "age": 5, "form": "1-3-1-1",  "rating": 145, "cheltenham_record": None},
            {"name": "I'll Sort That",     "trainer": "Gary Moore",         "jockey": "Joshua Moore",
             "odds": "14/1", "age": 6, "form": "1-1-2",    "rating": 142, "cheltenham_record": None},
        ]
    },
    "Ryanair Chase": {
        "grade": "G1", "day": "Thursday 12 March",
        "entries": [
            {"name": "Fact To File",      "trainer": "Willie Mullins",     "jockey": "Paul Townend",
             "odds": "4/5",  "age": 8, "form": "1-1-1-11", "rating": 175, "cheltenham_record": "Won 2025 Ryanair Chase"},
            {"name": "Panic Attack",      "trainer": "Dan Skelton",        "jockey": "Harry Skelton",
             "odds": "20/1", "age": 7, "form": "1-1-2-21", "rating": 163, "cheltenham_record": None},
            {"name": "Protektorat",       "trainer": "Dan Skelton",        "jockey": "Harry Skelton",
             "odds": "25/1", "age": 11,"form": "1-2-3-P1", "rating": 161, "cheltenham_record": "Placed 2022 RSA; 2023 Ryanair"},
            {"name": "Jagwar",            "trainer": "Nicky Henderson",    "jockey": "Nico de Boinville",
             "odds": "25/1", "age": 7, "form": "1-3-2-51", "rating": 167, "cheltenham_record": None},
            {"name": "Energumene",        "trainer": "Willie Mullins",     "jockey": "Mark Walsh",
             "odds": "40/1", "age": 11,"form": "1-1-1-21", "rating": 172, "cheltenham_record": "Won 2022 QMCC; Won 2023 QMCC; Won 2025 QMCC"},
            {"name": "Better Days Ahead", "trainer": "Willie Mullins",     "jockey": "Patrick Mullins",
             "odds": "50/1", "age": 7, "form": "1-1-2-31", "rating": 157, "cheltenham_record": None},
            {"name": "Edwardstone",       "trainer": "Alan King",          "jockey": "Tom Cannon",
             "odds": "100/1","age": 11,"form": "2-P-3-P1", "rating": 156, "cheltenham_record": "Won 2022 Arkle"},
            {"name": "Croke Park",        "trainer": "Tony Martin",        "jockey": "Robbie Power",
             "odds": "100/1","age": 8, "form": "3-4-2-31", "rating": 154, "cheltenham_record": None},
        ]
    },
    "JCB Triumph Hurdle": {
        "grade": "G1", "day": "Friday 13 March",
        "entries": [
            {"name": "Proactif",       "trainer": "Francois Nicolle",   "jockey": "Pierre-Louis Bicocchi",
             "odds": "7/2",  "age": 4, "form": "1-1-1-1",  "rating": 142, "cheltenham_record": None},
            {"name": "Selma De Vary",  "trainer": "Willie Mullins",     "jockey": "Paul Townend",
             "odds": "9/2",  "age": 4, "form": "1-1-1",    "rating": 137, "cheltenham_record": None},
            {"name": "Minella Study",  "trainer": "Nicky Henderson",    "jockey": "Nico de Boinville",
             "odds": "7/1",  "age": 4, "form": "1-1-2-1",  "rating": 135, "cheltenham_record": None},
            {"name": "Maestro Conti",  "trainer": "Gordon Elliott",     "jockey": "Jack Kennedy",
             "odds": "15/2", "age": 4, "form": "1-2-1-1",  "rating": 134, "cheltenham_record": None},
            {"name": "Winston Junior", "trainer": "Willie Mullins",     "jockey": "Mark Walsh",
             "odds": "13/2", "age": 4, "form": "1-1-1",    "rating": 133, "cheltenham_record": None},
            {"name": "Mange Tout",     "trainer": "Nicky Henderson",    "jockey": "James Bowen",
             "odds": "8/1",  "age": 4, "form": "1-1-2-21", "rating": 132, "cheltenham_record": None},
            {"name": "Macho Man",      "trainer": "Gordon Elliott",     "jockey": "Jack Kennedy",
             "odds": "8/1",  "age": 4, "form": "1-3-1-21", "rating": 130, "cheltenham_record": None},
        ]
    },
    "Albert Bartlett Novices Hurdle": {
        "grade": "G1", "day": "Friday 13 March",
        "entries": [
            {"name": "Panda Boy",        "trainer": "Willie Mullins",    "jockey": "Paul Townend",
             "odds": "3/1",  "age": 6, "form": "1-1-1",    "rating": 156, "cheltenham_record": None},
            {"name": "Magical Zoe",      "trainer": "Emmet Mullins",     "jockey": "Danny Mullins",
             "odds": "7/2",  "age": 5, "form": "1-1-1-1",  "rating": 153, "cheltenham_record": None},
            {"name": "Good Time Jonny",  "trainer": "Nicky Henderson",   "jockey": "Nico de Boinville",
             "odds": "9/2",  "age": 6, "form": "1-2-1-1",  "rating": 149, "cheltenham_record": None},
            {"name": "Inver Park",       "trainer": "Gordon Elliott",    "jockey": "Jack Kennedy",
             "odds": "6/1",  "age": 6, "form": "1-1-2-1",  "rating": 147, "cheltenham_record": None},
            {"name": "Henry Higgins",    "trainer": "Willie Mullins",    "jockey": "Patrick Mullins",
             "odds": "10/1", "age": 6, "form": "1-1-2-21", "rating": 145, "cheltenham_record": None},
            {"name": "Slade Steel",      "trainer": "Paul Nicholls",     "jockey": "Harry Cobden",
             "odds": "12/1", "age": 6, "form": "1-2-1-31", "rating": 143, "cheltenham_record": None},
        ]
    },
    "Turners Novices Chase": {
        "grade": "G1", "day": "Thursday 12 March",
        "entries": [
            {"name": "Koktail Divin",      "trainer": "Willie Mullins",    "jockey": "Paul Townend",
             "odds": "9/2",  "age": 7, "form": "1-1-1-22", "rating": 162, "cheltenham_record": None},
            {"name": "Regent's Stroll",    "trainer": "Nicky Henderson",   "jockey": "Nico de Boinville",
             "odds": "6/1",  "age": 6, "form": "1-1-1-11", "rating": 165, "cheltenham_record": None},
            {"name": "Meetmebythesea",     "trainer": "Gordon Elliott",    "jockey": "Jack Kennedy",
             "odds": "6/1",  "age": 7, "form": "1-2-1-21", "rating": 163, "cheltenham_record": None},
            {"name": "Slade Steel",        "trainer": "Paul Nicholls",     "jockey": "Harry Cobden",
             "odds": "9/1",  "age": 6, "form": "1-1-2-31", "rating": 158, "cheltenham_record": None},
            {"name": "Sixmilebridge",      "trainer": "Willie Mullins",    "jockey": "Mark Walsh",
             "odds": "9/1",  "age": 7, "form": "1-1-1-42", "rating": 157, "cheltenham_record": None},
            {"name": "Waterford Whispers", "trainer": "Henry de Bromhead", "jockey": "Jack Kennedy",
             "odds": "12/1", "age": 7, "form": "1-2-1-31", "rating": 155, "cheltenham_record": None},
        ]
    },
    "Dawn Run Mares Novices Hurdle": {
        "grade": "G2", "day": "Wednesday 11 March",
        "entries": [
            {"name": "Bambino Fever",    "trainer": "Willie Mullins",    "jockey": "Paul Townend",
             "odds": "4/5",  "age": 5, "form": "1-1-1",    "rating": 142, "cheltenham_record": None},
            {"name": "Oldschool Outlaw", "trainer": "Joseph O'Brien",   "jockey": "Mark Walsh",
             "odds": "4/1",  "age": 5, "form": "1-2-1-1",  "rating": 136, "cheltenham_record": None},
            {"name": "Echoing Silence",  "trainer": "Gordon Elliott",   "jockey": "Jack Kennedy",
             "odds": "10/1", "age": 5, "form": "1-2-1-31", "rating": 130, "cheltenham_record": None},
            {"name": "La Conquiere",     "trainer": "Nicky Henderson",  "jockey": "Nico de Boinville",
             "odds": "14/1", "age": 5, "form": "1-1-3-21", "rating": 127, "cheltenham_record": None},
        ]
    },
    "Ultima Handicap Chase": {
        "grade": "H", "day": "Tuesday 10 March",
        "entries": [
            {"name": "Fastorslow",      "trainer": "Nicky Henderson",    "jockey": "Nico de Boinville",
             "odds": "40/1", "age": 9, "form": "3-1-2-21", "rating": 147, "cheltenham_record": None},
            {"name": "Banbridge",       "trainer": "Gordon Elliott",     "jockey": "Jack Kennedy",
             "odds": "40/1", "age": 12,"form": "1-P-1-21", "rating": 145, "cheltenham_record": "Placed 2024"},
            {"name": "Nick Rockett",    "trainer": "Gordon Elliott",     "jockey": "Jack Kennedy",
             "odds": "40/1", "age": 9, "form": "1-2-1-31", "rating": 143, "cheltenham_record": None},
            {"name": "Impaire Et Passe","trainer": "Philippe Peltier",   "jockey": "TBD",
             "odds": "66/1", "age": 10,"form": "2-3-1-P2", "rating": 140, "cheltenham_record": None},
        ]
    },
    "National Hunt Chase": {
        "grade": "G4", "day": "Tuesday 10 March",
        "entries": [
            {"name": "Backmersackme",   "trainer": "Henry de Bromhead",  "jockey": "Jack Kennedy",
             "odds": "9/2",  "age": 7, "form": "1-1-1",    "rating": 135, "cheltenham_record": None},
        ]
    },
    "Foxhunter Chase": {
        "grade": "H", "day": "Friday 13 March",
        "entries": [
            {"name": "Lecky Watson",    "trainer": "Stephanie Sykes",    "jockey": "Derek O'Connor",
             "odds": "100/1","age": 10,"form": "1-1-2-1",  "rating": 130, "cheltenham_record": None},
        ]
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# COMPREHENSIVE SCORING ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def odds_to_decimal(odds_str):
    """Convert fractional or decimal odds string to decimal float."""
    if not odds_str or odds_str == "?":
        return 20.0
    try:
        if "/" in odds_str:
            n, d = odds_str.split("/")
            return int(n) / int(d) + 1
        return float(odds_str)
    except:
        return 20.0


def going_bonus(horse):
    """Apply 2026 ground-conditions adjustment."""
    trainer = horse.get("trainer", "")
    bonus   = 0
    note    = ""

    # Check if French trainer (penalise on soft)
    if trainer in FRENCH_TRAINERS:
        bonus -= 8
        note = f"French trainer {trainer}: -8 (soft penalty)"
    elif trainer in SOFT_GROUND_BONUS_TRAINERS:
        b = SOFT_GROUND_BONUS_TRAINERS[trainer]
        bonus += b
        note = f"Soft-ground specialist {trainer}: +{b}"
    elif trainer in SOFT_GROUND_PENALTY_TRAINERS:
        b = SOFT_GROUND_PENALTY_TRAINERS[trainer]
        bonus += b
        note = f"Ground concern {trainer}: {b}"

    return bonus, note


def score_horse_comprehensive(horse, race_meta):
    """
    Full scoring: base + trainer + jockey + combo + festival record +
    form + rating + going bonus + age + race-type fit + historical signal.
    Returns (score, reasons_list, warnings_list)
    """
    score    = 40
    reasons  = []
    warnings = []

    trainer = horse.get("trainer", "")
    jockey  = horse.get("jockey", "")
    form    = horse.get("form", "") or ""
    rating  = horse.get("rating", 0) or 0
    age     = horse.get("age",    0) or 0
    record  = horse.get("cheltenham_record", "") or ""

    # ── 1. TRAINER ────────────────────────────────────────────────────────────
    trainer_pts = {
        "Willie Mullins":       25,
        "Nicky Henderson":      20,
        "Gordon Elliott":       18,
        "Henry de Bromhead":    15,
        "Gavin Cromwell":       12,
        "Emmet Mullins":        10,
        "Joseph O'Brien":        9,
        "Joseph Patrick O'Brien":9,
        "Paul Nicholls":         8,
        "Alan King":             8,
        "Emma Lavelle":          8,
        "Rebecca Curtis":        7,
        "Ben Pauling":           7,
        "Dan Skelton":           8,
        "Jeremy Scott":          6,
        "Paul Nolan":            6,
        "Gary Moore":            5,
        "Thomas Mullins":        8,
        "Tony Martin":           5,
        "Peter Fahey":           8,
        "Gavin Cromwell":       12,
    }
    tp = trainer_pts.get(trainer, 4)
    score += tp
    reasons.append(f"Trainer {trainer}: +{tp}")

    # ── 2. JOCKEY ─────────────────────────────────────────────────────────────
    jockey_pts = {
        "Paul Townend":           20,
        "Nico de Boinville":      15,
        "Jack Kennedy":           12,
        "Rachael Blackmore":      12,
        "Mark Walsh":              8,
        "Danny Mullins":           8,
        "Patrick Mullins":         8,
        "Davy Russell":            7,
        "Harry Cobden":            6,
        "Tom Cannon":              6,
        "Aidan Coleman":           6,
        "Keith Donoghue":          6,
        "Harry Skelton":           7,
        "Felix de Giles":          4,
        "Bryan Cooper":            6,
        "Jonjo O'Neill Jr":        5,
        "Adam Wedge":              5,
        "Joshua Moore":            4,
        "James Bowen":             5,
        "Pierre-Louis Bicocchi":   5,
        "Robbie Power":            5,
        "Derek O'Connor":          4,
    }
    jp = jockey_pts.get(jockey, 3)
    score += jp
    reasons.append(f"Jockey {jockey}: +{jp}")

    # ── 3. ELITE COMBO ────────────────────────────────────────────────────────
    combos = {
        ("Willie Mullins",    "Paul Townend"):        15,
        ("Nicky Henderson",   "Nico de Boinville"):   12,
        ("Gordon Elliott",    "Jack Kennedy"):         8,
        ("Henry de Bromhead", "Rachael Blackmore"):    8,
        ("Gavin Cromwell",    "Danny Mullins"):         8,
        ("Dan Skelton",       "Harry Skelton"):         6,
        ("Willie Mullins",    "Patrick Mullins"):       8,
        ("Willie Mullins",    "Mark Walsh"):            8,
        ("Gordon Elliott",    "Davy Russell"):          5,
    }
    cb = combos.get((trainer, jockey), 0)
    if cb:
        score += cb
        reasons.append(f"Elite combo: +{cb}")

    # ── 4. PREVIOUS FESTIVAL RECORD ───────────────────────────────────────────
    if record:
        won_count  = record.lower().count("won")
        placed_count = sum(1 for p in ["2nd", "3rd", "placed"] if p in record.lower())
        prev_trial = 0
        if won_count >= 2:
            prev_trial = 25
            reasons.append(f"Multi-Festival winner (+{prev_trial}): {won_count} wins")
        elif won_count == 1:
            prev_trial = 20
            reasons.append(f"Previous Festival winner (+{prev_trial}): {record[:60]}")
        elif placed_count:
            prev_trial = 10
            reasons.append(f"Previous Festival placed (+{prev_trial}): {record[:60]}")
        score += prev_trial

    # ── 5. CURRENT FORM ───────────────────────────────────────────────────────
    form_clean = form.replace("-", "").replace(" ", "")
    if form_clean:
        # Recent form is left to right = oldest to newest (most-recent-first notation reversed)
        wins = form_clean.count("1")
        last = form_clean[-1]  # most recent run
        if last == "1":
            score += 18
            reasons.append("Won last run: +18")
        elif last == "2":
            score += 10
            reasons.append("2nd last run: +10")
        elif last == "3":
            score += 5
            reasons.append("3rd last run: +5")
        elif last in ("P", "U", "F"):
            score -= 10
            warnings.append(f"Last run: {last} (pulled up/fell/unseated): -10")
        elif last == "0":
            score -= 8
            warnings.append("Last run: unplaced: -8")

        # Unbeaten sequence (3+ runs all 1s)
        if wins >= 3 and "P" not in form_clean and "0" not in form_clean and "F" not in form_clean:
            score += 12
            reasons.append(f"Unbeaten run ({wins} wins): +12")

    # ── 6. OFFICIAL RATING ────────────────────────────────────────────────────
    if rating:
        if rating >= 180:
            score += 30; reasons.append(f"Rating {rating} (elite): +30")
        elif rating >= 175:
            score += 25; reasons.append(f"Rating {rating} (top class): +25")
        elif rating >= 170:
            score += 20; reasons.append(f"Rating {rating} (top class): +20")
        elif rating >= 165:
            score += 15; reasons.append(f"Rating {rating} (high class): +15")
        elif rating >= 160:
            score += 12; reasons.append(f"Rating {rating} (very good): +12")
        elif rating >= 155:
            score += 9;  reasons.append(f"Rating {rating} (good): +9")
        elif rating >= 150:
            score += 7;  reasons.append(f"Rating {rating} (solid): +7")
        elif rating >= 145:
            score += 5;  reasons.append(f"Rating {rating}: +5")
        elif rating >= 140:
            score += 3;  reasons.append(f"Rating {rating}: +3")

    # ── 7. AGE (race-type appropriate) ────────────────────────────────────────
    race_type = race_meta.get("type", "")
    if "Gold Cup" in race_type or "Championship Chase" in race_type:
        # Sweet spot 8-9 for Gold Cup
        if age in (8, 9):
            score += 8; reasons.append(f"Age {age}: Gold Cup sweet spot +8")
        elif age in (7, 10):
            score += 3; reasons.append(f"Age {age}: acceptable age +3")
        elif age >= 11:
            score -= 5; warnings.append(f"Age {age}: possibly over the hill -5")
    elif "Novice" in race_type or "NH Flat" in race_type:
        if age in (5, 6):
            score += 6; reasons.append(f"Age {age}: ideal novice age +6")
        elif age == 7:
            score += 3; reasons.append(f"Age {age}: acceptable novice age +3")
        elif age >= 8:
            score -= 4; warnings.append(f"Age {age}: old for a novice -4")
    elif "Juvenile" in race_type:
        if age == 4:
            score += 5; reasons.append(f"Age {age}: juvenile horse correct age +5")

    # ── 8. GOING ADJUSTMENT (2026 soft/heavy forecast) ────────────────────────
    g_bonus, g_note = going_bonus(horse)
    if g_bonus:
        score += g_bonus
        if g_bonus > 0:
            reasons.append(f"Ground bonus: {g_note}")
        else:
            warnings.append(f"Ground concern: {g_note}")

    # ── 9. ODDS (implied market confidence) ───────────────────────────────────
    raw_odds  = horse.get("odds", "")
    if not raw_odds or raw_odds == "?":
        raw_odds = RP_LIVE_ODDS.get(horse.get("name", "").lower(), "")
    dec_odds = odds_to_decimal(raw_odds)
    if dec_odds <= 2.0:
        score += 15; reasons.append(f"Market fav ({raw_odds}): +15")
    elif dec_odds <= 3.0:
        score += 12; reasons.append(f"Strong market ({raw_odds}): +12")
    elif dec_odds <= 5.0:
        score += 8;  reasons.append(f"Fav-ish price ({raw_odds}): +8")
    elif dec_odds <= 8.0:
        score += 5;  reasons.append(f"Reasonable price ({raw_odds}): +5")
    elif dec_odds <= 15.0:
        score += 2;  reasons.append(f"Outsider price ({raw_odds}): +2")
    # No penalty for 16/1+ — can win at any price at Cheltenham

    # ── 10. HISTORICAL PATTERN CROSS-MATCH ────────────────────────────────────
    # Check if this trainer/race combination has won the same race in last 10 years
    race_name = race_meta.get("name", "")
    hist_wins = 0
    for yr, yr_data in WINNERS.items():
        for hist_race, hist_data in yr_data.items():
            # Rough name match
            if any(k in race_name for k in hist_race.split()[:2]) or any(k in hist_race for k in race_name.split()[:2]):
                if hist_data["trainer"] == trainer:
                    hist_wins += 1
    if hist_wins >= 3:
        score += 12; reasons.append(f"Historical: {trainer} won this race {hist_wins}x in 10yrs +12")
    elif hist_wins == 2:
        score += 8;  reasons.append(f"Historical: {trainer} won this race twice +8")
    elif hist_wins == 1:
        score += 4;  reasons.append(f"Historical: {trainer} won this race before +4")

    return round(score, 1), reasons, warnings


# ─────────────────────────────────────────────────────────────────────────────
# BUILD FULL RACE FIELDS
# ─────────────────────────────────────────────────────────────────────────────

STOP_WORDS = {"hurdle", "hurdles", "chase", "novices", "novice", "the",
              "of", "a", "an", "de", "brothers", "challenge", "trophy",
              "handicap", "mares", "jcb", "close", "albert", "st"}

def race_name_match(target, candidate):
    """
    Return match score between two race names.
    Uses only the DISTINCTIVE words (not stop words).
    Requires at least 2 distinctive words to match for a positive hit.
    NOTE: Exact / substring checks run BEFORE stop-word filtering so that
    races whose names consist entirely of stop words (e.g. "Close Brothers
    Mares Hurdle") still match correctly.
    """
    t_lo = target.lower()
    c_lo = candidate.lower()

    # Exact full match — must be checked FIRST (before stop-word filtering)
    if t_lo == c_lo:
        return True
    # One is contained in the other (substring)
    if t_lo in c_lo or c_lo in t_lo:
        return True

    def distinctive(name):
        return {w.lower() for w in name.split()
                if w.lower() not in STOP_WORDS and len(w) > 2}

    t_words = distinctive(target)
    c_words = distinctive(candidate)
    if not t_words or not c_words:
        return False
    # At least 2 distinctive words match
    common = t_words & c_words
    return len(common) >= 2


def build_race_field(race_sched):
    """
    Merge all sources for a given race into a single list of horses.
    Sources: SUPPLEMENTARY_RACES first (exact match), then RACES_2026, then ADDITIONAL_RUNNERS.
    """
    name = race_sched["name"]
    horses = []
    seen  = set()

    def add_horse(h):
        k = h.get("name", "").strip().lower()
        if k and k not in seen:
            seen.add(k)
            horses.append(h)

    # Source 1: SUPPLEMENTARY_RACES (exact / high-fidelity match first)
    for r_name, r_data in SUPPLEMENTARY_RACES.items():
        if race_name_match(name, r_name):
            for h in r_data.get("entries", []):
                add_horse(h)

    # Source 2: RACES_2026 (championship races — exact/high-fidelity match)
    for r_name, r_data in RACES_2026.items():
        if race_name_match(name, r_name):
            for h in r_data.get("entries", []):
                add_horse(h)

    # Source 3: ADDITIONAL_RUNNERS (from cheltenham_full_fields_2026)
    key = race_sched["key"].replace("d", "day").replace("r", "_race")
    for ar_key, ar_list in ADDITIONAL_RUNNERS.items():
        if ar_key == key:
            for h in ar_list:
                add_horse(h)

    # Fill odds from RP_LIVE_ODDS for any horse missing odds
    for h in horses:
        if not h.get("odds") or h["odds"] == "?":
            live = RP_LIVE_ODDS.get(h["name"].lower().strip(), "")
            if live:
                h["odds"] = live

    return horses


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyse_all_races(filter_race=None):
    """Score every horse in every race; return sorted results."""
    results = {}

    for race in RACE_SCHEDULE:
        name = race["name"]
        if filter_race and filter_race.lower() not in name.lower():
            continue

        field = build_race_field(race)
        if not field:
            results[name] = {"race": race, "horses": [], "winner": None}
            continue

        scored = []
        for h in field:
            sc, reasons, warnings = score_horse_comprehensive(h, race)
            scored.append({
                "name":     h.get("name", "Unknown"),
                "trainer":  h.get("trainer", ""),
                "jockey":   h.get("jockey", ""),
                "odds":     h.get("odds", "?"),
                "age":      h.get("age", 0),
                "form":     h.get("form", ""),
                "rating":   h.get("rating", 0),
                "record":   h.get("cheltenham_record", "") or "",
                "score":    sc,
                "reasons":  reasons,
                "warnings": warnings,
            })

        scored.sort(key=lambda x: x["score"], reverse=True)

        results[name] = {
            "race":   race,
            "horses": scored,
            "winner": scored[0] if scored else None,
            "gap":    (scored[0]["score"] - scored[1]["score"]) if len(scored) > 1 else 0,
        }

    return results


# ─────────────────────────────────────────────────────────────────────────────
# CROSS-HORSE COMPARISON (horses running in multiple races)
# ─────────────────────────────────────────────────────────────────────────────

def cross_horse_analysis(results):
    """Identify horses declared in multiple races and cross-compare scores."""
    horse_races = defaultdict(list)
    for race_name, r in results.items():
        for h in r["horses"]:
            horse_races[h["name"].lower()].append({
                "race":    race_name,
                "score":   h["score"],
                "trainer": h["trainer"],
            })

    dual_entries = {k: v for k, v in horse_races.items() if len(v) > 1}
    return dual_entries


# ─────────────────────────────────────────────────────────────────────────────
# HISTORICAL COMPARISON — 10-year trainer/form patterns vs our 2026 picks
# ─────────────────────────────────────────────────────────────────────────────

def historical_trainer_races():
    """Count trainer wins by race-type from 10-year WINNERS data."""
    tr_race = defaultdict(Counter)
    for yr, yr_data in WINNERS.items():
        for race, data in yr_data.items():
            tr_race[data["trainer"]][race] += 1
    return tr_race


def previous_race_type_analysis():
    """
    What types of races did eventual Cheltenham winners run in before the festival?
    From 10-yr data: track last race form + what race type they came from.
    Pattern extraction from available data.
    """
    prep_patterns = {
        "Champion Hurdle":           ["Grade 1 Champion Trial", "Contenders Hurdle", "Irish Champion Hurdle"],
        "Gold Cup":                  ["Savills Chase", "King George VI", "Denman Chase", "Irish Gold Cup"],
        "Stayers Hurdle":            ["Long Walk Hurdle", "Liverpool Hurdle", "Galmoy Hurdle"],
        "Queen Mother Champion Chase":["Clarence House Chase","Grade 1 2m Chase"],
        "Arkle Challenge Trophy":    ["Grade 1 Novice Chase","Dublin Racing Festival"],
        "Supreme Novices Hurdle":    ["Grade 1 Novice Hurdle","Russian Hero/Tattersalls"],
        "Champion Bumper":           ["Grade 1 INH Bumper", "Grade 1 Bumper"],
        "Ryanair Chase":             ["Old Roan", "Grade 1 Chase 2m4f-2m5f"],
        "JCB Triumph Hurdle":        ["Leopardstown Juvenile", "Spring Juvenile Hurdle"],
        "Albert Bartlett":           ["Pertemps Qualifier", "Grade 2 Staying Novice"],
        "Ballymore":                 ["Grade 1 Novice Hurdle 2m4-2m5f", "Spring Juvenile"],
        "Turners Novices Chase":     ["Grade 1 Novice Chase 2m4f"],
    }
    return prep_patterns


# ─────────────────────────────────────────────────────────────────────────────
# PULL FROM DYNAMODB
# ─────────────────────────────────────────────────────────────────────────────

def pull_dynamodb_picks():
    """Fetch latest picks from CheltenhamPicks DynamoDB table."""
    try:
        import boto3
        dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
        table    = dynamodb.Table('CheltenhamPicks')
        resp     = table.scan()
        items    = resp.get('Items', [])
        # Sort by score desc per race
        picks = {}
        for item in items:
            rn = item.get('race_name', '')
            if rn not in picks or float(item.get('score', 0)) > float(picks[rn].get('score', 0)):
                picks[rn] = item
        return picks
    except Exception as e:
        print(f"  [DynamoDB] Could not connect: {e}")
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# PRINT OUTPUT
# ─────────────────────────────────────────────────────────────────────────────

DAY_NAMES = {1: "CHAMPION DAY", 2: "LADIES DAY", 3: "ST PATRICK'S EVE", 4: "GOLD CUP DAY"}
DAY_DATES = {1: "Tue 10 Mar", 2: "Wed 11 Mar", 3: "Thu 12 Mar", 4: "Fri 13 Mar"}

def stars(score):
    if score >= 180: return "★★★★★"
    if score >= 160: return "★★★★☆"
    if score >= 140: return "★★★☆☆"
    if score >= 120: return "★★☆☆☆"
    return "★☆☆☆☆"

def conf(score):
    if score >= 175: return "ELITE CONFIDENCE"
    if score >= 160: return "HIGH CONFIDENCE"
    if score >= 145: return "STRONG"
    if score >= 130: return "SOLID"
    if score >= 115: return "MODERATE"
    return "LOW"

def print_results(results, dynamo_picks=None, verbose=False):
    prev_day = None

    for race in RACE_SCHEDULE:
        name = race["name"]
        if name not in results:
            continue
        r = results[name]
        day = race["day"]
        horses  = r["horses"]
        winner  = r["winner"]
        gap     = r.get("gap", 0)
        is_skip = race["is_skip"]
        grade   = race["grade"]

        # Day header
        if day != prev_day:
            going = GOING_2026.get(f"Day {day} ({['','10 Mar','11 Mar','12 Mar','13 Mar'][day]})", "")
            print(f"\n{'━'*90}")
            print(f"  {'🏁'} DAY {day} — {DAY_NAMES[day].upper()}  ·  {DAY_DATES[day]}  ·  Going: {going}")
            print(f"{'━'*90}")
            prev_day = day

        # Race header
        grade_label = f"[{grade}]" if grade else ""
        skip_tag    = " [SKIP — OPINION ONLY]" if is_skip else ""
        print(f"\n  {'─'*86}")
        print(f"  {grade_label:8} {name}{skip_tag}")
        print(f"  {'─'*86}")

        if not horses:
            print(f"    ⚠  No declarations data available")
            continue

        # Print top 5 horses
        top5 = horses[:5]
        for i, h in enumerate(top5):
            rank_icon = ["🥇","🥈","🥉","4️⃣ ","5️⃣ "][i]
            rec   = f" [{h['record'][:50]}]" if h["record"] else ""
            warns = " ⚠ " + "; ".join(h["warnings"][:2]) if h["warnings"] else ""
            print(f"    {rank_icon} {h['name']:<28} Score:{h['score']:>6.0f}  Odds:{h['odds']:>8}  "
                  f"Age:{h['age']}  RPR:{h['rating']:>3}  Form:{h['form']:{12}}"
                  f"  {conf(h['score'])}")
            if i == 0:
                print(f"         Trainer: {h['trainer']}  |  Jockey: {h['jockey']}")
                if h["record"]:
                    print(f"         Festival record: {h['record'][:80]}")
                if verbose and h["reasons"]:
                    print(f"         Scoring: {' | '.join(h['reasons'][:4])}")
                if h["warnings"]:
                    print(f"         {warns}")

        # More horses
        if len(horses) > 5:
            others = horses[5:]
            print(f"    {'─'*80}")
            print(f"    Others in field ({len(others)}):")
            for h in others:
                print(f"       • {h['name']:<26} {h['trainer']:<25} Score:{h['score']:>5.0f}  "
                      f"Odds:{h['odds']:>7}  Form:{h['form']}")

        # Winner call
        if winner:
            skip_note = "[OPINION ONLY — not a betting pick]" if is_skip else ""
            print(f"\n    🎯 PREDICTED WINNER: {winner['name'].upper():<28} "
                  f"{stars(winner['score'])}  {conf(winner['score'])}  "
                  f"(Score: {winner['score']:.0f}, Gap: {gap:.0f}pts)  {skip_note}")
            second_name = horses[1]["name"] if len(horses) > 1 else "—"
            if gap >= 20:
                print(f"    ✅ CLEAR LEADER — gap of {gap:.0f} points over 2nd ({second_name})")
            elif gap >= 10:
                print(f"    ⚠  Moderate margin — worth watching {second_name} each-way")
            elif len(horses) > 1:
                print(f"    ⚡ TIGHT RACE — {second_name} only {gap:.0f}pts behind, possible upset")

        # DynamoDB cross-reference
        if dynamo_picks:
            db_pick = dynamo_picks.get(name)
            if db_pick:
                db_horse = db_pick.get('horse', '?')
                db_score = db_pick.get('score', '?')
                db_tier  = db_pick.get('bet_tier', '?')
                match = "✓ MATCH" if winner and db_horse.lower() == winner['name'].lower() else "≠ DIFFERENT"
                print(f"    📦 DynamoDB stored: {db_horse} (score: {db_score}, tier: {db_tier}) {match}")


def print_winner_summary(results, dynamo_picks=None):
    """Print compact one-line-per-race winner summary."""
    print(f"\n{'═'*90}")
    print(f"  CHELTENHAM 2026 — COMPLETE WINNER PREDICTIONS SUMMARY")
    print(f"  Ground: Day1 G/S → Day2 G/S-S → Day3 Soft → Day4 Soft/Soft-Heavy")
    print(f"{'═'*90}")
    print(f"  {'#':<3} {'Race':<38} {'Winner':<28} {'Score':>6} {'Odds':>8} {'Trainer'}")
    print(f"  {'─'*88}")

    race_count = 0
    for race in RACE_SCHEDULE:
        name = race["name"]
        if name not in results:
            continue
        r = results[name]
        winner = r["winner"]
        if not winner:
            continue
        race_count += 1
        day  = race["day"]
        skip = "  [skip]" if race["is_skip"] else ""
        tier = "🎯" if not race["is_skip"] else "📋"
        day_marker = f"D{day}"

        db_flag = ""
        if dynamo_picks:
            db_pick = dynamo_picks.get(name)
            if db_pick:
                db_horse = db_pick.get('horse', '?')
                db_flag = " ✓DB" if db_horse.lower() == winner['name'].lower() else f" ≠{db_horse}"

        print(f"  {tier} {day_marker} {name:<36} {winner['name']:<28} {winner['score']:>6.0f} "
              f"{winner['odds']:>8}  {winner['trainer']}{skip}{db_flag}")

    print(f"  {'─'*88}")
    print(f"  Total: {race_count} races predicted\n")

    # Top conviction betting picks
    print(f"  TOP CONVICTION PLAYS (Grade 1, not skip, gap ≥ 15pts):")
    print(f"  {'─'*70}")
    for race in RACE_SCHEDULE:
        if race["is_skip"] or race["grade"] not in ("G1", "G2"):
            continue
        name = race["name"]
        if name not in results:
            continue
        r = results[name]
        if not r["winner"] or r.get("gap", 0) < 15:
            continue
        w = r["winner"]
        print(f"    🔥 {name:<36} → {w['name']:<26} {w['odds']:>8}  Score:{w['score']:.0f}  Gap:{r['gap']:.0f}pts")


def print_cross_horse(dual):
    """Print cross-race horse analysis."""
    if not dual:
        return
    print(f"\n{'═'*90}")
    print(f"  CROSS-RACE DECLARATIONS (horses in multiple races)")
    print(f"{'═'*90}")
    for horse, entries in dual.items():
        print(f"\n  🐎 {horse.title()}")
        for e in entries:
            print(f"     → {e['race']:<40} Score: {e['score']:.0f}  Trainer: {e['trainer']}")


def print_historical_context(results):
    """Print historical pattern match for top picks."""
    tr_race = historical_trainer_races()
    prep    = previous_race_type_analysis()

    print(f"\n{'═'*90}")
    print(f"  HISTORICAL CONTEXT — TRAINER DOMINANCE BY RACE")
    print(f"{'═'*90}")

    for race in RACE_SCHEDULE:
        if race["is_skip"] or race["grade"] not in ("G1",):
            continue
        name = race["name"]
        if name not in results:
            continue
        r   = results[name]
        win = r["winner"]
        if not win:
            continue

        # Find historical wins for trainer in this race
        trainer = win["trainer"]
        hist = 0
        for yr, yr_data in WINNERS.items():
            for rn, rd in yr_data.items():
                if any(k in name for k in rn.split()[:2]) or any(k in rn for k in name.split()[:2]):
                    if rd["trainer"] == trainer:
                        hist += 1

        # Prep race pattern
        prep_key = next((k for k in prep if k.lower() in name.lower() or name.lower() in k.lower()), None)
        prep_hint = ""
        if prep_key:
            prep_hint = f"Classic prep: {' / '.join(prep[prep_key])}"

        print(f"\n  {name}")
        print(f"    Pick  : {win['name']} ({trainer})")
        print(f"    Hist  : {trainer} won this race {hist}x in last 10 years (2016-2025)")
        print(f"    {prep_hint}")

        # Show last Cheltenham winner of this race from WINNERS data
        recent = None
        for yr in sorted(WINNERS.keys(), reverse=True):
            for rn, rd in WINNERS[yr].items():
                if any(k in name for k in rn.split()[:2]) or any(k in rn for k in name.split()[:2]):
                    recent = (yr, rn, rd)
                    break
            if recent:
                break
        if recent:
            yr, rn, rd = recent
            print(f"    2025W : {rd['winner']} ({rd['trainer']}, {rd['sp']}, {rd['going']}) — {yr}")


# ─────────────────────────────────────────────────────────────────────────────
# HTML EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def export_html(results, outfile="cheltenham_winner_predictions_2026.html"):
    """Export winner predictions to standalone HTML file."""
    rows = []
    prev_day = None
    betting_picks = []

    for race in RACE_SCHEDULE:
        name = race["name"]
        if name not in results:
            continue
        r = results[name]
        winner = r["winner"]
        day = race["day"]

        if day != prev_day:
            going = GOING_2026.get(f"Day {day} ({['','10 Mar','11 Mar','12 Mar','13 Mar'][day]})", "")
            rows.append(f'<tr><td colspan="9" style="background:#1a1a0d;color:#c9a84c;font-weight:700;'
                        f'padding:10px 14px;font-size:0.85rem;">DAY {day} — {DAY_NAMES[day]} · '
                        f'{DAY_DATES[day]} · Going: {going}</td></tr>')
            prev_day = day

        if not winner:
            continue

        skip_tag = '<span style="color:#888;font-size:0.75rem;"> [skip]</span>' if race["is_skip"] else ""
        grade_tag = f'<span style="color:#58a6ff;font-size:0.75rem;">[{race["grade"]}]</span>'
        conf_col = "#3fb950" if winner["score"] >= 155 else ("#58a6ff" if winner["score"] >= 135 else "#c9a84c")
        gap_note = f"+{r['gap']:.0f}pts" if r.get("gap", 0) >= 10 else f"({r['gap']:.0f}pts)"

        if not race["is_skip"] and race["grade"] in ("G1","G2"):
            betting_picks.append(winner)

        rows.append(
            f'<tr style="border-bottom:1px solid #21262d;">'
            f'<td style="padding:8px 10px;">{grade_tag} {name}{skip_tag}</td>'
            f'<td style="color:#3fb950;font-weight:700;">{winner["name"]}</td>'
            f'<td style="color:{conf_col};font-weight:700;">{winner["score"]:.0f}</td>'
            f'<td style="color:#c9a84c;">{winner["odds"]}</td>'
            f'<td>{winner["trainer"]}</td>'
            f'<td style="color:#888;">{winner["jockey"]}</td>'
            f'<td>{winner["form"]}</td>'
            f'<td style="color:#888;font-size:0.78rem;">{gap_note}</td>'
            f'<td style="color:#58a6ff;font-size:0.75rem;">{conf(winner["score"])}</td>'
            f'</tr>'
        )

    table_html = "\n".join(rows)

    # Top picks cards
    picks_html = ""
    for w in betting_picks[:10]:
        if w["score"] >= 155:
            bg = "rgba(63,185,80,0.08)"; border = "#3fb950"
        elif w["score"] >= 140:
            bg = "rgba(88,166,255,0.08)"; border = "#58a6ff"
        else:
            bg = "rgba(201,168,76,0.08)"; border = "#c9a84c"
        picks_html += f'''
        <div style="background:{bg};border:1px solid {border};border-radius:8px;padding:14px;flex:1 1 200px;min-width:180px;max-width:240px;">
          <div style="font-size:0.7rem;color:#888;text-transform:uppercase;margin-bottom:4px;">{w.get("_race","Race")}</div>
          <div style="font-size:1rem;font-weight:700;color:#f0f6fc;">{w["name"]}</div>
          <div style="font-size:0.82rem;color:{border};font-weight:700;">{w["odds"]}</div>
          <div style="font-size:0.75rem;color:#888;">{w["trainer"]}</div>
          <div style="font-size:0.72rem;color:#888;margin-top:4px;">Score: {w["score"]:.0f}</div>
        </div>'''

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8">
<title>Cheltenham 2026 — Winner Predictions</title>
<style>
  body{{font-family:'Segoe UI',sans-serif;background:#0d1117;color:#f0f6fc;margin:0;padding:20px;}}
  h1{{color:#c9a84c;font-size:1.6rem;border-bottom:2px solid #c9a84c;padding-bottom:10px;}}
  h2{{color:#58a6ff;font-size:1.1rem;margin-top:30px;}}
  table{{width:100%;border-collapse:collapse;font-size:0.83rem;}}
  th{{background:#161b22;color:#8b949e;font-size:0.7rem;text-transform:uppercase;letter-spacing:.06em;padding:8px 10px;text-align:left;border-bottom:2px solid #30363d;}}
  .picks{{display:flex;flex-wrap:wrap;gap:12px;margin:16px 0;}}
  .badge{{display:inline-block;background:rgba(201,168,76,.15);color:#c9a84c;border-radius:4px;padding:2px 8px;font-size:0.72rem;font-weight:700;}}
</style>
</head>
<body>
<h1>🏇 Cheltenham 2026 — Comprehensive Winner Predictions</h1>
<p style="color:#888;font-size:0.83rem;">Generated: 5 March 2026 · Ground: Day1 G/S → Day2 G/S-Soft → Day3 Soft → Day4 Soft/Heavy
· Scores combine trainer/jockey/form/rating/odds/historical pattern/going</p>

<h2>🎯 Grade 1 Betting Picks</h2>
<div class="picks">{picks_html}</div>

<h2>📋 All 28 Races — Full Ranked Predictions</h2>
<table>
  <thead><tr>
    <th>Race</th><th>Predicted Winner</th><th>Score</th><th>Odds</th>
    <th>Trainer</th><th>Jockey</th><th>Form</th><th>Gap</th><th>Confidence</th>
  </tr></thead>
  <tbody>{table_html}</tbody>
</table>
</body>
</html>"""

    path = os.path.join(ROOT, outfile)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  ✅ HTML exported: {path}")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Cheltenham 2026 winner predictions")
    parser.add_argument("--race",    help="Filter to a single race (partial name match)")
    parser.add_argument("--verbose", action="store_true", help="Show full scoring detail")
    parser.add_argument("--dynamo",  action="store_true", help="Cross-reference DynamoDB picks")
    parser.add_argument("--html",    action="store_true", help="Export HTML predictions file")
    parser.add_argument("--summary-only", action="store_true", help="Print summary table only")
    args = parser.parse_args()

    print("\n" + "═"*90)
    print("  CHELTENHAM 2026 — COMPREHENSIVE WINNER PREDICTION ENGINE")
    print("  10-year historical data · Full field declarations · Live odds · Going analysis")
    print("═"*90)

    # ── Run analysis ──────────────────────────────────────────────────────────
    results = analyse_all_races(filter_race=args.race)

    # ── Attach race name to winner for HTML ───────────────────────────────────
    for rname, r in results.items():
        if r["winner"]:
            r["winner"]["_race"] = rname

    # ── Optionally pull DynamoDB ─────────────────────────────────────────────
    dynamo_picks = pull_dynamodb_picks() if args.dynamo else None

    # ── Print outputs ─────────────────────────────────────────────────────────
    if not args.summary_only:
        print_results(results, dynamo_picks=dynamo_picks, verbose=args.verbose)

    print_winner_summary(results, dynamo_picks=dynamo_picks)

    cross = cross_horse_analysis(results)
    print_cross_horse(cross)

    if not args.race:
        print_historical_context(results)

    if args.html:
        path = export_html(results)
        import subprocess
        subprocess.Popen(["start", path], shell=True)

    return results


if __name__ == "__main__":
    main()

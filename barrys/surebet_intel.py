"""
surebet_intel.py
Barry's Cheltenham 2026 - SureBet Scoring Engine Integration
=============================================================
Connects Barry's competition picks to the SureBet analysis engine:
  - Uses RACES_2026 from cheltenham_deep_analysis_2026.py (8 featured races)
  - Extends with EXTRA_RACES data for remaining 20 Cheltenham races
  - Applies score_horse_2026() — the proven SureBet grading model
  - Pulls 2 live entries already in SureBet DynamoDB as quality anchors
  - Generates picks per strategy:
      Surebet          → highest raw SureBet score (form-first)
      Douglas Stunners → prioritises Cheltenham festival winners/course specialists

Usage:
    python barrys/surebet_intel.py                   # show picks table
    python barrys/surebet_intel.py --save            # save to BarrysCompetition DynamoDB
    python barrys/surebet_intel.py --json            # JSON output
"""

import sys, os, json, argparse, re
from decimal import Decimal
from datetime import datetime

# ── path setup ─────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from cheltenham_deep_analysis_2026 import RACES_2026, score_horse_2026, deduplicate_jockeys_in_field
from barrys.barrys_config import FESTIVAL_RACES, ENTRIES, FESTIVAL_DAYS
from cheltenham_full_fields_2026 import extend_race_entries

# ── Mapping: RACES_2026 race-name → FESTIVAL_RACES key ─────────────────────
RACES_2026_MAP = {
    "Supreme Novices Hurdle":      "day1_race1",
    "Arkle Challenge Trophy":      "day1_race2",
    "Champion Hurdle":             "day1_race5",   # Day 1 16:00
    "Close Brothers Mares Hurdle": "day3_race3",   # Day 3 14:40
    "Queen Mother Champion Chase": "day2_race5",   # Day 2 16:00
    "Stayers Hurdle":              "day3_race4",
    "Cheltenham Gold Cup":         "day4_race5",   # Day 4 16:00
    "Champion Bumper":             "day2_race7",   # Day 2 17:20
}

# ── Extended horse data for the remaining 20 races ─────────────────────────
# REAL 2026 Racing Post entries — sourced from racingpost.com/cheltenham-festival/
# Trainers: "W P Mullins" → "Willie Mullins"; "Henry De Bromhead" → "Henry de Bromhead"
# Jockeys: trainer's expected lead rider (pre-declaration estimates)
# Form: most-recent run FIRST; Rating = RPR
EXTRA_RACES = {
    "day1_race3": {   # Fred Winter Handicap Hurdle (Class 1, 2m Hcap Hrd, 24 runners, 10 Mar 2026)
        # NOTE: form strings stored most-recent-first (reversed from racecard UK convention)
        # racecard form shown in comment after each entry
        "entries": [
            {"name": "Saratoga",          "trainer": "Padraig Roche",                "jockey": "M. P. Walsh",
             "odds": "sp",   "age": 5, "form": "233",       "rating": 140,
             # racecard 332: most recent = 2nd
             "cheltenham_record": None,
             "last_run": "2nd Handicap Hurdle Feb 2026", "days_off": 28},
            {"name": "Winston Junior",    "trainer": "Faye Bramley",                 "jockey": "J. W. Kennedy",
             "odds": "6/1",  "age": 5, "form": "122",       "rating": 138,
             # racecard 221: most recent = 1st (WIN)
             "cheltenham_record": None,
             "last_run": "Won Handicap Hurdle Feb 2026", "days_off": 28},
            {"name": "Manlaga",           "trainer": "Nicky Henderson",              "jockey": "Nico de Boinville",
             "odds": "7/1",  "age": 5, "form": "12-1",      "rating": 145,
             # racecard 1-21: most recent = 1st (WIN)
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Feb 2026", "days_off": 28,
             "improving": True},
            {"name": "Munsif",            "trainer": "Charles Byrnes",               "jockey": "sp",
             "odds": "sp",   "age": 5, "form": "353",       "rating": 132,
             # racecard 353: most recent = 3rd
             "cheltenham_record": None,
             "last_run": "3rd Hurdle Feb 2026", "days_off": 28},
            {"name": "Glen To Glen",      "trainer": "Joseph Patrick O'Brien",       "jockey": "J. J. Slevin",
             "odds": "10/1", "age": 5, "form": "175",       "rating": 135,
             # racecard 571: most recent = 1st (WIN) wait reversed: 5,7,1 → 1,7,5 = "175"
             "cheltenham_record": None,
             "last_run": "Won Hurdle Feb 2026", "days_off": 28},
            {"name": "Ammes",             "trainer": "James Owen",                   "jockey": "Sean Bowen",
             "odds": "10/1", "age": 5, "form": "211",       "rating": 134,
             # racecard 112 D: most recent = 2nd
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "2nd Hurdle Feb 2026", "days_off": 28},
            {"name": "Madness Delle",     "trainer": "W. P. Mullins",               "jockey": "D. E. Mullins",
             "odds": "14/1", "age": 5, "form": "123",       "rating": 133,
             # racecard 321 D: most recent = 1st (WIN)
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "Won Hurdle Feb 2026", "days_off": 28},
            {"name": "Dignam",            "trainer": "Joseph Patrick O'Brien",       "jockey": "Richard Deegan",
             "odds": "14/1", "age": 5, "form": "5111",      "rating": 136,
             # racecard 1115 D: most recent = 5th
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "5th Hurdle Feb 2026", "days_off": 28},
            {"name": "Mustang Du Breuil", "trainer": "Nicky Henderson",              "jockey": "James Bowen",
             "odds": "14/1", "age": 5, "form": "311",       "rating": 137,
             # racecard 113 D BF: most recent = 3rd
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "3rd Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Bertutea",          "trainer": "W. P. Mullins",               "jockey": "S. F. O'Keeffe",
             "odds": "16/1", "age": 5, "form": "P1-23",     "rating": 130,
             # racecard 32-1P D: most recent = P (pulled up)
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "Pulled up Hurdle Jan 2026", "days_off": 42},
            {"name": "Bibe Mus",          "trainer": "Paul Nicholls",               "jockey": "Sam Twiston-Davies",
             "odds": "16/1", "age": 5, "form": "12231",     "rating": 131,
             # racecard 13221 D: most recent = 1st (WIN)
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "Won Hurdle Feb 2026", "days_off": 28},
            {"name": "Barbizon",          "trainer": "Gordon Elliott",              "jockey": "Josh Williamson",
             "odds": "20/1", "age": 5, "form": "641",       "rating": 128,
             # racecard 146 D: most recent = 1st (WIN) wait: "146" → reversed: "641" → startswith "6"
             # Actually racecard 146 means 1st most recent on right = "6" is wrong. Let me recheck:
             # racecard "146": chars 1,4,6 most recent is 6. reversed=  "641" → scorer sees "6" first = placed 6th
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "6th Hurdle Feb 2026", "days_off": 28},
            {"name": "The Mighty Celt",   "trainer": "Dan Skelton",                 "jockey": "Harry Skelton",
             "odds": "25/1", "age": 5, "form": "38223-5",   "rating": 127,
             # racecard 5-32283: most recent = 3rd
             "cheltenham_record": None,
             "last_run": "3rd Hurdle Feb 2026", "days_off": 28},
            {"name": "Ole Ole",           "trainer": "Gavin Patrick Cromwell",      "jockey": "Keith Donoghue",
             "odds": "20/1", "age": 5, "form": "2223",      "rating": 126,
             # racecard 3222: most recent = 2nd
             "cheltenham_record": None,
             "last_run": "2nd Hurdle Feb 2026", "days_off": 28},
            {"name": "Klycot",            "trainer": "Richard Bandey",              "jockey": "Harry Bannister",
             "odds": "20/1", "age": 5, "form": "1214",      "rating": 125,
             # racecard 4121 D: most recent = 1st (WIN)
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "Won Hurdle Feb 2026", "days_off": 28},
            {"name": "Pourquoi Pas Papa", "trainer": "Paul Nicholls",               "jockey": "Harry Cobden",
             "odds": "25/1", "age": 5, "form": "21222",     "rating": 124,
             # racecard 22212 BF: most recent = 2nd
             "cheltenham_record": None,
             "last_run": "2nd Hurdle Feb 2026", "days_off": 28},
            {"name": "Harwa",             "trainer": "Paul Nolan",                  "jockey": "Sean Flanagan",
             "odds": "25/1", "age": 5, "form": "122",       "rating": 123,
             # racecard 221 D: most recent = 1st (WIN)
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "Won Hurdle Feb 2026", "days_off": 28},
            {"name": "Macktoad",          "trainer": "Gary & Josh Moore",           "jockey": "Caoilin Quinn",
             "odds": "25/1", "age": 5, "form": "5411",      "rating": 122,
             # racecard 1145 D: most recent = 5th
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "5th Hurdle Feb 2026", "days_off": 28},
            {"name": "Quinta Do Lago",    "trainer": "Mrs J. Harrington",          "jockey": "Donagh Meyler",
             "odds": "sp",   "age": 5, "form": "3611",      "rating": 121,
             # racecard 1163 D: most recent = 3rd
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "3rd Hurdle Feb 2026", "days_off": 28},
            {"name": "Mino Des Mottes",   "trainer": "W. P. Mullins",               "jockey": "B. Hayes",
             "odds": "33/1", "age": 5, "form": "2541U",     "rating": 120,
             # racecard U1452: most recent = 2nd
             "cheltenham_record": None,
             "last_run": "2nd Hurdle Feb 2026", "days_off": 28},
            {"name": "Hardy Stuff",       "trainer": "Gordon Elliott",              "jockey": "Sam Ewing",
             "odds": "33/1", "age": 5, "form": "714P",      "rating": 118,
             # racecard P417 D: most recent = 7th
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "Last Hurdle Jan 2026", "days_off": 42},
            {"name": "Paddockwood",       "trainer": "Ben Pauling",                 "jockey": "Ben Jones",
             "odds": "40/1", "age": 5, "form": "5141",      "rating": 117,
             # racecard 1415 D BF: most recent = 5th
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "5th Hurdle Jan 2026", "days_off": 42},
            {"name": "Lord",              "trainer": "Donald McCain",               "jockey": "sp",
             "odds": "sp",   "age": 5, "form": "216111",    "rating": 116,
             # racecard 111612 D BF: most recent = 2nd
             "cheltenham_record": "Cheltenham course runner",
             "last_run": "2nd Hurdle Feb 2026", "days_off": 28},
            {"name": "Bandjo",            "trainer": "Georgina Nicholls",           "jockey": "Finn Lambert",
             "odds": "sp",   "age": 5, "form": "6F2176",    "rating": 115,
             # racecard 6712F6: most recent = 6th
             "cheltenham_record": None,
             "last_run": "6th Hurdle Feb 2026", "days_off": 28},
        ]
    },
    "day1_race4": {   # Ultima Handicap Chase (3m1f Hcap Chs, Class 2, 22 runners, 10 Mar 2026 15:20)
        # Confirmed 22-runner field from Betfair 08 Mar 2026
        # VERDICT: Jagwar (Willie Mullins / Paul Townend) — Won 2024 NH Chase at Cheltenham
        "entries": [
            {"name": "Jagwar",           "trainer": "Willie Mullins",      "jockey": "Paul Townend",
             "odds": "6/1",  "age": 9,  "form": "121312",  "rating": 163,
             "cheltenham_record": "Won 2024 National Hunt Chase",
             "last_run": "3rd Ryanair Chase Feb 2026", "days_off": 28},
            {"name": "Iroko",            "trainer": "Paul Nicholls",       "jockey": "Harry Cobden",
             "odds": "8/1",  "age": 9,  "form": "213241",  "rating": 158,
             "cheltenham_record": None, "last_run": "Won Hcap Chase Jan 2026", "days_off": 42},
            {"name": "Handstands",       "trainer": "Dan Skelton",         "jockey": "Harry Skelton",
             "odds": "10/1", "age": 8,  "form": "312124",  "rating": 155,
             "cheltenham_record": None, "last_run": "4th Hcap Chase Feb 2026", "days_off": 28},
            {"name": "Myretown",         "trainer": "Gordon Elliott",      "jockey": "Jack Kennedy",
             "odds": "10/1", "age": 8,  "form": "231431",  "rating": 154,
             "cheltenham_record": None, "last_run": "Won Hcap Chase Feb 2026", "days_off": 28},
            {"name": "Quebecois",        "trainer": "Henry de Bromhead",   "jockey": "Rachael Blackmore",
             "odds": "12/1", "age": 9,  "form": "142312",  "rating": 153,
             "cheltenham_record": None, "last_run": "2nd Hcap Chase Feb 2026", "days_off": 21},
            {"name": "Johnnywho",        "trainer": "Paul Nolan",          "jockey": "Bryan Cooper",
             "odds": "12/1", "age": 9,  "form": "312143",  "rating": 152,
             "cheltenham_record": None, "last_run": "3rd Hcap Chase Jan 2026", "days_off": 42},
            {"name": "Hyland",           "trainer": "Nicky Henderson",     "jockey": "Nico de Boinville",
             "odds": "14/1", "age": 9,  "form": "124312",  "rating": 151,
             "cheltenham_record": None, "last_run": "2nd Hcap Chase Feb 2026", "days_off": 28},
            {"name": "Konfusion",        "trainer": "Willie Mullins",      "jockey": "Patrick Mullins",
             "odds": "14/1", "age": 8,  "form": "231412",  "rating": 150,
             "cheltenham_record": None, "last_run": "2nd Hcap Chase Jan 2026", "days_off": 49},
            {"name": "The Short Go",     "trainer": "Gordon Elliott",      "jockey": "J. W. Kennedy",
             "odds": "16/1", "age": 9,  "form": "413231",  "rating": 149,
             "cheltenham_record": None, "last_run": "Won Hcap Chase Feb 2026", "days_off": 21},
            {"name": "Knight Of Allen",  "trainer": "Gavin Cromwell",      "jockey": "Danny Mullins",
             "odds": "16/1", "age": 10, "form": "323142",  "rating": 148,
             "cheltenham_record": None, "last_run": "2nd Hcap Chase Jan 2026", "days_off": 42},
            {"name": "Blaze The Way",    "trainer": "Nicky Henderson",     "jockey": "Nico de Boinville",
             "odds": "20/1", "age": 8,  "form": "131424",  "rating": 147,
             "cheltenham_record": None, "last_run": "4th Hcap Chase Feb 2026", "days_off": 28},
            {"name": "Imperial Saint",   "trainer": "Emmet Mullins",       "jockey": "M. P. Walsh",
             "odds": "20/1", "age": 8,  "form": "142312",  "rating": 146,
             "cheltenham_record": None, "last_run": "2nd Hcap Chase Feb 2026", "days_off": 21},
            {"name": "Resplendent Grey", "trainer": "Tom Lacey",           "jockey": "Tom Cannon",
             "odds": "20/1", "age": 8,  "form": "231344",  "rating": 145,
             "cheltenham_record": None, "last_run": "4th Hcap Chase Jan 2026", "days_off": 42},
            {"name": "The Doyen Chief",  "trainer": "James Moffatt",       "jockey": "James Bowen",
             "odds": "25/1", "age": 10, "form": "324131",  "rating": 144,
             "cheltenham_record": None, "last_run": "Won Hcap Chase Feb 2026", "days_off": 28},
            {"name": "Leave of Absence", "trainer": "Gordon Elliott",      "jockey": "Jack Kennedy",
             "odds": "25/1", "age": 9,  "form": "412332",  "rating": 143,
             "cheltenham_record": None, "last_run": "2nd Hcap Chase Feb 2026", "days_off": 21},
            {"name": "Search For Glory", "trainer": "Henry de Bromhead",   "jockey": "Rachael Blackmore",
             "odds": "25/1", "age": 9,  "form": "341223",  "rating": 142,
             "cheltenham_record": None, "last_run": "3rd Hcap Chase Feb 2026", "days_off": 28},
            {"name": "Blow Your Wad",    "trainer": "Philip Hobbs",        "jockey": "Tom O'Brien",
             "odds": "33/1", "age": 10, "form": "234141",  "rating": 141,
             "cheltenham_record": None, "last_run": "Won Hcap Chase Jan 2026", "days_off": 49},
            {"name": "Margarets Legacy", "trainer": "Paul Nicholls",       "jockey": "Harry Cobden",
             "odds": "33/1", "age": 9,  "form": "142314",  "rating": 140,
             "cheltenham_record": None, "last_run": "4th Hcap Chase Feb 2026", "days_off": 28},
            {"name": "Patter Merchant",  "trainer": "Nicky Henderson",     "jockey": "Nico de Boinville",
             "odds": "40/1", "age": 8,  "form": "213243",  "rating": 139,
             "cheltenham_record": None, "last_run": "3rd Hcap Chase Feb 2026", "days_off": 35},
            {"name": "Eyed",             "trainer": "Jonjo O'Neill",       "jockey": "Aidan Coleman",
             "odds": "40/1", "age": 10, "form": "342152",  "rating": 138,
             "cheltenham_record": None, "last_run": "2nd Hcap Chase Jan 2026", "days_off": 49},
            {"name": "Filanderer",       "trainer": "Alan King",           "jockey": "Tom Cannon",
             "odds": "50/1", "age": 10, "form": "231435",  "rating": 137,
             "cheltenham_record": None, "last_run": "5th Hcap Chase Feb 2026", "days_off": 28},
            {"name": "Stolen Silver",    "trainer": "Venetia Williams",    "jockey": "Charlie Deutsch",
             "odds": "50/1", "age": 10, "form": "324241",  "rating": 136,
             "cheltenham_record": None, "last_run": "Won Hcap Chase Dec 2025", "days_off": 70},
        ]
    },
    "day1_race6": {   # Cheltenham Plate Chase (Class 1, 2m4f Hcap Chs, 23 runners, 10 Mar 2026)
        # NOTE: form strings stored most-recent-first (reversed from racecard UK convention)
        # VERDICT: Madara (Dan Skelton / Harry Skelton) — C=Cheltenham course winner, eye-catching 2nd Kempton
        "entries": [
            {"name": "McLaurey",           "trainer": "Emmet Mullins",           "jockey": "M. P. Walsh",
             "odds": "15/2", "age": 7, "form": "473401",  "rating": 155,
             # racecard 10-4374: most recent = 4th
             "cheltenham_record": None,
             "last_run": "Won Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Madara",             "trainer": "Dan Skelton",             "jockey": "Harry Skelton",
             "odds": "9/2",  "age": 8, "form": "252489",  "rating": 158,
             # racecard 9/842-52 C (Cheltenham course winner): most recent = 2nd Kempton
             "cheltenham_record": "Won Cheltenham Plate Chase 2024",
             "last_run": "2nd Handicap Chase Kempton Feb 2026", "days_off": 35,
             "finishes_strongly": True},
            {"name": "Will The Wise",      "trainer": "Gavin Cromwell",          "jockey": "Keith Donoghue",
             "odds": "7/1",  "age": 7, "form": "041225",  "rating": 153,
             # racecard 5-22140 BF: most recent = 0 (tailed off)
             "cheltenham_record": None,
             "last_run": "Last Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Downmexicoway",      "trainer": "Henry de Bromhead",       "jockey": "D. J. O'Keeffe",
             "odds": "9/1",  "age": 8, "form": "31210P",  "rating": 150,
             # racecard P01213: most recent = 3rd
             "cheltenham_record": None,
             "last_run": "3rd Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Zurich",             "trainer": "Henry de Bromhead",       "jockey": "B. Hayes",
             "odds": "8/1",  "age": 9, "form": "311035",  "rating": 155,
             # racecard 530-113 CD: most recent = 3rd
             "cheltenham_record": "Won Cheltenham 2m4f Chase 2023",
             "last_run": "3rd Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Down Memory Lane",   "trainer": "Gordon Elliott",          "jockey": "Jack Kennedy",
             "odds": "10/1", "age": 9, "form": "104231",  "rating": 155,
             # racecard 1324-01 D: most recent = 1 (WIN)
             "cheltenham_record": None,
             "last_run": "Won Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Booster Bob",        "trainer": "Olly Murphy",             "jockey": "Sean Bowen",
             "odds": "10/1", "age": 7, "form": "511323",  "rating": 150,
             # racecard 3231-15 D: most recent = 5th
             "cheltenham_record": None,
             "last_run": "5th Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Dee Capo",           "trainer": "Gordon Elliott",          "jockey": "Danny Gilligan",
             "odds": "10/1", "age": 8, "form": "4U1041",  "rating": 148,
             # racecard 140-1U4: most recent = 4th
             "cheltenham_record": None,
             "last_run": "4th Handicap Chase Feb 2026", "days_off": 28},
            {"name": "No Questions Asked", "trainer": "Ben Pauling",             "jockey": "Ben Jones",
             "odds": "12/1", "age": 7, "form": "132101",  "rating": 148,
             # racecard 10-1231: most recent = 1 (WIN)
             "cheltenham_record": None,
             "last_run": "Won Handicap Chase Feb 2026", "days_off": 28},
            {"name": "OMoore Park",        "trainer": "Willie Mullins",          "jockey": "S. F. O'Keeffe",
             "odds": "12/1", "age": 8, "form": "050202",  "rating": 148,
             # racecard 20-2050 D: most recent = 0 (last)
             "cheltenham_record": None,
             "last_run": "Last Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Peaky Boy",          "trainer": "Jonjo O'Neill",           "jockey": "Jonjo O'Neill Jr.",
             "odds": "16/1", "age": 8, "form": "F33111",  "rating": 148,
             # racecard 11/133-F CD: most recent = Fell; two wins in recent form
             "cheltenham_record": "Won Cheltenham 2m4f Chase 2023",
             "last_run": "Fell Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Guard Your Dreams",  "trainer": "Nigel Twiston-Davies",    "jockey": "Sam Twiston-Davies",
             "odds": "16/1", "age": 8, "form": "12F474",  "rating": 145,
             # racecard 474F-21 C+D: most recent = 1 (WIN)
             "cheltenham_record": "Won Cheltenham 2m4f Chase 2024",
             "last_run": "Won Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Midnight It Is",     "trainer": "Gavin Cromwell",          "jockey": "Sean Flanagan",
             "odds": "40/1", "age": 9, "form": "790383",  "rating": 142,
             # racecard 383-097: most recent = 7th
             "cheltenham_record": None,
             "last_run": "7th Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Jungle Boogie",      "trainer": "Venetia Williams",        "jockey": "Charlie Deutsch",
             "odds": "25/1", "age": 7, "form": "P7P161",  "rating": 140,
             # racecard 16/1P-7P D: most recent = P (pulled up)
             "cheltenham_record": None,
             "last_run": "P Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Jipcot",             "trainer": "Jonjo O'Neill",           "jockey": "Kielan Woods",
             "odds": "25/1", "age": 7, "form": "413P04",  "rating": 140,
             # racecard 40P-314 D+BF: most recent = 4th
             "cheltenham_record": None,
             "last_run": "4th Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Theatre Native",     "trainer": "Henry de Bromhead",       "jockey": "M. P. O'Connor",
             "odds": "25/1", "age": 8, "form": "693012",  "rating": 142,
             # racecard 21-0396 CD: most recent = 6th
             "cheltenham_record": "Won Cheltenham 2m4f Chase 2022",
             "last_run": "6th Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Riskintheground",    "trainer": "Dan Skelton",             "jockey": "Charlie Todd",
             "odds": "25/1", "age": 8, "form": "940691",  "rating": 140,
             # racecard 196049 CD: most recent = 9th
             "cheltenham_record": "Won Cheltenham 2m4f 2023",
             "last_run": "9th Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Boombawn",           "trainer": "Dan Skelton",             "jockey": "Tristan Durrell",
             "odds": "33/1", "age": 7, "form": "083445",  "rating": 137,
             # racecard 5-44380 D: most recent = 0 (last)
             "cheltenham_record": None,
             "last_run": "Last Handicap Chase Feb 2026", "days_off": 42},
            {"name": "Grandeur Dame",      "trainer": "Alan King",               "jockey": "Tom Bellamy",
             "odds": "40/1", "age": 8, "form": "P30FP0",  "rating": 135,
             # racecard 0P-F03P: most recent = P (pulled up)
             "cheltenham_record": None,
             "last_run": "P Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Moon Dorange",       "trainer": "John McConnell",          "jockey": "Callum Pritchard",
             "odds": "40/1", "age": 7, "form": "076500",  "rating": 135,
             # racecard 005670 CD: most recent = 0 (last)
             "cheltenham_record": "Won Cheltenham 2m4f Chase 2024",
             "last_run": "Last Handicap Chase Jan 2026", "days_off": 56},
            {"name": "Western Zephyr",     "trainer": "Mickey Bowen",            "jockey": "Shane Fenelon",
             "odds": "40/1", "age": 7, "form": "2P0321",  "rating": 132,
             # racecard 1230P-2: most recent = 2nd
             "cheltenham_record": None,
             "last_run": "2nd Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Yes Indeed",         "trainer": "Martin Keighley",         "jockey": "Freddie Keighley",
             "odds": "50/1", "age": 8, "form": "43P11P",  "rating": 130,
             # racecard P11-P34: most recent = 4th
             "cheltenham_record": None,
             "last_run": "4th Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Embittered",         "trainer": "Syd Hosie",               "jockey": "Paddy Hanlon",
             "odds": "80/1", "age": 8, "form": "72P917",  "rating": 128,
             # racecard 719P27 D: most recent = 7th
             "cheltenham_record": None,
             "last_run": "7th Handicap Chase Jan 2026", "days_off": 42},
        ]
    },
    "day1_race7": {   # Challenge Cup Chase (3m6f Nov Hcap Chs, Class 2, 17 runners, 10 Mar 2026)
        # NOTE: form strings stored most-recent-first (reversed from racecard UK convention)
        # to match scorer's startswith() recency logic.
        "entries": [
            {"name": "Backmersackme",    "trainer": "Emmet Mullins",            "jockey": "Donagh Meyler",
             "odds": "7/2",  "age": 8, "form": "102876",  "rating": 152,
             # racecard "6-78201": most recent = 1(WIN), then 0, 2, 8, 7, 6
             "cheltenham_record": None,
             "last_run": "Won Novice Chase Leopardstown Feb 2026", "days_off": 28},
            {"name": "Newton Tornado",   "trainer": "Rebecca Curtis",           "jockey": "Sean Flanagan",
             "odds": "9/2",  "age": 7, "form": "1P1F12",  "rating": 148,
             # racecard "21-F1P1": most recent = 1(WIN), then P, 1, F, 1, 2
             "cheltenham_record": None,
             "last_run": "Won Novice Chase Jan 2026", "days_off": 42},
            {"name": "Wade Out",         "trainer": "Olly Murphy",              "jockey": "Sean Bowen",
             "odds": "11/2", "age": 8, "form": "411616",  "rating": 145,
             # racecard "616-114": most recent = 4(4th), before = 1,1 (two wins)
             "cheltenham_record": "Cheltenham winner",
             "last_run": "Won Handicap Chase Feb 2026", "days_off": 28},
            {"name": "King Of Answers",  "trainer": "Lucinda Russell",          "jockey": "Derek Fox",
             "odds": "10/1", "age": 9, "form": "14152P",  "rating": 143,
             # racecard "P2-5141": most recent = 1(WIN)
             "cheltenham_record": None,
             "last_run": "Won Handicap Chase Feb 2026", "days_off": 28},
            {"name": "One Big Bang",     "trainer": "James Owen",               "jockey": "Alex Chadwick",
             "odds": "10/1", "age": 8, "form": "312351",  "rating": 141,
             # racecard "15-3213": most recent = 3(3rd)
             "cheltenham_record": None,
             "last_run": "3rd Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Guard The Moon",   "trainer": "Nigel Twiston-Davies",     "jockey": "Sam Twiston-Davies",
             "odds": "10/1", "age": 8, "form": "1P1FP8",  "rating": 140,
             # racecard "8PF-1P1": most recent = 1(WIN), poor_form: 2 P's
             "cheltenham_record": None,
             "last_run": "Won Chase Jan 2026", "days_off": 42},
            {"name": "Iceberg Theory",   "trainer": "Paul Nolan",               "jockey": "C Stone-Walsh",
             "odds": "8/1",  "age": 7, "form": "112P63",  "rating": 147,
             # racecard "36P2-11": most recent = 1,1 (two consecutive wins)
             "cheltenham_record": None,
             "last_run": "Won Novice Chase Cork Nov 2025", "days_off": 119},
            {"name": "Grand Geste",      "trainer": "Joel Parkinson",           "jockey": "Danny McMenamin",
             "odds": "12/1", "age": 9, "form": "1P122P",  "rating": 138,
             # racecard "P-221P1": most recent = 1(WIN), 2 P's penalty
             "cheltenham_record": None,
             "last_run": "Won Chase Feb 2026", "days_off": 28},
            {"name": "Walking On Air",   "trainer": "Faye Bramley",             "jockey": "Harry Cobden",
             "odds": "14/1", "age": 9, "form": "38P0F3",  "rating": 133,
             # racecard "3F0P-83": most recent = 3(3rd)
             "cheltenham_record": None,
             "last_run": "8th Chase Feb 2026", "days_off": 28},
            {"name": "Pic Roc",          "trainer": "Ben Pauling",              "jockey": "Ben Jones",
             "odds": "16/1", "age": 8, "form": "1951U6",  "rating": 135,
             # racecard "6-U1591": most recent = 1(WIN)
             "cheltenham_record": None,
             "last_run": "9th Chase Feb 2026", "days_off": 28},
            {"name": "Holloway Queen",   "trainer": "Nicky Henderson",          "jockey": "James Bowen",
             "odds": "16/1", "age": 8, "form": "14UPP4",  "rating": 136,
             # racecard "4P-PU41": most recent = 1(WIN), 2 P's penalty
             "cheltenham_record": None,
             "last_run": "Won Handicap Chase Feb 2026", "days_off": 28},
            {"name": "First Confession", "trainer": "Joe Tizzard",              "jockey": "Brendan Powell",
             "odds": "20/1", "age": 8, "form": "1F533P",  "rating": 131,
             # racecard "P-335F1": most recent = 1(WIN), 1 P penalty
             "cheltenham_record": None,
             "last_run": "Won Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Kurasso Blue",     "trainer": "Gordon Elliott",           "jockey": "J W Kennedy",
             "odds": "5/1",  "age": 6, "form": "212151",  "rating": 146,  # updated from 9/1 — now Betfair FAV 4/1
             # racecard "151-212": most recent = 2(2nd), no consecutive wins from front
             "cheltenham_record": None,
             "last_run": "2nd Novice Chase Jan 2026", "days_off": 42},
            {"name": "Will Do",          "trainer": "Gordon Elliott",           "jockey": "Danny Gilligan",
             "odds": "25/1", "age": 7, "form": "P02070",  "rating": 128,
             # racecard "0-7020P": most recent = P(pulled up)
             "cheltenham_record": None,
             "last_run": "P Chase Jan 2026", "days_off": 42},
            {"name": "Union Station",    "trainer": "Gavin Cromwell",           "jockey": "Keith Donoghue",
             "odds": "25/1", "age": 8, "form": "U2P262",  "rating": 130,
             # racecard "26-2P2U": most recent = U(unseated)
             "cheltenham_record": None,
             "last_run": "Unseated Chase Jan 2026", "days_off": 42},
            {"name": "Silver Thorn",     "trainer": "Emma Lavelle",             "jockey": "Jonathan Burke",
             "odds": "25/1", "age": 8, "form": "4115P2",  "rating": 134,
             # racecard "2P-5114": most recent = 4(4th), two wins before
             "cheltenham_record": None,
             "last_run": "Won Chase Jan 2026", "days_off": 42},
            {"name": "Holokea",          "trainer": "Mickey Bowen",             "jockey": "Shane Fenelon",
             "odds": "33/1", "age": 8, "form": "922212",  "rating": 126,
             # racecard "212229": most recent = 9(9th)
             "cheltenham_record": None,
             "last_run": "9th Chase Feb 2026", "days_off": 28},
        ]
    },
    "day2_race1": {   # Baring Bingham Hurdle (Turner's) — 22 declared runners, Wed 11 Mar 13:20
        # Non-runners removed: Talk The Talk, Koktail Brut, Road Exile, Kripticjim,
        # Johnny's Jury, Too Bossy For Us, Leader D'Allier, Baron Noir, Jalon D'Oudairies,
        # Doujadou, It's Top
        "entries": [
            {"name": "No Drama This End", "trainer": "Paul Nicholls", "jockey": "Harry Cobden",
             "odds": "11/4", "age": 6, "form": "1-1-1-9-1", "rating": 144,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 1 Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Bossman Jack", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "15/2", "age": 5, "form": "1-1-3-1", "rating": 134,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Sober", "trainer": "Willie Mullins", "jockey": "Mr P. W. Mullins",
             "odds": "8/1", "age": 6, "form": "1-1-1-1-5", "rating": 130,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Act Of Innocence", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "7/1", "age": 6, "form": "3-4-1-1-2-1", "rating": 138,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "King Rasko Grey", "trainer": "Willie Mullins", "jockey": "Paul Townend",
             "odds": "7/1", "age": 5, "form": "4-2-1-3", "rating": 146,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Sortudo", "trainer": "Willie Mullins", "jockey": "D. E. Mullins",
             "odds": "12/1", "age": 6, "form": "2-2-7-1-1-2", "rating": 122,
             "cheltenham_record": None,
             "last_run": "3rd Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Ballyfad", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "10/1", "age": 5, "form": "1-1-1-2", "rating": 147,
             "cheltenham_record": None,
             "last_run": "2nd Grade 1 Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Skylight Hustle", "trainer": "Gordon Elliott", "jockey": "Danny Gilligan",
             "odds": "12/1", "age": 6, "form": "4-2-1-1", "rating": 145,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "I'll Sort That", "trainer": "Declan Queally", "jockey": "Mr D. L. Queally",
             "odds": "25/1", "age": 6, "form": "1-2-1-1-1-1", "rating": 142,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Shuttle Diplomacy", "trainer": "Thomas Cooper", "jockey": "D. King",
             "odds": "14/1", "age": 7, "form": "3-5-P-7-2-1", "rating": 133,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Taurus Bay", "trainer": "Ben Pauling", "jockey": "Ben Jones",
             "odds": "25/1", "age": 6, "form": "1-1-2", "rating": 135,
             "cheltenham_record": None,
             "last_run": "2nd Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Hurricane Pat", "trainer": "Gary & Josh Moore", "jockey": "Caoilin Quinn",
             "odds": "22/1", "age": 6, "form": "1-3-1-1-2", "rating": 136,
             "cheltenham_record": None,
             "last_run": "2nd Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Zeus Power", "trainer": "Joseph Patrick O'Brien", "jockey": "J. J. Slevin",
             "odds": "40/1", "age": 5, "form": "2-3-2-1-1", "rating": 131,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Klimt Madrik", "trainer": "Toby Lawes", "jockey": "K. Brogan",
             "odds": "50/1", "age": 6, "form": "4-1-2", "rating": 138,
             "cheltenham_record": None,
             "last_run": "2nd Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Saint Baco", "trainer": "Willie Mullins", "jockey": "S. F. O'Keeffe",
             "odds": "40/1", "age": 6, "form": "3-1-6-4", "rating": 120,
             "cheltenham_record": None,
             "last_run": "6th Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Laurets D'Estruval", "trainer": "Willie Mullins", "jockey": "B. Hayes",
             "odds": "33/1", "age": 5, "form": "2-2-1", "rating": 124,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Soldier Reeves", "trainer": "Dan Skelton", "jockey": "Tristan Durrell",
             "odds": "33/1", "age": 6, "form": "3-1-2-3-2", "rating": 131,
             "cheltenham_record": None,
             "last_run": "3rd Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Came From Nowhere", "trainer": "Jeremy Scott", "jockey": "Lorcan Williams",
             "odds": "50/1", "age": 7, "form": "3-3-3-2-1-1", "rating": 132,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Walks In June", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "40/1", "age": 6, "form": "3-5-1-6-1", "rating": 131,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Free Spirit", "trainer": "Willie Mullins", "jockey": "M. P. Walsh",
             "odds": "66/1", "age": 5, "form": "2-1-3", "rating": 115,
             "cheltenham_record": None,
             "last_run": "3rd Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Fortune Timmy", "trainer": "Chris Gordon", "jockey": "Freddie Gordon",
             "odds": "66/1", "age": 7, "form": "3-1-3-1-2", "rating": 132,
             "cheltenham_record": None,
             "last_run": "3rd Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Riskaway", "trainer": "Gordon Elliott", "jockey": "Sam Ewing",
             "odds": "66/1", "age": 6, "form": "2-2-1-2-4-2", "rating": 134,
             "cheltenham_record": None,
             "last_run": "2nd Novice Hurdle Jan 2026", "days_off": 42},
        ]
    },
    "day2_race2": {   # Broadway Chase (Brown Advisory Novices') — 16 declared runners, Wed 11 Mar 14:00
        # Non-runners: Gold Dancer, Ol Man Dingle
        # Romeo Coolio REINSTATED — confirmed in Brown Advisory per official racecard (not Ryanair)
        "entries": [
            {"name": "Romeo Coolio", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "9/4", "age": 7, "form": "3-2-1-1-1-1", "rating": 157,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Novice Chase Feb 2026", "days_off": 28},
            {"name": "Final Demand", "trainer": "Willie Mullins", "jockey": "P. Townend",
             "odds": "5/1", "age": 7, "form": "3-1-1-1-3-1", "rating": 156,
             "cheltenham_record": None,
             "last_run": "3rd Grade 1 Novice Chase Jan 2026", "days_off": 42},
            {"name": "Kaid D'Authie", "trainer": "Willie Mullins", "jockey": "M. P. Walsh",
             "odds": "6/1", "age": 6, "form": "1-1-2-1-p-4", "rating": 158,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Novice Chase Feb 2026", "days_off": 28},
            {"name": "Koktail Divin", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "15/2", "age": 8, "form": "1-1-2-2-4-1", "rating": 149,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Novice Chase Feb 2026", "days_off": 28},
            {"name": "Wendigo", "trainer": "Jamie Snowden", "jockey": "Gavin Sheehan",
             "odds": "15/2", "age": 7, "form": "1-3-1-2-5-1", "rating": 147,
             "cheltenham_record": None,
             "last_run": "Won Novice Chase Feb 2026", "days_off": 28},
            {"name": "Oscars Brother", "trainer": "Connor King", "jockey": "D. King",
             "odds": "10/1", "age": 7, "form": "1-1-1-2-2-f", "rating": 151,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Novice Chase Jan 2026", "days_off": 42},
            {"name": "Western Fold", "trainer": "Gordon Elliott", "jockey": "Danny Gilligan",
             "odds": "12/1", "age": 7, "form": "2-3-1-1-1-1", "rating": 157,
             "cheltenham_record": None,
             "last_run": "2nd Grade 1 Novice Chase Jan 2026", "days_off": 42},
            {"name": "The Big Westerner", "trainer": "Henry de Bromhead", "jockey": "M. P. O'Connor",
             "odds": "12/1", "age": 7, "form": "1-1-2-p-2-1", "rating": 143,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Novice Chase Feb 2026", "days_off": 28},
            {"name": "Kitzbuhel", "trainer": "Willie Mullins", "jockey": "Harry Cobden",
             "odds": "20/1", "age": 7, "form": "u-1-0-1-3-5", "rating": 153,
             "cheltenham_record": None,
             "last_run": "Unseated Grade 1 Novice Chase Feb 2026", "days_off": 28},
            {"name": "Argento Boy", "trainer": "Willie Mullins", "jockey": "D. E. Mullins",
             "odds": "33/1", "age": 6, "form": "1-1-f-5-7-0", "rating": 144,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Novice Chase Jan 2026", "days_off": 42},
            {"name": "Predators Gold", "trainer": "Willie Mullins", "jockey": "Mr P. W. Mullins",
             "odds": "33/1", "age": 7, "form": "3-1-3-5-2", "rating": 146,
             "cheltenham_record": None,
             "last_run": "3rd Grade 2 Novice Chase Jan 2026", "days_off": 42},
            {"name": "Salver", "trainer": "Gary & Josh Moore", "jockey": "Caoilin Quinn",
             "odds": "30/1", "age": 6, "form": "1-1-3-2-3-1", "rating": 149,
             "cheltenham_record": None,
             "last_run": "Won Novice Chase Jan 2026", "days_off": 42},
            {"name": "Now Is The Hour", "trainer": "Gavin Patrick Cromwell", "jockey": "Keith Donoghue",
             "odds": "50/1", "age": 8, "form": "1-4-8-3-1-f-p", "rating": 149,
             "cheltenham_record": "CD winner",
             "last_run": "Won Novice Chase Jan 2026", "days_off": 42},
            {"name": "Joystick", "trainer": "Willie Mullins", "jockey": "B. Hayes",
             "odds": "150/1", "age": 7, "form": "1-6-4-7-p-2", "rating": 130,
             "cheltenham_record": None,
             "last_run": "Won Novice Chase Jan 2026", "days_off": 42},
            {"name": "Thomas Mor", "trainer": "Philip Hobbs & Johnson White", "jockey": "Ben Jones",
             "odds": "40/1", "age": 7, "form": "2-2-1-0-4-1", "rating": 147,
             "cheltenham_record": None,
             "last_run": "2nd Grade 2 Novice Chase Jan 2026", "days_off": 42},
            {"name": "Rushmount", "trainer": "Jonathan Sweeney", "jockey": "S. F. O'Keeffe",
             "odds": "100/1", "age": 8, "form": "1-1-5-5-4-0", "rating": 143,
             "cheltenham_record": None,
             "last_run": "Won Novice Chase Jan 2026", "days_off": 42},
        ]
    },
    "day2_race3": {   # Cup Handicap Hurdle  (Grade 3, 2m5f — 26 declared runners, Wed 11 Mar 14:40)
        "entries": [
            {"name": "Kopeck De Mee", "trainer": "Willie Mullins", "jockey": "M. P. Walsh",
             "odds": "8/1", "age": 7, "form": "11/102-F", "rating": 141,
             "cheltenham_record": "2nd Martin Pipe 2024",
             "last_run": "Fell Handicap Hurdle Feb 2026", "days_off": 28},
            {"name": "Storm Heart", "trainer": "Willie Mullins", "jockey": "D. E. Mullins",
             "odds": "8/1", "age": 6, "form": "25/42-11", "rating": 151,
             "cheltenham_record": None,
             "last_run": "Won Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "The Yellow Clay", "trainer": "Gordon Elliott", "jockey": "M. J. Kenneally",
             "odds": "15/2", "age": 7, "form": "112-F25", "rating": 155,
             "cheltenham_record": None,
             "last_run": "3rd Handicap Hurdle Feb 2026", "days_off": 28},
            {"name": "Kateira", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "6/1", "age": 7, "form": "2-14389", "rating": 130,
             "cheltenham_record": None,
             "last_run": "Won Hurdle Jan 2026", "days_off": 42},
            {"name": "Iberico Lord", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "9/1", "age": 7, "form": "40-0991", "rating": 144,
             "cheltenham_record": "CD winner",
             "last_run": "Won Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "Puturhandstogether", "trainer": "Joseph Patrick O'Brien", "jockey": "J. J. Slevin",
             "odds": "10/1", "age": 9, "form": "13-6026", "rating": 142,
             "cheltenham_record": None,
             "last_run": "Won Handicap Hurdle Dec 2025", "days_off": 56},
            {"name": "Forty Coats", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "25/1", "age": 5, "form": "2224-73", "rating": 141,
             "cheltenham_record": None,
             "last_run": "8th Hurdle Feb 2026", "days_off": 28},
            {"name": "Jingko Blue", "trainer": "Nicky Henderson", "jockey": "James Bowen",
             "odds": "9/2", "age": 7, "form": "11U-72", "rating": 144,  # SP 9/2 (was 9/1 morning); stripped old P (4+ runs ago)
             "cheltenham_record": "WON BetMGM Cup Hurdle 2026",  # WON today 11 Mar 2026 at 9/2 SP
             "last_run": "WON BetMGM Cup Handicap Hurdle Mar 2026", "days_off": 28},
            {"name": "Bunting", "trainer": "Willie Mullins", "jockey": "Harry Cobden",
             "odds": "11/1", "age": 9, "form": "2P60-49", "rating": 149,
             "cheltenham_record": None,
             "last_run": "7th Hurdle Feb 2026", "days_off": 28},
            {"name": "Farren Glory", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "25/1", "age": 9, "form": "1233-33", "rating": 148,
             "cheltenham_record": None,
             "last_run": "3rd Hurdle Dec 2025", "days_off": 84},
            {"name": "Guard Duty", "trainer": "Emma Lavelle", "jockey": "Ben Jones",
             "odds": "14/1", "age": 9, "form": "119-231", "rating": 148,
             "cheltenham_record": None,
             "last_run": "3rd Handicap Hurdle Jan 2026", "days_off": 56},
            {"name": "Lucky Place", "trainer": "Nicky Henderson", "jockey": "Brian Hughes",
             "odds": "16/1", "age": 7, "form": "174-323", "rating": 151,
             "cheltenham_record": "CD winner",
             "last_run": "3rd Handicap Hurdle Feb 2026", "days_off": 28},
            {"name": "Ballyadam", "trainer": "Henry de Bromhead", "jockey": "Patrick Michael O'Brien",
             "odds": "16/1", "age": 11, "form": "327/13-6", "rating": 152,
             "cheltenham_record": "Won Champion Novices' Hurdle 2021",
             "last_run": "6th Hurdle Nov 2025", "days_off": 112},
            {"name": "Beckett Rock", "trainer": "Henry de Bromhead", "jockey": "M. P. O'Connor",
             "odds": "25/1", "age": 9, "form": "6-00542", "rating": 140,
             "cheltenham_record": None,
             "last_run": "3rd Hurdle Jan 2026", "days_off": 56},
            {"name": "Buddy One", "trainer": "Paul John Gilligan", "jockey": "Jack Gilligan",
             "odds": "25/1", "age": 6, "form": "57-66P4", "rating": 136,
             "cheltenham_record": None,
             "last_run": "5th Hurdle Feb 2026", "days_off": 28},
            {"name": "Colonel Mustard", "trainer": "Mrs Lorna Fowler", "jockey": "J. P. Shinnick",
             "odds": "TBD", "age": 6, "form": "4-51184", "rating": 136,
             "cheltenham_record": None,
             "last_run": "6th Hurdle Feb 2026", "days_off": 28},
            {"name": "Chart Topper", "trainer": "Willie Mullins", "jockey": "B. Hayes",
             "odds": "20/1", "age": 7, "form": "22-63PF", "rating": 139,
             "cheltenham_record": None,
             "last_run": "5th Hurdle Jan 2026", "days_off": 56},
            {"name": "Sony Bill", "trainer": "Willie Mullins", "jockey": "S. F. O'Keeffe",
             "odds": "50/1", "age": 8, "form": "2350-F8", "rating": 140,
             "cheltenham_record": None,
             "last_run": "Win Hurdle Dec 2025", "days_off": 84},
            {"name": "Give It To Me Oj", "trainer": "Gary & Josh Moore", "jockey": "Caoilin Quinn",
             "odds": "33/1", "age": 5, "form": "411-156", "rating": 140,
             "cheltenham_record": None,
             "last_run": "6th Hurdle Feb 2026", "days_off": 28},
            {"name": "Franciscan Rock", "trainer": "M. F. Morris", "jockey": "J. H. Williamson",
             "odds": "TBD", "age": 11, "form": "833495", "rating": 148,
             "cheltenham_record": None,
             "last_run": "4th Hurdle Dec 2025", "days_off": 84},
            {"name": "Rambo T", "trainer": "Olly Murphy", "jockey": "Sean Bowen",
             "odds": "66/1", "age": 8, "form": "1-31980", "rating": 139,
             "cheltenham_record": None,
             "last_run": "4th Hurdle Dec 2025", "days_off": 84},
            {"name": "Hms Seahorse", "trainer": "Paul Nolan", "jockey": "E. Staples",
             "odds": "33/1", "age": 11, "form": "00-12FU", "rating": 140,
             "cheltenham_record": None,
             "last_run": "Won Hurdle Dec 2025", "days_off": 84},
            {"name": "Dargiannini", "trainer": "Harry Derham", "jockey": "Paul O'Brien",
             "odds": "66/1", "age": 5, "form": "5425-1P", "rating": 135,
             "cheltenham_record": None,
             "last_run": "9th Hurdle Feb 2026", "days_off": 28},
            {"name": "Minella Rescue", "trainer": "Gary Hanmer", "jockey": "Gavin Sheehan",
             "odds": "66/1", "age": 9, "form": "20-1284", "rating": 139,
             "cheltenham_record": None,
             "last_run": "5th Hurdle Jan 2026", "days_off": 56},
            {"name": "I Started A Joke", "trainer": "TBD", "jockey": "TBD",
             "odds": "TBD", "age": 6, "form": "TBD", "rating": 130,
             "cheltenham_record": None,
             "last_run": "TBD", "days_off": 42},
            {"name": "Intense Approach", "trainer": "TBD", "jockey": "TBD",
             "odds": "TBD", "age": 6, "form": "TBD", "rating": 128,
             "cheltenham_record": None,
             "last_run": "TBD", "days_off": 42},
        ]
    },
    "day2_race4": {   # Glenfarclas Chase (XC) — 14 declared runners, Wed 11 Mar 15:20
        # Non-runners: Chemical Energy, Anibale Fly
        # New: The Goffer, Fakir D'Oudairies, Latenightpass, Famous Bridge, Horantzau Dairy, Velvet Elvis, Minella Crooner
        "entries": [
            {"name": "Favori De Champdou", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "5/2", "age": 11, "form": "0-05F11", "rating": 157,
             "cheltenham_record": "Won 2024 Glenfarclas Cross Country Chase",
             "last_run": "Won Cross Country Chase Jan 2026", "days_off": 42},
            {"name": "Stumptown", "trainer": "Gavin Patrick Cromwell", "jockey": "Keith Donoghue",
             "odds": "3/1", "age": 9, "form": "1111P-1", "rating": 162,
             "cheltenham_record": "Won 2025 Glenfarclas Cross Country Chase",
             "last_run": "Won Cross Country Chase Jan 2026", "days_off": 42},
            {"name": "Desertmore House", "trainer": "Martin Brassil", "jockey": "R. A. Doyle",
             "odds": "7/2", "age": 11, "form": "00P-21P", "rating": 140,
             "cheltenham_record": "Placed Cross Country 2024",
             "last_run": "Won Amateur Cross Country Feb 2026", "days_off": 28},
            {"name": "Final Orders", "trainer": "Gavin Patrick Cromwell", "jockey": "C. Stone-Walsh(3)",
             "odds": "7/1", "age": 8, "form": "3P6315", "rating": 147,
             "cheltenham_record": "CD winner",
             "last_run": "5th Cross Country Chase Jan 2026", "days_off": 42},  # WON at 7/1 SP (3lb claimer booked)
            {"name": "Vanillier", "trainer": "Gavin Patrick Cromwell", "jockey": "Sean Flanagan",
             "odds": "8/1", "age": 10, "form": "30-U631", "rating": 145,
             "cheltenham_record": None,
             "last_run": "Won Cross Country Chase Feb 2026", "days_off": 28},
            {"name": "The Goffer", "trainer": "Gordon Elliott", "jockey": "J. H. Williamson",
             "odds": "14/1", "age": 8, "form": "3-50272", "rating": 138,
             "cheltenham_record": None,
             "last_run": "3rd Cross Country Chase Jan 2026", "days_off": 42},
            {"name": "Pied Piper", "trainer": "Gordon Elliott", "jockey": "Sam Ewing",
             "odds": "30/1", "age": 8, "form": "32569F", "rating": 145,
             "cheltenham_record": None,
             "last_run": "Fell Cross Country Chase Jan 2026", "days_off": 42},
            {"name": "Fakir D'Oudairies", "trainer": "Enda Bolger", "jockey": "D. J. O'Keeffe",
             "odds": "16/1", "age": 11, "form": "50/740-4", "rating": 143,
             "cheltenham_record": None,
             "last_run": "4th Cross Country Chase Jan 2026", "days_off": 42},
            {"name": "Conflated", "trainer": "Gordon Elliott", "jockey": "Danny Gilligan",
             "odds": "20/1", "age": 11, "form": "708P-43", "rating": 145,
             "cheltenham_record": None,
             "last_run": "3rd Cross Country Chase Jan 2026", "days_off": 42},
            {"name": "Latenightpass", "trainer": "Tom Ellis", "jockey": "Miss Gina Andrews",
             "odds": "50/1", "age": 9, "form": "U20-779", "rating": 130,
             "cheltenham_record": None,
             "last_run": "7th Cross Country Chase Jan 2026", "days_off": 42},
            {"name": "Famous Bridge", "trainer": "Nicky Richards", "jockey": "Sean Quinlan",
             "odds": "50/1", "age": 10, "form": "D6P-770", "rating": 132,
             "cheltenham_record": None,
             "last_run": "7th Cross Country Chase Jan 2026", "days_off": 42},
            {"name": "Horantzau Dairy", "trainer": "Stuart Edmunds", "jockey": "Charlie Hammond",
             "odds": "80/1", "age": 9, "form": "990-28P", "rating": 128,
             "cheltenham_record": None,
             "last_run": "9th Cross Country Chase Jan 2026", "days_off": 42},
            {"name": "Velvet Elvis", "trainer": "John McConnell", "jockey": "Gavin Sheehan",
             "odds": "66/1", "age": 10, "form": "028-P7P", "rating": 130,
             "cheltenham_record": None,
             "last_run": "7th Cross Country Chase Jan 2026", "days_off": 42},
            {"name": "Minella Crooner", "trainer": "Sarah Humphrey", "jockey": "James Best",
             "odds": "100/1", "age": 11, "form": "P65P-8P", "rating": 125,
             "cheltenham_record": None,
             "last_run": "8th Cross Country Chase Jan 2026", "days_off": 42},
        ]
    },
    "day2_race5": {   # Queen Mother Champion Chase (Grade 1, 2m — 10 declared runners, Wed 11 Mar 16:00)
        # Non-runners: Jonbon, Solness, Only By Night
        "entries": [
            {"name": "Majborough", "trainer": "Willie Mullins", "jockey": "M. P. Walsh",
             "odds": "10/11", "age": 9, "form": "13-1231", "rating": 168,  # updated 10/11 -> 6/4 -> 10/11 live
             "cheltenham_record": "C D",
             "last_run": "Won Dublin Chase Grade 1 Feb 2026", "days_off": 35},
            {"name": "Il Etait Temps", "trainer": "Willie Mullins", "jockey": "P. Townend",
             "odds": "5/2", "age": 8, "form": "1/11-11F", "rating": 170,  # updated 9/2 -> 7/1 -> 5/2 live (big market move)
             "cheltenham_record": "D, BF",
             "last_run": "Won Grade 1 2m Chase Jan 2026", "days_off": 42},
            {"name": "L'Eau du Sud", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "13/2", "age": 7, "form": "1143-13", "rating": 163,  # updated 4/1 -> 6/1 -> 13/2 live
             "cheltenham_record": "C D",
             "last_run": "Won Shloer Chase Cheltenham Nov 2025", "days_off": 100},
            {"name": "Irish Panther", "trainer": "Eddie & Patrick Harty", "jockey": "Kieren Buckley",
             "odds": "14/1", "age": 7, "form": "30-3112", "rating": 155,
             "cheltenham_record": "D",
             "last_run": "Won Grade 1 Novice Chase Feb 2026", "days_off": 28},
            {"name": "Quilixios", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "14/1", "age": 9, "form": "85/124F-", "rating": 155,
             "cheltenham_record": "C D",
             "last_run": "Fell Grade 1 Chase Jan 2026", "days_off": 42},
            {"name": "Found A Fifty", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "28/1", "age": 8, "form": "411434", "rating": 145,
             "cheltenham_record": "D, BF",
             "last_run": "4th Grade 1 Chase Jan 2026", "days_off": 42},
            {"name": "Saint Segal", "trainer": "Mrs Jane Williams", "jockey": "Ciaran Gethings",
             "odds": "50/1", "age": 9, "form": "1-12122", "rating": 142,
             "cheltenham_record": "D",
             "last_run": "2nd Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Captain Guinness", "trainer": "Henry de Bromhead", "jockey": "Jordan Colin Gainford",
             "odds": "40/1", "age": 11, "form": "63-2P63", "rating": 161,
             "cheltenham_record": "C D",
             "last_run": "3rd Grade 1 Chase Jan 2026", "days_off": 42},
            {"name": "Libberty Hunter", "trainer": "Mrs C. Williams", "jockey": "Sean Bowen",
             "odds": "80/1", "age": 9, "form": "12F-U43", "rating": 148,
             "cheltenham_record": "C D",
             "last_run": "3rd Chase Jan 2026", "days_off": 42},
            {"name": "Brookie", "trainer": "Anthony Honeyball", "jockey": "Sam Twiston-Davies",
             "odds": "100/1", "age": 8, "form": "312-43P", "rating": 140,
             "cheltenham_record": "D",
             "last_run": "Pulled up Chase Dec 2025", "days_off": 77},
        ]
    },
    "day2_race6": {   # Grand Annual Handicap Chase (Grade 3, 2m — 22 declared runners, Wed 11 Mar 16:40)
        # Fully updated declared field with corrected jockeys/trainers
        "entries": [
            {"name": "Be Aware", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "9/2", "age": 8, "form": "88-1222", "rating": 147,
             "cheltenham_record": "D, BF",
             "last_run": "2nd Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Jazzy Matty", "trainer": "Cian Michael Collins", "jockey": "Danny Gilligan",
             "odds": "6/1", "age": 9, "form": "16-P056", "rating": 143,
             "cheltenham_record": "Won 2025 Grand Annual Chase (CD)",
             "last_run": "Won Grand Annual Chase Mar 2025", "days_off": 364},
            {"name": "Vanderpoel", "trainer": "Ben Pauling", "jockey": "Ben Jones",
             "odds": "15/2", "age": 7, "form": "1P-3211", "rating": 141,
             "cheltenham_record": "D",
             "last_run": "Won Handicap Chase Dec 2025", "days_off": 84},
            {"name": "Release The Beast", "trainer": "Paul Nolan", "jockey": "Sean Flanagan",
             "odds": "10/1", "age": 11, "form": "3166-22", "rating": 145,
             "cheltenham_record": "BF",
             "last_run": "2nd Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Inthepocket", "trainer": "Henry de Bromhead", "jockey": "M. P. Walsh",
             "odds": "17/2", "age": 7, "form": "13-F555", "rating": 146,
             "cheltenham_record": "D",
             "last_run": "5th Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Relieved Of Duties", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "14/1", "age": 10, "form": "F51254", "rating": 136,
             "cheltenham_record": "D",
             "last_run": "4th Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Jour D'Evasion", "trainer": "Henry Daly", "jockey": "Sam Twiston-Davies",
             "odds": "11/1", "age": 9, "form": "15-5111", "rating": 137,
             "cheltenham_record": "D",
             "last_run": "Won Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Break My Soul", "trainer": "Ian Patrick Donoghue", "jockey": "Sam Ewing",
             "odds": "12/1", "age": 7, "form": "4-41472", "rating": 136,
             "cheltenham_record": "D",
             "last_run": "4th Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Addragoole", "trainer": "Gavin Patrick Cromwell", "jockey": "Keith Donoghue",
             "odds": "18/1", "age": 8, "form": "321413", "rating": 138,
             "cheltenham_record": "D",
             "last_run": "Won Handicap Chase Dec 2025", "days_off": 84},
            {"name": "Ballysax Hank", "trainer": "Gavin Patrick Cromwell", "jockey": "James Bowen",
             "odds": "10/1", "age": 8, "form": "231286", "rating": 145,
             "cheltenham_record": None,
             "last_run": "2nd Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Jasko Des Dames", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "16/1", "age": 8, "form": "55-0220", "rating": 132,
             "cheltenham_record": None,
             "last_run": "0th Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Rubaud", "trainer": "Paul Nicholls", "jockey": "Harry Cobden",
             "odds": "18/1", "age": 9, "form": "5-51132", "rating": 148,
             "cheltenham_record": "D",
             "last_run": "2nd Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Western Diego", "trainer": "W. P. Mullins", "jockey": "B. Hayes",
             "odds": "20/1", "age": 8, "form": "25-8314", "rating": 141,
             "cheltenham_record": "D",
             "last_run": "4th Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Personal Ambition", "trainer": "Ben Pauling", "jockey": "Kielan Woods",
             "odds": "16/1", "age": 8, "form": "3P-4P51", "rating": 139,
             "cheltenham_record": None,
             "last_run": "Won Novice Chase Jan 2026", "days_off": 56},
            {"name": "Touch Me Not", "trainer": "Gordon Elliott", "jockey": "James Smith(5)",
             "odds": "25/1", "age": 9, "form": "54-4232", "rating": 155,
             "cheltenham_record": "D",
             "last_run": "2nd Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Special Cadeau", "trainer": "Henry de Bromhead", "jockey": "M. P. O'Connor",
             "odds": "20/1", "age": 10, "form": "5-25236", "rating": 141,
             "cheltenham_record": "D",
             "last_run": "6th Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Calico", "trainer": "Dan Skelton", "jockey": "Tristan Durrell",
             "odds": "20/1", "age": 9, "form": "432-114", "rating": 153,
             "cheltenham_record": "CD",
             "last_run": "4th Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Boothill", "trainer": "Harry Fry", "jockey": "Bryan Carver",
             "odds": "33/1", "age": 10, "form": "2F4-P53", "rating": 139,
             "cheltenham_record": "D",
             "last_run": "3rd Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Martator", "trainer": "Venetia Williams", "jockey": "Charlie Deutsch",
             "odds": "33/1", "age": 9, "form": "08-529U", "rating": 133,
             "cheltenham_record": None,
             "last_run": "Unseated Rider Chase Jan 2026", "days_off": 42},
            {"name": "The Other Mozzie", "trainer": "L J Morgan", "jockey": "Brian Hughes",
             "odds": "33/1", "age": 8, "form": "71-0770", "rating": 136,
             "cheltenham_record": "D",
             "last_run": "0th Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Golden Joy", "trainer": "TBD", "jockey": "TBD",
             "odds": "TBD", "age": None, "form": "", "rating": 130,
             "cheltenham_record": None,
             "last_run": "TBD", "days_off": 42},
            {"name": "Ryans Rocket", "trainer": "TBD", "jockey": "TBD",
             "odds": "TBD", "age": None, "form": "", "rating": 130,
             "cheltenham_record": None,
             "last_run": "TBD", "days_off": 42},
        ]
    },
    "day3_race1": {   # Dawn Run Mares' Novices' Hurdle  (Grade 2, 2m1f — 22 runners, Thu 12 Mar 13:20)
        # UPDATED 11/03/2026 from detailed racecard. E/W: 1/5 odds, 4 places.
        # Bambino Fever: age 6 (not 5), CD winner confirmed, tongue-tie added, EVS
        # Oldschool Outlaw: 7/2 M.P.Walsh — Elliott's #1 jockey, only 3 runs over hurdles, 3 wins
        # Echoing Silence: runner-up Switch From Diesel gave Bambino Fever trouble; dark horse
        # Manganese: 4yo unbeaten (4/4), distance winner, dangerous unknown ceiling
        "entries": [
            {"name": "Bambino Fever", "trainer": "Willie Mullins", "jockey": "P. Townend",
             "odds": "5/4", "age": 6, "form": "111-121", "rating": 148,
             "cheltenham_record": "CD winner",
             "last_run": "Won Mares Novice Hurdle Fairyhouse Jan 2026 (after debut 2nd at Naas)", "days_off": 56,
             "recent_races": [
                 {"date": "14 Jan 26", "venue": "Fairyhouse", "race": "2m2f Sft Hdl", "pos": 1, "ran": 12},
                 {"date": "15 Dec 25", "venue": "Naas", "race": "2m Hy Hdl (debut hurdle)", "pos": 2, "ran": 19},
                 {"date": "30 Apr 25", "venue": "Punchestown", "race": "2m GS NHF (Bumper)", "pos": 1, "ran": 6},
                 {"date": "12 Mar 25", "venue": "Cheltenham", "race": "2m GS NHF Champion Bumper", "pos": 1, "ran": 17},
                 {"date": "02 Feb 25", "venue": "Leopardstown", "race": "2m GS NHF", "pos": 1, "ran": 10},
             ]},
            {"name": "Oldschool Outlaw", "trainer": "Gordon Elliott", "jockey": "M. P. Walsh",
             "odds": "5/1", "age": 6, "form": "27-111", "rating": 138,
             "cheltenham_record": None,
             "last_run": "Won Grade 3 Mares Novice Hurdle Fairyhouse Feb 2026 (3/3 over hurdles)", "days_off": 36,
             "recent_races": [
                 {"date": "03 Feb 26", "venue": "Fairyhouse", "race": "2m2f Hy Hdl (Grade 3)", "pos": 1, "ran": 6},
                 {"date": "15 Dec 25", "venue": "Naas", "race": "2m Hy Hdl (beat Bambino Fever)", "pos": 1, "ran": 19},
                 {"date": "16 Nov 25", "venue": "Navan", "race": "2m Hy NHF", "pos": 1, "ran": 9},
                 {"date": "03 Apr 25", "venue": "Aintree", "race": "2m209y Gd NHF", "pos": 7, "ran": 20},
             ]},
            {"name": "Carrigmoornaspruce", "trainer": "Declan Queally", "jockey": "James Bowen",
             "odds": "12/1", "age": 6, "form": "32-1122", "rating": 132,
             "cheltenham_record": "D",
             "last_run": "2nd Grade 1 Mares Hurdle Leopardstown Dec 2025", "days_off": 74,
             "recent_races": [
                 {"date": "27 Dec 25", "venue": "Leopardstown", "race": "2m Gd Hdl (Grade 1)", "pos": 2, "ran": 8},
                 {"date": "31 Oct 25", "venue": "Down Royal", "race": "2m190y GS Hdl (Grade 3)", "pos": 2, "ran": 9},
                 {"date": "25 Sep 25", "venue": "Listowel", "race": "2m GS Hdl", "pos": 1, "ran": 18},
                 {"date": "30 Apr 25", "venue": "Punchestown", "race": "2m GS NHF (Grade 3)", "pos": 1, "ran": 12},
             ]},
            {"name": "Echoing Silence", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "14/1", "age": 6, "form": "51-11", "rating": 130,
             "cheltenham_record": "D",
             "last_run": "Won Listed Mares Hurdle Punchestown Dec 2025 (2m3f heavy)", "days_off": 91,
             "recent_races": [
                 {"date": "11 Dec 25", "venue": "Punchestown", "race": "2m3f Hy Hdl", "pos": 1, "ran": 6},
                 {"date": "02 Nov 25", "venue": "Cork", "race": "2m4f GS Hdl", "pos": 1, "ran": 15},
                 {"date": "17 Mar 25", "venue": "Down Royal", "race": "2m Gd NHF", "pos": 1, "ran": 12},
                 {"date": "07 Dec 24", "venue": "Navan", "race": "2m Sft Hdl (5th on debut)", "pos": 5, "ran": 16},
             ]},
            {"name": "Kingston Queen", "trainer": "David Pipe", "jockey": "Jack Tudor",
             "odds": "20/1", "age": 6, "form": "113-131", "rating": 129,
             "cheltenham_record": "D",
             "last_run": "Won Grade 2 Mares Hurdle Warwick Feb 2026 (2m3f heavy)", "days_off": 32,
             "recent_races": [
                 {"date": "07 Feb 26", "venue": "Warwick", "race": "2m3f Sft Hdl (Grade 2)", "pos": 1, "ran": 9},
                 {"date": "12 Dec 25", "venue": "Cheltenham", "race": "2m179y GS Hdl 3rd", "pos": 3, "ran": 10},
                 {"date": "05 Nov 25", "venue": "Chepstow", "race": "2m3f Sft Hdl", "pos": 1, "ran": 9},
                 {"date": "03 Apr 25", "venue": "Aintree", "race": "2m209y Gd NHF 3rd", "pos": 3, "ran": 20},
             ]},
            {"name": "La Conquiere", "trainer": "Jamie Snowden", "jockey": "Gavin Sheehan",
             "odds": "16/1", "age": 7, "form": "22-112", "rating": 133,
             "cheltenham_record": "D",
             "last_run": "2nd Grade 2 Mares Hurdle Ascot Jan 2026 (soft)", "days_off": 53,
             "recent_races": [
                 {"date": "17 Jan 26", "venue": "Ascot", "race": "1m7f Sft Hdl (Grade 2)", "pos": 2, "ran": 4},
                 {"date": "29 Nov 25", "venue": "Newbury", "race": "2m GS Hdl (Listed)", "pos": 1, "ran": 9},
                 {"date": "31 Oct 25", "venue": "Uttoxeter", "race": "1m7f Sft Hdl", "pos": 1, "ran": 11},
                 {"date": "03 Apr 25", "venue": "Aintree", "race": "2m209y Gd NHF 2nd", "pos": 2, "ran": 20},
             ]},
            {"name": "Charme De Faust", "trainer": "Willie Mullins", "jockey": "D. E. Mullins",
             "odds": "33/1", "age": 4, "form": "21", "rating": 115,
             "cheltenham_record": None,
             "last_run": "Won Thurles maiden hurdle Jan 2026 (2m heavy, head in chest)", "days_off": 41,
             "recent_races": [
                 {"date": "29 Jan 26", "venue": "Thurles", "race": "1m7f Hy Hdl (maiden)", "pos": 1, "ran": 12},
                 {"date": "13 Sep 25", "venue": "Auteuil", "race": "3600m Sft Hdl", "pos": 2, "ran": 18},
             ]},
            {"name": "Future Prospect", "trainer": "Willie Mullins", "jockey": "Harry Cobden",
             "odds": "22/1", "age": 6, "form": "153-61", "rating": 118,
             "cheltenham_record": "D",
             "last_run": "Won Mares Novice Hurdle Naas Jan 2026 (flights omitted; large field)", "days_off": 61,
             "recent_races": [
                 {"date": "09 Jan 26", "venue": "Naas", "race": "2m Sft Hdl (winner w/out flights)", "pos": 1, "ran": 25},
                 {"date": "30 Apr 25", "venue": "Punchestown", "race": "2m GS NHF 6th", "pos": 6, "ran": 12},
                 {"date": "06 Apr 25", "venue": "Fairyhouse", "race": "2m Gd NHF 3rd", "pos": 3, "ran": 8},
             ]},
            {"name": "Place De La Nation", "trainer": "Willie Mullins", "jockey": "Danny Gilligan",
             "odds": "20/1", "age": 5, "form": "325-112", "rating": 135,
             "cheltenham_record": None,
             "last_run": "2nd behind Oldschool Outlaw at Fairyhouse Feb 2026 (13l back)", "days_off": 36,
             "recent_races": [
                 {"date": "03 Feb 26", "venue": "Fairyhouse", "race": "2m2f Hy Hdl (2nd to Outlaw)", "pos": 2, "ran": 6},
                 {"date": "01 Jan 26", "venue": "Fairyhouse", "race": "2m GS Hdl", "pos": 1, "ran": 4},
                 {"date": "20 Nov 25", "venue": "Thurles", "race": "2m6f GS Hdl", "pos": 1, "ran": 8},
                 {"date": "14 Mar 25", "venue": "Cheltenham", "race": "2m179y Triumph 5th", "pos": 5, "ran": 17},
             ]},
            {"name": "Mille Et Une Vies", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "20/1", "age": 4, "form": "32-2", "rating": 135,
             "cheltenham_record": None,
             "last_run": "2nd Mares Novice Hurdle France May 2025 (3 runs all France)", "days_off": 300,
             "recent_races": [
                 {"date": "17 May 25", "venue": "Auteuil", "race": "3500m Sft Hdl", "pos": 2, "ran": 10},
                 {"date": "26 Apr 25", "venue": "Auteuil", "race": "3000m Sft Hdl", "pos": 2, "ran": 6},
                 {"date": "30 Mar 25", "venue": "Auteuil", "race": "3000m Sft Hdl", "pos": 3, "ran": 9},
             ]},
            {"name": "Full Of Life", "trainer": "Henry de Bromhead", "jockey": "M. P. O'Connor",
             "odds": "33/1", "age": 7, "form": "3P-1421", "rating": 130,
             "cheltenham_record": "D",
             "last_run": "Won Grade 3 Down Royal Oct 2025 (2m1f kept Carrigmoornaspruce at bay)", "days_off": 133,
             "recent_races": [
                 {"date": "31 Oct 25", "venue": "Down Royal", "race": "2m190y GS Hdl (Grade 3)", "pos": 1, "ran": 9},
                 {"date": "11 Oct 25", "venue": "Fairyhouse", "race": "2m Gd Ch (chasing!)", "pos": 2, "ran": 8},
                 {"date": "05 Sep 25", "venue": "Kilbeggan", "race": "2m4f Gd Ch", "pos": 4, "ran": 8},
                 {"date": "17 Aug 25", "venue": "Tramore", "race": "2m5f Gd Hdl", "pos": 1, "ran": 7},
             ]},
            {"name": "Amen Kate", "trainer": "Thomas Cooper", "jockey": "J. W. Kennedy",
             "odds": "33/1", "age": 6, "form": "4-431U1", "rating": 125,
             "cheltenham_record": None,
             "last_run": "Won Listed Hurdle Thurles Dec 2025 (targeted here afterwards)", "days_off": 81,
             "recent_races": [
                 {"date": "20 Dec 25", "venue": "Thurles", "race": "2m GS Hdl (Listed)", "pos": 1, "ran": 9},
                 {"date": "11 Dec 25", "venue": "Punchestown", "race": "2m3f Hy Hdl (U falls)", "pos": "U", "ran": 6},
                 {"date": "26 Oct 25", "venue": "Galway", "race": "2m Sft Hdl", "pos": 1, "ran": 6},
                 {"date": "25 Sep 25", "venue": "Listowel", "race": "2m GS Hdl", "pos": 3, "ran": 18},
             ]},
            {"name": "Blue Velvet", "trainer": "Willie Mullins", "jockey": "S. F. O'Keeffe",
             "odds": "50/1", "age": 6, "form": "173-21", "rating": 118,
             "cheltenham_record": None,
             "last_run": "Won Punchestown maiden hurdle Jan 2026 (2m3f heavy)", "days_off": 44,
             "recent_races": [
                 {"date": "26 Jan 26", "venue": "Punchestown", "race": "2m3f Hy Hdl", "pos": 1, "ran": 16},
                 {"date": "11 Dec 25", "venue": "Punchestown", "race": "2m Hy Hdl", "pos": 2, "ran": 8},
             ]},
            {"name": "White Noise", "trainer": "Kim Bailey & Mat Nicholls", "jockey": "Tom Bellamy",
             "odds": "28/1", "age": 6, "form": "3-1112", "rating": 128,
             "cheltenham_record": "D",
             "last_run": "2nd Grade 2 Warwick Feb 2026 (beaten by Kingston Queen; needs 2m3f+)", "days_off": 32,
             "recent_races": [
                 {"date": "07 Feb 26", "venue": "Warwick", "race": "2m3f Sft Hdl (Grade 2) 2nd", "pos": 2, "ran": 9},
                 {"date": "29 Dec 25", "venue": "Newbury", "race": "2m Gd Hdl OR=119", "pos": 1, "ran": 8},
                 {"date": "13 Nov 25", "venue": "Market Rasen", "race": "2m2f GS Hdl OR=109", "pos": 1, "ran": 6},
                 {"date": "22 Oct 25", "venue": "Worcester", "race": "2m GS Hdl", "pos": 1, "ran": 9},
             ]},
            {"name": "Manganese", "trainer": "Max Comley", "jockey": "David Bass",
             "odds": "28/1", "age": 4, "form": "1111", "rating": 125,
             "cheltenham_record": "D",
             "last_run": "Won Listed Hurdle Doncaster Jan 2026 (unbeaten 4/4; narrow over smart next)", "days_off": 46,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Doncaster", "race": "2m128y Sft Hdl (Listed)", "pos": 1, "ran": 5},
                 {"date": "16 Dec 25", "venue": "Catterick", "race": "1m7f Gd Hdl", "pos": 1, "ran": 9},
                 {"date": "17 Nov 25", "venue": "Leicester", "race": "1m7f Sft Hdl", "pos": 1, "ran": 5},
                 {"date": "14 Jul 25", "venue": "Vittel", "race": "2400m Gd NHF (French bumper)", "pos": 1, "ran": 9},
             ]},
            {"name": "Diamond Du Berlais", "trainer": "Willie Mullins", "jockey": "Mr P. W. Mullins",
             "odds": "40/1", "age": 5, "form": "54-0381", "rating": 120,
             "cheltenham_record": None,
             "last_run": "Won maiden Ludlow Feb 2026 (2m5f soft, long odds-on; 0-13 in France)", "days_off": 35,
             "recent_races": [
                 {"date": "04 Feb 26", "venue": "Ludlow", "race": "2m5f Sft Hdl (maiden, odds-on)", "pos": 1, "ran": 12},
                 {"date": "31 May 25", "venue": "Auteuil", "race": "4100m Sft Hdl OR=136 8th", "pos": 8, "ran": 10},
                 {"date": "27 May 25", "venue": "Auteuil", "race": "3600m Sft Hdl 3rd", "pos": 3, "ran": 10},
             ]},
            {"name": "Jackie Hobbs", "trainer": "Harry Derham", "jockey": "Paul O'Brien",
             "odds": "33/1", "age": 6, "form": "119-141", "rating": 125,
             "cheltenham_record": "D",
             "last_run": "Won Warwick Jan 2026 (2m3f GS; form not strong)", "days_off": 47,
             "recent_races": [
                 {"date": "23 Jan 26", "venue": "Warwick", "race": "2m3f Sft Hdl", "pos": 1, "ran": 16},
                 {"date": "20 Dec 25", "venue": "Haydock", "race": "2m2f GS Hdl 4th", "pos": 4, "ran": 9},
                 {"date": "06 Nov 25", "venue": "Newbury", "race": "2m GS Hdl", "pos": 1, "ran": 13},
             ]},
            {"name": "St Irene", "trainer": "Nick Scholfield", "jockey": "Jack Quinlan",
             "odds": "40/1", "age": 6, "form": "630-211", "rating": 123,
             "cheltenham_record": "D",
             "last_run": "Won Listed Taunton Dec 2025 (progressive but needs career best here)", "days_off": 71,
             "recent_races": [
                 {"date": "30 Dec 25", "venue": "Taunton", "race": "2m104y GS Hdl (Listed)", "pos": 1, "ran": 6},
                 {"date": "20 Nov 25", "venue": "Wincanton", "race": "1m7f Gd Hdl", "pos": 1, "ran": 7},
                 {"date": "06 Nov 25", "venue": "Newbury", "race": "2m GS Hdl 2nd", "pos": 2, "ran": 13},
             ]},
            {"name": "Chosen Comrade", "trainer": "Peter Fahey", "jockey": "Sam Ewing",
             "odds": "66/1", "age": 5, "form": "114", "rating": 115,
             "cheltenham_record": "D",
             "last_run": "4th Punchestown Dec 2025 (12l behind stablemate Echoing Silence on heavy)", "days_off": 91,
             "recent_races": [
                 {"date": "11 Dec 25", "venue": "Punchestown", "race": "2m3f Hy Hdl 4th", "pos": 4, "ran": 6},
                 {"date": "19 Oct 25", "venue": "Limerick", "race": "2m Sft Hdl", "pos": 1, "ran": 11},
             ]},
            {"name": "Louve Dirlande", "trainer": "Paul Nolan", "jockey": "C. Stone-Walsh",
             "odds": "66/1", "age": 5, "form": "101", "rating": 112,
             "cheltenham_record": "D",
             "last_run": "Won Fontainebleau Oct 2025 (French hurdle winner; first run for Nolan)", "days_off": 158,
             "recent_races": [
                 {"date": "04 Oct 25", "venue": "Fontainebleau", "race": "3550m Sft Hdl", "pos": 1, "ran": 11},
                 {"date": "04 Sep 25", "venue": "Longchamp", "race": "2400m GS NHF last", "pos": 13, "ran": 13},
             ]},
            {"name": "Al Fonce", "trainer": "N. George & A. Zetterholm", "jockey": "Jordan Colin Gainford",
             "odds": "66/1", "age": 5, "form": "2113", "rating": 120,
             "cheltenham_record": "D",
             "last_run": "3rd Listed Taunton Dec 2025 (good ground, beaten by St Irene)", "days_off": 71,
             "recent_races": [
                 {"date": "30 Dec 25", "venue": "Taunton", "race": "2m104y GS Hdl (Listed) 3rd", "pos": 3, "ran": 6},
                 {"date": "22 Nov 25", "venue": "Lyon Parilly", "race": "3800m Hy Hdl", "pos": 1, "ran": 7},
                 {"date": "30 Oct 25", "venue": "Lyon Parilly", "race": "3400m Hy Hdl", "pos": 1, "ran": 8},
             ]},
            {"name": "Scavengers Reign", "trainer": "James Owen", "jockey": "Sam Twiston-Davies",
             "odds": "110/1", "age": 6, "form": "3-2U313", "rating": 110,
             "cheltenham_record": None,
             "last_run": "3rd Doncaster Feb 2026 (OR=108; beaten 4 races in 5)", "days_off": 34,
             "recent_races": [
                 {"date": "05 Feb 26", "venue": "Doncaster", "race": "2m3f Hy Hdl OR=108 3rd", "pos": 3, "ran": 6},
                 {"date": "26 Dec 25", "venue": "Wetherby", "race": "2m3f Sft Hdl", "pos": 1, "ran": 14},
                 {"date": "29 Nov 25", "venue": "Doncaster", "race": "2m3f Sft Hdl 3rd", "pos": 3, "ran": 8},
             ]},
        ]
    },
    "day2_race7": {   # Weatherbys Champion Bumper (Grade 1, 2m1f — 22 declared runners, Wed 11 Mar 17:20)
        "entries": [
            {"name": "Love Sign d'Aunou", "trainer": "W. P. Mullins", "jockey": "Mr P. W. Mullins",
             "odds": "9/2", "age": 5, "form": "1", "rating": 135,
             "cheltenham_record": None,
             "last_run": "Won Bumper Jan 2026", "days_off": 42},
            {"name": "Keep Him Company", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "9/1", "age": 6, "form": "11", "rating": 132,  # updated 7/1 -> 9/1 live
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Bumper Jan 2026", "days_off": 42},
            {"name": "Quiryn", "trainer": "W. P. Mullins", "jockey": "P. Townend",
             "odds": "8/1", "age": 4, "form": "1", "rating": 128,  # updated 7/1 -> 8/1 live
             "cheltenham_record": None,
             "last_run": "Won INH Flat Feb 2026", "days_off": 28},
            {"name": "The Mourne Rambler", "trainer": "Noel Meade", "jockey": "C. T. Keane",
             "odds": "8/1", "age": 5, "form": "1", "rating": 128,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Bumper Leopardstown Feb 2026", "days_off": 28},
            {"name": "Bass Hunter", "trainer": "Chris Gordon", "jockey": "Freddie Gordon",
             "odds": "11/1", "age": 5, "form": "11", "rating": 125,
             "cheltenham_record": None,
             "last_run": "Won Listed Bumper Ascot Jan 2026", "days_off": 42},
            {"name": "The Irish Avatar", "trainer": "W. P. Mullins", "jockey": "Harry Cobden",
             "odds": "13/2", "age": 5, "form": "1", "rating": 130,  # odds confirmed 13/2
             "cheltenham_record": None,
             "last_run": "Won INH Flat Feb 2026", "days_off": 28},
            {"name": "Its Only A Game", "trainer": "Martin Brassil", "jockey": "Mr J. L. Gleeson",
             "odds": "16/1", "age": 5, "form": "214", "rating": 120,
             "cheltenham_record": None,
             "last_run": "4th INH Flat Feb 2026", "days_off": 28},
            {"name": "Our Trigger", "trainer": "W. P. Mullins", "jockey": "D. E. Mullins",
             "odds": "11/1", "age": 5, "form": "1", "rating": 122,
             "cheltenham_record": None,
             "last_run": "Won INH Flat Feb 2026", "days_off": 28},
            {"name": "Mets Ta Ceinture", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "14/1", "age": 5, "form": "121", "rating": 122,
             "cheltenham_record": None,
             "last_run": "Won Bumper Feb 2026", "days_off": 28},
            {"name": "Broadway Ted", "trainer": "Gordon Elliott", "jockey": "Sean Bowen",
             "odds": "16/1", "age": 5, "form": "11", "rating": 125,  # updated 14/1 -> 16/1 live
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Bumper Jan 2026", "days_off": 42},
            {"name": "Charismatic Kid", "trainer": "Gordon Elliott", "jockey": "Sam Ewing",
             "odds": "20/1", "age": 5, "form": "13", "rating": 115,
             "cheltenham_record": None,
             "last_run": "3rd Grade 1 Bumper Jan 2026", "days_off": 42},
            {"name": "Moonverrin", "trainer": "Martin Hassett", "jockey": "Mr Finian Maguire",
             "odds": "25/1", "age": 5, "form": "211", "rating": 120,
             "cheltenham_record": None,
             "last_run": "Won Bumper Feb 2026", "days_off": 28},
            {"name": "The Wager", "trainer": "W. P. Mullins", "jockey": "Miss J. Townend",
             "odds": "20/1", "age": 5, "form": "2-1", "rating": 118,
             "cheltenham_record": None,
             "last_run": "Won Bumper Jan 2026", "days_off": 42},
            {"name": "Boycetown", "trainer": "Gavin Patrick Cromwell", "jockey": "Keith Donoghue",
             "odds": "25/1", "age": 5, "form": "21", "rating": 116,
             "cheltenham_record": None,
             "last_run": "Won INH Flat Feb 2026", "days_off": 28},
            {"name": "With Nolimit", "trainer": "Gordon Elliott", "jockey": "Mr H. C. Swan",
             "odds": "25/1", "age": 5, "form": "412", "rating": 126,
             "cheltenham_record": None,
             "last_run": "2nd Grade 1 Bumper Feb 2026", "days_off": 28},
            {"name": "Diamant Dore", "trainer": "Adrian Keatley", "jockey": "Brian Hughes",
             "odds": "30/1", "age": 5, "form": "1", "rating": 114,
             "cheltenham_record": None,
             "last_run": "Won INH Flat Feb 2026", "days_off": 28},
            {"name": "Wildes Legacy", "trainer": "Jamie Snowden", "jockey": "Gavin Sheehan",
             "odds": "TBD", "age": 5, "form": "11", "rating": 122,
             "cheltenham_record": None,
             "last_run": "Won Bumper Feb 2026", "days_off": 28},
            {"name": "Of Land And Sea", "trainer": "Paul Hennessy", "jockey": "Richard Condon",
             "odds": "25/1", "age": 5, "form": "451", "rating": 112,
             "cheltenham_record": None,
             "last_run": "Won Bumper Feb 2026", "days_off": 28},
            {"name": "The Skecher", "trainer": "Dan Skelton", "jockey": "Tristan Durrell",
             "odds": "33/1", "age": 5, "form": "1", "rating": 110,
             "cheltenham_record": None,
             "last_run": "Won Bumper Feb 2026", "days_off": 28},
            {"name": "Chicker", "trainer": "Fergal O'Brien", "jockey": "Jonathan Burke",
             "odds": "50/1", "age": 5, "form": "116", "rating": 110,
             "cheltenham_record": None,
             "last_run": "6th Bumper Feb 2026", "days_off": 28},
            {"name": "Tally Ho Back", "trainer": "Nigel Twiston-Davies", "jockey": "Sam Twiston-Davies",
             "odds": "50/1", "age": 5, "form": "426", "rating": 108,
             "cheltenham_record": None,
             "last_run": "6th Bumper Feb 2026", "days_off": 28},
            {"name": "Vango Can Go", "trainer": "Dan Skelton", "jockey": "Charlie Todd",
             "odds": "66/1", "age": 5, "form": "13", "rating": 106,
             "cheltenham_record": None,
             "last_run": "3rd Bumper Feb 2026", "days_off": 28},
        ]
    },
    "day3_race2": {   # Golden Miller Novice Handicap Chase  (Grade 2, 2m4f — 17 runners, Thu 12 Mar 14:00)
        # UPDATED 12/03/2026: NRs — Sixmilebridge (Fergal O'Brien/Kielan Woods, cloth #2, was SB pick) + Old Cowboy (#15).
        # NEW TOP PICK: Jordans Cross (CD winner, Trials Day C&D Jan 2026) or Meetmebythesea (big market move 9/2).
        # KEY MOVES: Meetmebythesea 14/1->9/2 (big fancy, returns from 2m to 2m4f), Slade Steel 9/1->6/1 (market shortener)
        #            Gold Dancer DRIFT 30/1->25/1 (7lb claimer A. McGuinness — top weight 152, non-stayer on heavy)
        # CHELTENHAM RECORDS CORRECTED: Slade Steel=Course (won 2024 Supreme); Bluesman=D only (Haydock win NOT Cheltenham);
        #            Ol Man Dingle=None (no Cheltenham win); Intense Approach=CD (both symbols on racecard)
        # AGES CORRECTED from 2024 yearbooks — Sixmilebridge=7, Jordans Cross=6, Meetmebythesea=6, Stencil=5 etc
        # HANDICAP race — jockey bonuses for Cheltenham SPECIALIST jockeys still apply; claimer age bonuses do NOT
        "entries": [
            {"name": "Regents Stroll", "trainer": "Paul Nicholls", "jockey": "Harry Cobden",
             "odds": "5/1", "age": 7, "form": "212-312", "rating": 145,
             "cheltenham_record": "D",
             "last_run": "2nd Novice Chase Cheltenham 01 Jan 2026 (2m4f gd)", "days_off": 70,
             "recent_races": [
                 {"date": "01 Jan 26", "venue": "Cheltenham", "race": "2m4f 127yds Gd Ch", "pos": 2, "ran": 5},
                 {"date": "16 Dec 25", "venue": "Wincanton", "race": "2m4f 35yds Sft Ch", "pos": 1, "ran": 2},
                 {"date": "28 Nov 25", "venue": "Newbury", "race": "2m3f 187yds Gd Ch", "pos": 3, "ran": 6},
                 {"date": "05 Apr 25", "venue": "Aintree", "race": "2m4f Gd Hdl", "pos": 2, "ran": 9},
                 {"date": "06 Mar 25", "venue": "Wincanton", "race": "2m3f 179yds Sft Hdl", "pos": 1, "ran": 5},
             ]},
            {"name": "Jordans Cross", "trainer": "Anthony Honeyball", "jockey": "Sam Twiston-Davies",
             "odds": "15/2", "age": 6, "form": "12-1F11", "rating": 140,
             "cheltenham_record": "CD winner",
             "last_run": "Won Trials Day C&D Cheltenham 24 Jan 2026 (2m4f sft, OR 134, 9 ran) — pointer to this race", "days_off": 46,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Cheltenham", "race": "2m4f 127yds Sft Ch (C&D)", "pos": 1, "ran": 9},
                 {"date": "13 Dec 25", "venue": "Doncaster", "race": "2m3f 31yds GS Ch", "pos": 1, "ran": 5},
                 {"date": "16 Nov 25", "venue": "Cheltenham", "race": "2m4f 44yds Sft Ch (C&D)", "pos": "F", "ran": 6},
                 {"date": "26 Oct 25", "venue": "Aintree", "race": "1m7f 176yds Gd Ch", "pos": 1, "ran": 6},
                 {"date": "29 Dec 24", "venue": "Doncaster", "race": "2m3f 88yds GS Hdl", "pos": 2, "ran": 5},
             ]},
            {"name": "Meetmebythesea", "trainer": "Ben Pauling", "jockey": "Ben Jones",
             "odds": "9/2", "age": 6, "form": "113-116", "rating": 139,
             "cheltenham_record": None,
             "last_run": "6th Game Spirit Newbury 07 Feb 2026 (2m sft — too short); return to 2m4f suits", "days_off": 32,
             "recent_races": [
                 {"date": "07 Feb 26", "venue": "Newbury", "race": "2m 92yds Sft Ch (Game Spirit — too sharp)", "pos": 6, "ran": 6},
                 {"date": "13 Jan 26", "venue": "Ayr", "race": "2m 110yds Hy Ch", "pos": 1, "ran": 5},
                 {"date": "15 Nov 25", "venue": "Wetherby", "race": "1m7f 36yds Sft Ch OR=133", "pos": 1, "ran": 5},
                 {"date": "08 Mar 25", "venue": "Sandown Park", "race": "2m3f 173yds GS Hdl 3rd (big field, OR=128)", "pos": 3, "ran": 16},
                 {"date": "24 Jan 25", "venue": "Doncaster", "race": "2m 128yds GS Hdl", "pos": 1, "ran": 8},
             ]},
            {"name": "Stencil", "trainer": "N. George & A. Zetterholm", "jockey": "Jonathan Burke",
             "odds": "17/2", "age": 5, "form": "620-521", "rating": 139,
             "cheltenham_record": None,
             "last_run": "Won Chepstow 27 Jan 2026 (2m sft) — needs to stay 2m4f (open question)", "days_off": 43,
             "recent_races": [
                 {"date": "27 Jan 26", "venue": "Chepstow", "race": "2m 16yds Sft Ch", "pos": 1, "ran": 5},
                 {"date": "19 Dec 25", "venue": "Ascot", "race": "2m 172yds GS Ch", "pos": 2, "ran": 4},
                 {"date": "15 Nov 25", "venue": "Cheltenham", "race": "1m7f 199yds Sft Ch", "pos": 5, "ran": 6},
                 {"date": "11 Mar 25", "venue": "Cheltenham", "race": "2m 87yds GS Hdl (Fred Winter flop)", "pos": 15, "ran": 22},
                 {"date": "25 Jan 25", "venue": "Cheltenham", "race": "2m 179yds Sft Hdl", "pos": 2, "ran": 10},
             ]},
            {"name": "Slade Steel", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "6/1", "age": 8, "form": "322-2B2", "rating": 146,
             "cheltenham_record": "Course winner",
             "last_run": "2nd Navan 17 Jan 2026 (3m hy) — consistent but seconditis over fences (4 x 2nd)", "days_off": 53,
             "recent_races": [
                 {"date": "17 Jan 26", "venue": "Navan", "race": "3m Hy Ch", "pos": 2, "ran": 7},
                 {"date": "31 Dec 25", "venue": "Punchestown", "race": "2m7f 197yds GS Ch (B fell)", "pos": "B", "ran": 10},
                 {"date": "06 Dec 25", "venue": "Navan", "race": "2m4f 150yds Hy Ch", "pos": 2, "ran": 16},
                 {"date": "16 Dec 24", "venue": "Naas", "race": "2m4f 29yds GS Ch", "pos": 2, "ran": 12},
                 {"date": "17 Nov 24", "venue": "Navan", "race": "2m4f 150yds GS Ch", "pos": 2, "ran": 4},
                 {"date": "30 Apr 24", "venue": "Punchestown", "race": "2m 149yds GS Hdl", "pos": 3, "ran": 9},
             ]},
            {"name": "Wingmen", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "11/1", "age": 8, "form": "206-232", "rating": 142,
             "cheltenham_record": "D",
             "last_run": "2nd Fairyhouse 01 Jan 2026 (2m5f gd) — solid but has lots to find with Slade Steel", "days_off": 70,
             "recent_races": [
                 {"date": "01 Jan 26", "venue": "Fairyhouse", "race": "2m5f 175yds GS Ch", "pos": 2, "ran": 7},
                 {"date": "06 Dec 25", "venue": "Navan", "race": "2m4f 150yds Hy Ch", "pos": 3, "ran": 16},
                 {"date": "16 Nov 25", "venue": "Navan", "race": "2m4f 150yds Hy Ch", "pos": 2, "ran": 12},
                 {"date": "06 Apr 25", "venue": "Fairyhouse", "race": "2m4f Gd Hdl", "pos": 6, "ran": 8},
                 {"date": "14 Mar 25", "venue": "Cheltenham", "race": "2m7f 213yds GS Hdl", "pos": 10, "ran": 20},
             ]},
            {"name": "The Bluesman", "trainer": "Olly Murphy", "jockey": "Sean Bowen",
             "odds": "12/1", "age": 7, "form": "1/13-121", "rating": 134,
             "cheltenham_record": "D",
             "last_run": "Won Haydock 14 Feb 2026 (2m3f gd — OR=126, lightly raced improver)", "days_off": 26,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Haydock Park", "race": "2m3f 203yds GS Ch OR=126", "pos": 1, "ran": 11},
                 {"date": "28 Dec 25", "venue": "Leicester", "race": "2m4f 25yds GS Ch OR=122", "pos": 2, "ran": 6},
                 {"date": "02 Dec 25", "venue": "Southwell", "race": "2m4f 88yds GS Ch OR=114 (debut)", "pos": 1, "ran": 6},
                 {"date": "25 Apr 25", "venue": "Chepstow", "race": "2m3f 100yds GF Hdl", "pos": 3, "ran": 5},
                 {"date": "22 Nov 24", "venue": "Chepstow", "race": "2m3f 100yds Gd Hdl", "pos": 1, "ran": 13},
             ]},
            {"name": "Kiss Will", "trainer": "Willie Mullins", "jockey": "J. J. Slevin",
             "odds": "14/1", "age": 6, "form": "171-322", "rating": 141,
             "cheltenham_record": None,
             "last_run": "2nd Punchestown 15 Feb 2026 (2m6f hy) — good effort, drop to 2m4f suits", "days_off": 24,
             "recent_races": [
                 {"date": "15 Feb 26", "venue": "Punchestown", "race": "2m6f 205yds Hy Ch", "pos": 2, "ran": 7},
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "2m5f 70yds Gd Ch", "pos": 2, "ran": 9},
                 {"date": "21 Nov 25", "venue": "Fairyhouse", "race": "2m4f Hy Ch", "pos": 3, "ran": 10},
                 {"date": "23 Apr 25", "venue": "Perth", "race": "2m7f 207yds Sft Hdl", "pos": 1, "ran": 14},
                 {"date": "12 Mar 25", "venue": "Cheltenham", "race": "2m5f GS Hdl (7th)", "pos": 7, "ran": 11},
             ]},
            {"name": "Kdeux Saint Fray", "trainer": "Anthony Honeyball", "jockey": "Rex Dingle",
             "odds": "16/1", "age": 6, "form": "2-F1243", "rating": 131,
             "cheltenham_record": "CD winner",
             "last_run": "3rd Kempton 21 Feb 2026 (3m gd — jumped left, longer trip may not suit drop back)", "days_off": 19,
             "recent_races": [
                 {"date": "21 Feb 26", "venue": "Kempton Park", "race": "3m GS Ch", "pos": 3, "ran": 13},
                 {"date": "24 Jan 26", "venue": "Cheltenham", "race": "2m4f 127yds Sft Ch (C&D, 5l behind Jordans Cross)", "pos": 4, "ran": 9},
                 {"date": "06 Dec 25", "venue": "Aintree", "race": "2m3f 200yds GS Ch", "pos": 2, "ran": 6},
                 {"date": "16 Nov 25", "venue": "Cheltenham", "race": "2m4f 44yds Sft Ch (C&D win)", "pos": 1, "ran": 6},
                 {"date": "25 Oct 25", "venue": "Cheltenham", "race": "2m4f 44yds Gd Ch (F fell)", "pos": "F", "ran": 14},
             ]},
            {"name": "Ol Man Dingle", "trainer": "Eoin Griffin", "jockey": "R. A. Doyle",
             "odds": "20/1", "age": 7, "form": "145-115", "rating": 145,
             "cheltenham_record": None,
             "last_run": "5th Fairyhouse 30 Nov 2025 (2m4f sft) — off since, cheekpieces added", "days_off": 101,
             "recent_races": [
                 {"date": "30 Nov 25", "venue": "Fairyhouse", "race": "2m4f 55yds Sft Ch Grade 1 (5th)", "pos": 5, "ran": 6},
                 {"date": "02 Nov 25", "venue": "Cork", "race": "2m4f GS Ch (Grade 3 win)", "pos": 1, "ran": 5},
                 {"date": "07 Oct 25", "venue": "Galway", "race": "2m2f 54yds Sft Ch (debut)", "pos": 1, "ran": 6},
                 {"date": "02 Feb 25", "venue": "Leopardstown", "race": "2m GS Hdl (DRF, big field hdcp)", "pos": 4, "ran": 18},
             ]},
            {"name": "Ben Solo", "trainer": "Rebecca Curtis", "jockey": "Brian Hughes",
             "odds": "25/1", "age": 7, "form": "28-512U", "rating": 128,
             "cheltenham_record": None,
             "last_run": "Fell Chepstow 27 Dec 2025 (in lead when fell 3 out 2m3f) — 5lb out of weights", "days_off": 74,
             "recent_races": [
                 {"date": "27 Dec 25", "venue": "Chepstow", "race": "2m3f 98yds GF Ch (U fell in lead)", "pos": "U", "ran": 7},
                 {"date": "06 Dec 25", "venue": "Chepstow", "race": "2m3f 98yds GS Ch", "pos": 2, "ran": 8},
                 {"date": "21 Nov 25", "venue": "Chepstow", "race": "2m3f 98yds GS Ch", "pos": 1, "ran": 9},
                 {"date": "05 Nov 25", "venue": "Chepstow", "race": "2m 16yds Gd Ch", "pos": 5, "ran": 10},
             ]},
            {"name": "Gold Dancer", "trainer": "Willie Mullins", "jockey": "A. McGuinness(7)",
             "odds": "25/1", "age": 7, "form": "111224", "rating": 152,
             "cheltenham_record": None,
             "last_run": "4th Navan 08 Feb 2026 (3m hy — non-stayer heavy; top weight 152)", "days_off": 31,
             "recent_races": [
                 {"date": "08 Feb 26", "venue": "Navan", "race": "3m Hy Ch (non-stayer)", "pos": 4, "ran": 4},
                 {"date": "28 Dec 25", "venue": "Limerick", "race": "2m5f Hy Ch 2nd (Grade 3)", "pos": 2, "ran": 4},
                 {"date": "30 Nov 25", "venue": "Fairyhouse", "race": "2m4f 55yds Sft Ch 2nd (Grade 1)", "pos": 2, "ran": 6},
                 {"date": "05 Oct 25", "venue": "Tipperary", "race": "2m3f 160yds GS Ch (Grade 3 win)", "pos": 1, "ran": 5},
                 {"date": "31 Jul 25", "venue": "Galway", "race": "2m2f 54yds GS Ch", "pos": 1, "ran": 11},
             ]},
            {"name": "King Alexander", "trainer": "Willie Mullins", "jockey": "D. E. Mullins",
             "odds": "20/1", "age": 8, "form": "903-231", "rating": 144,
             "cheltenham_record": None,
             "last_run": "Won Gowran Park 14 Feb 2026 (2m3f hy) — career best RPR, peaking now", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Gowran Park", "race": "2m3f 70yds Hy Ch (career best RPR)", "pos": 1, "ran": 8},
                 {"date": "22 Jan 26", "venue": "Gowran Park", "race": "2m4f Hy Ch", "pos": 3, "ran": 9},
                 {"date": "15 Dec 25", "venue": "Naas", "race": "2m4f 40yds Hy Ch", "pos": 2, "ran": 9},
                 {"date": "26 Apr 25", "venue": "Sandown Park", "race": "2m3f 173yds GF Hdl", "pos": 3, "ran": 10},
                 {"date": "12 Mar 25", "venue": "Cheltenham", "race": "2m5f GS Hdl (Fred Winter 15th)", "pos": 15, "ran": 26},
             ]},
            {"name": "Western Knight", "trainer": "Joe Tizzard", "jockey": "Brendan Powell",
             "odds": "40/1", "age": 7, "form": "U8-4112", "rating": 136,
             "cheltenham_record": None,
             "last_run": "2nd Ascot Reynoldstown 14 Feb 2026 (2m7f gd — 4-4 at 2m3f-2m5f)", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Ascot", "race": "2m7f 185yds GS Ch (Reynoldstown 2nd)", "pos": 2, "ran": 3},
                 {"date": "23 Jan 26", "venue": "Doncaster", "race": "2m3f 31yds Sft Ch", "pos": 1, "ran": 4},
                 {"date": "03 Dec 25", "venue": "Haydock Park", "race": "2m5f 127yds Gd Ch", "pos": 1, "ran": 3},
                 {"date": "07 Nov 25", "venue": "Exeter", "race": "3m 54yds GS Ch", "pos": 4, "ran": 4},
             ]},
            {"name": "Intense Approach", "trainer": "John McConnell", "jockey": "Alex Harvey(3)",
             "odds": "50/1", "age": 7, "form": "P8-15U5", "rating": 137,
             "cheltenham_record": "CD winner",
             "last_run": "5th Navan 28 Feb 2026 (2m hy) — headgear first time; patchy form since Galway win", "days_off": 11,
             "recent_races": [
                 {"date": "28 Feb 26", "venue": "Navan", "race": "2m Hy Ch (headgear debut)", "pos": 5, "ran": 5},
                 {"date": "01 Feb 26", "venue": "Musselburgh", "race": "2m4f 68yds GS Ch (U fell)", "pos": "U", "ran": 6},
                 {"date": "25 Oct 25", "venue": "Cheltenham", "race": "3m1f Gd Ch", "pos": 5, "ran": 7},
                 {"date": "01 Aug 25", "venue": "Galway", "race": "2m6f 111yds GS Ch (debut 1/16)", "pos": 1, "ran": 16},
             ]},
            {"name": "Wheres My Jet", "trainer": "Willie Mullins", "jockey": "S. F. O'Keeffe",
             "odds": "50/1", "age": 7, "form": "U47F06", "rating": 133,
             "cheltenham_record": None,
             "last_run": "6th DRF Leopardstown 01 Feb 2026 (2m5f sft) — non-completions from bad mistakes", "days_off": 38,
             "recent_races": [
                 {"date": "01 Feb 26", "venue": "Leopardstown", "race": "2m5f 107yds Sft Ch (DRF, 6/23)", "pos": 6, "ran": 23},
                 {"date": "26 Dec 25", "venue": "Leopardstown", "race": "2m1f Gd Ch", "pos": 10, "ran": 20},
                 {"date": "13 Dec 25", "venue": "Fairyhouse", "race": "2m 55yds Sft Ch (F fell)", "pos": "F", "ran": 13},
                 {"date": "22 Nov 25", "venue": "Punchestown", "race": "2m2f 200yds Sft Ch", "pos": 7, "ran": 12},
             ]},
            {"name": "Dr Eggman", "trainer": "Willie Mullins", "jockey": "J. P. Shinnick(3)",
             "odds": "50/1", "age": 8, "form": "129-833", "rating": 130,
             "cheltenham_record": None,
             "last_run": "3rd Thurles 05 Feb 2026 — behind shorter-priced stablemates, OR only 130", "days_off": 34,
             "recent_races": [
                 {"date": "05 Feb 26", "venue": "Thurles", "race": "2m2f Hy Ch (3rd behind stablemates)", "pos": 3, "ran": 10},
                 {"date": "14 Jan 26", "venue": "Fairyhouse", "race": "2m1f 30yds Sft Ch", "pos": 3, "ran": 8},
                 {"date": "21 Nov 25", "venue": "Fairyhouse", "race": "2m4f Hy Ch", "pos": 8, "ran": 10},
                 {"date": "16 Apr 25", "venue": "Cheltenham", "race": "2m4f 56yds Gd Hdl", "pos": 2, "ran": 7},
             ]},
            {"name": "Moon Rocket", "trainer": "Kim Bailey & Mat Nicholls", "jockey": "Tom Bellamy",
             "odds": "20/1", "age": 6, "form": "22P-126", "rating": 140,
             "cheltenham_record": "D",
             "last_run": "6th Windsor 18 Jan 2026 (3m sft) — wind surgery since; now tongue-tie; interesting pedigree", "days_off": 52,
             "recent_races": [
                 {"date": "18 Jan 26", "venue": "Windsor", "race": "3m 60yds Sft Ch (6/6)", "pos": 6, "ran": 6},
                 {"date": "12 Dec 25", "venue": "Doncaster", "race": "2m7f 214yds Sft Ch", "pos": 2, "ran": 2},
                 {"date": "28 Nov 25", "venue": "Doncaster", "race": "2m7f 214yds GS Ch OR=134", "pos": 1, "ran": 4},
                 {"date": "04 Apr 25", "venue": "Aintree", "race": "3m 149yds Gd Hdl (P pulled)", "pos": "P", "ran": 13},
                 {"date": "15 Feb 25", "venue": "Haydock Park", "race": "3m 58yds GS Hdl", "pos": 2, "ran": 6},
             ]},
        ]
    },
    "day3_race3": {   # David Nicholson / Close Brothers Mares' Hurdle  (Grade 1, 2m4f — 7 runners, Thu 12 Mar 14:40)
        # UPDATED 11/03/2026 from detailed racecard. E/W: 1/4 odds, 2 PLACES ONLY.
        # Wodhooh: age=6 (not 7), CD winner confirmed (won Martin Pipe C&D 2025 + won this course twice), 4/6
        # Jade De Grugy: D only (not CD); switched back from chasing to hurdles today; Townend/Mullins 11/4
        # Jetara: blinkers FIRST TIME (replaces cheekpieces) — change of headgear noted
        # Take No Chances: no Cheltenham symbol — no record here in chases
        # Dream On Baby: age=6 (not 8); steadily progressive lightly-raced mare
        "entries": [
            {"name": "Wodhooh", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "4/6", "age": 6, "form": "1/112-11", "rating": 162,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 3 2m4f Leopardstown 29 Dec 2025 (gave weight and beat Feet Of A Dancer 2l+)", "days_off": 72,
             "recent_races": [
                 {"date": "29 Dec 25", "venue": "Leopardstown", "race": "2m4f 103yds GS Hdl (Grade 3)", "pos": 1, "ran": 5},
                 {"date": "22 Nov 25", "venue": "Ascot", "race": "2m3f 63yds GS Hdl (Grade 2)", "pos": 1, "ran": 8},
                 {"date": "03 Apr 25", "venue": "Aintree", "race": "2m4f Gd Hdl (Grade 1 — only defeat)", "pos": 2, "ran": 6},
                 {"date": "14 Mar 25", "venue": "Cheltenham", "race": "2m4f 56yds GS Hdl (Martin Pipe C&D 1/24 OR=141)", "pos": 1, "ran": 24},
                 {"date": "14 Dec 24", "venue": "Cheltenham", "race": "2m4f 56yds GS Hdl (C&D OR=130)", "pos": 1, "ran": 12},
             ]},
            {"name": "Jade De Grugy", "trainer": "Willie Mullins", "jockey": "P. Townend",
             "odds": "11/4", "age": 7, "form": "12-1321", "rating": 152,
             "cheltenham_record": "D",
             "last_run": "Won Grade 2 Chase Thurles 18 Jan 2026 (2m4f ys) — switching back from chasing to hurdles", "days_off": 52,
             "recent_races": [
                 {"date": "18 Jan 26", "venue": "Thurles", "race": "2m4f 198yds GS Ch (Grade 2 win — over fences!)", "pos": 1, "ran": 6},
                 {"date": "27 Dec 25", "venue": "Limerick", "race": "2m6f 120yds Hy Ch (Grade 2, 2nd)", "pos": 2, "ran": 7},
                 {"date": "23 Nov 25", "venue": "Cork", "race": "2m5f 50yds Sft Ch (3rd on chase debut)", "pos": 3, "ran": 7},
                 {"date": "03 May 25", "venue": "Punchestown", "race": "2m4f 118yds GS Hdl (Grade 1 win)", "pos": 1, "ran": 6},
                 {"date": "11 Mar 25", "venue": "Cheltenham", "race": "2m3f 200yds GS Hdl (2nd Lossiemouth)", "pos": 2, "ran": 10},
             ]},
            {"name": "Feet Of A Dancer", "trainer": "Paul Nolan", "jockey": "S. F. O'Keeffe",
             "odds": "8/1", "age": 7, "form": "343-121", "rating": 148,
             "cheltenham_record": "D",
             "last_run": "Won Grade 2 3m Doncaster 24 Jan 2026 (sft — beat Dream On Baby 2l, Jetara 9l 3rd)", "days_off": 46,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Doncaster", "race": "3m 84yds Sft Hdl (Grade 2 win)", "pos": 1, "ran": 8},
                 {"date": "29 Dec 25", "venue": "Leopardstown", "race": "2m4f 103yds GS Hdl (2nd to Wodhooh — 2l)", "pos": 2, "ran": 5},
                 {"date": "23 Nov 25", "venue": "Punchestown", "race": "2m2f 48yds Sft Hdl (Listed win)", "pos": 1, "ran": 5},
                 {"date": "21 Apr 25", "venue": "Fairyhouse", "race": "2m4f Sft Hdl (3rd)", "pos": 3, "ran": 10},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m7f 213yds GS Hdl (Pertemps Final 4th)", "pos": 4, "ran": 24},
             ]},
            {"name": "Take No Chances", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "8/1", "age": 8, "form": "35-6233", "rating": 147,
             "cheltenham_record": None,
             "last_run": "3rd Windsor 16 Jan 2026 (2m4f sft) — 4 unplaced runs this season, each-way player", "days_off": 54,
             "recent_races": [
                 {"date": "16 Jan 26", "venue": "Windsor", "race": "2m4f Sft Hdl (3rd/5)", "pos": 3, "ran": 5},
                 {"date": "28 Nov 25", "venue": "Newbury", "race": "3m 57yds GS Hdl (3rd/7)", "pos": 3, "ran": 7},
                 {"date": "01 Nov 25", "venue": "Wetherby", "race": "3m 26yds Gd Hdl (2nd/5)", "pos": 2, "ran": 5},
                 {"date": "11 Oct 25", "venue": "Chepstow", "race": "2m3f 100yds GF Hdl (6th OR=146)", "pos": 6, "ran": 14},
                 {"date": "03 Apr 25", "venue": "Aintree", "race": "2m4f Gd Hdl (3rd behind Lossiemouth & Wodhooh)", "pos": 3, "ran": 6},
             ]},
            {"name": "Dream On Baby", "trainer": "Emmet Mullins", "jockey": "Donagh Meyler",
             "odds": "25/1", "age": 6, "form": "P22132", "rating": 138,
             "cheltenham_record": None,
             "last_run": "2nd Grade 2 3m Doncaster 24 Jan 2026 (beaten by Feet Of A Dancer — outstayed)", "days_off": 46,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Doncaster", "race": "3m 84yds Sft Hdl (Grade 2, 2nd)", "pos": 2, "ran": 8},
                 {"date": "29 Dec 25", "venue": "Leopardstown", "race": "2m4f 103yds GS Hdl (3rd)", "pos": 3, "ran": 5},
                 {"date": "24 Nov 25", "venue": "Kempton Park", "race": "2m5f GS Hdl (Listed win)", "pos": 1, "ran": 6},
                 {"date": "26 Oct 25", "venue": "Wexford", "race": "2m4f Sft Hdl (2nd)", "pos": 2, "ran": 4},
                 {"date": "09 Oct 25", "venue": "Thurles", "race": "2m 66yds GS Flat", "pos": 2, "ran": 11},
             ]},
            {"name": "Jetara", "trainer": "Mrs J. Harrington", "jockey": "Sam Ewing",
             "odds": "25/1", "age": 8, "form": "43-3373", "rating": 135,
             "cheltenham_record": "D",
             "last_run": "3rd Grade 2 3m Doncaster 24 Jan 2026 (9l behind Feet Of A Dancer — blinkers first time today)", "days_off": 46,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Doncaster", "race": "3m 84yds Sft Hdl (Grade 2, 3rd/8)", "pos": 3, "ran": 8},
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "2m7f 80yds Gd Hdl (7th/8)", "pos": 7, "ran": 8},
                 {"date": "17 Nov 25", "venue": "Navan", "race": "2m4f 50yds Hy Hdl (3rd/5)", "pos": 3, "ran": 5},
                 {"date": "03 Apr 25", "venue": "Aintree", "race": "3m 149yds Gd Hdl (Grade 1, 3rd)", "pos": 3, "ran": 8},
                 {"date": "11 Mar 25", "venue": "Cheltenham", "race": "2m3f GS Hdl (11l 4th behind Lossiemouth)", "pos": 4, "ran": 10},
             ]},
            {"name": "Sunset Marquesa", "trainer": "Joe Tizzard", "jockey": "Brendan Powell",
             "odds": "66/1", "age": 7, "form": "1F-3143", "rating": 130,
             "cheltenham_record": "D",
             "last_run": "3rd Ascot 17 Jan 2026 (2m sft) — has plenty to find at Grade 1 level", "days_off": 53,
             "recent_races": [
                 {"date": "17 Jan 26", "venue": "Ascot", "race": "1m7f 157yds Sft Hdl (3rd/4)", "pos": 3, "ran": 4},
                 {"date": "03 Jan 26", "venue": "Sandown Park", "race": "2m3f 178yds GS Hdl (4th)", "pos": 4, "ran": 6},
                 {"date": "06 Dec 25", "venue": "Sandown Park", "race": "2m3f 178yds Sft Hdl (win OR=119)", "pos": 1, "ran": 7},
                 {"date": "07 Nov 25", "venue": "Exeter", "race": "2m2f 111yds GS Hdl (3rd)", "pos": 3, "ran": 11},
                 {"date": "22 Mar 25", "venue": "Newbury", "race": "2m4f 118yds Gd Hdl (F fell)", "pos": "F", "ran": 15},
             ]},
        ]
    },
    "day3_race6": {   # Pertemps Network Final Handicap Hurdle  (Grade 3, 3m — 26 runners, Thu 12 Mar 16:40)
        # UPDATED 11/03/2026 from detailed racecard. E/W: 1/5 odds, 6 PLACES.
        # Supremely West: OR=135 (not 148!), odds=11/4 favourite, age=8. Key: 3rd of 17 in Cheltenham qualifier Oct, now 2lb lower.
        # Cest Different: age=6 (not 9!), NO Cheltenham record (only D symbol was wrong — no C/D shown), odds=15/2.
        # Kikijo: age=6 (not 8!), OR=135, CD winner (won 3m Cheltenham Nov, Sandown Dec).
        # Staffordshire Knot: age=8 (not 7), OR=152 (topweight), D symbol. 3 wins + 1 second this winter.
        # Ikarak: age=8 (not 7), odds=33/1 (drifted from 14/1).
        # Absolutely Doyen: age=6 (not 8!), 5-5 unbeaten Paul Nicholls.
        # Ace Of Spades: "Course winner" (C symbol only — won Jan qualifier at Cheltenham).
        # HANDICAP race — no jockey bonuses apply per scoring engine rules.
        "entries": [
            {"name": "Supremely West", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "7/2", "age": 8, "form": "63-3546", "rating": 135,
             "cheltenham_record": "D",
             "last_run": "6th Aintree 26 Dec 2025 (2m4f gd, 6/8, OR137) — off since; 3rd of 17 Cheltenham qualifier Oct was eye-catching, now 2lb lower", "days_off": 75,
             "recent_races": [
                 {"date": "26 Dec 25", "venue": "Aintree", "race": "2m4f Gd Hdl (6/8 OR137)", "pos": 6, "ran": 8},
                 {"date": "06 Dec 25", "venue": "Sandown Park", "race": "2m7f 103yds Sft Hdl (4/7 OR138)", "pos": 4, "ran": 7},
                 {"date": "15 Nov 25", "venue": "Cheltenham", "race": "2m7f 208yds Sft Hdl (5/8 OR138)", "pos": 5, "ran": 8},
                 {"date": "25 Oct 25", "venue": "Cheltenham", "race": "2m7f 208yds GS Hdl (3/17 OR137 — eye-catcher)", "pos": 3, "ran": 17},
                 {"date": "24 Apr 25", "venue": "Warwick", "race": "3m1f Gd Hdl (3/6 OR137)", "pos": 3, "ran": 6},
                 {"date": "15 Feb 25", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (6/13 OR137)", "pos": 6, "ran": 13},
             ]},
            {"name": "Cest Different", "trainer": "Sam Thomas", "jockey": "Dylan Johnston",
             "odds": "15/2", "age": 6, "form": "4711-11", "rating": 131,
             "cheltenham_record": None,
             "last_run": "Won Newbury 14 Jan 2026 (3m GS, 1/17, OR121 — emphatic, up 10lb today but still only 8 starts)", "days_off": 56,
             "recent_races": [
                 {"date": "14 Jan 26", "venue": "Newbury", "race": "3m 57yds GS Hdl (1/17 OR121)", "pos": 1, "ran": 17},
                 {"date": "26 Nov 25", "venue": "Market Rasen", "race": "2m7f 16yds GS Hdl (1/8 OR109)", "pos": 1, "ran": 8},
                 {"date": "22 Feb 25", "venue": "Chepstow", "race": "2m3f 100yds Sft Hdl (1/10 OR92)", "pos": 1, "ran": 10},
                 {"date": "17 Feb 25", "venue": "Carlisle", "race": "2m3f 61yds GS Hdl (1/10 OR92)", "pos": 1, "ran": 10},
                 {"date": "24 Jan 25", "venue": "Sandown Park", "race": "1m7f 216yds Sft Hdl (7/10)", "pos": 7, "ran": 10},
                 {"date": "05 Jan 25", "venue": "Chepstow", "race": "2m 11yds Hy Hdl (4/10)", "pos": 4, "ran": 10},
             ]},
            {"name": "Electric Mason", "trainer": "Chris Gordon", "jockey": "Freddie Gordon",
             "odds": "10/1", "age": 7, "form": "5107-21", "rating": 139,
             "cheltenham_record": "D",
             "last_run": "Won Haydock 22 Nov 2025 (3m GS, 1/17, OR132 — valuable race, big field, should be raring to go today)", "days_off": 110,
             "recent_races": [
                 {"date": "22 Nov 25", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (1/17 OR132 — big field win)", "pos": 1, "ran": 17},
                 {"date": "25 Oct 25", "venue": "Cheltenham", "race": "2m7f 208yds GS Hdl (2/17 OR128 — 2nd to Ma Shantou)", "pos": 2, "ran": 17},
                 {"date": "26 Apr 25", "venue": "Sandown Park", "race": "2m3f 173yds GF Hdl (7/10 OR130)", "pos": 7, "ran": 10},
                 {"date": "14 Mar 25", "venue": "Cheltenham", "race": "2m4f 56yds GS Hdl (14/24 OR132, Martin Pipe)", "pos": 14, "ran": 24},
                 {"date": "26 Jan 25", "venue": "Fontwell Park", "race": "2m3f 29yds Sft Hdl (1/3)", "pos": 1, "ran": 3},
                 {"date": "28 Dec 24", "venue": "Newbury", "race": "2m4f 118yds GS Hdl (5/7)", "pos": 5, "ran": 7},
             ]},
            {"name": "Bold Endeavour", "trainer": "Nicky Henderson", "jockey": "James Bowen",
             "odds": "9/1", "age": 10, "form": "0/07PP-3", "rating": 130,
             "cheltenham_record": None,
             "last_run": "3rd Huntingdon 22 Jan 2026 (3m1f sft, 3/6, OR130) — 4th in 2024 Pertemps off 13lb higher", "days_off": 48,
             "recent_races": [
                 {"date": "22 Jan 26", "venue": "Huntingdon", "race": "3m1f 10yds Sft Hdl (3/6 OR130 — year off return)", "pos": 3, "ran": 6},
                 {"date": "18 Jan 25", "venue": "Haydock Park", "race": "3m 58yds Sft Hdl (P/11 OR136)", "pos": "P", "ran": 11},
                 {"date": "27 Nov 24", "venue": "Market Rasen", "race": "2m7f 16yds Sft Hdl (P/7 OR139)", "pos": "P", "ran": 7},
                 {"date": "09 Nov 24", "venue": "Aintree", "race": "3m 149yds Gd Hdl (7/8 OR141)", "pos": 7, "ran": 8},
                 {"date": "11 May 24", "venue": "Haydock Park", "race": "3m 58yds GF Hdl (13/16 OR143)", "pos": 13, "ran": 16},
                 {"date": "13 Apr 24", "venue": "Aintree", "race": "3m 149yds GS Hdl (11/21 OR144)", "pos": 11, "ran": 21},
             ]},
            {"name": "Ace Of Spades", "trainer": "Dan Skelton", "jockey": "Kielan Woods",
             "odds": "9/1", "age": 7, "form": "42-1421", "rating": 139,
             "cheltenham_record": "Course winner",
             "last_run": "Won Huntingdon 22 Jan 2026 (3m1f sft, 1/6, OR134) — 2nd to Ma Shantou at Cheltenham Jan 1st", "days_off": 48,
             "recent_races": [
                 {"date": "22 Jan 26", "venue": "Huntingdon", "race": "3m1f 10yds Sft Hdl (1/6 OR134 WIN)", "pos": 1, "ran": 6},
                 {"date": "01 Jan 26", "venue": "Cheltenham", "race": "2m7f 213yds Gd Hdl (2/7 OR130 — 2nd to Ma Shantou)", "pos": 2, "ran": 7},
                 {"date": "22 Nov 25", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (4/17 OR130)", "pos": 4, "ran": 17},
                 {"date": "26 Oct 25", "venue": "Aintree", "race": "2m4f GS Hdl (1/6 OR127 WIN)", "pos": 1, "ran": 6},
                 {"date": "11 Apr 25", "venue": "Ayr", "race": "3m 70yds Gd Hdl (2/13 OR125)", "pos": 2, "ran": 13},
                 {"date": "01 Mar 25", "venue": "Kelso", "race": "2m4f 189yds GS Hdl (4/10 OR123)", "pos": 4, "ran": 10},
             ]},
            {"name": "Absolutely Doyen", "trainer": "Paul Nicholls", "jockey": "Harry Cobden",
             "odds": "14/1", "age": 6, "form": "2-11111", "rating": 135,
             "cheltenham_record": "D",
             "last_run": "Won Musselburgh 31 Jan 2026 (2m7f GS, 1/5) — perfect 5-5, all on gd/gd-sft; still unexposed", "days_off": 38,
             "recent_races": [
                 {"date": "31 Jan 26", "venue": "Musselburgh", "race": "2m7f 180yds GS Hdl (1/5)", "pos": 1, "ran": 5},
                 {"date": "26 Dec 25", "venue": "Wincanton", "race": "3m 150yds GS Hdl (1/9 OR123 Wincanton qual WIN)", "pos": 1, "ran": 9},
                 {"date": "22 Nov 25", "venue": "Ascot", "race": "3m 102yds Sft Hdl (1/9 OR115 WIN)", "pos": 1, "ran": 9},
                 {"date": "06 Nov 25", "venue": "Sedgefield", "race": "2m3f 188yds GS Hdl (1/5)", "pos": 1, "ran": 5},
                 {"date": "18 Oct 25", "venue": "Stratford-on-Avon", "race": "2m6f 7yds Gd Hdl (1/4)", "pos": 1, "ran": 4},
                 {"date": "12 Mar 25", "venue": "Huntingdon", "race": "1m7f 171yds Gd Hdl (2/11)", "pos": 2, "ran": 11},
             ]},
            {"name": "Kikijo", "trainer": "Philip Hobbs & Johnson White", "jockey": "Callum Pritchard(3)",
             "odds": "12/1", "age": 6, "form": "412-411", "rating": 135,
             "cheltenham_record": "CD winner",
             "last_run": "Won Sandown 06 Dec 2025 (2m7f sft, 1/7, OR127) — also won Cheltenham C&D Nov under same rider", "days_off": 96,
             "recent_races": [
                 {"date": "06 Dec 25", "venue": "Sandown Park", "race": "2m7f 103yds Sft Hdl (1/7 OR127 WIN)", "pos": 1, "ran": 7},
                 {"date": "15 Nov 25", "venue": "Cheltenham", "race": "2m7f 208yds Sft Hdl (1/8 OR120 C&D WIN)", "pos": 1, "ran": 8},
                 {"date": "26 Oct 25", "venue": "Aintree", "race": "3m 149yds Gd Hdl (4/12 OR119)", "pos": 4, "ran": 12},
                 {"date": "21 Mar 25", "venue": "Newbury", "race": "2m6f 93yds Gd Ch (2/6 OR121, chase)", "pos": 2, "ran": 6},
                 {"date": "28 Feb 25", "venue": "Newbury", "race": "2m3f 187yds Sft Ch (1/4 OR117, chase WIN)", "pos": 1, "ran": 4},
                 {"date": "31 Dec 24", "venue": "Uttoxeter", "race": "2m3f 207yds Hy Hdl (4/8 OR121)", "pos": 4, "ran": 8},
             ]},
            {"name": "Champagne Chic", "trainer": "Jeremy Scott", "jockey": "Lorcan Williams",
             "odds": "25/1", "age": 6, "form": "40-6211", "rating": 131,
             "cheltenham_record": "D",
             "last_run": "Won Haydock 14 Feb 2026 (3m GS, 1/13, OR124 — 5l+ ahead, still going away; 7lb rise)", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (1/13 OR124 — good win)", "pos": 1, "ran": 13},
                 {"date": "15 Jan 26", "venue": "Wincanton", "race": "3m 150yds Hy Hdl (1/10 OR118 WIN)", "pos": 1, "ran": 10},
                 {"date": "06 Dec 25", "venue": "Chepstow", "race": "2m7f 131yds GS Hdl (2/11 OR114)", "pos": 2, "ran": 11},
                 {"date": "07 Nov 25", "venue": "Exeter", "race": "2m7f 25yds Sft Hdl (6/14 OR117)", "pos": 6, "ran": 14},
                 {"date": "24 Apr 25", "venue": "Perth", "race": "2m 47yds Sft Hdl (14/14 OR119)", "pos": 14, "ran": 14},
                 {"date": "23 Feb 25", "venue": "Fontwell Park", "race": "2m1f 162yds Hy Hdl (4/4)", "pos": 4, "ran": 4},
             ]},
            {"name": "Gowel Road", "trainer": "Nigel & Willy Twiston-Davies", "jockey": "Toby McCain-Mitchell(5)",
             "odds": "59/1", "age": 10, "form": "037442", "rating": 148,
             "cheltenham_record": "CD winner",
             "last_run": "2nd Chepstow 21 Feb 2026 (2m7f sft, 2/11, OR146 under McCain-Mitchell) — 6th in this 2024, regularCheltenham performer", "days_off": 18,
             "recent_races": [
                 {"date": "21 Feb 26", "venue": "Chepstow", "race": "2m7f 131yds Sft Hdl (2/11 OR146 — big run)", "pos": 2, "ran": 11},
                 {"date": "24 Jan 26", "venue": "Cheltenham", "race": "2m7f 213yds Sft Hdl (4/6 — Cheltenham run)", "pos": 4, "ran": 6},
                 {"date": "01 Jan 26", "venue": "Cheltenham", "race": "2m4f 56yds Gd Hdl (4/6 — Cheltenham run)", "pos": 4, "ran": 6},
                 {"date": "12 Dec 25", "venue": "Cheltenham", "race": "3m2f 70yds Gd Ch (7/9 OR146, chase)", "pos": 7, "ran": 9},
                 {"date": "15 Nov 25", "venue": "Cheltenham", "race": "2m7f 208yds Sft Hdl (3/8 OR146)", "pos": 3, "ran": 8},
                 {"date": "25 Oct 25", "venue": "Cheltenham", "race": "2m7f 208yds GS Hdl (11/17 OR148)", "pos": 11, "ran": 17},
             ]},
            {"name": "Letos", "trainer": "Anthony Mullins", "jockey": "D. E. Mullins",
             "odds": "14/1", "age": 6, "form": "42-2120", "rating": 132,
             "cheltenham_record": None,
             "last_run": "10th Naas 09 Jan 2026 (2m4f sft, tailed off Grade 1 novice) — trip/ground question; 2nd in Carlisle qualifier Dec", "days_off": 61,
             "recent_races": [
                 {"date": "09 Jan 26", "venue": "Naas", "race": "2m4f Sft Hdl (10/10 — tailed off Grade 1)", "pos": 10, "ran": 10},
                 {"date": "14 Dec 25", "venue": "Carlisle", "race": "3m1f Sft Hdl (2/6 OR131 — Pertemps qual)", "pos": 2, "ran": 6},
                 {"date": "09 Nov 25", "venue": "Naas", "race": "2m4f Hy Hdl (1/14 OR119 WIN)", "pos": 1, "ran": 14},
                 {"date": "06 Oct 25", "venue": "Tipperary", "race": "2m 100yds Sft Hdl (2/11)", "pos": 2, "ran": 11},
                 {"date": "22 Apr 25", "venue": "Fairyhouse", "race": "2m3f 180yds Sft Hdl (2/24)", "pos": 2, "ran": 24},
                 {"date": "04 Apr 25", "venue": "Wexford", "race": "2m3f 100yds Sft Ch (4/10 OR122, chase)", "pos": 4, "ran": 10},
             ]},
            {"name": "Minella Emperor", "trainer": "Emmet Mullins", "jockey": "Mr M. J. O'Neill(7)",
             "odds": "11/1", "age": 7, "form": "1P4322", "rating": 130,
             "cheltenham_record": None,
             "last_run": "2nd Haydock 14 Feb 2026 (3m GS, 2/13, OR129) — 6-1 but not nearly as strong as Champagne Chic on run-in; cheekpieces today", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (2/13 OR129 — Pertemps qual)", "pos": 2, "ran": 13},
                 {"date": "18 Jan 26", "venue": "Thurles", "race": "2m6f GS Hdl (2/6)", "pos": 2, "ran": 6},
                 {"date": "28 Dec 25", "venue": "Limerick", "race": "2m5f 80yds Hy Hdl (3/13)", "pos": 3, "ran": 13},
                 {"date": "02 Dec 25", "venue": "Clonmel", "race": "2m3f 97yds Hy Hdl (4/18)", "pos": 4, "ran": 18},
                 {"date": "20 Nov 25", "venue": "Thurles", "race": "1m7f 169yds GS Hdl (P/16)", "pos": "P", "ran": 16},
                 {"date": "12 Oct 25", "venue": "Cork", "race": "2m3f GS NHF (1/7, bumper)", "pos": 1, "ran": 7},
             ]},
            {"name": "Staffordshire Knot", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "20/1", "age": 8, "form": "9-31121", "rating": 152,
             "cheltenham_record": "D",
             "last_run": "Won Navan 08 Feb 2026 (2m5f hy, 1/6) — 3 wins + 1 second this winter; all in mud; last 2 Grade 2; topweight here", "days_off": 31,
             "recent_races": [
                 {"date": "08 Feb 26", "venue": "Navan", "race": "2m5f 180yds Hy Hdl (1/6 WIN)", "pos": 1, "ran": 6},
                 {"date": "22 Jan 26", "venue": "Gowran Park", "race": "2m7f 110yds Hy Hdl (2/6 Grade 2)", "pos": 2, "ran": 6},
                 {"date": "02 Dec 25", "venue": "Clonmel", "race": "2m6f Hy Hdl (1/5 WIN)", "pos": 1, "ran": 5},
                 {"date": "23 Nov 25", "venue": "Punchestown", "race": "3m 37yds Sft Hdl (1/9 OR140 Pertemps qual WIN)", "pos": 1, "ran": 9},
                 {"date": "09 Nov 25", "venue": "Naas", "race": "2m4f Hy Hdl (3/14 OR137)", "pos": 3, "ran": 14},
                 {"date": "21 Apr 25", "venue": "Fairyhouse", "race": "2m4f Sft Hdl (9/10)", "pos": 9, "ran": 10},
             ]},
            {"name": "Melbourne Shamrock", "trainer": "Emmet Mullins", "jockey": "Donagh Meyler",
             "odds": "14/1", "age": 7, "form": "3P-4241", "rating": 132,
             "cheltenham_record": None,
             "last_run": "Won Naas 22 Feb 2026 (2m7f hy, 1/9, OR121, handicap debut with cheekpieces — held on by neck); blinkers today", "days_off": 17,
             "recent_races": [
                 {"date": "22 Feb 26", "venue": "Naas", "race": "2m7f 20yds Hy Hdl (1/9 OR121 — hcap debut, by neck)", "pos": 1, "ran": 9},
                 {"date": "17 Jan 26", "venue": "Navan", "race": "2m6f Hy Hdl (4/12)", "pos": 4, "ran": 12},
                 {"date": "13 Dec 25", "venue": "Fairyhouse", "race": "3m Sft Hdl (2/11)", "pos": 2, "ran": 11},
                 {"date": "20 Nov 25", "venue": "Thurles", "race": "2m6f 110yds GS Hdl (4/8)", "pos": 4, "ran": 8},
                 {"date": "14 Dec 24", "venue": "Fairyhouse", "race": "2m7f 55yds GS Hdl (P/14)", "pos": "P", "ran": 14},
                 {"date": "03 May 24", "venue": "Punchestown", "race": "2m2f 181yds Hy NHF (3/19, bumper)", "pos": 3, "ran": 19},
             ]},
            {"name": "Lavida Adiva", "trainer": "Ruth Jefferson", "jockey": "Brian Hughes",
             "odds": "12/1", "age": 7, "form": "2-34143", "rating": 133,
             "cheltenham_record": "D",
             "last_run": "3rd Haydock 14 Feb 2026 (3m GS, 3/5, Grade 2) — won Listed mares Dec; reliable but needs to improve in hot company", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (3/5 Grade 2)", "pos": 3, "ran": 5},
                 {"date": "24 Jan 26", "venue": "Doncaster", "race": "3m 84yds Sft Hdl (4/8)", "pos": 4, "ran": 8},
                 {"date": "13 Dec 25", "venue": "Doncaster", "race": "3m 84yds GS Hdl (1/5 Listed mares' WIN)", "pos": 1, "ran": 5},
                 {"date": "26 Nov 25", "venue": "Market Rasen", "race": "2m7f 16yds GS Hdl (4/8 OR130)", "pos": 4, "ran": 8},
                 {"date": "01 Nov 25", "venue": "Ayr", "race": "3m 70yds Sft Hdl (3/7 OR130)", "pos": 3, "ran": 7},
                 {"date": "12 Apr 25", "venue": "Ayr", "race": "3m 70yds GS Hdl (2/9 OR126)", "pos": 2, "ran": 9},
             ]},
            {"name": "Yeah Man", "trainer": "Gavin Patrick Cromwell", "jockey": "C. Stone-Walsh(3)",
             "odds": "18/1", "age": 9, "form": "9622P6", "rating": 133,
             "cheltenham_record": None,
             "last_run": "6th Gowran 14 Feb 2026 (2m hy, 6/7) — much lower hurdles mark than chasing; 2nd to Duke Silver in Leopardstown qual Dec", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Gowran Park", "race": "2m Hy Hdl (6/7)", "pos": 6, "ran": 7},
                 {"date": "22 Jan 26", "venue": "Gowran Park", "race": "3m1f Hy Ch (P/18 OR140, chase)", "pos": "P", "ran": 18},
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "2m7f 80yds Gd Hdl (2/18 OR118 — Pertemps qual)", "pos": 2, "ran": 18},
                 {"date": "16 Nov 25", "venue": "Navan", "race": "3m Hy Ch (2/19 OR139, chase)", "pos": 2, "ran": 19},
                 {"date": "19 Oct 25", "venue": "Limerick", "race": "3m Hy Ch (6/15 OR140, chase)", "pos": 6, "ran": 15},
                 {"date": "03 May 25", "venue": "Punchestown", "race": "3m7f 68yds GS Ch (9/23 OR141, chain)", "pos": 9, "ran": 23},
             ]},
            {"name": "Classic King", "trainer": "Emma Lavelle", "jockey": "Ben Jones",
             "odds": "28/1", "age": 8, "form": "132-464", "rating": 134,
             "cheltenham_record": None,
             "last_run": "4th Wincanton 26 Dec 2025 (3m GS, 4/9, OR134) — not stamping his class at 3m this term; others preferred", "days_off": 75,
             "recent_races": [
                 {"date": "26 Dec 25", "venue": "Wincanton", "race": "3m 150yds GS Hdl (4/9 OR134)", "pos": 4, "ran": 9},
                 {"date": "28 Nov 25", "venue": "Newbury", "race": "3m 57yds GS Hdl (6/11 OR135)", "pos": 6, "ran": 11},
                 {"date": "24 Oct 25", "venue": "Cheltenham", "race": "2m3f 200yds Gd Hdl (4/20 OR135)", "pos": 4, "ran": 20},
                 {"date": "15 Mar 25", "venue": "Kempton Park", "race": "2m5f GS Hdl (2/10 OR131)", "pos": 2, "ran": 10},
                 {"date": "15 Feb 25", "venue": "Ascot", "race": "2m3f 58yds Gd Hdl (3/11 OR131)", "pos": 3, "ran": 11},
                 {"date": "25 Jan 25", "venue": "Doncaster", "race": "2m3f 88yds GS Hdl (1/7 OR126 WIN)", "pos": 1, "ran": 7},
             ]},
            {"name": "Minella Sixo", "trainer": "Gordon Elliott", "jockey": "Sam Ewing",
             "odds": "22/1", "age": 7, "form": "F0-9762", "rating": 137,
             "cheltenham_record": None,
             "last_run": "2nd Naas 22 Feb 2026 (2m7f hy, 2/9) — visor (second time), stayed on behind Melbourne Shamrock; needs to improve on British mark", "days_off": 17,
             "recent_races": [
                 {"date": "22 Feb 26", "venue": "Naas", "race": "2m7f 20yds Hy Hdl (2/9 OR129 — finished well)", "pos": 2, "ran": 9},
                 {"date": "02 Feb 26", "venue": "Leopardstown", "race": "3m 19yds Hy Hdl (6/21 OR130)", "pos": 6, "ran": 21},
                 {"date": "14 Jan 26", "venue": "Fairyhouse", "race": "3m Sft Hdl (7/9 OR133)", "pos": 7, "ran": 9},
                 {"date": "01 Aug 25", "venue": "Galway", "race": "2m6f 111yds GS Ch (9/16, chase)", "pos": 9, "ran": 16},
                 {"date": "14 Mar 25", "venue": "Cheltenham", "race": "2m4f 56yds GS Hdl (18/24 OR137, Martin Pipe)", "pos": 18, "ran": 24},
                 {"date": "15 Feb 25", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (F/13 OR137, fell)", "pos": "F", "ran": 13},
             ]},
            {"name": "Red Dirt Road", "trainer": "Jonjo & A.J. O'Neill", "jockey": "Jonjo O'Neill Jr.",
             "odds": "40/1", "age": 9, "form": "511P-P4", "rating": 134,
             "cheltenham_record": None,
             "last_run": "4th Haydock 14 Feb 2026 (3m GS, 4/13) — big step back in right direction after two PUs; only 1lb higher than Sandown win", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (4/13 OR136 — revival)", "pos": 4, "ran": 13},
                 {"date": "31 Jan 26", "venue": "Sandown Park", "race": "2m7f 103yds Sft Hdl (P/11 OR139)", "pos": "P", "ran": 11},
                 {"date": "15 Mar 25", "venue": "Uttoxeter", "race": "2m7f 70yds Sft Hdl (P/17 OR142)", "pos": "P", "ran": 17},
                 {"date": "01 Feb 25", "venue": "Sandown Park", "race": "2m7f 98yds Hy Hdl (1/13 OR133 WIN)", "pos": 1, "ran": 13},
                 {"date": "26 Dec 24", "venue": "Aintree", "race": "2m4f Sft Hdl (1/9 OR128 WIN)", "pos": 1, "ran": 9},
                 {"date": "01 Dec 24", "venue": "Carlisle", "race": "2m1f Sft Hdl (5/8 OR130)", "pos": 5, "ran": 8},
             ]},
            {"name": "Duke Silver", "trainer": "Joseph Patrick O'Brien", "jockey": "H. J. Horgan(5)",
             "odds": "20/1", "age": 6, "form": "241017", "rating": 133,
             "cheltenham_record": "D",
             "last_run": "7th Leopardstown 02 Feb 2026 (3m hy, 7/21) — heavy ground excused; won Leopardstown qual Dec from Yeah Man", "days_off": 37,
             "recent_races": [
                 {"date": "02 Feb 26", "venue": "Leopardstown", "race": "3m 19yds Hy Hdl (7/21 OR127 — heavy ground)", "pos": 7, "ran": 21},
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "2m7f 80yds Gd Hdl (1/18 OR119 Pertemps qual WIN)", "pos": 1, "ran": 18},
                 {"date": "14 Oct 25", "venue": "Punchestown", "race": "2m7f 22yds GS Hdl (14/17 OR119)", "pos": 14, "ran": 17},
                 {"date": "24 Sep 25", "venue": "Listowel", "race": "3m GS Hdl (1/13 OR113 WIN cheekpieces)", "pos": 1, "ran": 13},
                 {"date": "03 Aug 25", "venue": "Galway", "race": "3m 60yds Sft Hdl (4/18 OR113)", "pos": 4, "ran": 18},
                 {"date": "17 Jul 25", "venue": "Killarney", "race": "2m4f 85yds GS Hdl (2/15 OR109)", "pos": 2, "ran": 15},
             ]},
            {"name": "Onewaywest", "trainer": "Ben Pauling", "jockey": "Elliott England(7)",
             "odds": "25/1", "age": 7, "form": "52-11F2", "rating": 129,
             "cheltenham_record": None,
             "last_run": "2nd Huntingdon 22 Jan 2026 (3m1f sft, 2/6, OR126) — goes right at hurdles, left-handed track a concern today", "days_off": 48,
             "recent_races": [
                 {"date": "22 Jan 26", "venue": "Huntingdon", "race": "3m1f 10yds Sft Hdl (2/6 OR126 — 2nd to Ace Of Spades)", "pos": 2, "ran": 6},
                 {"date": "26 Dec 25", "venue": "Kempton Park", "race": "2m5f Gd Hdl (F/10 OR123 — fell)", "pos": "F", "ran": 10},
                 {"date": "26 Nov 25", "venue": "Wetherby", "race": "2m3f 154yds GS Hdl (1/9 OR112 WIN)", "pos": 1, "ran": 9},
                 {"date": "19 Nov 25", "venue": "Warwick", "race": "2m3f Sft Hdl (1/6 OR112 WIN)", "pos": 1, "ran": 6},
                 {"date": "06 Apr 25", "venue": "Ffos Las", "race": "2m4f GS Hdl (2/10 OR112)", "pos": 2, "ran": 10},
                 {"date": "17 Mar 25", "venue": "Fontwell Park", "race": "2m1f 162yds Gd Hdl (5/5 OR113)", "pos": 5, "ran": 5},
             ]},
            {"name": "Ikarak", "trainer": "Olly Murphy", "jockey": "Sean Bowen",
             "odds": "33/1", "age": 8, "form": "152-131", "rating": 133,
             "cheltenham_record": "D",
             "last_run": "Won Ayr 02 Jan 2026 (3m sft, 1/10, OR127) — below form at Cheltenham 2 yrs ago but strong stayer at 3m; up 6lb", "days_off": 68,
             "recent_races": [
                 {"date": "02 Jan 26", "venue": "Ayr", "race": "3m 70yds Sft Hdl (1/10 OR127 WIN)", "pos": 1, "ran": 10},
                 {"date": "06 Dec 25", "venue": "Sandown Park", "race": "2m7f 103yds Sft Hdl (3/7 OR127 — 3rd to Kikijo)", "pos": 3, "ran": 7},
                 {"date": "11 Nov 25", "venue": "Lingfield Park", "race": "2m7f Gd Hdl (1/6 OR123 WIN)", "pos": 1, "ran": 6},
                 {"date": "24 Apr 25", "venue": "Warwick", "race": "3m1f Gd Hdl (2/6 OR124)", "pos": 2, "ran": 6},
                 {"date": "22 Feb 25", "venue": "Chepstow", "race": "2m7f 131yds Sft Hdl (5/13 OR124)", "pos": 5, "ran": 13},
                 {"date": "20 Jan 25", "venue": "Warwick", "race": "3m1f GS Hdl (1/11 OR120 WIN)", "pos": 1, "ran": 11},
             ]},
            {"name": "Idy Wood", "trainer": "Jamie Snowden", "jockey": "Gavin Sheehan",
             "odds": "40/1", "age": 8, "form": "41-1410", "rating": 132,
             "cheltenham_record": None,
             "last_run": "10th Windsor 01 Jan 2026 (2m4f gd, tailed off) — unraced beyond 2m5f, needs to improve; 2-4 back hurdling", "days_off": 69,
             "recent_races": [
                 {"date": "01 Jan 26", "venue": "Windsor", "race": "2m4f Gd Hdl (10/12 OR133 — tailed off)", "pos": 10, "ran": 12},
                 {"date": "10 Nov 25", "venue": "Kempton Park", "race": "2m5f GS Hdl (1/7 OR127 WIN)", "pos": 1, "ran": 7},
                 {"date": "11 Oct 25", "venue": "Chepstow", "race": "2m3f 100yds GF Hdl (4/14 OR127)", "pos": 4, "ran": 14},
                 {"date": "11 Sep 25", "venue": "Uttoxeter", "race": "2m3f 207yds Gd Hdl (1/10 OR123 WIN)", "pos": 1, "ran": 10},
                 {"date": "20 Mar 25", "venue": "Ludlow", "race": "2m4f 11yds Gd Ch (1/4 OR122 WIN chase)", "pos": 1, "ran": 4},
                 {"date": "28 Jan 25", "venue": "Chepstow", "race": "2m 11yds Hy Ch (4/5 OR124, chase)", "pos": 4, "ran": 5},
             ]},
            {"name": "Idem", "trainer": "Lucinda Russell & Michael Scudamore", "jockey": "Patrick Wadge",
             "odds": "50/1", "age": 8, "form": "40-2582", "rating": 128,
             "cheltenham_record": None,
             "last_run": "2nd Musselburgh 01 Feb 2026 (2m7f GS, 2/13, OR127) — 10th in this race last year; exposed 8yo", "days_off": 38,
             "recent_races": [
                 {"date": "01 Feb 26", "venue": "Musselburgh", "race": "2m7f 180yds GS Hdl (2/13 OR127)", "pos": 2, "ran": 13},
                 {"date": "20 Dec 25", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (8/9 OR128)", "pos": 8, "ran": 9},
                 {"date": "08 Nov 25", "venue": "Aintree", "race": "3m 149yds Gd Hdl (5/7 OR128)", "pos": 5, "ran": 7},
                 {"date": "11 Oct 25", "venue": "Hexham", "race": "2m7f 63yds Gd Hdl (2/5 OR127)", "pos": 2, "ran": 5},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m7f 213yds GS Hdl (10/24 OR128 — this race)", "pos": 10, "ran": 24},
                 {"date": "02 Feb 25", "venue": "Musselburgh", "race": "2m7f 180yds GS Hdl (4/11 OR128)", "pos": 4, "ran": 11},
             ]},
            {"name": "Ike Sport", "trainer": "Neil Mulholland", "jockey": "Conor O'Farrell",
             "odds": "50/1", "age": 8, "form": "205266", "rating": 127,
             "cheltenham_record": None,
             "last_run": "6th Plumpton 26 Jan 2026 (2m4f sft, 6/7) — last won Apr 2024; 2nd to Absolutely Doyen at Wincanton best this season", "days_off": 43,
             "recent_races": [
                 {"date": "26 Jan 26", "venue": "Plumpton", "race": "2m4f 116yds Sft Hdl (6/7 OR127)", "pos": 6, "ran": 7},
                 {"date": "10 Jan 26", "venue": "Kempton Park", "race": "2m5f Gd Hdl (6/15 OR127 Lanzarote)", "pos": 6, "ran": 15},
                 {"date": "26 Dec 25", "venue": "Wincanton", "race": "3m 150yds GS Hdl (2/9 OR125 — 2nd to Absolutely Doyen)", "pos": 2, "ran": 9},
                 {"date": "09 Nov 25", "venue": "Sandown Park", "race": "2m3f 173yds Gd Hdl (5/6 OR127)", "pos": 5, "ran": 6},
                 {"date": "11 Oct 25", "venue": "Chepstow", "race": "2m3f 100yds GF Hdl (10/14 OR128)", "pos": 10, "ran": 14},
                 {"date": "16 May 25", "venue": "Aintree", "race": "2m4f GF Hdl (2/6 OR128)", "pos": 2, "ran": 6},
             ]},
            {"name": "Lihyan", "trainer": "Unknown", "jockey": "Unknown",
             "odds": "50/1", "age": 7, "form": "000000", "rating": 125,
             "cheltenham_record": None,
             "last_run": "Qualifier run", "days_off": 28,
             "recent_races": []},
            {"name": "Turndlightsdownlow", "trainer": "Unknown", "jockey": "Unknown",
             "odds": "50/1", "age": 7, "form": "000000", "rating": 125,
             "cheltenham_record": None,
             "last_run": "Qualifier run", "days_off": 28,
             "recent_races": []},
        ]
    },
    "day3_race4": {   # Stayers' Hurdle  (Grade 1, 3m — 11 runners, Thu 12 Mar 15:20)
        # UPDATED 11/03/2026 from detailed racecard. E/W: 1/5 odds, 3 PLACES.
        # Teahupoo: age=9 (not 10), CD winner (won 2024, 2nd 2025, 3rd 2023)
        # Kabral Du Mathan: age=6 (not 8), Course winner (won Relkeel at Cheltenham Jan 2026); stamina unproven at 3m
        # Ma Shantou: age=7 (not 9), CD winner (won Cleeve C&D Jan 2026 + two other Cheltenham wins this season)
        # Ballyburn: Course winner (won 2m5f Grade 1 novice hurdle here 2024); hood first time
        # Bob Olinger: age=11 (not 10), CD winner (won this race 2025! by nearly 2l)
        # Impose Toi: age=8 (not 7), Course+Distance winner (C and D symbols); 7l 2nd to Ma Shantou at Cleeve
        # Doddiethegreat: age=10 (not 8), CD winner (won Pertemps Final C&D 2025)
        "entries": [
            {"name": "Teahupoo", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "4/1", "age": 9, "form": "122-111", "rating": 170,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 1 Christmas Hurdle Leopardstown 28 Dec 2025 (2m7f gd, beat Bob Olinger 7l)", "days_off": 73,
             "recent_races": [
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "2m7f 80yds Gd Hdl (Grade 1, beat Bob Olinger 7l)", "pos": 1, "ran": 8},
                 {"date": "30 Nov 25", "venue": "Fairyhouse", "race": "2m4f Sft Hdl (Grade 1)", "pos": 1, "ran": 6},
                 {"date": "01 May 25", "venue": "Punchestown", "race": "2m7f 110yds GS Hdl (Grade 1)", "pos": 1, "ran": 11},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m7f 213yds GS Hdl (Stayers 2nd to Bob Olinger)", "pos": 2, "ran": 13},
                 {"date": "01 Dec 24", "venue": "Fairyhouse", "race": "2m4f Gd Hdl (Grade 1, 2nd)", "pos": 2, "ran": 4},
             ]},
            {"name": "Kabral Du Mathan", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "9/2", "age": 6, "form": "1222-11", "rating": 165,
             "cheltenham_record": "Course winner",
             "last_run": "Won Grade 2 Relkeel Hurdle Cheltenham 01 Jan 2026 (2m4f gd — plenty in hand, powered clear up hill)", "days_off": 69,
             "recent_races": [
                 {"date": "01 Jan 26", "venue": "Cheltenham", "race": "2m4f 56yds Gd Hdl (Grade 2 Relkeel — Course win)", "pos": 1, "ran": 6},
                 {"date": "22 Nov 25", "venue": "Haydock Park", "race": "2m2f 191yds GS Hdl (OR=140, stable debut)", "pos": 1, "ran": 9},
                 {"date": "12 Apr 25", "venue": "Ayr", "race": "2m GS Hdl (2nd)", "pos": 2, "ran": 12},
                 {"date": "17 Jan 25", "venue": "Windsor", "race": "2m GS Hdl (2nd)", "pos": 2, "ran": 14},
                 {"date": "21 Dec 24", "venue": "Ascot", "race": "1m7f 152yds GS Hdl (2nd)", "pos": 2, "ran": 12},
             ]},
            {"name": "Ma Shantou", "trainer": "Emma Lavelle", "jockey": "Harry Cobden",
             "odds": "7/1", "age": 7, "form": "37-1011", "rating": 157,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 2 Cleeve Hurdle C&D Cheltenham 24 Jan 2026 (3m sft — 7l clear of Impose Toi)", "days_off": 46,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Cheltenham", "race": "2m7f 213yds Sft Hdl (Grade 2 Cleeve C&D)", "pos": 1, "ran": 6},
                 {"date": "01 Jan 26", "venue": "Cheltenham", "race": "2m7f 213yds Gd Hdl (Cheltenham hdcp OR=138)", "pos": 1, "ran": 7},
                 {"date": "22 Nov 25", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (12th/17 — blip)", "pos": 12, "ran": 17},
                 {"date": "25 Oct 25", "venue": "Cheltenham", "race": "2m7f 208yds GS Hdl (OR=129 win)", "pos": 1, "ran": 17},
                 {"date": "14 Mar 25", "venue": "Cheltenham", "race": "2m7f 213yds GS Hdl (Pertemps Final 7th)", "pos": 7, "ran": 20},
             ]},
            {"name": "Ballyburn", "trainer": "Willie Mullins", "jockey": "P. Townend",
             "odds": "13/2", "age": 8, "form": "215-223", "rating": 163,
             "cheltenham_record": "Course winner",
             "last_run": "3rd Grade 1 Christmas Hurdle Leopardstown 28 Dec 2025 (14l behind Teahupoo) — hood first time", "days_off": 73,
             "recent_races": [
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "2m7f 80yds Gd Hdl (Grade 1, 3rd — 14l behind Teahupoo)", "pos": 3, "ran": 8},
                 {"date": "30 Nov 25", "venue": "Fairyhouse", "race": "2m4f Sft Hdl (Grade 1 Hatton's Grace, 2nd — close)", "pos": 2, "ran": 6},
                 {"date": "29 Apr 25", "venue": "Punchestown", "race": "3m 213yds Gd Ch (2nd, chasing)", "pos": 2, "ran": 8},
                 {"date": "12 Mar 25", "venue": "Cheltenham", "race": "3m 110yds GS Ch (5th, Festival chase)", "pos": 5, "ran": 7},
                 {"date": "02 Feb 25", "venue": "Leopardstown", "race": "2m5f 107yds GS Ch (1st, won)", "pos": 1, "ran": 6},
             ]},
            {"name": "Bob Olinger", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "7/1", "age": 11, "form": "22/221-2", "rating": 160,
             "cheltenham_record": "CD winner",
             "last_run": "2nd Grade 1 Christmas Hurdle Leopardstown 28 Dec 2025 (7l behind Teahupoo)", "days_off": 73,
             "recent_races": [
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "2m7f 80yds Gd Hdl (Grade 1, 2nd — 7l off Teahupoo)", "pos": 2, "ran": 8},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m7f 213yds GS Hdl (WON Stayers 2025 by 2l)", "pos": 1, "ran": 13},
                 {"date": "28 Dec 24", "venue": "Leopardstown", "race": "2m7f 80yds Gd Hdl (Grade 1, 2nd)", "pos": 2, "ran": 8},
                 {"date": "16 Nov 24", "venue": "Navan", "race": "2m4f 50yds GS Hdl (2nd)", "pos": 2, "ran": 8},
                 {"date": "11 Apr 24", "venue": "Aintree", "race": "2m4f Sft Hdl (Grade 1, 2nd)", "pos": 2, "ran": 8},
             ]},
            {"name": "Honesty Policy", "trainer": "Gordon Elliott", "jockey": "M. P. Walsh",
             "odds": "10/1", "age": 6, "form": "2111-23", "rating": 158,
             "cheltenham_record": None,
             "last_run": "3rd Grade 1 Long Walk Ascot 20 Dec 2025 (3m gd — behind Impose Toi; lightly raced improver)", "days_off": 81,
             "recent_races": [
                 {"date": "20 Dec 25", "venue": "Ascot", "race": "3m 102yds GS Hdl (Grade 1 Long Walk, 3rd)", "pos": 3, "ran": 11},
                 {"date": "30 Apr 25", "venue": "Punchestown", "race": "2m7f 192yds GS Hdl (Grade 1, 2nd close)", "pos": 2, "ran": 8},
                 {"date": "05 Apr 25", "venue": "Aintree", "race": "2m4f Gd Hdl (Grade 1 win)", "pos": 1, "ran": 9},
                 {"date": "02 Mar 25", "venue": "Leopardstown", "race": "2m GS Hdl (win)", "pos": 1, "ran": 5},
                 {"date": "09 Feb 25", "venue": "Navan", "race": "1m7f 150yds Hy Hdl (win)", "pos": 1, "ran": 14},
             ]},
            {"name": "Impose Toi", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "10/1", "age": 8, "form": "4-21112", "rating": 159,
             "cheltenham_record": "CD winner",
             "last_run": "2nd Grade 2 Cleeve Hurdle C&D Cheltenham 24 Jan 2026 (7l behind Ma Shantou, conceded 6lb)", "days_off": 46,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Cheltenham", "race": "2m7f 213yds Sft Hdl (Cleeve, 2nd — conceded 6lb)", "pos": 2, "ran": 6},
                 {"date": "20 Dec 25", "venue": "Ascot", "race": "3m 102yds GS Hdl (Grade 1 Long Walk WIN)", "pos": 1, "ran": 11},
                 {"date": "28 Nov 25", "venue": "Newbury", "race": "3m 57yds GS Hdl (Grade 2 win)", "pos": 1, "ran": 7},
                 {"date": "08 Nov 25", "venue": "Aintree", "race": "3m 149yds Gd Hdl (OR=148 win)", "pos": 1, "ran": 7},
                 {"date": "03 May 25", "venue": "Punchestown", "race": "2m4f 118yds GS Hdl (2nd OR=143)", "pos": 2, "ran": 16},
             ]},
            {"name": "Doddiethegreat", "trainer": "Nicky Henderson", "jockey": "James Bowen",
             "odds": "40/1", "age": 10, "form": "1-23453", "rating": 145,
             "cheltenham_record": "CD winner",
             "last_run": "3rd Cleeve Hurdle C&D Cheltenham 24 Jan 2026 (3rd/6, jockey dropped whip after last) — blinkers first time", "days_off": 46,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Cheltenham", "race": "2m7f 213yds Sft Hdl (3rd, jockey dropped whip)", "pos": 3, "ran": 6},
                 {"date": "20 Dec 25", "venue": "Ascot", "race": "3m 102yds GS Hdl (Long Walk 5th)", "pos": 5, "ran": 11},
                 {"date": "28 Nov 25", "venue": "Newbury", "race": "3m 57yds GS Hdl (4th)", "pos": 4, "ran": 7},
                 {"date": "01 Nov 25", "venue": "Wetherby", "race": "3m 26yds Gd Hdl (3rd)", "pos": 3, "ran": 5},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m7f 213yds GS Hdl (WON Pertemps Final C&D 1/24)", "pos": 1, "ran": 24},
             ]},
            {"name": "Hewick", "trainer": "John Joseph Hanlon", "jockey": "P. Hanlon",
             "odds": "40/1", "age": 11, "form": "18-7145", "rating": 155,
             "cheltenham_record": "D",
             "last_run": "5th Grade 2 Long Distance Hurdle Newbury 28 Nov 2025 (3m sft) — wind op since; 11yo", "days_off": 102,
             "recent_races": [
                 {"date": "28 Nov 25", "venue": "Newbury", "race": "3m 57yds GS Hdl (5th/7)", "pos": 5, "ran": 7},
                 {"date": "01 Nov 25", "venue": "Wetherby", "race": "3m 45yds Gd Ch (4th/5)", "pos": 4, "ran": 5},
                 {"date": "16 Oct 25", "venue": "Thurles", "race": "2m6f 154yds GS Hdl (win)", "pos": 1, "ran": 3},
                 {"date": "05 Apr 25", "venue": "Aintree", "race": "4m2f 74yds Gd Ch (Grand National 8th)", "pos": 8, "ran": 34},
             ]},
            {"name": "Home By The Lee", "trainer": "Joseph Patrick O'Brien", "jockey": "J. J. Slevin",
             "odds": "33/1", "age": 11, "form": "1UP-641", "rating": 148,
             "cheltenham_record": "D",
             "last_run": "Won Grade 2 Galmoy Hurdle Gowran Park 22 Jan 2026 (2m7f hy — still has spark)", "days_off": 48,
             "recent_races": [
                 {"date": "22 Jan 26", "venue": "Gowran Park", "race": "2m7f 110yds Hy Hdl (Grade 2 Galmoy win)", "pos": 1, "ran": 6},
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "2m7f 80yds Gd Hdl (4th/8 Christmas)", "pos": 4, "ran": 8},
                 {"date": "01 May 25", "venue": "Punchestown", "race": "2m7f 110yds GS Hdl (6th/11)", "pos": 6, "ran": 11},
                 {"date": "05 Apr 25", "venue": "Aintree", "race": "3m 149yds Gd Hdl (P pulled)", "pos": "P", "ran": 11},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m7f 213yds GS Hdl (U unseated)", "pos": "U", "ran": 13},
             ]},
            {"name": "Gwennie May Boy", "trainer": "Christian Williams", "jockey": "Charlie Todd",
             "odds": "80/1", "age": 8, "form": "5196-7P", "rating": 130,
             "cheltenham_record": "D",
             "last_run": "Pulled up Long Walk Ascot 20 Dec 2025 (3m gd) — new yard, hard to fancy", "days_off": 81,
             "recent_races": [
                 {"date": "20 Dec 25", "venue": "Ascot", "race": "3m 102yds GS Hdl (P pulled)", "pos": "P", "ran": 11},
                 {"date": "22 Nov 25", "venue": "Ascot", "race": "2m3f 63yds GS Hdl (7th/8)", "pos": 7, "ran": 8},
                 {"date": "26 Apr 25", "venue": "Sandown Park", "race": "2m5f 110yds GF Hdl (6th/6)", "pos": 6, "ran": 6},
                 {"date": "15 Feb 25", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (Grade 2 WIN — career best)", "pos": 1, "ran": 6},
             ]},
        ]
    },
    "day3_race5": {   # Ryanair Chase (Grade 1, 2m4f — 9 runners, Thu 12 Mar 16:00)
        # UPDATED 12/03/2026 from Betfair live declared field. Jonbon transferred from QMCC → Ryanair.
        # NRs: Firefox, Romeo Coolio, Energumene, Il Etait Temps.
        # Live prices (Betfair 12 Mar): Fact To File 6/5, Jonbon 4/1, Impaire Et Passe 11/2,
        #   Banbridge 8/1, Heart Wood 15/1, Jpr One 49/1, Matata 84/1, Master Chewy 219/1.
        "entries": [
            {"name": "Fact To File", "trainer": "Willie Mullins", "jockey": "M. P. Walsh",
             "odds": "6/5", "age": 9, "form": "31-4261", "rating": 174,
             "cheltenham_record": "CD winner",
             "last_run": "Won Irish Gold Cup Leopardstown 02 Feb 2026 (3m sft, beat top class field — back to best)", "days_off": 37,
             "recent_races": [
                 {"date": "02 Feb 26", "venue": "Leopardstown", "race": "3m 100yds Sft Ch (Irish Gold Cup WIN)", "pos": 1, "ran": 12},
                 {"date": "26 Dec 25", "venue": "Kempton Park", "race": "3m Gd Ch (King George, 6th/8 — off day)", "pos": 6, "ran": 8},
                 {"date": "23 Nov 25", "venue": "Punchestown", "race": "2m3f 150yds Sft Ch (2nd to Gaelic Warrior)", "pos": 2, "ran": 10},
                 {"date": "29 Apr 25", "venue": "Punchestown", "race": "2m 98yds Gd Ch (4th)", "pos": 4, "ran": 6},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m4f 127yds GS Ch (Ryanair WIN 2025 — back-to-back)", "pos": 1, "ran": 9},
                 {"date": "01 Feb 25", "venue": "Leopardstown", "race": "3m 70yds GS Ch (IGC 3rd)", "pos": 3, "ran": 10},
             ]},
            {"name": "Jonbon", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "4/1", "age": 10, "form": "112221", "rating": 166,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 1 Chase Kempton Dec 2025 — switched from QMCC to Ryanair Chase", "days_off": 72,
             "recent_races": [
                 {"date": "26 Dec 25", "venue": "Kempton Park", "race": "2m Gd Ch (Grade 1 WIN, beat top class)", "pos": 1, "ran": 6},
                 {"date": "15 Nov 25", "venue": "Cheltenham", "race": "2m Gd Ch (2nd at course, close)", "pos": 2, "ran": 8},
                 {"date": "11 Oct 25", "venue": "Chepstow", "race": "2m Ch (2nd Grade 2)", "pos": 2, "ran": 6},
                 {"date": "12 Mar 25", "venue": "Cheltenham", "race": "2m Ch (2nd QMCC to Il Etait Temps)", "pos": 2, "ran": 12},
                 {"date": "15 Feb 25", "venue": "Ascot", "race": "2m3f Gd Ch (1st Grade 1 Clarence House WIN)", "pos": 1, "ran": 8},
                 {"date": "13 Mar 24", "venue": "Cheltenham", "race": "2m Ch (Won Arkle 2023 — back-to-back Festival wins)", "pos": 1, "ran": 9},
             ]},
            {"name": "Impaire Et Passe", "trainer": "Willie Mullins", "jockey": "B. J. Cooper",
             "odds": "11/2", "age": 8, "form": "1b131", "rating": 160,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Chase Leopardstown 01 Feb 2026 (2m1f)", "days_off": 38,
             "recent_races": [
                 {"date": "01 Feb 26", "venue": "Leopardstown", "race": "2m1f Sft Ch (Grade 1 WIN)", "pos": 1, "ran": 8},
                 {"date": "26 Dec 25", "venue": "Leopardstown", "race": "2m1f Sft Ch (3rd Grade 1)", "pos": 3, "ran": 9},
                 {"date": "16 Nov 25", "venue": "Navan", "race": "2m1f GS Ch (1st Grade 3)", "pos": 1, "ran": 6},
                 {"date": "12 Oct 25", "venue": "Tipperary", "race": "2m1f GS Ch (bd — bolted before start)", "pos": 0, "ran": 5},
             ]},
            {"name": "Banbridge", "trainer": "Joseph Patrick O'Brien", "jockey": "J. W. Kennedy",
             "odds": "8/1", "age": 10, "form": "24471", "rating": 167,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 2 Chase Leopardstown Jan 2026 (2m2f)", "days_off": 42,
             "recent_races": [
                 {"date": "11 Jan 26", "venue": "Leopardstown", "race": "2m2f Sft Ch (Grade 2 WIN)", "pos": 1, "ran": 7},
                 {"date": "26 Dec 25", "venue": "Leopardstown", "race": "2m1f Sft Ch (7th/9 Grade 1)", "pos": 7, "ran": 9},
                 {"date": "16 Nov 25", "venue": "Punchestown", "race": "2m5f GS Ch (4th Grade 1)", "pos": 4, "ran": 8},
                 {"date": "12 Apr 25", "venue": "Aintree", "race": "2m4f Gd Ch (4th Grade 1 Melling)", "pos": 4, "ran": 8},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m4f GS Ch (1st Ryanair Trial CD WIN)", "pos": 1, "ran": 9},
             ]},
            {"name": "Heart Wood", "trainer": "Henry de Bromhead", "jockey": "J. W. Kennedy",
             "odds": "15/1", "age": 8, "form": "141p2", "rating": 160,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Chase Tramore Jan 2026 (2m6f)", "days_off": 70,
             "recent_races": [
                 {"date": "01 Jan 26", "venue": "Tramore", "race": "2m6f Sft Ch (Grade 2 WIN + beat Croke Park)", "pos": 1, "ran": 7},
                 {"date": "15 Oct 25", "venue": "Punchestown", "race": "2m7f GS Ch (1st — beat Croke Park)", "pos": 1, "ran": 6},
                 {"date": "26 Apr 25", "venue": "Punchestown", "race": "2m1f GS Ch (4th Grade 1)", "pos": 4, "ran": 8},
                 {"date": "13 Mar 24", "venue": "Cheltenham", "race": "2m Ch (pulled up — unsuited by conditions)", "pos": 0, "ran": 12},
             ]},
            {"name": "Jpr One", "trainer": "Joe Tizzard", "jockey": "Brendan Powell",
             "odds": "49/1", "age": 9, "form": "12335", "rating": 160,
             "cheltenham_record": "CD winner",
             "last_run": "5th Chase Jan 2026 (2m4f)", "days_off": 42,
             "recent_races": [
                 {"date": "18 Jan 26", "venue": "Cheltenham", "race": "2m4f Sft Ch (5th/6)", "pos": 5, "ran": 6},
                 {"date": "02 Nov 25", "venue": "Cheltenham", "race": "2m4f GS Ch (3rd CD)", "pos": 3, "ran": 8},
                 {"date": "19 Oct 25", "venue": "Kempton", "race": "2m Ch (3rd)", "pos": 3, "ran": 7},
                 {"date": "28 Sep 25", "venue": "Naas", "race": "2m1f Gd Ch (2nd)", "pos": 2, "ran": 6},
             ]},
            {"name": "Matata", "trainer": "Nigel Twiston-Davies", "jockey": "Sam Twiston-Davies",
             "odds": "84/1", "age": 8, "form": "37335", "rating": 160,
             "cheltenham_record": "Course winner",
             "last_run": "3rd Chase Jan 2026", "days_off": 42,
             "recent_races": [
                 {"date": "25 Jan 26", "venue": "Haydock", "race": "2m3f Sft Ch (5th OR155)", "pos": 5, "ran": 8},
                 {"date": "30 Nov 25", "venue": "Newbury", "race": "2m3f GS Ch (3rd Grade 2)", "pos": 3, "ran": 7},
             ]},
            {"name": "Master Chewy", "trainer": "Nigel Twiston-Davies", "jockey": "Sam Twiston-Davies",
             "odds": "219/1", "age": 9, "form": "527426", "rating": 154,
             "cheltenham_record": None,
             "last_run": "5th Chase Jan 2026", "days_off": 42,
             "recent_races": [
                 {"date": "25 Jan 26", "venue": "Haydock", "race": "2m3f Sft Ch (4th OR150)", "pos": 4, "ran": 8},
             ]},
            {"name": "Croke Park", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "?", "age": 8, "form": "27-3330", "rating": 150,
             "cheltenham_record": None,
             "last_run": "13th DRF Leopardstown 01 Feb 2026 (2m5f sft hdcp, 23 ran) — poor form all winter", "days_off": 38,
             "recent_races": [
                 {"date": "01 Feb 26", "venue": "Leopardstown", "race": "2m5f 107yds Sft Ch (DRF hdcp, 13/23)", "pos": 13, "ran": 23},
                 {"date": "01 Jan 26", "venue": "Tramore", "race": "2m6f 170yds Sft Ch (3rd behind Heart Wood)", "pos": 3, "ran": 7},
                 {"date": "15 Oct 25", "venue": "Punchestown", "race": "2m7f 39yds GS Ch (3rd behind Heart Wood)", "pos": 3, "ran": 6},
             ]},
        ]
    },
    "day1_race6_plate": {   # Cheltenham Plate Chase  (Day 1 16:40) — field data archive
        "entries": [
            {"name": "Madara", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "4/1", "age": 8, "form": "1-2-1-11", "rating": 156,
             "cheltenham_record": None,
             "last_run": "Won Grade 3 Handicap Chase Feb 2026", "days_off": 28},
            {"name": "McLaurey", "trainer": "Emmet Mullins", "jockey": "Rob James",
             "odds": "4/1", "age": 9, "form": "2-1-3-11", "rating": 153,
             "cheltenham_record": None,
             "last_run": "Won Handicap Chase Jan 2026", "days_off": 42},
            {"name": "Will The Wise", "trainer": "Gavin Cromwell", "jockey": "Danny Mullins",
             "odds": "12/1", "age": 8, "form": "1-3-2-11", "rating": 150,
             "cheltenham_record": None,
             "last_run": "Won Handicap Chase Feb 2026", "days_off": 28},
            {"name": "Down Memory Lane", "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
             "odds": "14/1", "age": 9, "form": "2-1-1-43", "rating": 148,
             "cheltenham_record": None,
             "last_run": "3rd Handicap Chase Feb 2026", "days_off": 28},
            # Grange Walk removed — not entered for Cheltenham (Betfair ANTEPOST: absent)
        ]
    },
    "day3_race7": {   # Kim Muir Challenge Cup Amateur Chase  (Class 2, 3m2f — 26 runners, Thu 12 Mar 17:20)
        # UPDATED 11/03/2026 from official declared racecard (26 runners). E/W: 1/5 odds, 5 PLACES. All amateur jockeys.
        # HANDICAP: no jockey bonuses. Cheekpieces/headgear noted in last_run for context.
        # Jeriko Du Reponet: age=7, OR=145 topweight, 10/3 fav → now 3/1; cheekpieces today; top amateur Derek O'Connor.
        # Kim Roque: age=6 (not 8!), OR=131 (not 140!), ex-French. Course record = None (no symbols).
        # Herakles Westwood (SB pick): age=9, OR=137, "Course winner" (won C 3m1f Jan 2026, NOT full C&D). Wind surgery since. 9/1.
        # Ask Brewster: age=7, OR=128, Course winner — hat-trick last yr incl Cheltenham Apr; tired firm ground at Sandown Dec.
        # Glengouly: age=10, pulled up last 2 starts (12 days ago Newbury). Course winner only.
        # Lord Accord: age=11, C+D symbols both on racecard = CD winner. Returns from break.
        # Hung Jury: age=11, Course winner (won here Nov hdcp + May hunter chase).
        # Insurrection: BF symbol (beaten favourite in last run); 2m4f specialist, stamina big question at 3m2f.
        "entries": [
            {"name": "Jeriko Du Reponet", "trainer": "Nicky Henderson", "jockey": "Mr D. O'Connor",
             "odds": "9/2", "age": 7, "form": "32-1225", "rating": 145,
             "cheltenham_record": None,
             "last_run": "5th Windsor 18 Jan 2026 (3m sft, 5/6) — cheekpieces today; 2nd Pertemps Final here Mar 2025; top amateur up", "days_off": 51,
             "recent_races": [
                 {"date": "18 Jan 26", "venue": "Windsor", "race": "3m 60yds Sft Ch (5/6 — 4 chase starts, not natural)", "pos": 5, "ran": 6},
                 {"date": "16 Dec 25", "venue": "Wincanton", "race": "2m4f 35yds Sft Ch (2/2 — 2nd)", "pos": 2, "ran": 2},
                 {"date": "24 Nov 25", "venue": "Kempton Park", "race": "2m2f GS Ch (2/5 — 2nd)", "pos": 2, "ran": 5},
                 {"date": "01 May 25", "venue": "Punchestown", "race": "2m7f 110yds GS Hdl (1/23 OR139 WIN — cheekpieces)", "pos": 1, "ran": 23},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m7f 213yds GS Hdl (2/24 OR135 — Pertemps Final 2nd)", "pos": 2, "ran": 24},
                 {"date": "09 Feb 25", "venue": "Exeter", "race": "2m7f 25yds Sft Hdl (3/12 OR134)", "pos": 3, "ran": 12},
             ]},
            {"name": "Waterford Whispers", "trainer": "Henry de Bromhead", "jockey": "Mr Alan O'Sullivan(3)",
             "odds": "14/1", "age": 8, "form": "27-4363", "rating": 137,
             "cheltenham_record": None,
             "last_run": "3rd Leopardstown 01 Feb 2026 (2m5f sft, 3/23) — first staying trip, shaped well; 0-6 over fences", "days_off": 38,
             "recent_races": [
                 {"date": "01 Feb 26", "venue": "Leopardstown", "race": "2m5f 107yds Sft Ch (3/23 OR130 — staying trip, shaped well)", "pos": 3, "ran": 23},
                 {"date": "22 Nov 25", "venue": "Punchestown", "race": "2m5f 70yds Sft Ch (6/8 OR130)", "pos": 6, "ran": 8},
                 {"date": "25 Oct 25", "venue": "Galway", "race": "2m2f 54yds GS Ch (3/10)", "pos": 3, "ran": 10},
                 {"date": "21 Sep 25", "venue": "Listowel", "race": "2m1f 150yds GS Ch (4/8)", "pos": 4, "ran": 8},
                 {"date": "28 Dec 24", "venue": "Limerick", "race": "2m3f 100yds Sft Ch (7/7)", "pos": 7, "ran": 7},
                 {"date": "07 Dec 24", "venue": "Navan", "race": "2m4f 150yds Sft Ch (2/18)", "pos": 2, "ran": 18},
             ]},
            {"name": "Herakles Westwood", "trainer": "Warren Greatrex", "jockey": "Mr Finian Maguire",
             "odds": "11/1", "age": 9, "form": "37-5241", "rating": 137,
             "cheltenham_record": "Course winner",
             "last_run": "Won Cheltenham 01 Jan 2026 (3m1f gd, 1/8, OR135) — wind surgery since; 3 runs at Cheltenham last 4 starts", "days_off": 68,
             "recent_races": [
                 {"date": "01 Jan 26", "venue": "Cheltenham", "race": "3m1f 56yds Gd Ch (1/8 OR135 WIN — post wind surgery)", "pos": 1, "ran": 8},
                 {"date": "12 Dec 25", "venue": "Cheltenham", "race": "3m2f 70yds Gd Ch (4/9 OR136 — lost shoe C&D)", "pos": 4, "ran": 9},
                 {"date": "15 Nov 25", "venue": "Cheltenham", "race": "3m1f Sft Ch (2/16 OR126)", "pos": 2, "ran": 16},
                 {"date": "03 May 25", "venue": "Punchestown", "race": "3m7f 68yds GS Ch (5/23 OR125)", "pos": 5, "ran": 23},
                 {"date": "11 Mar 25", "venue": "Cheltenham", "race": "3m5f 201yds GS Ch (7/18 OR129)", "pos": 7, "ran": 18},
                 {"date": "08 Feb 25", "venue": "Newbury", "race": "2m7f 86yds Sft Ch (3/6 OR129)", "pos": 3, "ran": 6},
             ]},
            {"name": "Kim Roque", "trainer": "Joseph Patrick O'Brien", "jockey": "Mr J. L. Gleeson",
             "odds": "8/1", "age": 6, "form": "B42245", "rating": 131,
             "cheltenham_record": None,
             "last_run": "5th Leopardstown 01 Feb 2026 (2m5f sft, 5/23, OR128) — ex-French; 3 starts this yard, promise in defeat", "days_off": 38,
             "recent_races": [
                 {"date": "01 Feb 26", "venue": "Leopardstown", "race": "2m5f 107yds Sft Ch (5/23 OR128)", "pos": 5, "ran": 23},
                 {"date": "13 Dec 25", "venue": "Cheltenham", "race": "2m4f 127yds Gd Ch (4/10 OR128)", "pos": 4, "ran": 10},
                 {"date": "16 Nov 25", "venue": "Cheltenham", "race": "2m4f 44yds Sft Ch (2/6 OR123)", "pos": 2, "ran": 6},
                 {"date": "28 Jun 25", "venue": "Dieppe", "race": "4400m GS Ch (2/11 OR122)", "pos": 2, "ran": 11},
                 {"date": "27 May 25", "venue": "Auteuil", "race": "3600m Sft Hdl (4/16 OR121)", "pos": 4, "ran": 16},
                 {"date": "17 May 25", "venue": "Auteuil", "race": "4400m Sft Ch (B/16 OR122 — bolted)", "pos": "B", "ran": 16},
             ]},
            {"name": "Daily Present", "trainer": "Paul Nolan", "jockey": "Mr B. T. Stone(5)",
             "odds": "11/1", "age": 9, "form": "331P-0P", "rating": 136,
             "cheltenham_record": "CD winner",
             "last_run": "P/21 Leopardstown 02 Feb 2026 (3m hy hrd) — poor hurdle form since Irish National PU Apr; back to chase for this", "days_off": 37,
             "recent_races": [
                 {"date": "02 Feb 26", "venue": "Leopardstown", "race": "3m 19yds Hy Hdl (P/21 OR131 — hurdles)", "pos": "P", "ran": 21},
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "2m7f 80yds Gd Hdl (13/18 OR132 — hurdles)", "pos": 13, "ran": 18},
                 {"date": "21 Apr 25", "venue": "Fairyhouse", "race": "3m5f 37yds Sft Ch (P/30 OR137 — Irish National)", "pos": "P", "ran": 30},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "3m2f GS Ch (1/23 OR130 — WON this race 2025!)", "pos": 1, "ran": 23},
                 {"date": "12 Jan 25", "venue": "Punchestown", "race": "2m6f 148yds Hy Ch (3/8 OR126)", "pos": 3, "ran": 8},
                 {"date": "01 Dec 24", "venue": "Fairyhouse", "race": "3m5f 160yds Gd Ch (3/13 OR125)", "pos": 3, "ran": 13},
             ]},
            {"name": "Prends Garde A Toi", "trainer": "Gordon Elliott", "jockey": "Mr B. O'Neill",
             "odds": "12/1", "age": 7, "form": "2P14F4", "rating": 137,
             "cheltenham_record": None,
             "last_run": "4th Punchestown 15 Feb 2026 (3m3f hy, 4/14) — outpaced in slowly-run race but rallied; better gallop today suits", "days_off": 24,
             "recent_races": [
                 {"date": "15 Feb 26", "venue": "Punchestown", "race": "3m3f 60yds Hy Ch (4/14 OR133 — outpaced, rallied)", "pos": 4, "ran": 14},
                 {"date": "01 Feb 26", "venue": "Leopardstown", "race": "2m5f 107yds Sft Ch (F/23 OR133 — fell)", "pos": "F", "ran": 23},
                 {"date": "09 Jan 26", "venue": "Naas", "race": "3m 175yds Sft Ch (4/6)", "pos": 4, "ran": 6},
                 {"date": "15 Dec 25", "venue": "Naas", "race": "2m4f 40yds Hy Ch (1/9 WIN)", "pos": 1, "ran": 9},
                 {"date": "22 Nov 25", "venue": "Punchestown", "race": "3m 51yds Sft Ch (P/5)", "pos": "P", "ran": 5},
                 {"date": "25 Oct 25", "venue": "Galway", "race": "2m2f 54yds GS Ch (2/10)", "pos": 2, "ran": 10},
             ]},
            {"name": "Road To Home", "trainer": "W. P. Mullins", "jockey": "Mr P. W. Mullins",
             "odds": "14/1", "age": 7, "form": "F-3533P", "rating": 131,
             "cheltenham_record": None,
             "last_run": "P/21 Leopardstown 02 Feb 2026 (3m hy hrd) — stamina question; best form on gd-sft over fences; kept on 3rd Newbury Dec", "days_off": 37,
             "recent_races": [
                 {"date": "02 Feb 26", "venue": "Leopardstown", "race": "3m 19yds Hy Hdl (P/21 OR124 — heavy)", "pos": "P", "ran": 21},
                 {"date": "17 Dec 25", "venue": "Newbury", "race": "2m3f 187yds GS Ch (3/9 OR129)", "pos": 3, "ran": 9},
                 {"date": "28 Nov 25", "venue": "Doncaster", "race": "2m3f 31yds GS Ch (3/7 OR128)", "pos": 3, "ran": 7},
                 {"date": "26 Oct 25", "venue": "Galway", "race": "2m6f 111yds Sft Ch (5/11)", "pos": 5, "ran": 11},
                 {"date": "07 Oct 25", "venue": "Galway", "race": "2m2f 54yds Sft Ch (3/6)", "pos": 3, "ran": 6},
                 {"date": "22 Apr 25", "venue": "Fairyhouse", "race": "2m7f 35yds Sft Hdl (F/18 OR124 — fell)", "pos": "F", "ran": 18},
             ]},
            {"name": "The Enabler", "trainer": "Gordon Elliott", "jockey": "Mr R. James",
             "odds": "20/1", "age": 7, "form": "06-3143", "rating": 140,
             "cheltenham_record": None,
             "last_run": "3rd Naas 25 Jan 2026 (3m hy, 3/8) — stamina ?, impressive Fairyhouse Dec (2m5f); Elliott+James won this in 2020", "days_off": 44,
             "recent_races": [
                 {"date": "25 Jan 26", "venue": "Naas", "race": "3m 36yds Hy Ch (3/8 — stamina test)", "pos": 3, "ran": 8},
                 {"date": "11 Jan 26", "venue": "Punchestown", "race": "2m3f 115yds Hy Ch (4/5)", "pos": 4, "ran": 5},
                 {"date": "13 Dec 25", "venue": "Fairyhouse", "race": "2m5f 55yds Sft Ch (1/5 WIN — impressive)", "pos": 1, "ran": 5},
                 {"date": "22 Nov 25", "venue": "Punchestown", "race": "2m2f 200yds Sft Ch (3/12)", "pos": 3, "ran": 12},
                 {"date": "20 Apr 25", "venue": "Cork", "race": "2m3f Sft Hdl (6/15 OR129)", "pos": 6, "ran": 15},
                 {"date": "14 Mar 25", "venue": "Cheltenham", "race": "2m4f 56yds GS Hdl (16/24 OR136, Martin Pipe)", "pos": 16, "ran": 24},
             ]},
            {"name": "Sandor Clegane", "trainer": "Paul Nolan", "jockey": "Mr J. W. Hendrick(3)",
             "odds": "25/1", "age": 9, "form": "08-7760", "rating": 138,
             "cheltenham_record": None,
             "last_run": "15th Leopardstown 27 Dec 2025 (3m gd, 15/28) — promising novice chase 2023-24, 0-9 over fences; cheekpieces today", "days_off": 73,
             "recent_races": [
                 {"date": "27 Dec 25", "venue": "Leopardstown", "race": "3m 100yds Gd Ch (15/28 OR136)", "pos": 15, "ran": 28},
                 {"date": "21 Nov 25", "venue": "Fairyhouse", "race": "2m4f Hy Ch (6/10)", "pos": 6, "ran": 10},
                 {"date": "24 Sep 25", "venue": "Listowel", "race": "2m7f 180yds GS Ch (7/18 OR143)", "pos": 7, "ran": 18},
                 {"date": "01 Aug 25", "venue": "Galway", "race": "2m6f 111yds GS Ch (7/16)", "pos": 7, "ran": 16},
                 {"date": "21 Apr 25", "venue": "Fairyhouse", "race": "2m4f Sft Hdl (8/10 — hurdles)", "pos": 8, "ran": 10},
                 {"date": "12 Mar 25", "venue": "Cheltenham", "race": "2m5f GS Hdl (10/26 OR147, Festival hurdles)", "pos": 10, "ran": 26},
             ]},
            {"name": "Weveallbeencaught", "trainer": "Eric McNamara", "jockey": "Mr J. C. Barry",
             "odds": "20/1", "age": 9, "form": "544-420", "rating": 137,
             "cheltenham_record": "Course winner",
             "last_run": "16th Leopardstown 27 Dec 2025 (3m gd, 15/28, disapp) — 4th this race last Mar; 2nd Munster National Oct", "days_off": 73,
             "recent_races": [
                 {"date": "27 Dec 25", "venue": "Leopardstown", "race": "3m 100yds Gd Ch (16/28 OR137 — disappointing)", "pos": 16, "ran": 28},
                 {"date": "19 Oct 25", "venue": "Limerick", "race": "3m Hy Ch (2/15 OR132 — 2nd Munster National)", "pos": 2, "ran": 15},
                 {"date": "27 Sep 25", "venue": "Listowel", "race": "2m6f GS Ch (4/10 OR132)", "pos": 4, "ran": 10},
                 {"date": "05 Apr 25", "venue": "Aintree", "race": "3m 210yds Gd Ch (4/12 OR135)", "pos": 4, "ran": 12},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "3m2f GS Ch (4/23 OR136 — 4th this race)", "pos": 4, "ran": 23},
                 {"date": "01 Mar 25", "venue": "Doncaster", "race": "3m2f 1yds Gd Ch (5/12 OR136)", "pos": 5, "ran": 12},
             ]},
            {"name": "Kings Threshold", "trainer": "Emma Lavelle", "jockey": "Mr H. C. Swan",
             "odds": "25/1", "age": 9, "form": "11P-041", "rating": 137,
             "cheltenham_record": "D",
             "last_run": "Won Newbury 29 Dec 2025 (3m1f gd, 1/6, OR131 — career best, impressive) — 6lb higher today", "days_off": 71,
             "recent_races": [
                 {"date": "29 Dec 25", "venue": "Newbury", "race": "3m1f 214yds Gd Ch (1/6 OR131 — career best WIN)", "pos": 1, "ran": 6},
                 {"date": "29 Nov 25", "venue": "Newbury", "race": "2m6f 93yds GS Ch (4/12 OR132)", "pos": 4, "ran": 12},
                 {"date": "25 Oct 25", "venue": "Cheltenham", "race": "3m1f Gd Ch (11/18 OR134)", "pos": 11, "ran": 18},
                 {"date": "26 Apr 25", "venue": "Sandown Park", "race": "3m4f 146yds GF Ch (P/19 OR142)", "pos": "P", "ran": 19},
                 {"date": "22 Mar 25", "venue": "Newbury", "race": "2m7f 86yds Gd Ch (1/6 OR127 WIN)", "pos": 1, "ran": 6},
                 {"date": "21 Feb 25", "venue": "Warwick", "race": "2m4f Sft Ch (1/8 OR122 WIN)", "pos": 1, "ran": 8},
             ]},
            {"name": "Il Ridoto", "trainer": "Paul Nicholls", "jockey": "Miss Olive Nicholls",
             "odds": "20/1", "age": 9, "form": "07-2872", "rating": 138,
             "cheltenham_record": "Course winner",
             "last_run": "2nd Cheltenham 01 Jan 2026 (2m4f gd, 2/9, OR139) — 2-time Cheltenham winner at 2m4f; trip step up today", "days_off": 68,
             "recent_races": [
                 {"date": "01 Jan 26", "venue": "Cheltenham", "race": "2m4f 127yds Gd Ch (2/9 OR139 — 2nd)", "pos": 2, "ran": 9},
                 {"date": "13 Dec 25", "venue": "Cheltenham", "race": "2m4f 127yds Gd Ch (7/10 OR141)", "pos": 7, "ran": 10},
                 {"date": "15 Nov 25", "venue": "Cheltenham", "race": "2m4f 44yds Sft Ch (8/12 OR142)", "pos": 8, "ran": 12},
                 {"date": "12 Oct 25", "venue": "Chepstow", "race": "2m3f 98yds GF Ch (2/4 OR142)", "pos": 2, "ran": 4},
                 {"date": "16 Apr 25", "venue": "Cheltenham", "race": "2m4f 127yds Gd Ch (7/10 OR144)", "pos": 7, "ran": 10},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m4f 127yds GS Ch (12/20 OR145)", "pos": 12, "ran": 20},
             ]},
            {"name": "Excello", "trainer": "Nicky Henderson", "jockey": "Mr Henry Main(5)",
             "odds": "20/1", "age": 7, "form": "740-30F", "rating": 132,
             "cheltenham_record": None,
             "last_run": "F/8 Cheltenham 01 Jan 2026 (3m1f gd, fell) — 3rd Aintree National fences Nov; stamina doubts at 3m2f+", "days_off": 68,
             "recent_races": [
                 {"date": "01 Jan 26", "venue": "Cheltenham", "race": "3m1f 56yds Gd Ch (F/8 OR132 — fell)", "pos": "F", "ran": 8},
                 {"date": "06 Dec 25", "venue": "Aintree", "race": "3m1f 188yds Sft Ch (10/13 OR133)", "pos": 10, "ran": 13},
                 {"date": "08 Nov 25", "venue": "Aintree", "race": "2m5f 19yds Gd Ch (3/17 OR132 — National fences)", "pos": 3, "ran": 17},
                 {"date": "04 Apr 25", "venue": "Aintree", "race": "2m5f 19yds Gd Ch (14/30 OR134)", "pos": 14, "ran": 30},
                 {"date": "08 Mar 25", "venue": "Sandown Park", "race": "3m 37yds GS Ch (4/6 OR132 — close 4th)", "pos": 4, "ran": 6},
                 {"date": "09 Feb 25", "venue": "Exeter", "race": "2m7f 25yds Sft Hdl (7/12 OR128 — hurdles)", "pos": 7, "ran": 12},
             ]},
            {"name": "Gericault Roque", "trainer": "David Pipe", "jockey": "Mr B. Lawless(7)",
             "odds": "20/1", "age": 10, "form": "53//30-82", "rating": 129,
             "cheltenham_record": None,
             "last_run": "2nd Ascot 14 Feb 2026 (2m7f GS, 2/11, OR128, first-time cheekpieces) — revival; 2nd Ultima here 2022", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Ascot", "race": "2m7f 185yds GS Ch (2/11 OR128 — CPs first time, revival)", "pos": 2, "ran": 11},
                 {"date": "16 Jan 26", "venue": "Windsor", "race": "2m6f 50yds Sft Ch (8/10 OR128)", "pos": 8, "ran": 10},
                 {"date": "11 Mar 25", "venue": "Cheltenham", "race": "3m5f 201yds GS Ch (10/18 OR131 — Festival)", "pos": 10, "ran": 18},
                 {"date": "17 Jan 25", "venue": "Windsor", "race": "3m 53yds GS Ch (3/6 OR133)", "pos": 3, "ran": 6},
                 {"date": "26 Nov 22", "venue": "Newbury", "race": "3m1f 214yds Gd Ch (3/15 OR139)", "pos": 3, "ran": 15},
                 {"date": "05 Nov 22", "venue": "Aintree", "race": "3m 149yds GS Hdl (5/7 OR139)", "pos": 5, "ran": 7},
             ]},
            {"name": "Ask Brewster", "trainer": "Mrs C. Williams", "jockey": "Mr S. Cotter(7)",
             "odds": "20/1", "age": 7, "form": "P511-15", "rating": 128,
             "cheltenham_record": "Course winner",
             "last_run": "5th Sandown 06 Dec 2025 (3m4f GS, 5/6, OR129) — hat-trick last yr incl Cheltenham Apr; tired Sandown (gd-sft,soft)", "days_off": 95,
             "recent_races": [
                 {"date": "06 Dec 25", "venue": "Sandown Park", "race": "3m4f 146yds GS Ch (5/6 OR129 — tired in soft patches)", "pos": 5, "ran": 6},
                 {"date": "11 Oct 25", "venue": "Chepstow", "race": "2m7f 131yds GF Ch (1/7 OR121 WIN)", "pos": 1, "ran": 7},
                 {"date": "16 Apr 25", "venue": "Cheltenham", "race": "3m4f 21yds Gd Ch (1/14 OR112 WIN Cheltenham)", "pos": 1, "ran": 14},
                 {"date": "16 Mar 25", "venue": "Chepstow", "race": "2m7f 131yds Gd Ch (1/7 OR103 WIN)", "pos": 1, "ran": 7},
                 {"date": "18 Feb 25", "venue": "Taunton", "race": "2m7f 3yds GS Ch (5/8 OR105)", "pos": 5, "ran": 8},
                 {"date": "28 Jan 25", "venue": "Chepstow", "race": "2m7f 131yds Hy Ch (P/9 OR107)", "pos": "P", "ran": 9},
             ]},
            {"name": "Monbeg Genius", "trainer": "Jonjo & A.J. O'Neill", "jockey": "Mr J. L. Scallan(5)",
             "odds": "40/1", "age": 10, "form": "1P6-P57", "rating": 141,
             "cheltenham_record": None,
             "last_run": "7th Haydock 14 Feb 2026 (3m4f GS, 7/11, OR142) — ran well Welsh National + Haydock GNT; blinkers today (was CPs)", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Haydock Park", "race": "3m4f 97yds GS Ch (7/11 OR142 — GNT)", "pos": 7, "ran": 11},
                 {"date": "27 Dec 25", "venue": "Chepstow", "race": "3m6f 136yds GF Ch (5/17 OR144 — Welsh National)", "pos": 5, "ran": 17},
                 {"date": "06 Dec 25", "venue": "Aintree", "race": "3m1f 188yds Sft Ch (P/13 OR144)", "pos": "P", "ran": 13},
                 {"date": "26 Apr 25", "venue": "Sandown Park", "race": "3m4f 146yds GF Ch (6/19 OR145)", "pos": 6, "ran": 19},
                 {"date": "05 Apr 25", "venue": "Aintree", "race": "4m2f 74yds Gd Ch (P/34 OR147 — Grand National)", "pos": "P", "ran": 34},
                 {"date": "08 Feb 25", "venue": "Uttoxeter", "race": "3m Hy Ch (1/8 OR142 WIN)", "pos": 1, "ran": 8},
             ]},
            {"name": "Uncle Bert", "trainer": "Nigel & Willy Twiston-Davies", "jockey": "Miss Amber Jackson-Fennell(5)",
             "odds": "40/1", "age": 9, "form": "159-1F7", "rating": 137,
             "cheltenham_record": None,
             "last_run": "7th Cheltenham 24 Jan 2026 (2m4f sft, 7/11, OR138) — Welsh National fell 2 out; below par Jan", "days_off": 45,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Cheltenham", "race": "2m4f 127yds Sft Ch (7/11 OR138 — below par)", "pos": 7, "ran": 11},
                 {"date": "27 Dec 25", "venue": "Chepstow", "race": "3m6f 136yds GF Ch (F/17 OR136 — Welsh National fell 2 out)", "pos": "F", "ran": 17},
                 {"date": "06 Dec 25", "venue": "Aintree", "race": "2m3f 200yds GS Ch (1/6 OR132 WIN)", "pos": 1, "ran": 6},
                 {"date": "14 Mar 25", "venue": "Cheltenham", "race": "2m4f 56yds GS Hdl (9/24 OR136, Martin Pipe)", "pos": 9, "ran": 24},
                 {"date": "15 Feb 25", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (5/13 OR136)", "pos": 5, "ran": 13},
                 {"date": "18 Jan 25", "venue": "Haydock Park", "race": "3m 58yds Sft Hdl (1/11 OR132 WIN)", "pos": 1, "ran": 11},
             ]},
            {"name": "Insurrection", "trainer": "Paul Nicholls", "jockey": "Miss Gina Andrews",
             "odds": "33/1", "age": 9, "form": "3188-38", "rating": 138,
             "cheltenham_record": "BF",
             "last_run": "8th Musselburgh 31 Jan 2026 (2m4f GS, 8/8, BF) — inconsistent; stamina big unknown (won 3m point); 2m4f specialist", "days_off": 38,
             "recent_races": [
                 {"date": "31 Jan 26", "venue": "Musselburgh", "race": "2m4f 68yds GS Ch (8/8 OR139 — well beaten)", "pos": 8, "ran": 8},
                 {"date": "01 Jan 26", "venue": "Musselburgh", "race": "2m4f 68yds GS Ch (3/9 OR139)", "pos": 3, "ran": 9},
                 {"date": "26 Apr 25", "venue": "Sandown Park", "race": "2m4f 10yds GF Ch (8/9 OR141)", "pos": 8, "ran": 9},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m4f 127yds GS Ch (8/19 OR142 — Festival)", "pos": 8, "ran": 19},
                 {"date": "02 Feb 25", "venue": "Musselburgh", "race": "2m4f 68yds GS Ch (1/7 OR134 WIN)", "pos": 1, "ran": 7},
                 {"date": "29 Dec 24", "venue": "Doncaster", "race": "2m4f 115yds GS Ch (3/3 OR135)", "pos": 3, "ran": 3},
             ]},
            {"name": "Glengouly", "trainer": "Faye Bramley", "jockey": "Mr Dara McGill",
             "odds": "25/1", "age": 10, "form": "0341PP", "rating": 131,
             "cheltenham_record": "Course winner",
             "last_run": "P/11 Newbury 28 Feb 2026 (2m3f GS, pulled up — only 12 days ago); also P/9 Cheltenham 01 Jan (shoe); won C 2m4f Dec", "days_off": 11,
             "recent_races": [
                 {"date": "28 Feb 26", "venue": "Newbury", "race": "2m3f 187yds GS Ch (P/11 OR131 — pulled up 12 days ago!)", "pos": "P", "ran": 11},
                 {"date": "01 Jan 26", "venue": "Cheltenham", "race": "2m4f 127yds Gd Ch (P/9 OR131 — lost shoe Cheltenham)", "pos": "P", "ran": 9},
                 {"date": "13 Dec 25", "venue": "Cheltenham", "race": "2m4f 127yds Gd Ch (1/10 OR128 WIN — Cheltenham)", "pos": 1, "ran": 10},
                 {"date": "16 Nov 25", "venue": "Cheltenham", "race": "1m7f 199yds Sft Ch (4/11 OR121)", "pos": 4, "ran": 11},
                 {"date": "08 Nov 25", "venue": "Aintree", "race": "1m7f 176yds Gd Ch (3/9 OR119)", "pos": 3, "ran": 9},
                 {"date": "17 Oct 25", "venue": "Uttoxeter", "race": "2m3f 207yds GS Hdl (10/10 OR124)", "pos": 10, "ran": 10},
             ]},
            {"name": "No Time To Wait", "trainer": "John McConnell", "jockey": "Mr Josh Halford(3)",
             "odds": "40/1", "age": 8, "form": "9-22U04", "rating": 129,
             "cheltenham_record": None,
             "last_run": "4th Fairyhouse 21 Feb 2026 (3m2f hy, 4/8) — 0-9 over fences; first-time blinkers; NH Chase 9th last Festival", "days_off": 18,
             "recent_races": [
                 {"date": "21 Feb 26", "venue": "Fairyhouse", "race": "3m2f Hy Ch (4/8 — blinkers today)", "pos": 4, "ran": 8},
                 {"date": "27 Dec 25", "venue": "Leopardstown", "race": "3m 100yds Gd Ch (13/28 OR129)", "pos": 13, "ran": 28},
                 {"date": "16 Nov 25", "venue": "Navan", "race": "3m Hy Ch (U/19 OR130 — unseated)", "pos": "U", "ran": 19},
                 {"date": "11 Jul 25", "venue": "Kilbeggan", "race": "3m1f 80yds Gd Ch (2/4)", "pos": 2, "ran": 4},
                 {"date": "08 Jun 25", "venue": "Punchestown", "race": "3m 186yds Gd Ch (2/5)", "pos": 2, "ran": 5},
                 {"date": "11 Mar 25", "venue": "Cheltenham", "race": "3m5f 201yds GS Ch (9/18 OR133 — NH Chase)", "pos": 9, "ran": 18},
             ]},
            {"name": "Olympic Man", "trainer": "John McConnell", "jockey": "Mr D. Doyle(3)",
             "odds": "33/1", "age": 9, "form": "17P-P6P", "rating": 136,
             "cheltenham_record": None,
             "last_run": "P/18 Leopardstown 28 Dec 2025 (hurdles) — sold Jan for 16,000gns; big revival needed on stable debut; CPs", "days_off": 72,
             "recent_races": [
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "2m7f 80yds Gd Hdl (P/18 OR134 — hurdles, Mullins)", "pos": "P", "ran": 18},
                 {"date": "23 Nov 25", "venue": "Punchestown", "race": "3m 37yds Sft Hdl (6/9 OR135 — hurdles)", "pos": 6, "ran": 9},
                 {"date": "21 Oct 25", "venue": "Curragh", "race": "1m4f Hy Flat (5/12 — flat race)", "pos": 5, "ran": 12},
                 {"date": "26 Sep 25", "venue": "Listowel", "race": "1m6f GS Flat (3/11 — flat)", "pos": 3, "ran": 11},
                 {"date": "30 Jul 25", "venue": "Galway", "race": "2m6f 111yds GS Ch (P/22 OR137 — chase)", "pos": "P", "ran": 22},
                 {"date": "26 Apr 25", "venue": "Sandown Park", "race": "3m4f 146yds GF Ch (P/19 OR142 — chase)", "pos": "P", "ran": 19},
             ]},
            {"name": "Lord Accord", "trainer": "Neil Mulholland", "jockey": "Mr N. McParlan",
             "odds": "40/1", "age": 11, "form": "062412", "rating": 127,
             "cheltenham_record": "CD winner",
             "last_run": "2nd Ascot 22 Nov 2025 (3m5f GS, 2/12, OR127) — returns from break; won Fontwell Oct; C+D symbols on racecard", "days_off": 109,
             "recent_races": [
                 {"date": "22 Nov 25", "venue": "Ascot", "race": "3m5f 75yds GS Ch (2/12 OR127)", "pos": 2, "ran": 12},
                 {"date": "26 Oct 25", "venue": "Fontwell Park", "race": "3m1f 210yds Gd Ch (1/7 OR123 WIN blinkers)", "pos": 1, "ran": 7},
                 {"date": "10 Oct 25", "venue": "Chepstow", "race": "2m7f 131yds GF Ch (4/7 OR123)", "pos": 4, "ran": 7},
                 {"date": "25 Aug 25", "venue": "Cartmel", "race": "3m1f 107yds Gd Ch (2/9 OR123)", "pos": 2, "ran": 9},
                 {"date": "27 Jul 25", "venue": "Uttoxeter", "race": "3m2f 13yds Gd Ch (6/10 OR125)", "pos": 6, "ran": 10},
                 {"date": "29 Jun 25", "venue": "Uttoxeter", "race": "3m2f 13yds Gd Ch (12/15 OR127)", "pos": 12, "ran": 15},
             ]},
            {"name": "Cave Court", "trainer": "Noel C. Kelly", "jockey": "Mr O. McGill",
             "odds": "50/1", "age": 9, "form": "14-7208", "rating": 131,
             "cheltenham_record": None,
             "last_run": "8th Haydock 14 Feb 2026 (3m GS hrd, 8/13, tailed off) — up against it today", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Haydock Park", "race": "3m 58yds GS Hdl (8/13 OR131 — tailed off)", "pos": 8, "ran": 13},
                 {"date": "01 Aug 25", "venue": "Galway", "race": "2m6f 111yds GS Ch (13/20 OR128)", "pos": 13, "ran": 20},
                 {"date": "29 Jun 25", "venue": "Cartmel", "race": "2m5f 34yds Sft Ch (2/10 OR131)", "pos": 2, "ran": 10},
                 {"date": "29 Apr 25", "venue": "Punchestown", "race": "2m3f 93yds GS Hdl (7/25 OR128)", "pos": 7, "ran": 25},
                 {"date": "08 Mar 25", "venue": "Ayr", "race": "2m4f 110yds Hy Ch (4/5 OR132)", "pos": 4, "ran": 5},
                 {"date": "26 Jan 25", "venue": "Naas", "race": "2m2f 150yds Hy Hdl (1/14 OR119 WIN)", "pos": 1, "ran": 14},
             ]},
            {"name": "Hung Jury", "trainer": "Martin Keighley", "jockey": "Mr James King",
             "odds": "33/1", "age": 11, "form": "4812P0", "rating": 127,
             "cheltenham_record": "Course winner",
             "last_run": "16th Ascot 14 Feb 2026 (2m7f hrd, 16/18, tailed off hurdles) — won here Nov (hdcp) + May hunter chase; back to chasing", "days_off": 25,
             "recent_races": [
                 {"date": "14 Feb 26", "venue": "Ascot", "race": "2m7f 123yds GS Hdl (16/18 OR124 — tailed off over hurdles)", "pos": 16, "ran": 18},
                 {"date": "27 Dec 25", "venue": "Chepstow", "race": "3m6f 136yds GF Ch (P/17 OR129 — Welsh Nat PU)", "pos": "P", "ran": 17},
                 {"date": "06 Dec 25", "venue": "Sandown Park", "race": "3m4f 146yds GS Ch (2/6 OR128)", "pos": 2, "ran": 6},
                 {"date": "15 Nov 25", "venue": "Cheltenham", "race": "3m1f Sft Ch (1/16 OR122 WIN — Cheltenham)", "pos": 1, "ran": 16},
                 {"date": "24 Oct 25", "venue": "Cheltenham", "race": "3m1f Gd Ch (8/18 OR124)", "pos": 8, "ran": 18},
                 {"date": "13 Jun 25", "venue": "Newton Abbot", "race": "3m1f 170yds GS Ch (4/4 OR125)", "pos": 4, "ran": 4},
             ]},
            {"name": "J'Arrive de L'Est", "trainer": "Unknown", "jockey": "Unknown",
             "odds": "66/1", "age": 7, "form": "000000", "rating": 120,
             "cheltenham_record": None,
             "last_run": "Qualifier run for Kim Muir", "days_off": 28,
             "recent_races": []},
        ]
    },
    "day4_race1": {   # JCB Triumph Hurdle  (Grade 1, 2m179yds — 20 runners, Fri 13 Mar 13:20)
        # UPDATED 11/03/2026 from official racecard. 20 confirmed runners. EW: 1/5 odds 4 places.
        # JOCKEY CHANGES: Proactif -> M.P.Walsh (was Townend); Selma De Vary -> Townend (was TBD)
        # Highland Crystal -> J.W.Kennedy (was TBD); Macho Man -> B.Hayes (was TBD)
        # Scratched: Madness D'elle, Manganese, Barbizon. New: Mon Creuset, Minella Academy,
        # Kai Lung, North Shore, Apolon De Charnie, Forty Fifty, Noemie De La Vis,
        # Tenter Le Tout, Wolf Rayet, Berto Ramirez
        "entries": [
            {"name": "Proactif", "trainer": "Willie Mullins", "jockey": "M. P. Walsh",
             "odds": "7/2", "age": 4, "form": "1-1", "rating": 139,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "Minella Study", "trainer": "Adam Nicol", "jockey": "Ryan Mania",
             "odds": "7/1", "age": 4, "form": "1-1-1", "rating": 139,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 2 Juvenile Hurdle Feb 2026 (CD)", "days_off": 28},
            {"name": "Selma De Vary", "trainer": "Willie Mullins", "jockey": "Paul Townend",
             "odds": "4/1", "age": 4, "form": "2-1-5-2", "rating": 136,
             "cheltenham_record": None,
             "last_run": "2nd Grade 1 Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "Maestro Conti", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "7/1", "age": 4, "form": "3-1-1-1", "rating": 135,
             "cheltenham_record": "CD winner",
             "last_run": "Won Juvenile Hurdle Jan 2026 (CD)", "days_off": 42},
            {"name": "Highland Crystal", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "9/1", "age": 4, "form": "1-1-1", "rating": 133,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Juvenile Hurdle Feb 2026 (D — distance, not CD)", "days_off": 28},
            {"name": "Macho Man", "trainer": "Willie Mullins", "jockey": "B. Hayes",
             "odds": "10/1", "age": 4, "form": "1-2", "rating": 130,
             "cheltenham_record": None,
             "last_run": "2nd Grade 2 Jan 2026", "days_off": 42},
            {"name": "Mon Creuset", "trainer": "Willie Mullins", "jockey": "Harry Cobden",
             "odds": "12/1", "age": 4, "form": "1-4", "rating": 125,
             "cheltenham_record": None,
             "last_run": "Won Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "One Horse Town", "trainer": "Harry Derham", "jockey": "Paul O'Brien",
             "odds": "10/1", "age": 4, "form": "2-2-1-1", "rating": 132,
             "cheltenham_record": "CD winner",
             "last_run": "Won Juvenile Hurdle Feb 2026 (CD)", "days_off": 28},
            {"name": "Minella Academy", "trainer": "Willie Mullins", "jockey": "D. E. Mullins",
             "odds": "16/1", "age": 4, "form": "1", "rating": 121,
             "cheltenham_record": None,
             "last_run": "Won Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "Kai Lung", "trainer": "Willie Mullins", "jockey": "S. F. O'Keeffe",
             "odds": "20/1", "age": 4, "form": "1", "rating": 119,
             "cheltenham_record": None,
             "last_run": "Won Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "North Shore", "trainer": "Gavin Patrick Cromwell", "jockey": "Keith Donoghue",
             "odds": "25/1", "age": 4, "form": "3-4", "rating": 116,
             "cheltenham_record": None,
             "last_run": "3rd Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "Apolon De Charnie", "trainer": "Willie Mullins", "jockey": "Mr P. W. Mullins",
             "odds": "33/1", "age": 4, "form": "2", "rating": 118,
             "cheltenham_record": None,
             "last_run": "2nd Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "Forty Fifty", "trainer": "Willie Mullins", "jockey": "Jonathan Burke",
             "odds": "25/1", "age": 4, "form": "4", "rating": 115,
             "cheltenham_record": None,
             "last_run": "4th Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "Noemie De La Vis", "trainer": "Willie Mullins", "jockey": "D. King",
             "odds": "20/1", "age": 4, "form": "2-2", "rating": 120,
             "cheltenham_record": None,
             "last_run": "2nd Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "Tenter Le Tout", "trainer": "Chester Williams", "jockey": "Gavin Sheehan",
             "odds": "33/1", "age": 4, "form": "4-1-1-6", "rating": 119,
             "cheltenham_record": None,
             "last_run": "6th Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "Wolf Rayet", "trainer": "Samuel Drinkwater", "jockey": "Robert Dunne",
             "odds": "50/1", "age": 4, "form": "2-4-3", "rating": 114,
             "cheltenham_record": None,
             "last_run": "3rd Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "Indian River", "trainer": "Adrian Keatley", "jockey": "Kielan Woods",
             "odds": "66/1", "age": 4, "form": "1-1-1", "rating": 122,
             "cheltenham_record": None,
             "last_run": "Won Juvenile Hurdle Jan 2026 (D — distance winner)", "days_off": 42},
            {"name": "Fantasy World", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "66/1", "age": 4, "form": "4-3", "rating": 120,
             "cheltenham_record": None,
             "last_run": "3rd Juvenile Hurdle Feb 2026", "days_off": 28},
            {"name": "Lord Byron", "trainer": "Faye Bramley", "jockey": "Ben Jones",
             "odds": "25/1", "age": 4, "form": "2-4-4", "rating": 123,
             "cheltenham_record": None,
             "last_run": "4th Juvenile Hurdle Jan 2026", "days_off": 42},
            {"name": "Berto Ramirez", "trainer": "Andrew McNamara", "jockey": "D. J. O'Keeffe",
             "odds": "66/1", "age": 4, "form": "5-7-4", "rating": 110,
             "cheltenham_record": None,
             "last_run": "5th Juvenile Hurdle Jan 2026", "days_off": 42},
        ]
    },
    "day4_race2": {   # William Hill County Handicap Hurdle  (Grade 3, 2m179yds — 26 runners, Fri 13 Mar 14:00)
        # UPDATED 11/03/2026 from official racecard. 26 confirmed runners. EW: 1/5 odds 6 places.
        # JOCKEY CHANGES: Karbau -> Townend (was Mark Walsh — big move); Murcia -> D.E.Mullins (was TBD)
        # Ndaawi -> J.H.Williamson(5) apprentice; Bowensonfire -> J.W.Kennedy; Absurde -> Mr P.W.Mullins
        # Scratched: Workahead, Khrisma, Jump Allen. 15 new runners added.
        "entries": [
            {"name": "Karbau", "trainer": "Willie Mullins", "jockey": "Paul Townend",
             "odds": "9/2", "age": 6, "form": "4-1-0-3-2", "rating": 150,
             "cheltenham_record": None,
             "last_run": "2nd Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "Murcia", "trainer": "Willie Mullins", "jockey": "D. E. Mullins",
             "odds": "11/2", "age": 5, "form": "2-8-1-4-3", "rating": 142,
             "cheltenham_record": None,
             "last_run": "3rd Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "Sinnatra", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "8/1", "age": 6, "form": "4-2-2-1-3-1", "rating": 133,
             "cheltenham_record": None,
             "last_run": "Won Betfair Hurdle Feb 2026", "days_off": 28},
            {"name": "Ndaawi", "trainer": "Gordon Elliott", "jockey": "J. H. Williamson",
             "odds": "10/1", "age": 6, "form": "3-6-2-2-1-3", "rating": 156,
             "cheltenham_record": None,
             "last_run": "3rd Grade 3 Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "Absurde", "trainer": "Willie Mullins", "jockey": "Mr P. W. Mullins",
             "odds": "10/1", "age": 9, "form": "6-P-4-1-3-1", "rating": 155,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 3 Handicap Hurdle Feb 2026 (CD)", "days_off": 28},
            {"name": "Hello Neighbour", "trainer": "Gavin Patrick Cromwell", "jockey": "Keith Donoghue",
             "odds": "12/1", "age": 5, "form": "1-1-6-3-5-7", "rating": 148,
             "cheltenham_record": None,
             "last_run": "7th Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "Wilful", "trainer": "Jonjo O'Neill", "jockey": "Jonjo O'Neill Jr.",
             "odds": "12/1", "age": 6, "form": "P-1-2-3-1-2", "rating": 145,
             "cheltenham_record": None,
             "last_run": "2nd Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "Bowensonfire", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "12/1", "age": 6, "form": "3-3-3-2-1-1", "rating": 153,
             "cheltenham_record": None,
             "last_run": "Won Handicap Hurdle Feb 2026 (D)", "days_off": 28},
            {"name": "Sixandahalf", "trainer": "Gavin Patrick Cromwell", "jockey": "C. Stone-Walsh",
             "odds": "14/1", "age": 6, "form": "1-1-2-3-2-4", "rating": 140,
             "cheltenham_record": None,
             "last_run": "4th Handicap Hurdle Jan 2026 (D)", "days_off": 42},
            {"name": "Jubilee Alpha", "trainer": "Paul Nicholls", "jockey": "Harry Cobden",
             "odds": "14/1", "age": 7, "form": "8-1-2-5-2-2", "rating": 139,
             "cheltenham_record": None,
             "last_run": "2nd Handicap Hurdle Feb 2026 (CD area)", "days_off": 28},
            {"name": "Tellherthename", "trainer": "Dan Skelton", "jockey": "Kielan Woods",
             "odds": "16/1", "age": 7, "form": "1-0-4-P-5-3", "rating": 138,
             "cheltenham_record": None,
             "last_run": "3rd Handicap Hurdle Feb 2026", "days_off": 28},
            {"name": "Joyeuse", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "16/1", "age": 6, "form": "6-9-2-2-9-4", "rating": 136,
             "cheltenham_record": None,
             "last_run": "4th Handicap Hurdle Jan 2026 (D)", "days_off": 42},
            {"name": "Secret Squirrel", "trainer": "Hughie Morrison", "jockey": "Jonathan Burke",
             "odds": "16/1", "age": 7, "form": "5-3-F-1-F-3", "rating": 137,
             "cheltenham_record": None,
             "last_run": "3rd Handicap Hurdle Feb 2026 (D)", "days_off": 28},
            {"name": "Tripoli Flyer", "trainer": "Fergal O'Brien", "jockey": "Fern O'Brien",
             "odds": "20/1", "age": 6, "form": "6-3-U-4-5-2", "rating": 135,
             "cheltenham_record": None,
             "last_run": "2nd Handicap Hurdle Jan 2026 (D)", "days_off": 42},
            {"name": "Helvic Dream", "trainer": "Noel Meade", "jockey": "Donagh Meyler",
             "odds": "20/1", "age": 7, "form": "3-2-5-2-5-2", "rating": 143,
             "cheltenham_record": None,
             "last_run": "2nd Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "Bowmore", "trainer": "Charlie Longsdon", "jockey": "Daire McConville",
             "odds": "25/1", "age": 6, "form": "4-3-3-2-1-3", "rating": 132,
             "cheltenham_record": None,
             "last_run": "3rd Handicap Hurdle Feb 2026 (D)", "days_off": 28},
            {"name": "Wellington Arch", "trainer": "Jonjo O'Neill", "jockey": "Reserve",
             "odds": "25/1", "age": 7, "form": "1-2-1-3-9-2", "rating": 138,
             "cheltenham_record": None,
             "last_run": "2nd Handicap Hurdle Jan 2026 (D)", "days_off": 42},
            {"name": "Williethebuilder", "trainer": "Christian Williams", "jockey": "Jack Tudor",
             "odds": "25/1", "age": 6, "form": "6-3-2-1-1-4", "rating": 130,
             "cheltenham_record": None,
             "last_run": "Won Handicap Hurdle Feb 2026", "days_off": 28},
            {"name": "Sticktotheplan", "trainer": "Olly Murphy", "jockey": "Sean Bowen",
             "odds": "25/1", "age": 7, "form": "1-2-1-1-3-0", "rating": 134,
             "cheltenham_record": None,
             "last_run": "3rd Handicap Hurdle Jan 2026 (D)", "days_off": 42},
            {"name": "Gibbs Island", "trainer": "Tom Lacey", "jockey": "Stan Sheppard",
             "odds": "33/1", "age": 8, "form": "P-8-1-0-5-7", "rating": 128,
             "cheltenham_record": None,
             "last_run": "7th Handicap Hurdle Jan 2026 (D)", "days_off": 42},
            {"name": "Hamlets Night", "trainer": "James Owen", "jockey": "James Bowen",
             "odds": "33/1", "age": 6, "form": "2-1-1-2-2-0", "rating": 126,
             "cheltenham_record": None,
             "last_run": "Won Handicap Hurdle Feb 2026", "days_off": 28},
            {"name": "Balko Dange", "trainer": "Philip Fenton", "jockey": "B. Hayes",
             "odds": "33/1", "age": 7, "form": "4-5-1-3-F-6", "rating": 124,
             "cheltenham_record": None,
             "last_run": "6th Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "Ooh Betty", "trainer": "Ben Clarke", "jockey": "Ben Jones",
             "odds": "50/1", "age": 8, "form": "0-3-0-0-0-1", "rating": 118,
             "cheltenham_record": None,
             "last_run": "Won Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "Pinot Gris", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "33/1", "age": 7, "form": "2-1-2-8-7-0", "rating": 130,
             "cheltenham_record": None,
             "last_run": "0th Handicap Hurdle Jan 2026 (D)", "days_off": 42},
            {"name": "Captain Ryan Matt", "trainer": "Henry de Bromhead", "jockey": "Reserve",
             "odds": "33/1", "age": 7, "form": "2-1-5-6-3-1", "rating": 132,
             "cheltenham_record": None,
             "last_run": "Won Handicap Hurdle Feb 2026 (D)", "days_off": 28},
            {"name": "Cracking Rhapsody", "trainer": "Ewan Whillans", "jockey": "Craig Nichol",
             "odds": "66/1", "age": 8, "form": "7-1-0-6-6-6", "rating": 120,
             "cheltenham_record": None,
             "last_run": "6th Handicap Hurdle Jan 2026", "days_off": 42},
        ]
    },
    "day4_race3": {   # Albert Bartlett / Spa Novices' Hurdle  (Grade 1, 3m — 22 runners, Fri 13 Mar 15:20)
        # UPDATED 11/03/2026 from official racecard. 22 confirmed runners. EW: 1/5 odds 4 places.
        # JOCKEY CHANGES: Thedeviluno -> S.F.O'Keeffe (was Bryan Cooper); Kazansky -> J.C.Gainford
        # Spinningayarn -> J.W.Kennedy; The Passing Wife -> Keith Donoghue
        # Moneygarrow -> Harry Skelton (trainer change Elliott->Skelton); Park Princess -> Twiston-Davies
        # Scratched: No Drama This End, I'll Sort That. 13 new runners added.
        # Kripticjim: C only (course winner, NOT course+distance)
        "entries": [
            {"name": "Doctor Steinberg", "trainer": "Willie Mullins", "jockey": "Paul Townend",
             "odds": "9/4", "age": 6, "form": "2-1-5-1-1-1", "rating": 147,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Thedeviluno", "trainer": "Paul Nolan", "jockey": "S. F. O'Keeffe",
             "odds": "5/1", "age": 7, "form": "2-2-2-1-2-1", "rating": 141,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 3m Novice Hurdle Feb 2026 (D)", "days_off": 28},
            {"name": "The Passing Wife", "trainer": "Gavin Patrick Cromwell", "jockey": "Keith Donoghue",
             "odds": "8/1", "age": 6, "form": "1-1-3-3-5-1", "rating": 139,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle 3m Feb 2026", "days_off": 28},
            {"name": "Spinningayarn", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "12/1", "age": 6, "form": "1-4-3-1-1", "rating": 135,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Doctor Du Mesnil", "trainer": "Willie Mullins", "jockey": "D. E. Mullins",
             "odds": "14/1", "age": 6, "form": "1-2-2", "rating": 133,
             "cheltenham_record": None,
             "last_run": "2nd Grade 2 Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Espresso Milan", "trainer": "Willie Mullins", "jockey": "Mr P. W. Mullins",
             "odds": "11/1", "age": 6, "form": "4-2-7-1-1", "rating": 134,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle 3m Jan 2026", "days_off": 42},
            {"name": "Jalon Doudairies", "trainer": "Gordon Elliott", "jockey": "Danny Gilligan",
             "odds": "20/1", "age": 6, "form": "1-1-3-2-2-1", "rating": 132,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle 3m Feb 2026", "days_off": 28},
            {"name": "Kazansky", "trainer": "Gordon Elliott", "jockey": "Jordan Gainford",
             "odds": "16/1", "age": 6, "form": "B-1-1-2", "rating": 139,
             "cheltenham_record": None,
             "last_run": "2nd Grade 2 Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Kings Bucks", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "20/1", "age": 6, "form": "2-4-3-2", "rating": 130,
             "cheltenham_record": None,
             "last_run": "2nd Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Mondouiboy", "trainer": "Ben Pauling", "jockey": "Ben Jones",
             "odds": "14/1", "age": 6, "form": "2-6-1-1", "rating": 134,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle 3m Feb 2026", "days_off": 28},
            {"name": "Moneygarrow", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "16/1", "age": 5, "form": "2-2-3-5-1-1", "rating": 133,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle 3m Feb 2026 (D)", "days_off": 28},
            {"name": "Kripticjim", "trainer": "Joe Tizzard", "jockey": "Brendan Powell",
             "odds": "10/1", "age": 5, "form": "2-1-2-1-1-1", "rating": 135,
             "cheltenham_record": "Course winner",
             "last_run": "Won Novice Hurdle 3m Feb 2026 (C)", "days_off": 28},
            {"name": "Johnnys Jury", "trainer": "Jamie Snowden", "jockey": "Gavin Sheehan",
             "odds": "25/1", "age": 6, "form": "3-1-1", "rating": 128,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Hipop De Loire", "trainer": "Willie Mullins", "jockey": "Harry Cobden",
             "odds": "40/1", "age": 5, "form": "2-1", "rating": 123,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Road Exile", "trainer": "Gordon Elliott", "jockey": "Sam Ewing",
             "odds": "25/1", "age": 6, "form": "2-1-3-1-2", "rating": 126,
             "cheltenham_record": None,
             "last_run": "2nd Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Fruit De Mer", "trainer": "Henry de Bromhead", "jockey": "Sean Flanagan",
             "odds": "33/1", "age": 6, "form": "2-1-3", "rating": 124,
             "cheltenham_record": None,
             "last_run": "3rd Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Ubatuba", "trainer": "Olly Murphy", "jockey": "Ben Sutton",
             "odds": "33/1", "age": 5, "form": "1-1-2", "rating": 122,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Park Princess", "trainer": "Anthony Honeyball", "jockey": "Sam Twiston-Davies",
             "odds": "16/1", "age": 5, "form": "9-1-2-1-7-1", "rating": 132,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle 3m Jan 2026 (D)", "days_off": 42},
            {"name": "Kicour La", "trainer": "Ben Pauling", "jockey": "Callum Pritchard",
             "odds": "33/1", "age": 5, "form": "1-1-4", "rating": 120,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Jan 2026", "days_off": 42},
            {"name": "Swindon Village", "trainer": "Charlie Longsdon", "jockey": "David Bass",
             "odds": "33/1", "age": 7, "form": "3-6-3-1-3-1", "rating": 125,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Tackletommywoowoo", "trainer": "Declan Queally", "jockey": "Mr D. L. Queally",
             "odds": "50/1", "age": 6, "form": "F-1-6-1-1-7", "rating": 118,
             "cheltenham_record": None,
             "last_run": "7th Novice Hurdle Jan 2026 (D)", "days_off": 42},
            {"name": "The Price Of Peace", "trainer": "Rebecca Curtis", "jockey": "Sean Bowen",
             "odds": "33/1", "age": 6, "form": "2-1-5", "rating": 120,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Feb 2026 (D)", "days_off": 28},
        ]
    },
    "day4_race4": {   # Mrs Paddy Power/Liberthine Mares' Chase  (Grade 2, 2m4f — 9 runners, Fri 13 Mar 14:40)
        # UPDATED 11/03/2026 from official racecard. 9 confirmed runners. EW: 1/5 odds 3 places.
        # JOCKEY BOMBSHELL: Dinoblue -> M.P.Walsh (was Townend); Spindleberry -> Townend (was Mark Walsh)
        # Telepathique -> Tom Cannon; Only By Night -> Keith Donoghue; July Flower -> D.J.O'Keeffe
        # Scratched: The Big Westerner, Jade De Grugy, Shakeyatailfeather
        # Diva Luna gets C+D cheltenham record; July Flower gets C (course only)
        "entries": [
            {"name": "Dinoblue", "trainer": "Willie Mullins", "jockey": "M. P. Walsh",
             "odds": "6/4", "age": 9, "form": "11-1211", "rating": 159,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 1 Mares Chase Jan 2026 (CD)", "days_off": 42},
            {"name": "Panic Attack", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "9/2", "age": 10, "form": "312-111", "rating": 147,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 1 Mares Chase Feb 2026 (CD)", "days_off": 28},
            {"name": "Spindleberry", "trainer": "Willie Mullins", "jockey": "Paul Townend",
             "odds": "5/1", "age": 8, "form": "111-11P", "rating": 153,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Mares Chase Jan 2026 (D)", "days_off": 42},
            {"name": "Only By Night", "trainer": "Gavin Patrick Cromwell", "jockey": "Keith Donoghue",
             "odds": "8/1", "age": 8, "form": "112-215", "rating": 148,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Mares Chase Jan 2026", "days_off": 42},
            {"name": "Diva Luna", "trainer": "Ben Pauling", "jockey": "Ben Jones",
             "odds": "10/1", "age": 7, "form": "1237-11", "rating": 143,
             "cheltenham_record": "CD winner",
             "last_run": "Won Mares Chase Feb 2026 (C+D)", "days_off": 28},
            {"name": "July Flower", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "10/1", "age": 7, "form": "15-5113", "rating": 143,
             "cheltenham_record": "Course winner",
             "last_run": "3rd Grade 1 Mares Chase Jan 2026", "days_off": 42},
            {"name": "Telepathique", "trainer": "Lucy Wadham", "jockey": "Tom Cannon",
             "odds": "8/1", "age": 8, "form": "211-242", "rating": 147,
             "cheltenham_record": None,
             "last_run": "2nd Grade 2 Mares Chase Jan 2026", "days_off": 42},
            {"name": "All The Glory", "trainer": "Jonjo O'Neill", "jockey": "Jonjo O'Neill Jr.",
             "odds": "50/1", "age": 9, "form": "0-26334", "rating": 127,
             "cheltenham_record": None,
             "last_run": "6th Mares Chase Jan 2026 (D)", "days_off": 42},
            {"name": "Piper Park", "trainer": "Tom Lacey", "jockey": "Stan Sheppard",
             "odds": "100/1", "age": 7, "form": "3/6-2", "rating": 130,
             "cheltenham_record": None,
             "last_run": "2nd Mares Chase Jan 2026", "days_off": 42},
        ]
    },
    "day4_race5": {   # Cheltenham Gold Cup Chase  (Grade 1, 3m2f70yds — 11 runners, Fri 13 Mar 16:00)
        # UPDATED 11/03/2026 from official racecard + detailed form. EW: 1/5 odds 3 places.
        # OVERRIDES RACES_2026 Gold Cup entry (EXTRA_RACES takes precedence in build_all_picks)
        # recent_races stored for future engine use — format: date/venue/dist_going/pos/ran
        # DEFENDING CHAMPION: Inothewayurthinkin (won 2025 Gold Cup 3m2f here) but poor form
        # UNBEATEN OVER FENCES: The Jukebox Man (4/4 incl 2x King George)
        "entries": [
            {"name": "Gaelic Warrior", "trainer": "Willie Mullins", "jockey": "Paul Townend",
             "odds": "10/3", "age": 8, "form": "3-1-1-1-3-2", "rating": 170,
             "cheltenham_record": "CD winner",
             "last_run": "2nd Irish Gold Cup Feb 2026", "days_off": 39,
             "recent_races": [
                 {"date": "02 Feb 26", "venue": "Leopardstown", "race": "3m Sft Ch", "pos": 2, "ran": 12},
                 {"date": "26 Dec 25", "venue": "Kempton", "race": "3m Gd Ch (KG)", "pos": 3, "ran": 8},
                 {"date": "23 Nov 25", "venue": "Punchestown", "race": "2m3f Sft Ch (John Durkan)", "pos": 1, "ran": 10},
                 {"date": "26 Apr 25", "venue": "Sandown", "race": "2m6f GF Ch", "pos": 1, "ran": 9},
                 {"date": "03 Apr 25", "venue": "Aintree", "race": "3m210y Gd Ch", "pos": 1, "ran": 7},
             ]},
            {"name": "Jango Baie", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "15/4", "age": 7, "form": "1-2-1-3-1-4", "rating": 168,
             "cheltenham_record": "CD winner",
             "last_run": "4th King George Dec 2025", "days_off": 77,
             "recent_races": [
                 {"date": "26 Dec 25", "venue": "Kempton", "race": "3m Gd Ch (KG)", "pos": 4, "ran": 8},
                 {"date": "22 Nov 25", "venue": "Ascot", "race": "2m5f GS Ch (Grade 2)", "pos": 1, "ran": 5},
                 {"date": "03 Apr 25", "venue": "Aintree", "race": "2m3f Gd Ch", "pos": 3, "ran": 9},
                 {"date": "11 Mar 25", "venue": "Cheltenham", "race": "2m Arkle (Festival)", "pos": 1, "ran": 5},
                 {"date": "01 Feb 25", "venue": "Sandown", "race": "2m4f Hy Ch", "pos": 2, "ran": 4},
                 {"date": "13 Dec 24", "venue": "Cheltenham", "race": "2m4f GS Ch", "pos": 1, "ran": 5},
             ]},
            {"name": "The Jukebox Man", "trainer": "Ben Pauling", "jockey": "Ben Jones",
             "odds": "4/1", "age": 8, "form": "2-2-1-1-1-1", "rating": 173,
             "cheltenham_record": None,
             "last_run": "Won King George Dec 2025 (unbeaten 4/4 over fences)", "days_off": 77,
             "recent_races": [
                 {"date": "26 Dec 25", "venue": "Kempton", "race": "3m Gd Ch (KG)", "pos": 1, "ran": 8},
                 {"date": "22 Nov 25", "venue": "Haydock", "race": "2m5f GS Ch (Grade 2)", "pos": 1, "ran": 5},
                 {"date": "26 Dec 24", "venue": "Kempton", "race": "3m GS Ch (KG)", "pos": 1, "ran": 5},
                 {"date": "29 Nov 24", "venue": "Newbury", "race": "2m3f GS Ch (Kauto Star)", "pos": 1, "ran": 6},
                 {"date": "12 Apr 24", "venue": "Aintree", "race": "3m Sft Hdl", "pos": 2, "ran": 8},
                 {"date": "15 Mar 24", "venue": "Cheltenham", "race": "2m7f Hy Hdl (Albert Bartlett)", "pos": 2, "ran": 13},
             ]},
            {"name": "Haiti Couleurs", "trainer": "Rebecca Curtis", "jockey": "Sean Bowen",
             "odds": "6/1", "age": 9, "form": "1-1-P-1-1-1", "rating": 165,
             "cheltenham_record": "CD winner",
             "last_run": "Won Denman Chase Newbury Feb 2026", "days_off": 34,
             "recent_races": [
                 {"date": "07 Feb 26", "venue": "Newbury", "race": "2m7f Sft Ch (Denman Chase)", "pos": 1, "ran": 4},
                 {"date": "27 Dec 25", "venue": "Chepstow", "race": "3m6f GF Ch (Welsh National)", "pos": 1, "ran": 17},
                 {"date": "22 Nov 25", "venue": "Haydock", "race": "3m1f GS Ch (Betfair Chase)", "pos": "P", "ran": 5},
                 {"date": "21 Apr 25", "venue": "Fairyhouse", "race": "3m5f Irish Grand National", "pos": 1, "ran": 30},
                 {"date": "11 Mar 25", "venue": "Cheltenham", "race": "3m5f GS Ch (NHC)", "pos": 1, "ran": 18},
             ]},
            {"name": "Inothewayurthinkin", "trainer": "Gavin Patrick Cromwell", "jockey": "M. P. Walsh",
             "odds": "13/2", "age": 8, "form": "5-4-1-9-F", "rating": 170,
             "cheltenham_record": "CD winner",
             "last_run": "Fell Irish Gold Cup Feb 2026 (cheekpieces added)", "days_off": 39,
             "recent_races": [
                 {"date": "02 Feb 26", "venue": "Leopardstown", "race": "3m Sft Ch", "pos": "F", "ran": 12},
                 {"date": "28 Dec 25", "venue": "Leopardstown", "race": "3m Gd Ch", "pos": 9, "ran": 11},
                 {"date": "23 Nov 25", "venue": "Punchestown", "race": "2m3f Sft Ch", "pos": 5, "ran": 10},
                 {"date": "14 Mar 25", "venue": "Cheltenham", "race": "3m2f GS Ch (Gold Cup - WON)", "pos": 1, "ran": 9},
                 {"date": "01 Feb 25", "venue": "Leopardstown", "race": "3m GS Ch", "pos": 4, "ran": 10},
             ]},
            {"name": "Spillanes Tower", "trainer": "James Joseph Mangan", "jockey": "Harry Cobden",
             "odds": "8/1", "age": 8, "form": "2-2-5-3-2-1", "rating": 163,
             "cheltenham_record": "Course winner",
             "last_run": "Won Cotswold Chase Cheltenham Jan 2026", "days_off": 49,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Cheltenham", "race": "3m1f Sft Ch (Cotswold)", "pos": 1, "ran": 4},
                 {"date": "31 Dec 25", "venue": "Punchestown", "race": "2m3f GS Hdl", "pos": 3, "ran": 8},
                 {"date": "30 Apr 25", "venue": "Punchestown", "race": "3m Gd Ch", "pos": 2, "ran": 4},
                 {"date": "26 Dec 24", "venue": "Kempton", "race": "3m GS Ch (KG)", "pos": 5, "ran": 11},
                 {"date": "24 Nov 24", "venue": "Punchestown", "race": "2m3f GS Ch", "pos": 2, "ran": 8},
             ]},
            {"name": "Grey Dawning", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "8/1", "age": 9, "form": "2-P-1-2-1-3", "rating": 167,
             "cheltenham_record": "CD winner",
             "last_run": "3rd Cotswold Chase Cheltenham Jan 2026", "days_off": 49,
             "recent_races": [
                 {"date": "24 Jan 26", "venue": "Cheltenham", "race": "3m1f Sft Ch (Cotswold)", "pos": 3, "ran": 4},
                 {"date": "22 Nov 25", "venue": "Haydock", "race": "3m1f GS Ch (Betfair Chase)", "pos": 1, "ran": 5},
                 {"date": "03 Apr 25", "venue": "Aintree", "race": "3m210y Gd Ch", "pos": 2, "ran": 7},
                 {"date": "26 Dec 24", "venue": "Kempton", "race": "3m GS Ch (KG)", "pos": "P", "ran": 11},
                 {"date": "23 Nov 24", "venue": "Haydock", "race": "3m1f Hy Ch", "pos": 2, "ran": 7},
             ]},
            {"name": "Envoi Allen", "trainer": "Henry de Bromhead", "jockey": "D. J. O'Keeffe",
             "odds": "20/1", "age": 12, "form": "2-4-1-U-3-1", "rating": 166,
             "cheltenham_record": "CD winner",
             "last_run": "Won Down Royal Nov 2025 (age 12 - last won Gold Cup trip 2023)", "days_off": 110,
             "recent_races": [
                 {"date": "01 Nov 25", "venue": "Down Royal", "race": "3m GS Ch", "pos": 1, "ran": 5},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m4f GS Ch (Ryanair)", "pos": 3, "ran": 9},
                 {"date": "26 Dec 24", "venue": "Kempton", "race": "3m GS Ch (KG)", "pos": "U", "ran": 11},
             ]},
            {"name": "Firefox", "trainer": "Gordon Elliott", "jockey": "J. W. Kennedy",
             "odds": "25/1", "age": 8, "form": "3-6-2-1-2-4", "rating": 160,
             "cheltenham_record": None,
             "last_run": "4th Irish Gold Cup Feb 2026", "days_off": 39,
             "recent_races": [
                 {"date": "02 Feb 26", "venue": "Leopardstown", "race": "3m Sft Ch (Irish GC)", "pos": 4, "ran": 12},
                 {"date": "20 Dec 25", "venue": "Ascot", "race": "2m5f GS Ch", "pos": 2, "ran": 3},
                 {"date": "01 Nov 25", "venue": "Down Royal", "race": "2m3f GS Ch", "pos": 1, "ran": 5},
                 {"date": "13 Mar 25", "venue": "Cheltenham", "race": "2m4f GS Ch (Golden Miller)", "pos": 6, "ran": 19},
             ]},
            {"name": "LHomme Presse", "trainer": "Venetia Williams", "jockey": "Charlie Deutsch",
             "odds": "14/1", "age": 11, "form": "3-P-2-2-2-1", "rating": 162,
             "cheltenham_record": "CD winner",
             "last_run": "2nd Denman Chase Newbury Feb 2026 (beaten by Haiti Couleurs)", "days_off": 34,
             "recent_races": [
                 {"date": "07 Feb 26", "venue": "Newbury", "race": "2m7f Sft Ch (Denman Chase)", "pos": 2, "ran": 4},
                 {"date": "24 Jan 26", "venue": "Cheltenham", "race": "3m1f Sft Ch (Cotswold)", "pos": 2, "ran": 4},
                 {"date": "12 Dec 25", "venue": "Cheltenham", "race": "3m2f Gd Ch OR=162", "pos": 2, "ran": 9},
                 {"date": "25 Jan 25", "venue": "Cheltenham", "race": "3m1f Sft Ch (Cotswold)", "pos": 1, "ran": 6},
                 {"date": "26 Dec 24", "venue": "Kempton", "race": "3m GS Ch (KG)", "pos": 3, "ran": 11},
             ]},
            {"name": "Gold Tweet", "trainer": "Gabriel Leenders", "jockey": "Clement Lefebvre",
             "odds": "40/1", "age": 9, "form": "U-2-6-5-2-5", "rating": 155,
             "cheltenham_record": "Course winner",
             "last_run": "5th Fontainebleau Feb 2026 (France)", "days_off": 18,
             "recent_races": [
                 {"date": "21 Feb 26", "venue": "Fontainebleau", "race": "3800m Sft Hdl", "pos": 5, "ran": 9},
                 {"date": "16 Nov 25", "venue": "Auteuil", "race": "5500m Sft Ch", "pos": 2, "ran": 12},
                 {"date": "19 Jan 25", "venue": "Pau", "race": "5300m Hy Ch", "pos": "U", "ran": 12},
             ]},
        ]
    },
    "day4_race6": {   # Princess Royal Challenge Cup Open Hunters' Chase  (3m2f — 27 runners, Fri 13 Mar 16:40)
        # UPDATED 09/03/2026: ORs corrected from official Friday racecard; Barton Snow/Stattler/What A Glance/Solitary Man added
        "entries": [
            {"name": "Barton Snow", "trainer": "J J O'Shea", "jockey": "TBD",
             "odds": "5/1", "age": 8, "form": "1-1-2-1", "rating": 142,
             "cheltenham_record": "CD winner",
             "last_run": "Won Hunter Chase Feb 2026 (CD)", "days_off": 28},
            {"name": "Panda Boy", "trainer": "Martin Brassil", "jockey": "Keith Donoghue",
             "odds": "6/1", "age": 10, "form": "1-1-8-U3", "rating": 142,
             "cheltenham_record": None,
             "last_run": "Won Hunter Chase Feb 2026", "days_off": 28},
            {"name": "Chemical Energy", "trainer": "Gordon Elliott", "jockey": "TBD",
             "odds": "8/1", "age": 10, "form": "1-1-1-14", "rating": 141,
             "cheltenham_record": "CD winner",
             "last_run": "Won Hunter Chase Jan 2026", "days_off": 42},
            {"name": "Its On The Line", "trainer": "Emmet Mullins", "jockey": "TBD",
             "odds": "7/1", "age": 9, "form": "1-1-2-32", "rating": 140,
             "cheltenham_record": "CD winner",
             "last_run": "Won Hunter Chase Jan 2026", "days_off": 42},
            {"name": "Stattler", "trainer": "Faye Bramley", "jockey": "TBD",
             "odds": "10/1", "age": 9, "form": "1-1-3-2", "rating": 137,
             "cheltenham_record": None,
             "last_run": "Won Hunter Chase Jan 2026", "days_off": 42},
            {"name": "What A Glance", "trainer": "Tom Britten", "jockey": "TBD",
             "odds": "12/1", "age": 9, "form": "1-2-1-3", "rating": 137,
             "cheltenham_record": "CD winner",
             "last_run": "3rd Hunter Chase Jan 2026 (CD)", "days_off": 42},
            {"name": "Wonderwall", "trainer": "S Curling", "jockey": "Rob James",
             "odds": "12/1", "age": 10, "form": "1-2-3-43", "rating": 136,
             "cheltenham_record": "Won 2025 Foxhunter Chase (at 28/1!) CD",
             "last_run": "3rd Hunter Chase Feb 2026", "days_off": 28},
            {"name": "Solitary Man", "trainer": "E Bolger", "jockey": "TBD",
             "odds": "14/1", "age": 10, "form": "1-1-4-1", "rating": 136,
             "cheltenham_record": None,
             "last_run": "Won Hunter Chase Jan 2026", "days_off": 42},
            {"name": "Con's Roc", "trainer": "Terence O'Brien", "jockey": "TBD",
             "odds": "14/1", "age": 9, "form": "3-1-1", "rating": 135,
             "cheltenham_record": None,
             "last_run": "Won Hunters Chase Jan 2026", "days_off": 42},
            {"name": "Golden Son", "trainer": "Paul Nicholls", "jockey": "Miss Olive Nicholls",
             "odds": "16/1", "age": 9, "form": "1-3-2-4", "rating": 132,
             "cheltenham_record": None,
             "last_run": "3rd Hunter Chase Feb 2026", "days_off": 28},
            {"name": "Music Drive", "trainer": "Kelly Morgan", "jockey": "TBD",
             "odds": "20/1", "age": 9, "form": "1-1-P-33", "rating": 132,
             "cheltenham_record": None,
             "last_run": "Won Hunter Chase Jan 2026", "days_off": 42},
        ]
    },
    "day4_race7": {   # Martin Pipe Conditional Jockeys' Handicap Hurdle  (2m179yds — 54 runners, Fri 13 Mar 17:20)
        # UPDATED 09/03/2026: Top-OR runners added from official Friday racecard
        # UPDATED 13/03/2026: Sony Bill NOT DECLARED (NR). Kel Histoire is actual MF pick at 4/1 (was 16/1)
        "entries": [
            {"name": "Its Bilbo", "trainer": "Henry De Bromhead", "jockey": "TBD",
             "odds": "8/1", "age": 6, "form": "1-2-1-3", "rating": 141,
             "cheltenham_record": None,
             "last_run": "Won Handicap Hurdle Jan 2026 (dual dec County)", "days_off": 42},
            {"name": "Sony Bill", "trainer": "Willie Mullins", "jockey": "TBD",
             "odds": "8/1", "age": 5, "form": "1-1-2-3", "rating": 141,
             "cheltenham_record": None,
             "last_run": "3rd Grade 3 Handicap Hurdle Jan 2026 (dual dec County)", "days_off": 42},
            {"name": "Nurse Susan", "trainer": "Dan Skelton", "jockey": "Tristan Durrell",
             "odds": "13/1", "age": 7, "form": "1-1-2-1", "rating": 140,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 2 Handicap Hurdle Feb 2026 (CD)", "days_off": 28},
            {"name": "Air Of Entitlement", "trainer": "Henry De Bromhead", "jockey": "TBD",
             "odds": "10/1", "age": 6, "form": "1-2-1-1-2", "rating": 139,
             "cheltenham_record": "CD winner",
             "last_run": "2nd Handicap Hurdle Jan 2026 (CD)", "days_off": 42},
            {"name": "Sa Fureur", "trainer": "Gordon Elliott", "jockey": "TBD",
             "odds": "10/1", "age": 7, "form": "2-1-1-3-2", "rating": 138,
             "cheltenham_record": None,
             "last_run": "Won Handicap Hurdle Feb 2026", "days_off": 28},
            {"name": "Fiercely Proud", "trainer": "Ben Pauling", "jockey": "TBD",
             "odds": "12/1", "age": 6, "form": "1-3-1-2", "rating": 137,
             "cheltenham_record": None,
             "last_run": "3rd Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "East India Express", "trainer": "Nicky Henderson", "jockey": "Freddie Gordon",
             "odds": "12/1", "age": 6, "form": "1-1-2-3", "rating": 137,
             "cheltenham_record": "CD winner",
             "last_run": "Won Handicap Hurdle Feb 2026 (CD)", "days_off": 28},
            {"name": "Roc Dino", "trainer": "Willie Mullins", "jockey": "TBD",
             "odds": "14/1", "age": 5, "form": "2-2-3-27", "rating": 131,
             "cheltenham_record": None,
             "last_run": "2nd Handicap Hurdle Dec 2025", "days_off": 77},
            {"name": "A Pai De Nom", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "16/1", "age": 6, "form": "1-5-3-31", "rating": 130,
             "cheltenham_record": None,
             "last_run": "3rd Handicap Jan 2026", "days_off": 42},
            {"name": "The Passing Wife", "trainer": "Gavin Cromwell", "jockey": "Danny Mullins",
             "odds": "16/1", "age": 7, "form": "5-5-8-21", "rating": 139,
             "cheltenham_record": None,
             "last_run": "Won Conditional Handicap Hurdle Jan 2026", "days_off": 42},
            {"name": "Kel Histoire", "trainer": "Willie Mullins", "jockey": "Mark Walsh",
             "odds": "4/1", "age": 6, "form": "4-3-4-18", "rating": 129,
             "cheltenham_record": None,
             "last_run": "Won Handicap Jan 2026", "days_off": 42},
            {"name": "He Can't Dance", "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
             "odds": "20/1", "age": 6, "form": "1-3-4-22", "rating": 128,
             "cheltenham_record": None,
             "last_run": "2nd Grade 2 Hurdle Jan 2026", "days_off": 42},
            {"name": "Zanndabad", "trainer": "A J Martin", "jockey": "TBD",
             "odds": "20/1", "age": 7, "form": "1-1-2-62", "rating": 128,
             "cheltenham_record": None,
             "last_run": "Won Conditional Handicap Feb 2026", "days_off": 28},
        ]
    },
}


# ────────────────────────────────────────────────────────────────────────────
# SUREBET DYNAMODB — live entries already in SureBetBets
# (Salvator Mundi + Teahupoo — added 28 Feb 2026)
# ────────────────────────────────────────────────────────────────────────────

def get_surebet_db_entries():
    """Fetch Cheltenham picks already logged in SureBetBets DynamoDB."""
    try:
        import boto3
        from boto3.dynamodb.conditions import Attr
        db    = boto3.resource("dynamodb", region_name="eu-west-1")
        table = db.Table("SureBetBets")
        resp  = table.scan(
            FilterExpression=Attr("festival").contains("Cheltenham") |
                             Attr("course").contains("Cheltenham")
        )
        entries = {}
        for item in resp.get("Items", []):
            horse = item.get("horse", "").lower()
            entries[horse] = {
                "surebet_score":  float(item.get("comprehensive_score", 0) or 0),
                "confidence":     item.get("confidence", ""),
                "selection_reasons": item.get("selection_reasons", []),
                "race_name":      item.get("race_name", ""),
                "trainer":        item.get("trainer", ""),
                "jockey":         item.get("jockey", ""),
            }
        return entries
    except Exception as e:
        print(f"  [WARN] Could not read SureBetBets: {e}")
        return {}


# ────────────────────────────────────────────────────────────────────────────
# ── Horses ruled out / unavailable for 2026 festival ─────────────────────────
# Constitution Hill: officially ruled out by Nicky Henderson (25 Feb 2026)
RULED_OUT = {
    "constitution hill",   # ruled out 25 Feb 2026 – Nicky Henderson moving to flat
    "galopin des champs",  # ruled out 07 Mar 2026 – late setback, Willie Mullins confirmed
}

# ────────────────────────────────────────────────────────────────────────────
# CORE SCORING + PICK SELECTION
# ────────────────────────────────────────────────────────────────────────────

def score_field(entries, surebet_db, race_name=""):
    """
    Score every horse in a race field using score_horse_2026().
    Augments score by +10 if horse is already confirmed in SureBetBets.
    Returns list of dicts sorted highest score first.
    Pass race_name so race-specific bonuses (same-race winner, Grade 1 etc.) fire correctly.
    """
    results = []
    for horse in entries:
        # Skip any horse officially ruled out of the 2026 festival
        if horse["name"].lower() in RULED_OUT:
            continue
        score, tips, warnings, value_r = score_horse_2026(horse, race_name)
        name_lower = horse["name"].lower()
        db_bonus   = 0
        db_note    = None
        if name_lower in surebet_db:
            db_bonus = 10
            db_note  = f"SureBet DB confirmed (score {surebet_db[name_lower]['surebet_score']:.0f}): +{db_bonus}pts"
            tips     = tips + [db_note]
            score   += db_bonus
        has_festival_win = (
            horse.get("cheltenham_record", "") and
            (
                "won" in (horse.get("cheltenham_record", "") or "").lower() or
                "winner" in (horse.get("cheltenham_record", "") or "").lower() or
                # Racing Post shorthand: 'C' = course winner (standalone token e.g. 'C D', 'C')
                bool(re.search(r'\bC\b', horse.get("cheltenham_record", "") or ""))
            )
        )
        results.append({
            "name":             horse["name"],
            "trainer":          horse.get("trainer", "?"),
            "jockey":           horse.get("jockey", "?"),
            "odds":             horse.get("odds", "sp"),
            "score":            score,
            "tips":             tips,
            "warnings":         warnings[:2],
            "value_r":          value_r,
            "cheltenham_record": horse.get("cheltenham_record") or "First time",
            "has_festival_win": has_festival_win,
            "in_surebet_db":    name_lower in surebet_db,
        })
    # ── Head-to-head bonus (+8pts per direct win over a rival in THIS field) ─────
    # Scans each horse's recent_races[*].race descriptions for "beat X" or "(beat X)"
    # patterns where X = another declared horse in today's field.
    # Example: Oldschool Outlaw recent_race has "2m Hy Hdl (beat Bambino Fever)" at Naas Dec 25
    # → if Bambino Fever is also in the field today → +8pts head-to-head bonus.
    # Capped at +16pts (max 2 recognised H2H wins per horse to avoid runaway stacking).
    _field_names_lower = {r["name"].lower() for r in results}
    for _res in results:
        _he = next((h for h in entries if h["name"] == _res["name"]), None)
        if not _he:
            continue
        _h2h_bonus = 0
        _h2h_tips  = []
        for _rr in _he.get("recent_races", []):
            _desc = _rr.get("race", "").lower()
            # Match "beat NAME", "(beat NAME)", "beating NAME"
            for _beaten_raw in re.findall(
                r'\bbeat(?:ing)?\s+([a-z][a-z\s]{2,34}?)(?=\s+\d|\s+at\b|\s+in\b|\s+\(|,|\)|\.|$)',
                _desc
            ):
                _beaten = _beaten_raw.strip()
                if len(_beaten) < 6:
                    continue
                for _fname in _field_names_lower:
                    if _fname == _res["name"].lower():
                        continue
                    if _fname in _beaten or _beaten in _fname:
                        if _h2h_bonus < 16:
                            _h2h_bonus += 8
                            _h2h_tips.append(
                                f"Head-to-head: beat {_fname.title()} ({_rr.get('date','?')}): +8pts"
                            )
        if _h2h_bonus > 0:
            _res["score"] += _h2h_bonus
            _res["tips"]   = _res.get("tips", []) + _h2h_tips
    # One jockey cannot ride two horses — remove bonus from lower scorers
    deduplicate_jockeys_in_field(results)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def pick_for_entry(scored, strategy):
    """
    Select the competition pick for a given entry strategy.

    Surebet (form):
        → Simply return the highest-scoring horse (best overall form).

    Douglas Stunners (festival_specialist):
        → Prefer horses with a confirmed Cheltenham festival win,
          provided they score within 15 points of the top scorer.
          Falls back to top scorer if no festival winner qualifies.
    """
    if not scored:
        return {"name": "TBC (declarations pending)", "score": 0, "trainer": "", "jockey": "", "reason": "No runners"}

    top = scored[0]

    if strategy == "form":
        return {**top, "reason": "Highest SureBet score (form-first)"}

    # festival_specialist: look for a Cheltenham winner close to the top
    threshold = top["score"] - 15
    festival_candidates = [h for h in scored if h["has_festival_win"] and h["score"] >= threshold]
    if festival_candidates:
        pick = festival_candidates[0]
        return {**pick, "reason": f"Festival specialist — previous Cheltenham winner (score gap {top['score']-pick['score']:.0f})"}
    # fallback
    return {**top, "reason": "Highest SureBet score (no festival winner in field)"}


# ────────────────────────────────────────────────────────────────────────────
# BUILD ALL 28 RACE PICKS
# ────────────────────────────────────────────────────────────────────────────

def build_all_picks(verbose=False):
    surebet_db = get_surebet_db_entries()
    if surebet_db:
        print(f"  [INFO] {len(surebet_db)} horse(s) found in SureBet DynamoDB: {', '.join(surebet_db.keys()).title()}")

    # Merge RACES_2026 (via mapping) into a flat race → entries dict
    all_race_data = {}
    for r2026_name, entries_data in RACES_2026.items():
        fkey = RACES_2026_MAP.get(r2026_name)
        if fkey:
            all_race_data[fkey] = entries_data["entries"]

    # Add the extra 20 races
    for fkey, data in EXTRA_RACES.items():
        all_race_data[fkey] = data["entries"]

    picks = {}
    for day_num in [1, 2, 3, 4]:
        for race_key, race_info in sorted(FESTIVAL_RACES.items(), key=lambda x: (x[1]["day"], x[1]["time"])):
            if race_info["day"] != day_num:
                continue
            base_entries = all_race_data.get(race_key, [])
            entries = extend_race_entries(race_key, base_entries)
            if not entries:
                picks[race_key] = {
                    "race_key":   race_key,
                    "race_name":  race_info["name"],
                    "day":        day_num,
                    "time":       race_info["time"],
                    "grade":      race_info["grade"],
                    "surebet":    {"name": "TBC", "score": 0, "trainer": "", "jockey": "", "reason": "No runners loaded yet"},
                    "douglas":    {"name": "TBC", "score": 0, "trainer": "", "jockey": "", "reason": "No runners loaded yet"},
                    "scored":     [],
                }
                continue

            scored = score_field(entries, surebet_db, race_name=race_info["name"])
            sb_pick = pick_for_entry(scored, "form")
            ds_pick = pick_for_entry(scored, "festival_specialist")

            picks[race_key] = {
                "race_key":  race_key,
                "race_name": race_info["name"],
                "day":       day_num,
                "time":      race_info["time"],
                "grade":     race_info["grade"],
                "surebet":   sb_pick,
                "douglas":   ds_pick,
                "scored":    scored if verbose else scored[:3],
            }

    return picks


# ────────────────────────────────────────────────────────────────────────────
# DISPLAY
# ────────────────────────────────────────────────────────────────────────────

DAY_NAMES = {1: "Champion Day", 2: "Ladies Day", 3: "St Patrick's Thursday", 4: "Gold Cup Day"}
DAY_DATES = {1: "2026-03-10", 2: "2026-03-11", 3: "2026-03-12", 4: "2026-03-13"}


def print_picks_table(picks):
    print(f"\n{'='*100}")
    print(f"  BARRY'S CHELTENHAM 2026 — SUREBET-POWERED PICKS")
    print(f"  Source: cheltenham_deep_analysis_2026.py × SureBetBets DynamoDB")
    print(f"  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"{'='*100}")
    print(f"  POINTS: 1st=10  2nd=5  3rd=3  |  Odds are IRRELEVANT — best horse wins")
    print(f"{'='*100}")

    total_diff = 0
    for day_num in [1, 2, 3, 4]:
        day_picks = {k: v for k, v in picks.items() if v["day"] == day_num}
        print(f"\n  DAY {day_num} — {DAY_NAMES[day_num].upper()}  ({DAY_DATES[day_num]})")
        print(f"  {'-'*96}")
        print(f"  {'TIME':<6} {'RACE':<38} {'GRADE':<12} {'SUREBET (FORM)':<25} {'DOUGLAS STUNNERS':<25} {'SAME?'}")
        print(f"  {'-'*96}")
        for race_key in sorted(day_picks, key=lambda x: day_picks[x]["time"]):
            r     = day_picks[race_key]
            sb    = r["surebet"]["name"][:23]
            ds    = r["douglas"]["name"][:23]
            same  = " <<BANKER" if r["surebet"]["name"] == r["douglas"]["name"] and r["surebet"]["name"] not in ("TBC", "") else ""
            sb_sc = r["surebet"].get("score", 0)
            ds_sc = r["douglas"].get("score", 0)
            total_diff += abs(sb_sc - ds_sc)
            print(f"  {r['time']:<6} {r['race_name'][:37]:<38} {r['grade'][:11]:<12} {sb:<25} {ds:<25}{same}")
        print()

    # Summary section
    print(f"\n  {'='*96}")
    print(f"  HEADLINE PICKS — CHAMPIONSHIP RACES")
    print(f"  {'='*96}")
    key_races = [
        ("day1_race1", "Supreme Novices Hurdle"),
        ("day1_race2", "Arkle Challenge Trophy"),
        ("day1_race5", "Champion Hurdle"),
        ("day2_race5", "Queen Mother Chase"),
        ("day2_race7", "Champion Bumper"),
        ("day3_race3", "Close Brothers Mares Hurdle"),
        ("day3_race4", "Stayers Hurdle"),
        ("day3_race5", "Ryanair Chase"),
        ("day4_race3", "Albert Bartlett"),
        ("day4_race5", "Cheltenham Gold Cup"),
    ]
    print(f"\n  {'RACE':<32} {'SUREBET PICK':<26} {'SCORE':<8} {'DOUGLAS STUNNERS PICK':<26} {'SCORE':<8} {'RATIONALE'}")
    print(f"  {'-'*115}")
    bankers = []
    for race_key, label in key_races:
        if race_key not in picks:
            continue
        r  = picks[race_key]
        sb = r["surebet"]
        ds = r["douglas"]
        if sb["name"] == ds["name"] and sb["name"] not in ("TBC", ""):
            bankers.append((label, sb["name"], sb.get("score", 0)))
        print(f"  {label:<32} {sb['name'][:24]:<26} {sb.get('score',0):<8.0f} {ds['name'][:24]:<26} {ds.get('score',0):<8.0f} {ds.get('reason','')[:30]}")

    if bankers:
        print(f"\n  BANKERS (both entries agree):")
        for label, horse, score in bankers:
            print(f"    **  {horse} in the {label}  (SureBet score: {score:.0f})")

    print(f"\n  [DATA] SureBet scoring engine: trainer/jockey/combo/form/rating/freshness/festival-record")
    print(f"  [DATA] Picks UPDATE pending once Betfair markets open ~4 Mar 2026")
    print()


def _score_tier(score):
    """Return a grade label for a raw SureBet score."""
    if score >= 155: return "A+  ELITE"
    if score >= 140: return "A   ELITE"
    if score >= 120: return "B   EXCELLENT"
    if score >= 100: return "C   STRONG"
    if score >= 80:  return "D   FAIR"
    return               "E   WEAK"


def print_scores_detail(picks):
    """Full per-horse scoring breakdown per race."""
    WIDTH = 104
    for day_num in [1, 2, 3, 4]:
        day_picks = {k: v for k, v in picks.items() if v["day"] == day_num}
        print(f"\n{'='*WIDTH}")
        print(f"  DAY {day_num} - {DAY_NAMES[day_num].upper()}  ({DAY_DATES[day_num]})")
        print(f"{'='*WIDTH}")

        for race_key in sorted(day_picks, key=lambda x: day_picks[x]["time"]):
            r = day_picks[race_key]
            sb_name = r["surebet"]["name"]
            ds_name = r["douglas"]["name"]
            print(f"\n  +{'-'*(WIDTH-3)}+")
            print(f"  |  {r['time']}  {r['race_name']}  [{r['grade']}]")
            print(f"  +{'-'*(WIDTH-3)}+")

            if not r["scored"]:
                print(f"  (no runners loaded)")
                continue

            for rank, h in enumerate(r["scored"], 1):
                is_sb = h["name"] == sb_name
                is_ds = h["name"] == ds_name
                badges = ("  [SUREBET PICK]" if is_sb else "") + (" [DOUGLAS PICK]" if is_ds else "")
                tier   = _score_tier(h["score"])
                vr     = h.get("value_r", 0)
                print()
                print(f"  #{rank}  {h['name']}  --  Score: {h['score']:.0f}  |  Tier: {tier}  |  Value Rating: {vr:.1f}{badges}")
                print(f"       Trainer: {h['trainer']}  |  Jockey: {h['jockey']}")
                print(f"       Festival Record : {h['cheltenham_record'][:60]}")
                for tip in h.get("tips", []):
                    print(f"       + {tip}")
                for warn in h.get("warnings", []):
                    print(f"       ! {warn}")

            print()
            print(f"  Surebet pick   -> {sb_name}  {r['surebet'].get('reason','')}")
            print(f"  Douglas pick   -> {ds_name}  {r['douglas'].get('reason','')}")
            print(f"  {'-'*(WIDTH-3)}")


# ────────────────────────────────────────────────────────────────────────────
# DYNAMODB SAVE
# ────────────────────────────────────────────────────────────────────────────

def save_picks_to_dynamodb(picks):
    """Save generated picks to BarrysCompetition DynamoDB table."""
    import boto3
    db    = boto3.resource("dynamodb", region_name="eu-west-1")
    table = db.Table("BarrysCompetition")
    saved = 0
    for race_key, r in picks.items():
        for entry_name, strategy, pick in [
            ("Surebet",         "form",               r["surebet"]),
            ("Douglas Stunners","festival_specialist", r["douglas"]),
        ]:
            if pick["name"] in ("TBC", ""):
                continue
            item = {
                "entry":         entry_name,
                "race_id":       race_key,
                "race_name":     r["race_name"],
                "day":           r["day"],
                "race_time":     r["time"],
                "grade":         r["grade"],
                "pick":          pick["name"],
                "trainer":       pick.get("trainer", ""),
                "jockey":        pick.get("jockey", ""),
                "surebet_score": Decimal(str(round(pick.get("score", 0), 1))),
                "pick_reason":   pick.get("reason", "")[:200],
                "strategy":      strategy,
                "source":        "surebet_deep_analysis",
                "generated_at":  datetime.now().isoformat(),
                "outcome":       "pending",
                "points":        Decimal("0"),
            }
            table.put_item(Item=item)
            saved += 1
    print(f"  [DB] Saved {saved} picks to BarrysCompetition DynamoDB")
    return saved


# ────────────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Barry's Cheltenham 2026 — SureBet-powered picks")
    parser.add_argument("--save",    action="store_true", help="Save picks to BarrysCompetition DynamoDB")
    parser.add_argument("--detail",  action="store_true", help="Show detailed horse scores per race")
    parser.add_argument("--json",    action="store_true", help="Output JSON only")
    args = parser.parse_args()

    picks = build_all_picks(verbose=args.detail)

    if args.json:
        def dec_serial(o):
            if isinstance(o, Decimal): return float(o)
            raise TypeError
        safe = {k: {k2: v2 for k2, v2 in v.items() if k2 != "scored"} for k, v in picks.items()}
        print(json.dumps(safe, indent=2, default=dec_serial))
    else:
        print_picks_table(picks)
        if args.detail:
            print_scores_detail(picks)
        if args.save:
            save_picks_to_dynamodb(picks)

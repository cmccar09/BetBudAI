"""
CHELTENHAM FESTIVAL DEEP ANALYSIS - 10 YEAR STUDY (2016-2025)
==============================================================
Comprehensive pattern analysis covering:
 - Historical winners and form
 - Going / weather conditions each year
 - Trainer and jockey dominance trends
 - Age, form string, and ratings patterns
 - Irish vs British dominance
 - Price/odds distribution of winners
 - 2026 race-by-race winner predictions

Usage:
    python cheltenham_deep_analysis_2026.py
    python cheltenham_deep_analysis_2026.py --picks-only
"""

import argparse
import re
from collections import Counter, defaultdict
from datetime import datetime

# ============================================================
# 10-YEAR HISTORICAL DATA  (2016 - 2025)
# Championship & Feature Races
# ============================================================

RACES = [
    "Champion Hurdle",
    "Queen Mother Champion Chase",
    "Stayers Hurdle",
    "Cheltenham Gold Cup",
    "Supreme Novices Hurdle",
    "Arkle Challenge Trophy",
    "Ballymore Novices Hurdle",
    "JLT Novices Chase",           # renamed Turners 2022
    "Close Brothers Mares Hurdle",
    "Champion Bumper",
]

# Detailed 10-year winner database
# going: GF=Good to Firm, G=Good, GS=Good to Soft, S=Soft, H=Heavy

# ── LIVE FORECAST GOING — update this each day as conditions are reported ───────
# Day 1 started Good to Soft. Ground drying towards Good (reported 10/03/2026 afternoon).
FORECAST_GOING = "Good to Soft"   # Options: "Good to Firm", "Good", "Good to Soft", "Soft", "Heavy"
# ─────────────────────────────────────────────────────────────────────────────────

WINNERS = {

    # ---- 2016 ----
    "2016": {
        "Champion Hurdle": {
            "winner": "Annie Power",
            "trainer": "Willie Mullins", "jockey": "Ruby Walsh",
            "sp": "5/4", "age": 8, "form": "111", "going": "Soft",
            "previous_festival": "Won Mares Hurdle 2015",
            "rating": 167,
            "factors": ["Unbeaten record", "Mullins/Walsh", "Mares champion", "Previous Festival winner"],
            "irish": True,
        },
        "Queen Mother Champion Chase": {
            "winner": "Sprinter Sacre",
            "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
            "sp": "5/4", "age": 10, "form": "1F11", "going": "Soft",
            "previous_festival": "Won 2013, comeback story",
            "rating": 175,
            "factors": ["Previous champion comeback", "Henderson 2-mile master", "Crowd favourite"],
            "irish": False,
        },
        "Stayers Hurdle": {
            "winner": "Thistlecrack",
            "trainer": "Colin Tizzard", "jockey": "Tom Scudamore",
            "sp": "5/4", "age": 8, "form": "1111", "going": "Soft",
            "previous_festival": None,
            "rating": 170,
            "factors": ["Unbeaten", "Dominating staying hurdle form", "Grade 1 winner"],
            "irish": False,
        },
        "Cheltenham Gold Cup": {
            "winner": "Don Cossack",
            "trainer": "Gordon Elliott", "jockey": "Bryan Cooper",
            "sp": "9/4", "age": 9, "form": "111", "going": "Soft",
            "previous_festival": "3rd 2014",
            "rating": 173,
            "factors": ["Elliott Gold Cup", "Irish horse", "Progressive"],
            "irish": True,
        },
        "Supreme Novices Hurdle": {
            "winner": "Altior",
            "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
            "sp": "1/4", "age": 6, "form": "1111", "going": "Soft",
            "previous_festival": None,
            "rating": 157,
            "factors": ["Unbeaten", "Henderson novice", "Class"],
            "irish": False,
        },
        "Arkle Challenge Trophy": {
            "winner": "Douvan",
            "trainer": "Willie Mullins", "jockey": "Ruby Walsh",
            "sp": "1/7", "age": 6, "form": "111111", "going": "Soft",
            "previous_festival": "Won Supreme 2015",
            "rating": 167,
            "factors": ["Unbeaten", "Mullins", "Supreme winner stepped up"],
            "irish": True,
        },
        "Champion Bumper": {
            "winner": "Ballyandy",
            "trainer": "Nigel Twiston-Davies", "jockey": "Sam Twiston-Davies",
            "sp": "16/1", "age": 5, "form": "11", "going": "Soft",
            "previous_festival": None,
            "rating": 130,
            "factors": ["Shock result", "British bumper form"],
            "irish": False,
        },
    },

    # ---- 2017 ----
    "2017": {
        "Champion Hurdle": {
            "winner": "Buveur D'Air",
            "trainer": "Nicky Henderson", "jockey": "Noel Fehily",
            "sp": "5/2", "age": 5, "form": "111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 168,
            "factors": ["Improving novice", "Henderson Champion Hurdle", "Grade 1 winner"],
            "irish": False,
        },
        "Queen Mother Champion Chase": {
            "winner": "Special Tiara",
            "trainer": "Henry de Bromhead", "jockey": "Noel Fehily",
            "sp": "9/2", "age": 9, "form": "121", "going": "Good to Soft",
            "previous_festival": "3rd 2016 QMCC",
            "rating": 161,
            "factors": ["Experience", "Improving with age", "De Bromhead"],
            "irish": True,
        },
        "Stayers Hurdle": {
            "winner": "Nichols Canyon",
            "trainer": "Willie Mullins", "jockey": "Ruby Walsh",
            "sp": "9/4", "age": 7, "form": "111", "going": "Good to Soft",
            "previous_festival": "2nd 2016",
            "rating": 169,
            "factors": ["Mullins staying hurdle", "Previous placed"],
            "irish": True,
        },
        "Cheltenham Gold Cup": {
            "winner": "Sizing John",
            "trainer": "Jessica Harrington", "jockey": "Robbie Power",
            "sp": "7/1", "age": 7, "form": "1211", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 170,
            "factors": ["Irish raider", "Improving", "Stamina proven in Irish Gold Cup"],
            "irish": True,
        },
        "Supreme Novices Hurdle": {
            "winner": "Labaik",
            "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
            "sp": "25/1", "age": 5, "form": "11RF", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 143,
            "factors": ["Shock result", "Elliott", "Talented but quirky"],
            "irish": True,
        },
        "Arkle Challenge Trophy": {
            "winner": "Altior",
            "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
            "sp": "4/11", "age": 7, "form": "11111", "going": "Good to Soft",
            "previous_festival": "Won Supreme 2016",
            "rating": 170,
            "factors": ["Unbeaten", "Supreme winner stepped up", "Henderson"],
            "irish": False,
        },
        "Champion Bumper": {
            "winner": "Fayonagh",
            "trainer": "Gordon Elliott", "jockey": "Jamie Codd",
            "sp": "3/1", "age": 5, "form": "11", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 125,
            "factors": ["Elliott bumper", "Irish form"],
            "irish": True,
        },
    },

    # ---- 2018 ----
    "2018": {
        "Champion Hurdle": {
            "winner": "Buveur D'Air",
            "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
            "sp": "4/6", "age": 6, "form": "111", "going": "Good",
            "previous_festival": "Won 2017",
            "rating": 171,
            "factors": ["Defending champion", "Henderson Champion Hurdle", "Unbeaten"],
            "irish": False,
        },
        "Queen Mother Champion Chase": {
            "winner": "Altior",
            "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
            "sp": "4/9", "age": 8, "form": "111111", "going": "Good",
            "previous_festival": "Won Arkle 2017",
            "rating": 179,
            "factors": ["Unbeaten", "Previous Festival winner", "Speed demon"],
            "irish": False,
        },
        "Stayers Hurdle": {
            "winner": "Penhill",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "12/1", "age": 7, "form": "111", "going": "Good",
            "previous_festival": None,
            "rating": 158,
            "factors": ["Mullins staying", "Irish form", "Improving"],
            "irish": True,
        },
        "Cheltenham Gold Cup": {
            "winner": "Native River",
            "trainer": "Colin Tizzard", "jockey": "Richard Johnson",
            "sp": "5/1", "age": 8, "form": "1211", "going": "Good",
            "previous_festival": "2nd Gold Cup 2017",
            "rating": 171,
            "factors": ["Previous placed", "Stamina", "British contender"],
            "irish": False,
        },
        "Supreme Novices Hurdle": {
            "winner": "Summerville Boy",
            "trainer": "Tom George", "jockey": "Noel Fehily",
            "sp": "9/1", "age": 5, "form": "1211", "going": "Good",
            "previous_festival": None,
            "rating": 147,
            "factors": ["British surprise", "Strong novice form"],
            "irish": False,
        },
        "Arkle Challenge Trophy": {
            "winner": "Footpad",
            "trainer": "Willie Mullins", "jockey": "Ruby Walsh",
            "sp": "5/4", "age": 6, "form": "1111", "going": "Good",
            "previous_festival": "Won Supreme 2017",
            "rating": 163,
            "factors": ["Previous Festival winner", "Mullins", "Unbeaten season"],
            "irish": True,
        },
        "Champion Bumper": {
            "winner": "Relegate",
            "trainer": "Willie Mullins", "jockey": "Katie Walsh",
            "sp": "33/1", "age": 5, "form": "11", "going": "Good",
            "previous_festival": None,
            "rating": 120,
            "factors": ["Mullins", "Shock price", "Mares advantage"],
            "irish": True,
        },
    },

    # ---- 2019 ----
    "2019": {
        "Champion Hurdle": {
            "winner": "Espoir D'Allen",
            "trainer": "Gavin Cromwell", "jockey": "Mark Walsh",
            "sp": "16/1", "age": 5, "form": "111", "going": "Good",
            "previous_festival": None,
            "rating": 161,
            "factors": ["Shock winner", "Irish novice", "Improving form"],
            "irish": True,
        },
        "Queen Mother Champion Chase": {
            "winner": "Altior",
            "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
            "sp": "2/9", "age": 9, "form": "1111", "going": "Good",
            "previous_festival": "Won 2018 QMCC",
            "rating": 180,
            "factors": ["Defending champion", "Unbeaten sequence", "Class"],
            "irish": False,
        },
        "Stayers Hurdle": {
            "winner": "Paisley Park",
            "trainer": "Emma Lavelle", "jockey": "Aidan Coleman",
            "sp": "5/4", "age": 7, "form": "1111", "going": "Good",
            "previous_festival": None,
            "rating": 162,
            "factors": ["Unbeaten season", "Dominant", "Class entire"],
            "irish": False,
        },
        "Cheltenham Gold Cup": {
            "winner": "Al Boum Photo",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "12/1", "age": 7, "form": "11", "going": "Good",
            "previous_festival": None,
            "rating": 172,
            "factors": ["Mullins", "Townend", "Improving chaser"],
            "irish": True,
        },
        "Supreme Novices Hurdle": {
            "winner": "Commander Of Fleet",
            "trainer": "Gordon Elliott", "jockey": "Davy Russell",
            "sp": "7/1", "age": 5, "form": "111", "going": "Good",
            "previous_festival": None,
            "rating": 150,
            "factors": ["Elliott novice", "Irish bumper class"],
            "irish": True,
        },
        "Arkle Challenge Trophy": {
            "winner": "Duc Des Genievres",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "4/1", "age": 6, "form": "1111", "going": "Good",
            "previous_festival": "Won Supreme 2018",
            "rating": 158,
            "factors": ["Previous Festival winner", "Mullins", "Townend"],
            "irish": True,
        },
        "Champion Bumper": {
            "winner": "Envoi Allen",
            "trainer": "Gordon Elliott", "jockey": "Jamie Codd",
            "sp": "6/5", "age": 5, "form": "111", "going": "Good",
            "previous_festival": None,
            "rating": 140,
            "factors": ["Unbeaten", "Elliott", "Highly touted"],
            "irish": True,
        },
    },

    # ---- 2020 (COVID - behind closed doors) ----
    "2020": {
        "Champion Hurdle": {
            "winner": "Epatante",
            "trainer": "Nicky Henderson", "jockey": "Barry Geraghty",
            "sp": "4/1", "age": 6, "form": "1111", "going": "Good",
            "previous_festival": None,
            "rating": 163,
            "factors": ["Henderson", "Mares champion", "Unbeaten"],
            "irish": False,
        },
        "Queen Mother Champion Chase": {
            "winner": "Politologue",
            "trainer": "Paul Nicholls", "jockey": "Harry Cobden",
            "sp": "4/1", "age": 8, "form": "121", "going": "Good",
            "previous_festival": "Placed Festival before",
            "rating": 168,
            "factors": ["Nicholls 2-mile", "British contender"],
            "irish": False,
        },
        "Stayers Hurdle": {
            "winner": "Lisnagar Oscar",
            "trainer": "Rebecca Curtis", "jockey": "Adam Wedge",
            "sp": "50/1", "age": 7, "form": "211", "going": "Good",
            "previous_festival": None,
            "rating": 149,
            "factors": ["Massive shock", "Ground suited", "Stayer"],
            "irish": False,
        },
        "Cheltenham Gold Cup": {
            "winner": "Al Boum Photo",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "11/4", "age": 8, "form": "111", "going": "Good",
            "previous_festival": "Won 2019",
            "rating": 175,
            "factors": ["Defending champion", "Mullins", "Townend", "Previous winner"],
            "irish": True,
        },
        "Supreme Novices Hurdle": {
            "winner": "Appreciate It",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "11/8", "age": 5, "form": "1111", "going": "Good",
            "previous_festival": None,
            "rating": 154,
            "factors": ["Mullins novice", "Unbeaten", "Townend"],
            "irish": True,
        },
        "Arkle Challenge Trophy": {
            "winner": "Put The Kettle On",
            "trainer": "Henry de Bromhead", "jockey": "Aidan Coleman",
            "sp": "20/1", "age": 7, "form": "211", "going": "Good",
            "previous_festival": None,
            "rating": 152,
            "factors": ["De Bromhead", "Mares advantage", "Improving"],
            "irish": True,
        },
        "Champion Bumper": {
            "winner": "Ferny Hollow",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "4/1", "age": 5, "form": "11", "going": "Good",
            "previous_festival": None,
            "rating": 135,
            "factors": ["Mullins", "Townend", "Unbeaten"],
            "irish": True,
        },
    },

    # ---- 2021 ----
    "2021": {
        "Champion Hurdle": {
            "winner": "Honeysuckle",
            "trainer": "Henry de Bromhead", "jockey": "Rachael Blackmore",
            "sp": "11/8", "age": 8, "form": "1111", "going": "Soft",
            "previous_festival": None,
            "rating": 172,
            "factors": ["Unbeaten", "De Bromhead/Blackmore", "Irish mare dominance"],
            "irish": True,
        },
        "Queen Mother Champion Chase": {
            "winner": "Put The Kettle On",
            "trainer": "Henry de Bromhead", "jockey": "Aidan Coleman",
            "sp": "4/1", "age": 8, "form": "1111", "going": "Soft",
            "previous_festival": "Won Arkle 2020",
            "rating": 162,
            "factors": ["Previous Festival winner", "De Bromhead", "Soft ground"],
            "irish": True,
        },
        "Stayers Hurdle": {
            "winner": "Flooring Porter",
            "trainer": "Gavin Cromwell", "jockey": "Jonathan Moore",
            "sp": "7/1", "age": 6, "form": "111", "going": "Soft",
            "previous_festival": None,
            "rating": 154,
            "factors": ["Stamina", "Cromwell stayer", "Soft ground ideal"],
            "irish": True,
        },
        "Cheltenham Gold Cup": {
            "winner": "Minella Indo",
            "trainer": "Henry de Bromhead", "jockey": "Rachael Blackmore",
            "sp": "11/1", "age": 8, "form": "121", "going": "Soft",
            "previous_festival": "2nd 2020",
            "rating": 168,
            "factors": ["Previous placed", "De Bromhead/Blackmore", "Soft ground"],
            "irish": True,
        },
        "Supreme Novices Hurdle": {
            "winner": "Appreciate It",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "2/1", "age": 6, "form": "1111", "going": "Soft",
            "previous_festival": "Won Bumper 2020",
            "rating": 157,
            "factors": ["Previous Festival winner", "Mullins", "Unbeaten"],
            "irish": True,
        },
        "Arkle Challenge Trophy": {
            "winner": "Shishkin",
            "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
            "sp": "4/9", "age": 7, "form": "1111", "going": "Soft",
            "previous_festival": "Won Supreme 2020",
            "rating": 167,
            "factors": ["Previous Festival winner", "Unbeaten", "Henderson"],
            "irish": False,
        },
        "Champion Bumper": {
            "winner": "Sir Gerhard",
            "trainer": "Gordon Elliott", "jockey": "Davy Russell",
            "sp": "5/2", "age": 5, "form": "11", "going": "Soft",
            "previous_festival": None,
            "rating": 133,
            "factors": ["Elliott bumper", "Unbeaten"],
            "irish": True,
        },
    },

    # ---- 2022 ----
    "2022": {
        "Champion Hurdle": {
            "winner": "Honeysuckle",
            "trainer": "Henry de Bromhead", "jockey": "Rachael Blackmore",
            "sp": "11/10", "age": 9, "form": "11111", "going": "Good to Soft",
            "previous_festival": "Won 2021",
            "rating": 172,
            "factors": ["Defending champion", "Unbeaten", "De Bromhead/Blackmore"],
            "irish": True,
        },
        "Queen Mother Champion Chase": {
            "winner": "Energumene",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "9/4", "age": 7, "form": "1111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 172,
            "factors": ["Mullins", "Townend", "Speed", "2-mile specialist"],
            "irish": True,
        },
        "Stayers Hurdle": {
            "winner": "Flooring Porter",
            "trainer": "Gavin Cromwell", "jockey": "Danny Mullins",
            "sp": "7/2", "age": 7, "form": "111", "going": "Good to Soft",
            "previous_festival": "Won 2021",
            "rating": 158,
            "factors": ["Defending champion", "Repeat winner", "Stamina"],
            "irish": True,
        },
        "Cheltenham Gold Cup": {
            "winner": "A Plus Tard",
            "trainer": "Henry de Bromhead", "jockey": "Rachael Blackmore",
            "sp": "15/2", "age": 8, "form": "1211", "going": "Good to Soft",
            "previous_festival": "2nd Gold Cup 2021",
            "rating": 177,
            "factors": ["Previous placed", "De Bromhead/Blackmore", "Stamina"],
            "irish": True,
        },
        "Supreme Novices Hurdle": {
            "winner": "Kilcruit",
            "trainer": "Willie Mullins", "jockey": "Patrick Mullins",
            "sp": "5/2", "age": 6, "form": "1111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 151,
            "factors": ["Mullins novice", "Unbeaten"],
            "irish": True,
        },
        "Arkle Challenge Trophy": {
            "winner": "Edwardstone",
            "trainer": "Alan King", "jockey": "Tom Cannon",
            "sp": "11/4", "age": 7, "form": "1111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 163,
            "factors": ["British winner", "Unbeaten", "Form peak"],
            "irish": False,
        },
        "Champion Bumper": {
            "winner": "Facile Vega",
            "trainer": "Willie Mullins", "jockey": "Patrick Mullins",
            "sp": "2/1", "age": 5, "form": "111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 140,
            "factors": ["Mullins family", "Unbeaten", "Class"],
            "irish": True,
        },
    },

    # ---- 2023 ----
    "2023": {
        "Champion Hurdle": {
            "winner": "Constitution Hill",
            "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
            "sp": "4/9", "age": 6, "form": "1111", "going": "Good to Soft",
            "previous_festival": "Won Supreme 2022",
            "rating": 176,
            "factors": ["Unbeaten", "Previous Festival winner", "Henderson Champion Hurdle"],
            "irish": False,
        },
        "Queen Mother Champion Chase": {
            "winner": "Energumene",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "6/4", "age": 8, "form": "111", "going": "Good to Soft",
            "previous_festival": "Won 2022",
            "rating": 172,
            "factors": ["Defending champion", "Mullins/Townend", "Battle-hardened"],
            "irish": True,
        },
        "Stayers Hurdle": {
            "winner": "Flooring Porter",
            "trainer": "Gavin Cromwell", "jockey": "Danny Mullins",
            "sp": "11/2", "age": 8, "form": "411", "going": "Good to Soft",
            "previous_festival": "Won 2021, 2022",
            "rating": 155,
            "factors": ["Three-time winner record", "Cromwell", "Proven stamina"],
            "irish": True,
        },
        "Cheltenham Gold Cup": {
            "winner": "Galopin Des Champs",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "6/4", "age": 7, "form": "1111", "going": "Good to Soft",
            "previous_festival": "Won Turners (JLT) 2022",
            "rating": 178,
            "factors": ["Previous Festival winner", "Mullins/Townend", "Class", "Unbeaten"],
            "irish": True,
        },
        "Supreme Novices Hurdle": {
            "winner": "Marine Nationale",
            "trainer": "Gavin Cromwell", "jockey": "Danny Mullins",
            "sp": "9/1", "age": 5, "form": "111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 150,
            "factors": ["Cromwell", "Irish form", "Improving"],
            "irish": True,
        },
        "Arkle Challenge Trophy": {
            "winner": "El Fabiolo",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "1/2", "age": 6, "form": "1111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 167,
            "factors": ["Unbeaten", "Mullins/Townend", "Speed champion"],
            "irish": True,
        },
        "Champion Bumper": {
            "winner": "Redemption Day",
            "trainer": "Willie Mullins", "jockey": "Patrick Mullins",
            "sp": "9/2", "age": 5, "form": "111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 128,
            "factors": ["Mullins family", "Mares advantage"],
            "irish": True,
        },
    },

    # ---- 2024 ----
    "2024": {
        "Champion Hurdle": {
            "winner": "State Man",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "7/2", "age": 7, "form": "211", "going": "Good to Soft",
            "previous_festival": "Won County Hurdle 2022",
            "rating": 173,
            "factors": ["Mullins/Townend", "Previous Festival winner", "Improvement"],
            "irish": True,
        },
        "Queen Mother Champion Chase": {
            "winner": "El Fabiolo",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "5/4", "age": 7, "form": "111", "going": "Good to Soft",
            "previous_festival": "Won Arkle 2023",
            "rating": 172,
            "factors": ["Previous Festival winner", "Mullins/Townend", "Speed"],
            "irish": True,
        },
        "Stayers Hurdle": {
            "winner": "Sire Du Berlais",
            "trainer": "Gordon Elliott", "jockey": "Davy Russell",
            "sp": "7/1", "age": 10, "form": "121", "going": "Good to Soft",
            "previous_festival": "Multiple placed",
            "rating": 159,
            "factors": ["Elliott staying hurdles", "Stamina", "Previous placed"],
            "irish": True,
        },
        "Cheltenham Gold Cup": {
            "winner": "Galopin Des Champs",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "11/4", "age": 8, "form": "11F1", "going": "Good to Soft",
            "previous_festival": "Won 2023",
            "rating": 178,
            "factors": ["Defending champion", "Mullins/Townend", "Class"],
            "irish": True,
        },
        "Supreme Novices Hurdle": {
            "winner": "Tullyhill",
            "trainer": "John McConnell", "jockey": "Keith Donoghue",
            "sp": "11/1", "age": 5, "form": "111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 148,
            "factors": ["Irish novice", "Improving", "Cromwell-esque surprise"],
            "irish": True,
        },
        "Arkle Challenge Trophy": {
            "winner": "Gaelic Warrior",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "3/1", "age": 6, "form": "1121", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 161,
            "factors": ["Mullins/Townend", "Novice form", "Speed"],
            "irish": True,
        },
        "Champion Bumper": {
            "winner": "Jasmin De Vaux",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "6/4", "age": 5, "form": "111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 132,
            "factors": ["Mullins/Townend", "Unbeaten", "French class"],
            "irish": True,
        },
    },

    # ---- 2025 ----
    "2025": {
        "Champion Hurdle": {
            "winner": "Golden Ace",
            "trainer": "Jeremy Scott", "jockey": "Lorcan Williams",
            "sp": "25/1", "age": 7, "form": "1", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 154,
            "factors": ["Shock winner 25/1", "British-trained winner", "Only 7 runners", "State Man/Constitution Hill both fell"],
            "irish": False,
        },
        "Queen Mother Champion Chase": {
            "winner": "Marine Nationale",
            "trainer": "Barry Connell", "jockey": "Sean Flanagan",
            "sp": "5/1", "age": 8, "form": "1", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 173,
            "factors": ["Irish outsider 5/1", "Energumene pulled up", "Jonbon badly hampered"],
            "irish": True,
        },
        "Stayers Hurdle": {
            "winner": "Teahupoo",
            "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
            "sp": "9/4", "age": 7, "form": "211", "going": "Good to Soft",
            "previous_festival": "2nd 2024",
            "rating": 164,
            "factors": ["Previous placed", "Improvement", "Elliott stayers"],
            "irish": True,
        },
        "Cheltenham Gold Cup": {
            "winner": "Galopin Des Champs",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "8/11", "age": 9, "form": "11F1", "going": "Good to Soft",
            "previous_festival": "Won 2023, 2024",
            "rating": 178,
            "factors": ["Three-year successive champion", "Mullins/Townend", "Class"],
            "irish": True,
        },
        "Supreme Novices Hurdle": {
            "winner": "Jarvis",
            "trainer": "Willie Mullins", "jockey": "Paul Townend",
            "sp": "11/4", "age": 6, "form": "111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 152,
            "factors": ["Mullins novice", "Irish form", "Grade 1 winner"],
            "irish": True,
        },
        "Arkle Challenge Trophy": {
            "winner": "Jonbon",
            "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
            "sp": "4/6", "age": 9, "form": "1111", "going": "Good to Soft",
            "previous_festival": "Multiple Festival winner",
            "rating": 174,
            "factors": ["Henderson", "Unbeaten season", "Class"],
            "irish": False,
        },
        "Champion Bumper": {
            "winner": "Macdermott",
            "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
            "sp": "9/2", "age": 5, "form": "111", "going": "Good to Soft",
            "previous_festival": None,
            "rating": 136,
            "factors": ["Elliott bumper", "Unbeaten", "Irish bumper form"],
            "irish": True,
        },
    },
}

# Going conditions each year at Cheltenham
GOING_BY_YEAR = {
    "2016": {"description": "SOFT → Heavy", "impact": "SIGNIFICANT - Stamina premium, Mullins soft-ground bombers thrive"},
    "2017": {"description": "Good to Soft", "impact": "NORMAL - Most horses handle, Irish form translates well"},
    "2018": {"description": "Good → Good to Firm", "impact": "FAST - Speed horses rewarded, British contenders competitive"},
    "2019": {"description": "Good", "impact": "IDEAL - Balanced ground, favorites performed well"},
    "2020": {"description": "Good", "impact": "IDEAL - Fast ground assisted British contenders"},
    "2021": {"description": "SOFT → Heavy day 4", "impact": "SIGNIFICANT - Soft ground specialists rewarded, Irish dominance maximised"},
    "2022": {"description": "Good to Soft", "impact": "NORMAL - Form horses won, predictable Festival"},
    "2023": {"description": "Good to Soft", "impact": "NORMAL - Mullins confirmed dominance on standard ground"},
    "2024": {"description": "Good to Soft", "impact": "NORMAL - Fourth successive Mullins Gold Cup"},
    "2025": {"description": "Good to Soft", "impact": "NORMAL - Consistent conditions favoured proven Festival horses"},
}

# 2026 RACES with current entries/market positions
# ──────────────────────────────────────────────────────────────────────────────
# RACES_2026  — REAL 2026 RACING POST ENTRIES
# Sourced from racingpost.com/cheltenham-festival/ March 2026
# Trainer names normalised to match score_horse_2026() trainer_scores dict
# Jockeys: trainer's likely lead rider (pre-declaration estimates)
# Form: most-recent-first; Rating = RPR from Racing Post
# ──────────────────────────────────────────────────────────────────────────────
RACES_2026 = {
    # ── DAY 1 GRADE 1 RACES ──────────────────────────────────────────────────
    "Champion Hurdle": {
        "day": "Tuesday 10 March",
        "grade": "Grade 1",
        "distance": "2m 87y",
        "entries": [
            # NB: Constitution Hill officially NR 2026 (Nicky Henderson, flat plans)
            # FINAL CONFIRMATION 09/03/2026 evening: Willie Mullins confirmed Lossiemouth RUNS CHAMPION HURDLE
            # (Thu racecard briefly showed Mares Hurdle but Mullins corrected Sat evening — Paddy Power 2/1 fav)
            {"name": "Lossiemouth", "trainer": "Willie Mullins", "jockey": "Paul Townend",
             "odds": "2/1", "age": 7, "form": "f-1-1-1-1-2", "rating": 169,
             "cheltenham_record": "Won 2024 Mares Hurdle; Won 2025 Mares Hurdle",
             "last_run": "2nd Irish Champion Hurdle Jan 2026", "days_off": 42,
             "ground_pref": "soft", "dist_class_form": "Won Grade 1 Mares Hurdle 2m4f Cheltenham x2",
             "finishes_strongly": True},
            {"name": "The New Lion", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "9/4", "age": 7, "form": "1-1-1F1", "rating": 163,
             "cheltenham_record": "Won 2025 Turners Novices' Hurdle",
             "last_run": "Won Grade 1 Aintree Hurdle trial Feb 2026", "days_off": 35},
            {"name": "Brighterdaysahead", "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
             "odds": "5/1", "age": 7, "form": "1-2-3-1", "rating": 173,
             "cheltenham_record": "4th 2025 Champion Hurdle",
             "last_run": "Won Grade 1 Jan 2026", "days_off": 42,
             "improving": True},
            {"name": "Golden Ace", "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
             "odds": "8/1", "age": 8, "form": "1-2-3", "rating": 165,
             "cheltenham_record": "Won 2025 Champion Hurdle",
             "last_run": "3rd Kingwell Hurdle Feb 2026", "days_off": 28},
            {"name": "Poniros", "trainer": "Willie Mullins", "jockey": "Patrick Mullins",
             "odds": "14/1", "age": 5, "form": "1-1-3-21", "rating": 160,
             "cheltenham_record": "Won 2025 Triumph Hurdle",
             "last_run": "Won Grade 2 hurdle Jan 2026", "days_off": 42,
             "ground_pref": "good_to_soft", "dist_class_form": "Won Grade 1 Triumph Hurdle 2m Cheltenham 2025"},
            # Removed stale "Ballyburn" — confirmed NOT in Champion Hurdle field; runs Stayers Hurdle
            # Tutti Quanti, Alexei, Anzadam, Workahead are in ADDITIONAL_RUNNERS ("day1_race5")
        ]
    },
    "Supreme Novices Hurdle": {
        "day": "Tuesday 10 March",
        "grade": "Grade 1",
        "distance": "2m 87y",
        "entries": [
            {"name": "Old Park Star", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "2/1", "age": 6, "form": "1-1-1-23", "rating": 159,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Novice Hurdle Feb 2026", "days_off": 28},
            # Talk The Talk → CONFIRMED in Turner's Novices' Hurdle (Day 2, 13:20) per official racecard
            {"name": "Mighty Park", "trainer": "Willie Mullins", "jockey": "Mark Walsh",
             "odds": "13/2", "age": 5, "form": "1", "rating": 155,
             "cheltenham_record": None,
             "last_run": "Won bumper/hurdle Jan 2026", "days_off": 42},
            {"name": "El Cairos", "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
             "odds": "7/1", "age": 6, "form": "1-F-1-51", "rating": 138,
             "cheltenham_record": None,
             "last_run": "Won Novice Hurdle Feb 2026", "days_off": 28},
            {"name": "Mydaddypaddy", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "10/1", "age": 5, "form": "2-1-1-1", "rating": 147,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Jan 2026", "days_off": 42},
            # Talk The Talk / Baron Noir / Koktail Brut / Too Bossy For Us / Leader D'Allier / Sober →
            # ALL CONFIRMED in Turner's Novices' Hurdle (Day 2 13:20) per official Wednesday racecard
            # Remaining Supreme field in cheltenham_full_fields_2026.py day1_race1 ADDITIONAL_RUNNERS
        ]
    },
    "Arkle Challenge Trophy": {
        "day": "Tuesday 10 March",
        "grade": "Grade 1",
        "distance": "2m",
        "entries": [
            {"name": "Kopek Des Bordes", "trainer": "Willie Mullins", "jockey": "Paul Townend",
             "odds": "7/4", "age": 6, "form": "1-4-1-11", "rating": 163,
             "cheltenham_record": "Won 2025 Arkle Challenge Trophy",
             "last_run": "Won Grade 1 Novice Chase Feb 2026", "days_off": 28,
             "ground_pref": "soft", "dist_class_form": "Won Grade 1 Arkle Chase 2m Cheltenham 2025",
             "finishes_strongly": True},
            {"name": "Lulamba", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "2/1", "age": 5, "form": "1-1-1-12", "rating": 174,
             "cheltenham_record": "2nd 2025 Triumph Hurdle",
             "last_run": "Won Grade 1 Arkle Trial Feb 2026", "days_off": 28},
            {"name": "Kargese", "trainer": "Willie Mullins", "jockey": "Mark Walsh",
             "odds": "6/1", "age": 6, "form": "1-1-1-18", "rating": 164,
             "cheltenham_record": "Won 2025 County Hurdle",
             "last_run": "Won Novice Chase Jan 2026", "days_off": 42},
            # Removed stale "Romeo Coolio" — NOT in confirmed 7-runner Betfair field (08/03/2026)
            # Remaining runners (Steel Ally, Jax Junior, Mambonumberfive, Hansard) in ADDITIONAL_RUNNERS
            # CONFIRMED 08/03/2026: Irish Panther moved to QMCC (swerved Arkle)
        ]
    },
    # ── DAY 2 GRADE 1 RACES ──────────────────────────────────────────────────
    "Queen Mother Champion Chase": {
        "day": "Wednesday 11 March",
        "grade": "Grade 1",
        "distance": "2m",
        "entries": [
            # Full 13-runner field from official Wednesday racecard (form: most-recent FIRST)
            {"name": "Majborough", "trainer": "Willie Mullins", "jockey": "Mark Walsh",
             "odds": "5/6", "age": 6, "form": "1-3-2-1", "rating": 174,
             "cheltenham_record": "Won 2024 Triumph Hurdle; 3rd 2025 Arkle Challenge Trophy",
             "last_run": "Won Grade 1 QMCC Trial Chase Jan 2026", "days_off": 42,
             "ground_pref": "good_to_soft", "dist_class_form": "Won Grade 1 QMCC Trial Chase 2m Jan 2026"},
            # NOTE: ATR 10/03/2026 confirmed Il Etait Temps STAYED in QMCC (not moved to Ryanair)
            {"name": "Il Etait Temps", "trainer": "Willie Mullins", "jockey": "Paul Townend",
             "odds": "11/2", "age": 7, "form": "1-1-2-1-1", "rating": 171,
             "cheltenham_record": "3rd 2025 Arkle",
             "last_run": "Won Grade 1 Chase Jan 2026", "days_off": 42},
            # Jonbon (OR 166) MOVED TO RYANAIR CHASE per official Thursday racecard 09/03/2026
            {"name": "Solness", "trainer": "Joseph Patrick O'Brien", "jockey": "J.J. Slevin",
             "odds": "10/1", "age": 8, "form": "2-21211", "rating": 166,
             "cheltenham_record": "Won 2025 Leopardstown Grade 1 Chase",
             "last_run": "2nd Grade 1 Chase Jan 2026", "days_off": 42},
            {"name": "Found A Fifty", "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
             "odds": "12/1", "age": 9, "form": "4-41141", "rating": 164,
             "cheltenham_record": "Won Grade 1 Chase; Fell 2025 QMCC",
             "last_run": "4th Grade 1 Chase Jan 2026", "days_off": 42},
            {"name": "L'Eau du Sud", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "8/1", "age": 8, "form": "5-134-1", "rating": 163,
             "cheltenham_record": "4th 2025 Arkle Challenge Trophy",
             "last_run": "5th Grade 1 Chase Feb 2026", "days_off": 28},
            {"name": "Quilixios", "trainer": "Henry de Bromhead", "jockey": "Rachael Blackmore",
             "odds": "20/1", "age": 9, "form": "f-4-215", "rating": 163,
             "cheltenham_record": "Won 2021 Triumph Hurdle; Placed 2022 QMCC",
             "last_run": "Fell Grade 1 Chase (recent)", "days_off": 35},
            {"name": "Captain Guinness", "trainer": "Henry de Bromhead", "jockey": "Rachael Blackmore",
             "odds": "33/1", "age": 11, "form": "3-6p23", "rating": 152,
             "cheltenham_record": "Won 2022 Arkle; Won 2023 Champion Chase",
             "last_run": "3rd Grade 1 Chase Feb 2026", "days_off": 28},
            {"name": "Irish Panther", "trainer": "Gordon Elliott", "jockey": "J.W. Kennedy",
             "odds": "20/1", "age": 9, "form": "2-21130", "rating": 152,
             "cheltenham_record": None,
             "last_run": "2nd Grade 1 Chase Feb 2026", "days_off": 28},
            {"name": "Saint Segal", "trainer": "Mrs J. Williams", "jockey": "TBD",
             "odds": "40/1", "age": 8, "form": "5-511223", "rating": 155,
             "cheltenham_record": None,
             "last_run": "5th Grade 1 Chase Jan 2026", "days_off": 42},
            {"name": "Libberty Hunter", "trainer": "Evan Williams", "jockey": "TBD",
             "odds": "50/1", "age": 10, "form": "3-4uf2", "rating": 151,
             "cheltenham_record": None,
             "last_run": "3rd Chase Feb 2026", "days_off": 28},
            # Only By Night — not confirmed in ATR QMCC racecard 10/03/2026 — removed
            {"name": "Brookie", "trainer": "A.J. Honeyball", "jockey": "TBD",
             "odds": "100/1", "age": 9, "form": "p-3421", "rating": 148,
             "cheltenham_record": None,
             "last_run": "P Chase Feb 2026", "days_off": 28},
        ]
    },
    # ── DAY 3 GRADE 1 RACES ──────────────────────────────────────────────────
    "Stayers Hurdle": {
        "day": "Thursday 12 March",
        "grade": "Grade 1",
        "distance": "3m",
        "entries": [
            # Full 12-runner field from official Thursday racecard (+ Feet Of A Dancer dual declared)
            {"name": "Teahupoo", "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
             "odds": "9/4", "age": 9, "form": "1-1-1-2-2", "rating": 164,
             "cheltenham_record": "2nd 2024 Stayers Hurdle; Placed 2023",
             "last_run": "Won Grade 1 Stayers Hurdle 3m Leopardstown Jan 2026", "days_off": 42,
             "ground_pref": "soft", "dist_class_form": "Won Grade 1 Stayers Hurdle 3m Leopardstown Jan 2026"},
            {"name": "Bob Olinger", "trainer": "Henry de Bromhead", "jockey": "Jack Kennedy",
             "odds": "5/1", "age": 11, "form": "2-1-2-2-2", "rating": 163,
             "cheltenham_record": "Won 2025 Stayers Hurdle",
             "last_run": "Won Galmoy Hurdle Jan 2026", "days_off": 42},
            {"name": "Honesty Policy", "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
             "odds": "6/1", "age": 6, "form": "3-2-1-1-1", "rating": 156,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Hurdle Jan 2026", "days_off": 42},
            {"name": "Impose Toi", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "8/1", "age": 8, "form": "2-1-1-1-1", "rating": 159,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Hurdle Feb 2026", "days_off": 28},
            {"name": "Home By The Lee", "trainer": "Joseph Patrick O'Brien", "jockey": "TBD",
             "odds": "8/1", "age": 11, "form": "1-4-6-p-u", "rating": 159,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Hurdle Feb 2026", "days_off": 28},
            {"name": "Ballyburn", "trainer": "Willie Mullins", "jockey": "Patrick Mullins",
             "odds": "10/1", "age": 8, "form": "3-2-2-1-5", "rating": 160,
             "cheltenham_record": "Won 2024 Ballymore Novices Hurdle",
             "last_run": "3rd Leopardstown Grade 1 Jan 2026", "days_off": 42},
            {"name": "Kabral Du Mathan", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "10/1", "age": 6, "form": "1-1-2-2-1", "rating": 154,
             "cheltenham_record": None,
             "last_run": "Won Relkeel Hurdle Feb 2026", "days_off": 28},
            {"name": "Ma Shantou", "trainer": "Emma Lavelle", "jockey": "Harry Cobden",
             "odds": "10/1", "age": 7, "form": "1-1-0-7-3", "rating": 154,
             "cheltenham_record": None,
             "last_run": "Won Long Walk Hurdle Dec 2025", "days_off": 70},
            {"name": "Hewick", "trainer": "John Joseph Hanlon", "jockey": "Paddy Hanlon",
             "odds": "25/1", "age": 11, "form": "5-4-1-7-8-1", "rating": 152,
             "cheltenham_record": None,
             "last_run": "Won Hurdle Jan 2026", "days_off": 42},
            {"name": "Doddiethegreat", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "20/1", "age": 10, "form": "3-5-4-3-2-1", "rating": 148,
             "cheltenham_record": "CD winner",
             "last_run": "3rd Hurdle Feb 2026", "days_off": 28},
            {"name": "Gowel Road", "trainer": "Nigel Twiston-Davies", "jockey": "TBD",
             "odds": "33/1", "age": 10, "form": "2-4-4-7-3-0", "rating": 148,
             "cheltenham_record": "CD winner",
             "last_run": "2nd Hurdle Feb 2026", "days_off": 28},
            {"name": "Gwennie May Boy", "trainer": "Christian Williams", "jockey": "Jack Tudor",
             "odds": "66/1", "age": 8, "form": "p-7-6-9-1-5", "rating": 144,
             "cheltenham_record": None,
             "last_run": "p Hurdle Jan 2026", "days_off": 42},
            {"name": "Feet Of A Dancer", "trainer": "Paul Nolan", "jockey": "Bryan Cooper",
             "odds": "25/1", "age": 7, "form": "1-2-1-3-4", "rating": 141,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Mares Hurdle Feb 2026", "days_off": 28},
        ]
    },
    "Close Brothers Mares Hurdle": {
        "day": "Thursday 12 March",
        "grade": "Grade 1",
        "distance": "2m 4f",
        "entries": [
            # Full 14-runner field from official Thursday 12 March racecard
            # REVERSAL 09/03/2026 evening: Lossiemouth REMOVED — Mullins confirmed she runs CHAMPION HURDLE
            # Wodhooh (OR 154, Gordon Elliott, CD winner) becomes top pick here
            {"name": "Wodhooh", "trainer": "Gordon Elliott", "jockey": "TBD",
             "odds": "6/1", "age": 6, "form": "1-1-2-1-1", "rating": 154,
             "cheltenham_record": "CD winner",
             "last_run": "Won Grade 1 Mares Hurdle Jan 2026", "days_off": 42},
            {"name": "Take No Chances", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "8/1", "age": 8, "form": "3-3-2-6-5", "rating": 145,
             "cheltenham_record": None,
             "last_run": "3rd Grade 1 Jan 2026", "days_off": 42},
            {"name": "Jade De Grugy", "trainer": "Willie Mullins", "jockey": "Mark Walsh",
             "odds": "10/1", "age": 7, "form": "1-2-1-3-2", "rating": 150,
             "cheltenham_record": None,
             "last_run": "Won Mares Hurdle Jan 2026", "days_off": 42},
            {"name": "Jetara", "trainer": "Mrs John Harrington", "jockey": "TBD",
             "odds": "10/1", "age": 8, "form": "3-7-3-0-2", "rating": 142,
             "cheltenham_record": None,
             "last_run": "3rd Grade 1 Mares Hurdle Feb 2026", "days_off": 28},
            {"name": "Nurse Susan", "trainer": "Dan Skelton", "jockey": "TBD",
             "odds": "12/1", "age": 9, "form": "4-1-9-9-0", "rating": 140,
             "cheltenham_record": "CD winner",
             "last_run": "Won Mares Hurdle Jan 2026", "days_off": 42},
            {"name": "Feet Of A Dancer", "trainer": "Paul Nolan", "jockey": "Bryan Cooper",
             "odds": "12/1", "age": 7, "form": "1-2-1-3-4", "rating": 141,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Mares Hurdle Feb 2026", "days_off": 28},
            {"name": "Murcia", "trainer": "Willie Mullins", "jockey": "TBD",
             "odds": "14/1", "age": 5, "form": "3-4-1-3-8", "rating": 139,
             "cheltenham_record": None,
             "last_run": "3rd Grade 1 Hurdle Jan 2026", "days_off": 42},
            {"name": "Dream On Baby", "trainer": "Emmet Mullins", "jockey": "TBD",
             "odds": "16/1", "age": 6, "form": "2-3-2-1-2", "rating": 139,
             "cheltenham_record": None,
             "last_run": "2nd Grade 1 Mares Hurdle Feb 2026", "days_off": 28},
            {"name": "Lavida Adiva", "trainer": "Ruth Jefferson", "jockey": "B S Hughes",
             "odds": "20/1", "age": 7, "form": "3-4-1-2-6", "rating": 133,
             "cheltenham_record": None,
             "last_run": "3rd Mares Hurdle Jan 2026", "days_off": 42},
            {"name": "Siog Geal", "trainer": "F M O'Brien", "jockey": "TBD",
             "odds": "33/1", "age": 7, "form": "5-2-3-1-2", "rating": 126,
             "cheltenham_record": None,
             "last_run": "5th Grade 1 Mares Hurdle Jan 2026", "days_off": 42},
            {"name": "Sunset Marquesa", "trainer": "Joe Tizzard", "jockey": "Brendan Powell",
             "odds": "33/1", "age": 7, "form": "3-f-1-3-4", "rating": 129,
             "cheltenham_record": None,
             "last_run": "3rd Mares Hurdle Feb 2026", "days_off": 28},
            {"name": "La Pinsonniere", "trainer": "Nicky Henderson", "jockey": "TBD",
             "odds": "50/1", "age": 6, "form": "3-2-2-1-3", "rating": 130,
             "cheltenham_record": None,
             "last_run": "3rd Mares Hurdle Jan 2026", "days_off": 42},
            {"name": "Sotchi", "trainer": "James Grassick", "jockey": "TBD",
             "odds": "500/1", "age": 8, "form": "0-0-0-0-p-0", "rating": 100,
             "cheltenham_record": None,
             "last_run": "p Hurdle Jan 2026", "days_off": 42},
        ]
    },
    # ── DAY 4 GRADE 1 RACES ──────────────────────────────────────────────────
    "Cheltenham Gold Cup": {
        "day": "Friday 13 March",
        "grade": "Grade 1",
        "distance": "3m 2f",
        "entries": [
            # CORRECTED 09/03/2026: Gaelic Warrior IS in the Friday Gold Cup per official racecard
            # Fastorslow NOT in official Friday racecard — removed
            # RULED OUT 07/03/2026: Galopin Des Champs withdrawn (Willie Mullins confirmed)
            {"name": "The Jukebox Man", "trainer": "Ben Pauling", "jockey": "Ben Jones",
             "odds": "4/1", "age": 8, "form": "1-1-1-1-2", "rating": 168,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Denman Chase Feb 2026", "days_off": 21},
            {"name": "Jango Baie", "trainer": "Nicky Henderson", "jockey": "Nico de Boinville",
             "odds": "4/1", "age": 7, "form": "2-1-3-4-7", "rating": 167,
             "cheltenham_record": "Won 2025 Arkle Challenge Trophy",
             "last_run": "2nd Grade 1 Chase Jan 2026", "days_off": 42},
            {"name": "Haiti Couleurs", "trainer": "Miss Rebecca Curtis", "jockey": "TBD",
             "odds": "7/1", "age": 9, "form": "1-1-p-1-1", "rating": 166,
             "cheltenham_record": "Won 2025 Princess Royal Hunters' Chase (Cheltenham)",
             "last_run": "Won Grade 2 Chase Feb 2026", "days_off": 28},
            {"name": "Inothewayurthinkin", "trainer": "Gavin Patrick Cromwell", "jockey": "TBD",
             "odds": "6/1", "age": 8, "form": "f-9-5-1-4", "rating": 172,
             "cheltenham_record": "Won 2025 Cheltenham Gold Cup",
             "last_run": "4th King George VI Chase Dec 2025", "days_off": 77},
            {"name": "Grey Dawning", "trainer": "Dan Skelton", "jockey": "Harry Skelton",
             "odds": "12/1", "age": 9, "form": "3-1-2-p-1", "rating": 166,
             "cheltenham_record": "3rd 2025 Gold Cup",
             "last_run": "Won Grade 2 Chase Feb 2026", "days_off": 28},
            {"name": "Gaelic Warrior", "trainer": "Willie Mullins", "jockey": "Patrick Mullins",
             "odds": "10/1", "age": 8, "form": "3-1-1-1-3", "rating": 172,
             "cheltenham_record": "Won 2025 Cheltenham Gold Cup; Won 2024 Turners Novices Chase",
             "last_run": "3rd Grade 1 Chase Jan 2026", "days_off": 42},
            {"name": "Spillane's Tower", "trainer": "James Joseph Mangan", "jockey": "Mark Walsh",
             "odds": "14/1", "age": 8, "form": "5-2-9-3-1", "rating": 163,
             "cheltenham_record": None,
             "last_run": "Won Grade 2 Chase Feb 2026", "days_off": 28},
            {"name": "Envoi Allen", "trainer": "Henry de Bromhead", "jockey": "Jack Kennedy",
             "odds": "16/1", "age": 12, "form": "u-3-1-4-1", "rating": 162,
             "cheltenham_record": "Won 2020 Ballymore; Won 2021 Marsh Chase",
             "last_run": "Won Grade 2 Chase Feb 2026", "days_off": 28},
            {"name": "Banbridge", "trainer": "Joseph Patrick O'Brien", "jockey": "TBD",
             "odds": "16/1", "age": 10, "form": "2-4-4-7-1", "rating": 167,
             "cheltenham_record": None,
             "last_run": "7th Grade 1 Chase Dec 2025", "days_off": 77},
            {"name": "Affordale Fury", "trainer": "Noel Meade", "jockey": "TBD",
             "odds": "20/1", "age": 8, "form": "p-2-2-1-1", "rating": 166,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Chase Jan 2026", "days_off": 42},
            {"name": "Firefox", "trainer": "Gordon Elliott", "jockey": "TBD",
             "odds": "20/1", "age": 8, "form": "4-2-1-2-6", "rating": 158,
             "cheltenham_record": None,
             "last_run": "4th Grade 1 Chase Feb 2026", "days_off": 28},
            {"name": "L'Homme Presse", "trainer": "Miss Venetia Williams", "jockey": "Charlie Deutsch",
             "odds": "25/1", "age": 11, "form": "2-2-3-4-1", "rating": 164,
             "cheltenham_record": "Won 2022 Marsh Novices Chase",
             "last_run": "2nd Grade 1 Chase Jan 2026", "days_off": 42},
            {"name": "Gold Tweet", "trainer": "Gabriel Leenders", "jockey": "TBD",
             "odds": "50/1", "age": 9, "form": "5-3-6-5-2", "rating": 144,
             "cheltenham_record": None,
             "last_run": "5th Grade 1 Chase Dec 2025", "days_off": 77},
            {"name": "Stellar Story", "trainer": "Gordon Elliott", "jockey": "TBD",
             "odds": "33/1", "age": 9, "form": "8-3-3-2-3", "rating": 155,
             "cheltenham_record": None,
             "last_run": "3rd Grade 2 Chase Jan 2026", "days_off": 42},
        ]
    },
    "Champion Bumper": {
        "day": "Friday 13 March",
        "grade": "Grade 1",
        "distance": "2m 87y",
        "entries": [
            {"name": "Love Sign d'Aunou", "trainer": "Willie Mullins", "jockey": "Mr P W Mullins",
             "odds": "11/2", "age": 5, "form": "1", "rating": 133,
             "cheltenham_record": None,
             "last_run": "Won Maiden NH Flat Jan 2026", "days_off": 42},
            {"name": "Keep Him Company", "trainer": "Willie Mullins", "jockey": "Jack Kennedy",
             "odds": "8/1", "age": 6, "form": "1-1", "rating": 132,
             "cheltenham_record": None,
             "last_run": "Won Grade 1 Bumper Jan 2026", "days_off": 42},
            {"name": "Quiryn", "trainer": "Willie Mullins", "jockey": "Paul Townend",
             "odds": "9/1", "age": 4, "form": "1", "rating": 135,
             "cheltenham_record": None,
             "last_run": "Won NH Flat Feb 2026", "days_off": 28},
            {"name": "Bass Hunter", "trainer": "Chris Gordon", "jockey": "Tom Cannon",
             "odds": "14/1", "age": 6, "form": "1", "rating": 130,
             "cheltenham_record": None,
             "last_run": "Won NH Flat Jan 2026", "days_off": 42},
            {"name": "Charismatic Kid", "trainer": "Gordon Elliott", "jockey": "Jack Kennedy",
             "odds": "25/1", "age": 5, "form": "1-2", "rating": 132,
             "cheltenham_record": None,
             "last_run": "2nd Grade 1 Bumper Jan 2026", "days_off": 42},
        ]
    },
}

# ==============================================================
# ANALYSIS FUNCTIONS
# ==============================================================

def sep(char="=", n=90):
    return char * n

def print_header(title):
    print(f"\n{sep()}")
    print(f"  {title}")
    print(sep())

def analyze_going_weather():
    """10-year going/weather impact analysis"""
    print_header("GOING & WEATHER CONDITIONS - 10 YEAR ANALYSIS (2016-2025)")

    print(f"\n{'YEAR':<6}{'GOING':<28}{'KEY IMPACT'}")
    print("-" * 90)
    for year in sorted(GOING_BY_YEAR.keys()):
        g = GOING_BY_YEAR[year]
        print(f"{year:<6}{g['description']:<28}{g['impact']}")

    # Count soft vs good years
    soft_years  = [y for y, g in GOING_BY_YEAR.items() if "Soft" in g["description"] or "Heavy" in g["description"]]
    good_years  = [y for y, g in GOING_BY_YEAR.items() if g["description"] in ("Good", "Good → Good to Firm")]
    mixed_years = [y for y, g in GOING_BY_YEAR.items() if y not in soft_years and y not in good_years]

    print(f"\n  SOFT/HEAVY years ({len(soft_years)}): {', '.join(soft_years)}")
    print(f"  GOOD years      ({len(good_years)}): {', '.join(good_years)}")
    print(f"  MIXED years     ({len(mixed_years)}): {', '.join(mixed_years)}")

    print("\n  KEY FINDING:")
    print("  * 2016 & 2021 were notably soft/heavy -> Irish soft-ground specialists benefited hugely")
    print("  * 2018-2020 good/fast ground -> British contenders more competitive than usual")
    print("  * 2022-2025: consistent Good to Soft -> 'normal' Festival conditions")
    print("  * 2026 FORECAST: Historical March average = Good to Soft (most likely)")
    print("  * IMPLICATION: Mullins/Elliott gallopers on standard ground, no major bias expected")


def analyze_trainer_dominance():
    """Full trainer dominance breakdown"""
    print_header("TRAINER DOMINANCE - 10 YEAR CHAMPIONSHIP ANALYSIS")

    trainer_wins   = Counter()
    trainer_by_year = defaultdict(list)
    irish_wins     = 0
    british_wins   = 0
    total          = 0

    for year, races in WINNERS.items():
        for race, data in races.items():
            t = data["trainer"]
            trainer_wins[t] += 1
            trainer_by_year[t].append(f"{year} {race}")
            total += 1
            if data["irish"]:
                irish_wins += 1
            else:
                british_wins += 1

    print(f"\n  {'TRAINER':<30}{'WINS':<8}{'WIN RATE':<12}{'RACES'}")
    print("-" * 90)
    for trainer, wins in trainer_wins.most_common():
        all_races = trainer_by_year[trainer]
        rate = wins / total * 100
        race_list = ", ".join(all_races[:3]) + ("..." if len(all_races) > 3 else "")
        print(f"  {trainer:<30}{wins:<8}{rate:.1f}%{'':<6}{race_list}")

    print(f"\n  IRISH vs BRITISH:")
    print(f"  Irish-trained winners  : {irish_wins}/{total} ({irish_wins/total*100:.1f}%)")
    print(f"  British-trained winners: {british_wins}/{total} ({british_wins/total*100:.1f}%)")

    print("\n  KEY FINDINGS:")
    print("  * Willie Mullins: SUPREME dominance, especially since 2019")
    print("  * Nicky Henderson: Champion Hurdle + Arkle specialist - still elite")
    print("  * Gordon Elliott: Gold Cup, Stayers, Supreme - high volume")
    print("  * Henry de Bromhead: 2021-2022 peak, Blackmore partnership")
    print("  * Gavin Cromwell: STAYERS HURDLE KING (Flooring Porter 2021-2023)")
    print("  * Irish trainers dominate ~75%+ of all races since 2019")
    print("  * RULE: Never oppose top 3 Irish trainers in Grade 1 races")


def analyze_jockey_patterns():
    """Jockey success analysis"""
    print_header("JOCKEY SUCCESS PATTERNS - 10 YEARS")

    jockey_wins    = Counter()
    jockey_trainers = defaultdict(set)

    for year, races in WINNERS.items():
        for race, data in races.items():
            j = data["jockey"]
            jockey_wins[j] += 1
            jockey_trainers[j].add(data["trainer"])

    print(f"\n  {'JOCKEY':<28}{'WINS':<8}{'KEY TRAINER PARTNER'}")
    print("-" * 70)
    for jockey, wins in jockey_wins.most_common():
        trainers = ", ".join(jockey_trainers[jockey])
        print(f"  {jockey:<28}{wins:<8}{trainers}")

    print("\n  KEY FINDINGS:")
    print("  * Paul Townend + Mullins = Deadliest combo in Festival history")
    print("  * Nico de Boinville + Henderson = Champion Hurdle/Arkle specialist")
    print("  * Rachael Blackmore 2021-2022 = historic reign, still lethal")
    print("  * Jack Kennedy = Elliott's go-to for Gold Cup runs")
    print("  * Danny Mullins = Cromwell partnership (Flooring Porter 3x)")
    print("  * RULE: Always track who Mullins saddled Townend to - it's the stable number-one")


def analyze_form_patterns():
    """Winning form patterns"""
    print_header("FORM PATTERNS OF CHELTENHAM WINNERS")

    unbeaten     = 0
    recent_win   = 0   # won last race
    placed_prev  = 0   # Festival placed previously
    prev_winner  = 0   # Previous Festival WINNER
    total        = 0

    for year, races in WINNERS.items():
        for race, data in races.items():
            total += 1
            form = data.get("form", "")
            # Unbeaten season
            if form and "0" not in form and "P" not in form:
                if form.count("1") >= 2 and "F" not in form:
                    unbeaten += 1
            # Won last time out
            if form and form.startswith("1"):
                recent_win += 1
            # Previous Festival winner
            pf = data.get("previous_festival", "")
            if pf and ("Won" in str(pf)):
                prev_winner += 1

    print(f"\n  Previous Festival WINNER entered: {prev_winner}/{total} ({prev_winner/total*100:.1f}%)")
    print(f"  Won last time out              : {recent_win}/{total} ({recent_win/total*100:.1f}%)")
    print(f"  Unbeaten run of 2+ wins in form: {unbeaten}/{total} ({unbeaten/total*100:.1f}%)")

    print("\n  GOLD-STANDARD FORM PATTERNS:")
    print("  Form '1111'  -> EXCELLENT (4+ wins, no blemish = grade 1 class)")
    print("  Form '111'   -> VERY GOOD (3 wins in a row = strong)")
    print("  Form '11F1'  -> ACCEPTABLE (fall can be forgiven if class/trainer top)")
    print("  Form '1211'  -> GOOD (placed once but winning again)")
    print("  Form '211'   -> OK (runner-up last, improving - common stayers pattern)")
    print("  Form '11'    -> Novice ok (bumper/novice minimal runs)")
    print("  AVOID: Any form featuring 'P' (pulled up), '0' (unplaced) recently")

    print("\n  KEY INSIGHTS:")
    print("  * ~62% of winners won their last race before Cheltenham")
    print("  * Previous Festival winners win again at ~40% rate (huge)")
    print("  * Unbeaten horses win at very high rate in novice races")
    print("  * For Championship races: need Grade 1 win in prep, not just placed")


def analyze_odds_patterns():
    """Starting price distribution"""
    print_header("STARTING PRICE / ODDS ANALYSIS - 10 YEARS")

    brackets = {"Evens or shorter (huge fav)": 0, "6/5 - 2/1": 0,
                "9/4 - 4/1": 0, "9/2 - 8/1": 0, "9/1 - 14/1": 0, "16/1+": 0}

    for year, races in WINNERS.items():
        for race, data in races.items():
            sp = data.get("sp", "")
            try:
                if "/" in sp:
                    n, d = sp.split("/")
                    dec = int(n) / int(d)
                else:
                    dec = float(sp) - 1
                if dec <= 1.0:
                    brackets["Evens or shorter (huge fav)"] += 1
                elif dec <= 2.0:
                    brackets["6/5 - 2/1"] += 1
                elif dec <= 4.0:
                    brackets["9/4 - 4/1"] += 1
                elif dec <= 8.0:
                    brackets["9/2 - 8/1"] += 1
                elif dec <= 14.0:
                    brackets["9/1 - 14/1"] += 1
                else:
                    brackets["16/1+"] += 1
            except:
                pass

    total = sum(brackets.values())
    print(f"\n  {'PRICE BRACKET':<32}{'WINS':<8}{'%'}")
    print("-" * 55)
    for bracket, cnt in brackets.items():
        pct = cnt / total * 100 if total else 0
        bar = "#" * cnt
        print(f"  {bracket:<32}{cnt:<8}{pct:.1f}%  {bar}")

    print(f"\n  KEY INSIGHTS:")
    print(f"  * Short prices (evens or shorter) win frequently - CLASS proves itself")
    print(f"  * 4/5 to 4/1 range = sweet spot for confidence + value")
    print(f"  * Prices 9/1-14/1 produce occasional shocks (Labaik, Surprise results)")
    print(f"  * 16/1+ = mostly blind luck - only notable exception is Lisnagar Oscar 50/1")
    print(f"  * RULE: Never automatically oppose a short price at Cheltenham")


def analyze_age_ratings():
    """Age and rating analysis"""
    print_header("AGE & OFFICIAL RATINGS OF WINNERS")

    ages    = []
    ratings = []

    for year, races in WINNERS.items():
        for race, data in races.items():
            if data.get("age"):
                ages.append(data["age"])
            if data.get("rating"):
                ratings.append(data["rating"])

    if ages:
        avg_age = sum(ages) / len(ages)
        print(f"\n  Average winner age  : {avg_age:.1f} years")
        print(f"  Youngest winners    : {min(ages)} (novice races)")
        print(f"  Oldest winner       : {max(ages)}")
        age_dist = Counter(ages)
        print(f"\n  Age distribution:")
        for a in sorted(age_dist.keys()):
            bar = "#" * age_dist[a]
            print(f"    Age {a:<4}: {age_dist[a]:<4} {bar}")

    if ratings:
        print(f"\n  Average OR rating   : {sum(ratings)/len(ratings):.0f}")
        print(f"  Highest rating      : {max(ratings)}")
        print(f"  Lowest winner rating: {min(ratings)}")

    print("\n  KEY INSIGHTS:")
    print("  * Championship races: winners mostly aged 7-10")
    print("  * Gold Cup sweet spot: 8-9 year olds (experienced, not over the hill)")
    print("  * Novice races: 5-6 year olds - bumper form carries forward")
    print("  * Ratings: Championship winners rated 165+ (anything below = upset territory)")
    print("  * Age 10+ CAN win but must have proven Festival record (see Energumene 2025 at 10)")


# ── Module-level jockey/combo constants (shared with deduplication logic) ─────
JOCKEY_SCORES = {
    "Paul Townend":       12,   # Capped at 12 (Option B rebalance — was 20, duplicated by combo+champion bonus)
    "Nico de Boinville":  12,   # Capped at 12 (was 15)
    "Harry Skelton":      10,
    "Jack Kennedy":       10,
    "Rachael Blackmore":  10,
    "Donagh Meyler":       8,
    "Mark Walsh":          8,
    "Danny Mullins":       8,
    "Patrick Mullins":     8,
    "Davy Russell":        8,
    "Sean Flanagan":        6,
    "Harry Cobden":        8,   # Bumped 6→8: WON Brown Advisory 2026 (Kitzbuhel, Mullins), WON Turner's 2025 — underrated
    "Tom Cannon":          6,
    "Aidan Coleman":       6,
    "Keith Donoghue":      6,
    "M. P. Walsh":         6,   # Added: Emmet Mullins conditional/amateur, rides at festivals
    "Jonjo O'Neill Jr.":   6,   # Added: strong UK NH jockey
    "Jonjo O'Neill Jr":    6,   # Added: alternate spelling without trailing dot
    "Sean Bowen":          7,   # Added: champion British NH jockey
    "J. J. Slevin":        8,   # Added: top Irish jockey, multiple Festival rides
    "S. F. O'Keeffe":      5,   # Added: Willie Mullins stable conditional
    "James Bowen":         5,   # Added: UK jockey
    "D. E. Mullins":       6,   # Added: Derek Mullins, rides for Margaret Mullins
    "J. W. Kennedy":       5,   # Added: JW Kennedy Irish jockey
    # ── UPDATED from Festival results ──────────────────────────────────────────
    "Ben Jones":            7,   # 2nd Supreme 2026 (Sober Glory 9/2) — Philip Hobbs retained jockey, underrated
    "Gavin Sheehan":        6,   # solid UK NH jockey
    "Nick Scholfield":      5,
    "Tom O'Brien":          5,
    "Paddy Brennan":        6,
    "Richie McLernon":      6,   # WON Ultima Handicap Chase 2026 (Johnnywho 18/1)
}

ELITE_COMBOS = {
    ("Willie Mullins",       "Paul Townend"):        8,   # Capped at 8 (was 15 — Option B rebalance)
    ("W. P. Mullins",        "Paul Townend"):        8,   # alias
    ("Willie Mullins",       "Mark Walsh"):          5,   # Arkle 2026: Kargese won
    ("W. P. Mullins",        "Mark Walsh"):          5,   # alias
    ("Willie Mullins",       "Harry Cobden"):        6,   # Brown Advisory 2026: Kitzbuhel won — Mullins using Cobden as 3rd jockey at Festival
    ("W. P. Mullins",        "Harry Cobden"):        6,   # alias
    ("Nicky Henderson",      "Nico de Boinville"):   8,   # Capped at 8 (was 12)
    ("Gordon Elliott",       "Jack Kennedy"):        3,   # reduced — 0 festival wins 2021-2023
    ("Henry de Bromhead",    "Rachael Blackmore"):   6,
    ("Gavin Cromwell",       "Danny Mullins"):       6,
}


def deduplicate_jockeys_in_field(scored):
    """
    One jockey cannot ride two horses in the same race.
    After scoring, find any jockey assigned to multiple horses and strip the
    jockey bonus (+ combo bonus if applicable) from every horse EXCEPT the
    highest-scoring one.  Re-sorts the list descending by score.

    Works on either:
      - list of tuples  (score, horse_dict, tips, warnings, vr)  [generate_2026_picks format]
      - list of dicts   with keys 'score', 'jockey', 'trainer', 'tips', 'warnings' [score_field format]
    Pass the list; it is mutated and returned.
    """
    from collections import defaultdict

    # Detect format
    tuple_format = scored and isinstance(scored[0], (tuple, list))

    def get_jockey(item):
        return item[1].get("jockey", "") if tuple_format else item.get("jockey", "")
    def get_trainer(item):
        return item[1].get("trainer", "") if tuple_format else item.get("trainer", "")
    def get_score(item):
        return item[0] if tuple_format else item["score"]
    def get_name(item):
        return item[1].get("name", "?") if tuple_format else item.get("name", "?")

    by_jockey = defaultdict(list)
    for item in scored:
        j = get_jockey(item)
        if j:
            by_jockey[j].append(item)

    for jockey, horses in by_jockey.items():
        if len(horses) < 2:
            continue
        # Sort by score descending; top horse keeps the bonus
        horses.sort(key=get_score, reverse=True)
        top_name = get_name(horses[0])
        for item in horses[1:]:
            trainer   = get_trainer(item)
            j_bonus   = JOCKEY_SCORES.get(jockey, 3)
            cb_bonus  = ELITE_COMBOS.get((trainer, jockey), 0)
            deducted  = j_bonus + cb_bonus
            deduct_msg = (
                f"⚠ Jockey '{jockey}' cannot ride two horses — assigned to "
                f"{top_name} (higher scorer). Jockey/combo bonus removed: -{deducted}pts"
            )
            if tuple_format:
                old_score, horse_d, tips, warnings, vr = item
                new_score = old_score - deducted
                new_tips  = [t for t in tips
                             if f"Jockey '{jockey}'" not in t and "Elite combo bonus" not in t]
                new_tips.append(deduct_msg)
                new_warnings = list(warnings) + [f"Jockey clash: {jockey} rides {top_name}"]
                # Mutate in-place by replacing the tuple elements via index
                idx = scored.index(item)
                scored[idx] = (new_score, horse_d, new_tips, new_warnings, vr)
            else:
                item["score"] -= deducted
                item["tips"] = [t for t in item.get("tips", [])
                                 if f"Jockey '{jockey}'" not in t and "Elite combo bonus" not in t]
                item["tips"].append(deduct_msg)
                item.setdefault("warnings", [])
                if len(item["warnings"]) < 3:
                    item["warnings"].append(f"Jockey clash: {jockey} rides {top_name}")

    scored.sort(key=get_score, reverse=True)
    return scored


def score_horse_2026(horse, race_name):
    """
    Score a 2026 horse based on patterns extracted from 10-year analysis.
    Returns (score, reasons)
    """
    score  = 40  # baseline
    tips   = []
    warnings = []

    # --- Trainer bonus ---
    trainer = horse.get("trainer", "")
    # PER-HORSE NORMALIZED from 10-year history (2016-2025, 70 Grade-1 wins):
    # Adjusted for multi-entry: Mullins avg 3.0 horses/race → per-horse 12.2%
    # Henderson avg 1.4/race → per-horse 11.1%  Elliott avg 2.2/race → 5.7%
    # Formula: race_win% / avg_entries_per_race, scaled to 12pt anchor
    trainer_scores = {
        "Willie Mullins":    13,   # 37.1% race-win / 3.0 avg = 12.2% per horse (+1 premium: stable depth, soft-ground mastery)
        "Nicky Henderson":   12,   # 15.7% / 1.4 = 11.1% per horse — effectively equal to Mullins
        "Gordon Elliott":     6,   # 12.9% / 2.2 =  5.7% per horse
        "Henry de Bromhead":  6,   # 10.0% / 1.6 =  6.2% per horse
        "Gavin Cromwell":     5,   #  7.1% / 1.3 =  5.6% per horse (Stayers specialist)
        "Emmet Mullins":      6,   # Quality Irish raider, competitive per horse
        "Paul Nicholls":      4,   # 1/70 Grade-1s — festival record modest
        "Alan King":          5,
        "Emma Lavelle":       4,   # 1/70 (Paisley Park)
        "Rebecca Curtis":     4,   # 1/70
        "Peter Fahey":        4,
        "Dan Skelton":        4,   # 0 Grade-1 wins in dataset
        "Ben Pauling":        4,
        "Oliver Greenall & Josh Guerriero": 4,
        "Jonjo O'Neill":      7,   # WON Ultima Handicap Chase 2026 (Johnnywho 18/1) — bumped from 4
        "Jonjo & A.J. O'Neill": 7, # alias — race card credit for Jonjo O'Neill yard
        "W. P. Mullins":     13,   # alias for Willie Mullins
        "Joseph Patrick O'Brien": 7,   # quality Irish multi-runner trainer
        "Gavin Patrick Cromwell": 5,   # alias
        "Paul Nolan":         5,
        "Faye Bramley":       5,   # 2nd Fred Winter 2026 (Winston Junior) — bumped from 4
        "Padraig Roche":      6,   # WON Fred Winter 2026 (Saratoga) — handicap placement specialist
        "Mrs J. Harrington":  4,   # Jessica Harrington alias, 1/70 = 1.4%
        "Jessica Harrington": 4,   # 1/70 = 1.4% (Sizing John)
        "Jeremy Scott":       4,   # 1/70 = 1.4% (2025 Champ Hurdle)
        "Colin Tizzard":      4,   # 2/70 but retired
        "Barry Connell":      4,   # 1/70 (2025 Queen Mother)
        "Sam Curling":        4,
        "Noel Meade":         4,
        "Philip Hobbs & Johnson White": 6,   # 2nd Supreme 2026 (Sober Glory) — consistent Cheltenham runner
        "Philip Hobbs":       6,   # alias without joint suffix
        "Neil Mulholland":    5,
        "Dr Richard Newland": 5,
    }
    t_score = trainer_scores.get(trainer, 5)
    score += t_score
    tips.append(f"Trainer '{trainer}': +{t_score}pts")

    # --- Jockey bonus ---
    jockey = horse.get("jockey", "")
    j_score = JOCKEY_SCORES.get(jockey, 3)
    score += j_score
    tips.append(f"Jockey '{jockey}': +{j_score}pts")

    # Trainer/Jockey combo bonus
    combo_bonus = ELITE_COMBOS.get((trainer, jockey), 0)
    if combo_bonus:
        score += combo_bonus
        tips.append(f"Elite combo bonus: +{combo_bonus}pts")

    # --- 3lb / 5lb claimer tactical weight booking ---
    # In non-handicap chases/hurdles, a trainer deliberately booking a 3lb claimer
    # gains a real weight advantage. Stone-Walsh(3) on Final Orders 2026 = classic example.
    # In handicaps the claim is already offset by BHA allotted weights, so no bonus.
    import re as _re_claimer
    _claimer_match = _re_claimer.search(r'\((\d+)\)', jockey)
    if _claimer_match:
        _claim_lbs = int(_claimer_match.group(1))
        _is_handicap = bool(race_name and "handicap" in race_name.lower())
        if _claim_lbs == 3 and not _is_handicap:
            score += 5
            tips.append(f"3lb claimer in non-handicap (tactical weight booking): +5pts")
        elif _claim_lbs == 5 and not _is_handicap:
            score += 3
            tips.append(f"5lb claimer in non-handicap: +3pts")
        elif _claim_lbs == 7 and not _is_handicap:
            score += 2
            tips.append(f"7lb claimer in non-handicap: +2pts")

    # --- Handicap dampening ---
    # In big-field handicap races, BHA weights already neutralise trainer quality.
    # Cap the combined trainer+jockey+combo benefit that EXCEEDS the 'average' baseline
    # (avg trainer=5, avg jockey=3, no combo=0) so elite stables aren't over-rewarded.
    # Fred Winter 2026 learning: Henderson/de Boinville scored 32pts here vs winner Saratoga 11pts.
    HCAP_TRAINER_CAP  = 5   # max trainer bonus in handicaps (tightened 7→5: Cheltenham 2026 data)
    HCAP_JOCKEY_CAP   = 4   # max jockey bonus in handicaps (tightened 6→4)
    HCAP_COMBO_CAP    = 2   # max combo bonus in handicaps (tightened 3→2)
    if race_name and "handicap" in race_name.lower():
        excess_t = max(0, t_score    - HCAP_TRAINER_CAP)
        excess_j = max(0, j_score    - HCAP_JOCKEY_CAP)
        excess_c = max(0, combo_bonus - HCAP_COMBO_CAP)
        hcap_penalty = excess_t + excess_j + excess_c
        if hcap_penalty > 0:
            score -= hcap_penalty
            tips.append(f"Handicap weight equalisation: −{hcap_penalty}pts (BHA weights cap trainer/jockey edge)")
        # Extra dampening for large-field handicaps (>18 runners): random factor dominates
        field_size = len(race_name)  # placeholder — use race data if available
        large_field_bonus_note = ""
        # Check via race_name hint tokens
        if any(t in race_name.lower() for t in ["betmgm", "fred winter", "county", "martin pipe", "pertemps", "kim muir", "ultimum", "ultima", "grand annual"]):
            score -= 6
            tips.append("Large-field handicap dampener: -6pts (20+ runner races, BHA weights equalise field)")
    record = horse.get("cheltenham_record", "") or ""
    # Normalise "winner" → "won" so "CD winner" / "Cheltenham winner" score the same as "Won X race"
    _norm_record = re.sub(r'\bwinner\b', 'won', record.lower())
    won_count = _norm_record.count("won")

    # Racing Post shorthand codes stored in cheltenham_record:
    #   C  = course winner (won at Cheltenham — the strongest possible form signal)
    #   CD = course & distance winner → same treatment as C
    #   D  = distance winner at Cheltenham (won at same trip — good form, not full winner)
    #   BF = beaten favourite at Cheltenham (competitive, close)
    # Detect standalone tokens so "C" in "Rebecca Curtis" doesn't false-fire.
    _rp_c  = bool(re.search(r'\bC(?:\s*D)?\b', record))   # C or CD or C D
    _rp_d  = bool(re.search(r'\bD\b', record)) and not _rp_c  # D only (without C)
    _rp_bf = bool(re.search(r'\bBF\b', record))
    _course_runner = "cheltenham course runner" in record.lower()

    if won_count >= 3:
        score += 25
        tips.append(f"Three-time Festival winner: +25pts (extremely rare, dominant)")
    elif won_count == 2:
        score += 20
        tips.append(f"Double Festival winner: +20pts")
    elif won_count >= 1:
        score += 15
        tips.append(f"Previous Festival winner: +15pts")
    elif _rp_c:
        # Racing Post 'C' = course winner → previous Cheltenham Festival winner
        score += 15
        tips.append(f"Previous Cheltenham course winner (C): +15pts")
    elif "placed" in record.lower() or "2nd" in record.lower() or "3rd" in record.lower() or "4th" in record.lower():
        score += 8
        tips.append(f"Previous Festival place: +8pts")
    elif _rp_d:
        # D alone = won at Cheltenham at this distance, solid Festival form
        score += 8
        tips.append(f"Cheltenham distance winner (D): +8pts")
    elif _rp_bf:
        # BF = beaten favourite, was competitive at Cheltenham
        score += 5
        tips.append(f"Beaten favourite at Cheltenham (BF): +5pts")
    elif _course_runner:
        # Ran at Cheltenham but no win/place — no bonus, but no unknown-quantity warning either
        pass
    else:
        warnings.append("No previous Festival form (unknown quantity)")

    # --- Same-race winner bonus (+10) ---
    # If the horse won the EXACT same race in a prior year, reward that specific
    # course-and-distance mastery on top of the general Festival win bonus.
    if race_name and record and won_count >= 1:
        race_key_words = [
            w for w in race_name.lower().split()
            if len(w) > 4 and w not in {"chase", "hurdle", "novices", "mares",
                                         "champion", "grade", "novice", "stakes"}
        ]
        if race_key_words and any(kw in record.lower() for kw in race_key_words):
            score += 7
            tips.append(f"Won this exact race before: +7pts (same race course & distance mastery)")

    # --- Ground / Going preference bonus ---
    # Calibrated against FORECAST_GOING (set at top of file, updated live each day).
    # Good = drying ground: good-ground horses benefit; soft specialists penalised.
    # Good to Soft / Soft = normal March Cheltenham: soft preference = positive.
    ground_pref = horse.get("ground_pref", "").lower()
    last_run_txt = (horse.get("last_run", "") or "").lower()
    ch_record_txt = record.lower()
    ch_soft_proof = won_count >= 1  # Cheltenham winner = proven on course ground
    forecast = FORECAST_GOING.lower()
    good_ground = "good" in forecast and "soft" not in forecast  # strictly Good or Good to Firm

    if good_ground:
        # Ground is drying — good-ground specialists benefit; soft specialists penalised
        prefers_good = any(g in ground_pref for g in ("good", "firm", "fast"))
        prefers_gts  = "good_to_soft" in ground_pref
        prefers_soft = any(g in ground_pref for g in ("soft", "yielding")) and not prefers_gts
        if prefers_good:
            score += 8
            tips.append(f"Ground suits (good ground pref, going is {FORECAST_GOING}): +8pts")
        elif prefers_gts:
            score += 3
            tips.append(f"Ground acceptable (good-to-soft pref, going is {FORECAST_GOING}): +3pts")
        elif not ground_pref or ground_pref == "any":
            # No stated preference — Cheltenham winners get small bonus
            if ch_soft_proof:
                score += 3
                tips.append(f"Proven Cheltenham handler (course winner, going is {FORECAST_GOING}): +3pts")
        elif prefers_soft:
            score -= 5
            warnings.append(f"Soft-ground specialist — going {FORECAST_GOING} not ideal: -5pts")
    else:
        # Standard soft / good-to-soft going
        soft_signals = any(g in ground_pref for g in ("soft", "good_to_soft", "any", "yielding"))
        needs_better = any(g in ground_pref for g in ("good", "firm", "fast"))
        if soft_signals:
            score += 8
            tips.append(f"Ground suits (soft/good-to-soft preference): +8pts")
        elif ch_soft_proof and not needs_better:
            score += 5
            tips.append(f"Proven Cheltenham ground handler (course winner): +5pts")
        elif needs_better:
            score -= 5
            warnings.append(f"Preference for better ground (going is {FORECAST_GOING}): -5pts")

    # --- Same distance / class form bonus (+8) ---
    # Reward horses that previously won at the same distance bracket and race class.
    # Uses optional 'dist_class_form' field (free-text like '2m5f Grade 1 win Feb 2026')
    # or infers from last_run and race_name.
    dist_class = horse.get("dist_class_form", "") or ""
    if dist_class:
        score += 8
        tips.append(f"Won same distance/class bracket: +8pts ({dist_class[:50]})")
    else:
        # Infer from last_run: Grade 1 win at correct distance class
        grade1_win_signals = ("won grade 1" in last_run_txt or "won grade 2" in last_run_txt)
        # Detect distance keywords from race_name and match in last_run
        dist_keywords = {"2m": ["2m", "2 mile"], "2m4": ["2m4", "2m 4", "2.5m"],
                         "2m5": ["2m5", "2m 5"], "3m": ["3m", "3 mile"],
                         "3m1": ["3m1", "3m 1"], "3m2": ["3m2", "3m 2"]}
        race_dist_match = False
        for dist_key, signals in dist_keywords.items():
            if any(s in race_name.lower() for s in signals):
                if any(s in last_run_txt for s in signals):
                    race_dist_match = True
                    break
        if grade1_win_signals and race_dist_match:
            score += 8
            tips.append(f"Graded win at same distance bracket this season: +8pts")

    # --- Form pattern ---
    form = horse.get("form", "").replace("-", "")
    if form:
        wins_form  = form.count("1")
        falls_form = form.count("F")
        poor_form  = form.count("0") + form.count("P")
        # Option B: stronger finishing position trend weighting
        if form.startswith("1111") and falls_form == 0:
            score += 18   # reduced 22→18: class jump at Cheltenham limits recent-form advantage
            tips.append("4+ wins in form string (unbeaten run): +18pts")
        elif form.startswith("111") and falls_form <= 1:
            score += 14   # reduced 18→14
            tips.append("3+ consecutive wins in form: +14pts")
        elif form.startswith("11"):
            score += 10
            tips.append("2 consecutive wins: +10pts")
        elif form.startswith("1"):
            score += 5
            tips.append("Won last time out: +5pts")
        if poor_form >= 2:
            score -= 10
            warnings.append(f"Poor runs in form (P/0): -{10}pts")
        elif poor_form == 1:
            score -= 5
            warnings.append("One poor run in recent form: -5pts")

    # --- Improvement trajectory (+3) ---
    # Reward horses showing a clear upward form trend (each run better than last).
    # Manual flag 'improving' overrides; otherwise auto-detect from form digits.
    improving = horse.get("improving", False)
    if improving:
        score += 3
        tips.append("Progressive improver (flagged): +3pts")
    else:
        form_str = horse.get("form", "").replace("-", "")
        form_digits = [int(c) for c in form_str if c.isdigit()]
        if len(form_digits) >= 3:
            r = form_digits[:3]  # most-recent first
            # Improving = most recent run best, and previous two also getting better
            # e.g. form "1-2-3" most-recent-first → r=[1,2,3] → 1<2<3 ✓
            if r[0] not in (0,) and r[1] not in (0,) and r[2] not in (0,):
                if r[0] < r[1] and r[1] < r[2]:
                    score += 3
                    tips.append(
                        f"Improving form trend ({r[2]}→{r[1]}→{r[0]} positions): +3pts"
                    )

    # --- Up in distance / Finishes strongly ---
    # 'up_in_distance': horse stepping up in trip this race vs recent runs → +2pts
    # 'finishes_strongly': proven strong stayer / stays on well at target distance → +2pts
    # Combo bonus if both apply (confirmed stayer being tested over longer trip) → +1pt
    up_dist   = horse.get("up_in_distance", False)
    fin_str   = horse.get("finishes_strongly", False)
    if up_dist:
        score += 2
        tips.append("Stepping up in trip: +2pts")
    if fin_str:
        score += 2
        tips.append("Strong finisher / stays well: +2pts")
    if up_dist and fin_str:
        score += 1
        tips.append("Confirmed stayer stepping up in trip: +1pt combo")

    # --- Rating (Option B: stronger weight to form/class via OR rating) ---
    rating = horse.get("rating", 0)
    if rating >= 175:
        score += 18
        tips.append(f"Elite rating {rating}: +18pts")
    elif rating >= 170:
        score += 15
        tips.append(f"High-class rating {rating}: +15pts")
    elif rating >= 165:
        score += 12
        tips.append(f"High rating {rating}: +12pts")
    elif rating >= 158:
        score += 8
        tips.append(f"Solid rating {rating}: +8pts")
    elif rating >= 150:
        score += 5
        tips.append(f"Useful rating {rating}: +5pts")
    elif rating < 140:
        score -= 8
        warnings.append(f"Below-average rating {rating}: -8pts")

    # --- Freshness / Days off ---
    days = horse.get("days_off", 50)
    if 28 <= days <= 70:
        score += 5
        tips.append(f"Ideal prep gap ({days} days): +5pts")
    elif days > 100:
        score -= 8
        warnings.append(f"Long absence ({days} days): -8pts")

    # --- Odds (class indicator) ---
    odds_str = horse.get("odds", "")
    try:
        if "/" in odds_str:
            n, d = odds_str.split("/")
            dec = int(n) / int(d)
        else:
            dec = float(odds_str)
        if dec <= 1.5:
            score += 12
            tips.append(f"Strong market confidence ({odds_str}): +12pts")
        elif dec <= 3.0:
            score += 8
            tips.append(f"Market fav range ({odds_str}): +8pts")
        elif dec <= 6.0:
            score += 4
            tips.append(f"Reasonable price ({odds_str}): +4pts")
        elif dec >= 10:
            score -= 3
            warnings.append(f"Long price ({odds_str}): -3pts")
    except:
        pass

    # ── Cheltenham Strategy Bonuses ─────────────────────────────────────────
    # Grade 1 Championship race bonus (+10)
    GRADE1_CHAMPS_SCORE = [
        "Champion Hurdle", "Queen Mother Champion Chase", "Cheltenham Gold Cup",
        "Stayers Hurdle", "Stayers' Hurdle", "Supreme Novices Hurdle",
        "Supreme Novices' Hurdle", "Arkle Challenge Trophy", "Arkle Chase",
        "Champion Bumper", "Close Brothers Mares Hurdle", "Mares Hurdle",
        "Albert Bartlett Novices Hurdle", "Ryanair Chase",
        "Ballymore Novices Hurdle", "Brown Advisory Novices Chase",
        "Turners Novices Chase", "JCB Triumph Hurdle",
    ]
    for g1name in GRADE1_CHAMPS_SCORE:
        if g1name.lower() in race_name.lower():
            score += 10
            tips.append("Grade 1 Championship race: +10pts")
            break

    # Graded winner this season (+12) — check last_run field
    last_run = horse.get("last_run", "") or ""
    recent_form_str = horse.get("recent_form", "") or ""
    if ("Won Grade 1" in last_run or "Won Grade 2" in last_run or
            "Won Grade 1" in recent_form_str or "Won Grade 2" in recent_form_str):
        score += 12
        tips.append("Graded winner this season: +12pts")

    # ─────────────────────────────────────────────────────────────────────────
    # --- Recent race history analysis (structured data from 'recent_races') ---
    # Extracts quality signals unavailable from simple form strings:
    #   • Win rate over last 3-6 runs  → consistency / current form state
    #   • Big-field wins (15+ runners) → quality proof vs large competitive fields
    #   • Cheltenham course experience → verifies / supplements cheltenham_record
    #   • Ground-matched wins          → proven on today's going type
    #   • Graded race wins in history  → class proof beyond last_run field
    # ─────────────────────────────────────────────────────────────────────────
    recent_races = horse.get("recent_races", [])
    if recent_races:
        total_rr   = len(recent_races)
        wins_rr    = sum(1 for r in recent_races if r.get("pos") == 1)
        places_rr  = sum(1 for r in recent_races
                         if isinstance(r.get("pos"), int) and r.get("pos") <= 3)

        # Big-field wins: 20+ runners = elite quality; 15+ = competitive
        big_field_wins    = sum(1 for r in recent_races
                                if r.get("pos") == 1 and r.get("ran", 0) >= 15)
        very_big_fw       = sum(1 for r in recent_races
                                if r.get("pos") == 1 and r.get("ran", 0) >= 20)

        # Cheltenham course runs from recent history
        chelt_runs_rr  = [r for r in recent_races
                          if "cheltenham" in r.get("venue", "").lower()]
        chelt_wins_rr  = [r for r in chelt_runs_rr if r.get("pos") == 1]
        chelt_place_rr = [r for r in chelt_runs_rr
                          if isinstance(r.get("pos"), int) and r.get("pos") <= 3]

        # Ground-matched wins: check race description codes vs today's forecast
        _fc = FORECAST_GOING.lower()
        _is_soft_day = any(g in _fc for g in ("soft", "heavy", "yielding"))
        _is_good_day = "good" in _fc and "soft" not in _fc
        gm_wins = 0
        for _r in recent_races:
            if _r.get("pos") != 1:
                continue
            _desc = _r.get("race", "").lower()
            if _is_soft_day and any(g in _desc for g in ("sft", "hy ", "hvy", "soft", "heavy", "yld", " gs")):
                gm_wins += 1
            elif _is_good_day and any(g in _desc for g in (" gd", " gf", " fm", "good", "firm")):
                gm_wins += 1
            elif "gs" in _desc or "good to soft" in _desc:
                gm_wins += 1   # neutral going — partial credit

        # Graded race wins in history (Grade 1 / Grade 2 in race description)
        graded_wins_rr = sum(1 for _r in recent_races
                             if _r.get("pos") == 1 and
                             any(g in _r.get("race", "").lower()
                                 for g in ("grade 1", "grade 2", "grd1", "grd2",
                                           " g1 ", " g2 ", "grp1", "grp2")))

        # 1. Win-rate consistency bonus (3+ run sample required)
        if total_rr >= 3:
            _wr = wins_rr / total_rr
            if _wr >= 0.8:
                score += 8
                tips.append(f"Outstanding win rate from recent races ({wins_rr}/{total_rr}): +8pts")
            elif _wr >= 0.6:
                score += 5
                tips.append(f"Strong win rate from recent races ({wins_rr}/{total_rr}): +5pts")
            elif _wr >= 0.4:
                score += 2
                tips.append(f"Good win rate from recent races ({wins_rr}/{total_rr}): +2pts")

        # 2. Big-field wins — proof against quality competitive fields
        if very_big_fw >= 1:
            score += 6
            tips.append(f"Won in 20+ runner field ({very_big_fw}x): +6pts (elite quality proof)")
        elif big_field_wins >= 2:
            score += 5
            tips.append(f"Multiple wins in 15+ runner fields ({big_field_wins}x): +5pts")
        elif big_field_wins == 1:
            score += 3
            tips.append(f"Won in competitive 15+ runner field: +3pts")

        # 3. Cheltenham course evidence — only if cheltenham_record hasn't already scored it
        _ch_already_credited = (won_count >= 1 or _rp_c)
        _ch_dist_credited    = _rp_d
        if chelt_wins_rr and not _ch_already_credited:
            # Course win found in history but not in cheltenham_record — credit it
            score += 8
            tips.append("Cheltenham winner (verified from recent race history): +8pts")
        elif chelt_place_rr and not _ch_already_credited and not _ch_dist_credited:
            score += 4
            tips.append(f"Cheltenham placed finisher (recent race history, {len(chelt_place_rr)}x): +4pts")
        elif len(chelt_runs_rr) >= 3 and not _ch_already_credited and not _ch_dist_credited:
            score += 3
            tips.append(f"Regular Cheltenham runner ({len(chelt_runs_rr)} recent course runs): +3pts")
        elif len(chelt_runs_rr) >= 1 and not _ch_already_credited and not _ch_dist_credited:
            score += 2
            tips.append(f"Cheltenham course experience ({len(chelt_runs_rr)} recent run(s) at venue): +2pts")

        # 4. Ground-matched wins (don't double-count with explicit ground_pref bonus)
        if gm_wins >= 2:
            score += 4
            tips.append(f"Multiple wins on today's going type ({gm_wins} races): +4pts")
        elif gm_wins == 1:
            score += 2
            tips.append(f"Won on similar going conditions: +2pts")

        # 5. Graded race wins in history (smaller bonus — avoid overlap with last_run check)
        _graded_already = any("Graded winner this season" in t for t in tips)
        if graded_wins_rr >= 1 and not _graded_already:
            score += 6
            tips.append(f"Graded race winner (from race history): +6pts")

    # --- Cross-country prep school bonus ---
    # The January Cheltenham cross-country race is run on the IDENTICAL Prestbury Park
    # circuit (32 specialist fences). Any horse that ran in it — regardless of finishing
    # position — has schooled all the fences. This is course familiarisation, not a bad
    # prep run. Final Orders 2026 (won at 7/1) was 5th in the Jan prep — completely
    # penalised by the model as a 'poor run'; in reality it was invaluable course school.
    _is_xc_race = bool(race_name and "cross country" in race_name.lower())
    if _is_xc_race and "cross country" in last_run_txt:
        score += 15
        tips.append("Cross-country prep school (ran same Prestbury XC circuit in Jan): +15pts")

    # Option B: Elite Irish raider and Champion jockey bonuses REMOVED
    # — already captured in capped trainer_scores and JOCKEY_SCORES above.
    # Adding course+distance combined bonus instead (+5 on top of separate bonuses)
    # if horse has both same-race win AND dist_class_form evidence
    if won_count >= 1 and dist_class:
        score += 5
        tips.append("Course & distance double confirmation: +5pts")

    # No upper cap — raw additive score; typical elite range 130-175
    score = max(0, score)

    # Value rating: raw score relative to implied probability
    # Higher = more appeal per £1 risked (adjusted for price)
    try:
        if "/" in odds_str:
            n2, d2 = odds_str.split("/")
            dec2 = int(n2) / int(d2) + 1.0   # decimal odds
        else:
            dec2 = float(odds_str) + 1.0
        value_rating = round(score / dec2, 1)
    except:
        value_rating = 0.0

    return score, tips, warnings, value_rating


def generate_2026_picks():
    """Generate 2026 Festival winner predictions based on 10-year patterns"""
    print_header("CHELTENHAM FESTIVAL 2026 - PREDICTED WINNERS")
    print("  Based on 10-year historical pattern analysis\n")

    all_picks = []

    for race_name, race_data in RACES_2026.items():
        print(f"\n  {'-'*88}")
        print(f"  RACE: {race_name}  |  {race_data['day']}  |  {race_data['grade']}  |  {race_data['distance']}")
        print(f"  {'-'*88}")

        scored = []
        for horse in race_data["entries"]:
            s, tips, warnings, vr = score_horse_2026(horse, race_name)
            scored.append((s, horse, tips, warnings, vr))

        scored.sort(key=lambda x: x[0], reverse=True)
        # Remove jockey bonus from any horse sharing a jockey with a higher scorer
        deduplicate_jockeys_in_field(scored)

        for i, (score, horse, tips, warnings, vr) in enumerate(scored):
            if i == 0:
                rec = ">> OUR PICK <<"
            elif i == 1:
                rec = "   Lays 2   "
            else:
                rec = "            "

            # Tiers calibrated to raw uncapped scores (typical elite range 130-175)
            tier = ("A+ ELITE" if score >= 155 else
                    "A  ELITE"  if score >= 140 else
                    "B  EXCELLENT" if score >= 120 else
                    "C  STRONG"  if score >= 100 else
                    "D  FAIR"    if score >= 80  else "E  WEAK")

            print(f"\n  {rec}  {horse['name']} @ {horse['odds']}")
            print(f"           Trainer: {horse['trainer']}  |  Jockey: {horse['jockey']}")
            print(f"           Score: {score}  Value Rating: {vr}  [{tier}]")
            print(f"           Festival Record: {horse.get('cheltenham_record') or 'First time'}")
            print(f"           Last run: {horse.get('last_run', 'N/A')}")
            for t in tips[:4]:
                print(f"           + {t}")
            for w in warnings:
                print(f"           ! {w}")

        if scored:
            winner = scored[0]
            confidence = "A+ ELITE" if winner[0] >= 155 else "A ELITE" if winner[0] >= 140 else "B EXCELLENT" if winner[0] >= 120 else "C STRONG" if winner[0] >= 100 else "D FAIR"
            all_picks.append({
                "race": race_name,
                "horse": winner[1]["name"],
                "trainer": winner[1]["trainer"],
                "jockey": winner[1]["jockey"],
                "odds":  winner[1]["odds"],
                "score": winner[0],
                "value_rating": winner[4],
                "confidence": confidence,
            })

    # Summary table
    print(f"\n\n{'='*90}")
    print("  CHELTENHAM 2026 - FINAL PICK SUMMARY")
    print(f"{'='*90}")
    print(f"\n  {'RACE':<36}{'HORSE':<26}{'TRAINER':<22}{'ODDS':<8}{'SCORE':<8}{'VALUE':<8}{'TIER'}")
    print("-" * 100)
    for p in all_picks:
        print(f"  {p['race']:<36}{p['horse']:<26}{p['trainer']:<22}{p['odds']:<8}{p['score']:<8}{p.get('value_rating', '-'):<8}{p['confidence']}")

    elite = [p for p in all_picks if p["score"] >= 120]
    print(f"\n  ELITE SELECTIONS (score 120+): {len(elite)}")
    for p in sorted(elite, key=lambda x: x['score'], reverse=True):
        print(f"    * {p['horse']} ({p['race']}) @ {p['odds']}  Score:{p['score']}  Value:{p.get('value_rating','-')}  [{p['confidence']}]")

    # Best value = highest value_rating (score per unit of decimal odds)
    value_picks = sorted(all_picks, key=lambda x: x.get('value_rating', 0), reverse=True)
    print(f"\n  TOP VALUE PICKS (score vs odds):")
    for p in value_picks[:4]:
        print(f"    * {p['horse']} ({p['race']}) @ {p['odds']}  Score:{p['score']}  Value:{p.get('value_rating','-')}")

    print(f"\n  BANKER OF THE FESTIVAL (highest raw score):")
    banker = max(all_picks, key=lambda x: x["score"])
    print(f"    ** {banker['horse']} in the {banker['race']} @ {banker['odds']} (Score:{banker['score']}  Value:{banker.get('value_rating','-')})")

    return all_picks


def run_full_analysis():
    """Master runner - full deep analysis"""
    print(f"\n{'#'*90}")
    print(f"  CHELTENHAM FESTIVAL DEEP ANALYSIS - 10 YEARS (2016-2025)")
    print(f"  Run date: {datetime.now().strftime('%d %B %Y %H:%M')}")
    print(f"  Preparing: Cheltenham Festival 2026 (10-13 March 2026)")
    print(f"{'#'*90}")

    analyze_going_weather()
    analyze_trainer_dominance()
    analyze_jockey_patterns()
    analyze_form_patterns()
    analyze_odds_patterns()
    analyze_age_ratings()
    picks = generate_2026_picks()

    print(f"\n{'#'*90}")
    print(f"  DEEP ANALYSIS COMPLETE")
    print(f"{'#'*90}")
    print("\n  BOTTOM LINE:")
    print("  1. Trust WILLIE MULLINS + PAUL TOWNEND more than any other signal")
    print("  2. PREVIOUS FESTIVAL WINNERS win again at 40%+ rate - back them")
    print("  3. SHORT PRICES at Cheltenham = Class. Don't oppose without reason")
    print("  4. IRISH form is real - respect it in every race")
    print("  5. Going: Good to Soft expected in 2026 (historical norm)")
    print("  6. AGE SWEET SPOT: Gold Cup 8-9, Hurdles 6-8, Novices 5-6")
    print("  7. FORM SIGNAL: Horse must have won a Grade 1 in prep season")
    print("  8. AVOID: Long absence (100+ days), poor form run, no Festival experience")
    print(f"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cheltenham Deep Analysis 2026")
    parser.add_argument("--picks-only", action="store_true", help="Show 2026 picks only")
    args = parser.parse_args()

    if args.picks_only:
        generate_2026_picks()
    else:
        run_full_analysis()

"""
barrys_config.py
Configuration for Barry's Cheltenham Bumper Competition 2026
"""

# Competition details
COMPETITION_NAME = "Barry's Cheltenham 2026"
PRIZE = 2500  # GBP
FESTIVAL_YEAR = 2026

# Cheltenham Festival dates
FESTIVAL_DAYS = {
    1: "2026-03-10",  # Champion Day (Tuesday)
    2: "2026-03-11",  # Ladies Day (Wednesday)
    3: "2026-03-12",  # St Patrick's Thursday
    4: "2026-03-13",  # Gold Cup Day (Friday)
}

# Team entries
ENTRIES = {
    "Surebet": {
        "strategy": "form",
        "description": "Form-first: best recent form, top trainer/jockey combos, class performer",
    },
    "Douglas Stunners": {
        "strategy": "festival_specialist",
        "description": "Festival specialist: Cheltenham course winners, festival-day trainers, progressive improvers",
    }
}

# Points system
POINTS = {
    1: 10,   # Winner
    2: 5,    # Second
    3: 3,    # Third
    0: 0     # Unplaced
}

# DynamoDB
DYNAMODB_TABLE = "BarrysCompetition"
DYNAMODB_REGION = "eu-west-1"

# Betfair
BETFAIR_MARKET_TYPE = "WIN"
BETFAIR_EVENT_TYPE_ID = "7"  # Horse Racing

# Scoring weights per strategy
# NOTE: Odds are irrelevant in this competition - 10pts for win regardless of price.
# Both strategies are purely about identifying the most likely winner/placer.
STRATEGY_WEIGHTS = {
    "form": {
        # Surebet: pure form - who is running best RIGHT NOW?
        "recent_form":         0.35,  # Last 3-5 runs (most important)
        "trainer_form":        0.20,  # Trainer current season win%
        "jockey_form":         0.20,  # Jockey festival/course record
        "course_distance":     0.15,  # Won over C&D before
        "class_level":         0.10,  # Grade 1 performer in Grade 1 = good sign
    },
    "festival_specialist": {
        # Douglas Stunners: who THRIVES at Cheltenham specifically?
        "festival_course_win": 0.35,  # Has won AT Cheltenham (massive edge)
        "trainer_chelt_record":0.25,  # Trainer Cheltenham win% (Mullins, Henderson etc)
        "progressive_form":    0.20,  # Improving run-on-run (unexposed horses)
        "recent_form":         0.12,  # Still matters
        "class_level":         0.08,  # Grade appropriateness
    }
}

# Festival races (28 total across 4 days)
# These are the scheduled races - will be confirmed via Betfair
FESTIVAL_RACES = {
    # DAY 1 - Champion Day (Tuesday 10 March)
    "day1_race1":  {"name": "Sky Bet Supreme Novices' Hurdle",       "day": 1, "time": "13:20", "grade": "Grade 1"},
    "day1_race2":  {"name": "Arkle Challenge Trophy Chase",          "day": 1, "time": "14:00", "grade": "Grade 1"},
    "day1_race3":  {"name": "Fred Winter Handicap Hurdle",           "day": 1, "time": "14:40", "grade": "Handicap"},
    "day1_race4":  {"name": "Ultima Handicap Chase",                 "day": 1, "time": "15:20", "grade": "Handicap"},
    "day1_race5":  {"name": "Unibet Champion Hurdle",                "day": 1, "time": "16:00", "grade": "Grade 1"},
    "day1_race6":  {"name": "Cheltenham Plate Chase",                "day": 1, "time": "16:40", "grade": "Handicap"},
    "day1_race7":  {"name": "National Hunt Chase",                   "day": 1, "time": "17:20", "grade": "Handicap"},

    # DAY 2 - Ladies Day (Wednesday 11 March)
    "day2_race1":  {"name": "Turner's Novices' Hurdle",              "day": 2, "time": "13:20", "grade": "Grade 1"},
    "day2_race2":  {"name": "Brown Advisory Novices' Chase",         "day": 2, "time": "14:00", "grade": "Grade 1"},
    "day2_race3":  {"name": "BetMGM Cup Hurdle",                     "day": 2, "time": "14:40", "grade": "Handicap"},
    "day2_race4":  {"name": "Glenfarclas Cross Country Chase",       "day": 2, "time": "15:20", "grade": "Grade 2"},
    "day2_race5":  {"name": "Queen Mother Champion Chase",           "day": 2, "time": "16:00", "grade": "Grade 1"},
    "day2_race6":  {"name": "Grand Annual Handicap Chase",           "day": 2, "time": "16:40", "grade": "Handicap"},
    "day2_race7":  {"name": "Champion Bumper",                       "day": 2, "time": "17:20", "grade": "NH Flat"},

    # DAY 3 - St Patrick's Thursday (Thursday 12 March)
    "day3_race1":  {"name": "Ryanair Mares' Novices' Hurdle",        "day": 3, "time": "13:20", "grade": "Grade 1"},
    "day3_race2":  {"name": "Jack Richards Novices' Chase",          "day": 3, "time": "14:00", "grade": "Grade 1"},
    "day3_race3":  {"name": "Close Brothers Mares' Hurdle",          "day": 3, "time": "14:40", "grade": "Grade 1"},
    "day3_race4":  {"name": "Paddy Power Stayers' Hurdle",           "day": 3, "time": "15:20", "grade": "Grade 1"},
    "day3_race5":  {"name": "Ryanair Chase",                         "day": 3, "time": "16:00", "grade": "Grade 1"},
    "day3_race6":  {"name": "Pertemps Handicap Hurdle",              "day": 3, "time": "16:40", "grade": "Handicap"},
    "day3_race7":  {"name": "Kim Muir Handicap Chase",               "day": 3, "time": "17:20", "grade": "Handicap"},

    # DAY 4 - Gold Cup Day (Friday 13 March)
    "day4_race1":  {"name": "JCB Triumph Hurdle",                    "day": 4, "time": "13:20", "grade": "Grade 1"},
    "day4_race2":  {"name": "County Handicap Hurdle",                "day": 4, "time": "14:00", "grade": "Handicap"},
    "day4_race3":  {"name": "Albert Bartlett Novices' Hurdle",       "day": 4, "time": "14:40", "grade": "Grade 1"},
    "day4_race4":  {"name": "Mrs Paddy Power Mares' Chase",          "day": 4, "time": "15:20", "grade": "Grade 2"},
    "day4_race5":  {"name": "Cheltenham Gold Cup",                   "day": 4, "time": "16:00", "grade": "Grade 1"},
    "day4_race6":  {"name": "St James's Place Hunters' Chase",       "day": 4, "time": "16:40", "grade": "Hunter Chase"},
    "day4_race7":  {"name": "Martin Pipe Handicap Hurdle",           "day": 4, "time": "17:20", "grade": "Handicap"},
}

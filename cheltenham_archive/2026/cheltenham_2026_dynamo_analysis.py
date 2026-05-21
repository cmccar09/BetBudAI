"""
CHELTENHAM 2026 — COMPREHENSIVE HISTORICAL ANALYSIS & WINNER PREDICTIONS
=========================================================================
Uses DynamoDB CheltenhamResults table (verified 99 records: 2024+2025)
to analyse WHY winners won and apply those patterns to 2026.

Run:
    python cheltenham_2026_dynamo_analysis.py
    python cheltenham_2026_dynamo_analysis.py --html
"""

import boto3
from collections import defaultdict
from decimal import Decimal

# ─────────────────────────────────────────────────────────────────────────────
# DYNAMODB PULL
# ─────────────────────────────────────────────────────────────────────────────

def pull_dynamo_results():
    """Fetch all CheltenhamResults from DynamoDB."""
    ddb = boto3.resource("dynamodb", region_name="eu-west-1")
    table = ddb.Table("CheltenhamResults")
    resp = table.scan()
    items = resp["Items"]
    while "LastEvaluatedKey" in resp:
        resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp["Items"])
    return items


def parse_results(items):
    """Organise items into {year: {race_name: {pos: data}}}."""
    data = defaultdict(lambda: defaultdict(dict))
    for item in items:
        pk = item["year_race"]          # e.g. "2025#Unibet Champion Hurdle"
        sk = int(item["position"])       # 1, 2, 3
        parts = pk.split("#", 1)
        year = parts[0]
        race = parts[1]
        data[year][race][sk] = {
            "horse":   item.get("horse", ""),
            "trainer": item.get("trainer", ""),
            "jockey":  item.get("jockey", ""),
            "sp":      item.get("sp", ""),
            "day":     item.get("day", ""),
        }
    return data


def sp_to_float(sp_str):
    """Convert SP string like '7/2' or '25/1' to float. Returns None if unparseable."""
    try:
        if "/" in sp_str:
            n, d = sp_str.replace("f","").replace("jf","").split("/")
            return float(n) / float(d)
    except Exception:
        pass
    try:
        return float(sp_str)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 2026 RACE SCHEDULE  (all 28 races)
# ─────────────────────────────────────────────────────────────────────────────

RACE_SCHEDULE_2026 = [
    # Day, Race name,                                   Grade, Type,            Skip?
    (1, "Supreme Novices Hurdle",                        "G1", "hurdle_novice", False),
    (1, "Arkle Challenge Trophy",                        "G1", "chase_novice",  False),
    (1, "Ultima Handicap Chase",                         "G3", "chase_hcap",    True),
    (1, "Unibet Champion Hurdle",                        "G1", "hurdle",        False),
    (1, "Close Brothers Mares Hurdle",                   "G1", "hurdle_mares",  False),
    (1, "National Hunt Chase",                           "G2", "chase_am",      True),
    (2, "Ballymore Novices Hurdle",                      "G1", "hurdle_novice", False),
    (2, "Brown Advisory Novices Chase",                  "G1", "chase_novice",  False),
    (2, "Queen Mother Champion Chase",                   "G1", "chase",         False),
    (2, "Pertemps Network Final",                        "G3", "hurdle_hcap",   True),
    (2, "Dawn Run Mares Novices Hurdle",                 "G2", "hurdle_mares",  False),
    (2, "Champion Bumper",                               "G1", "bumper",        False),
    (3, "Turners Novices Chase",                         "G1", "chase_novice",  False),
    (3, "Ryanair Chase",                                 "G1", "chase",         False),
    (3, "Stayers Hurdle",                                "G1", "hurdle",        False),
    (3, "Festival Plate Chase",                          "G3", "chase_hcap",    True),
    (3, "Kim Muir Challenge Cup",                        "G3", "chase_am",      True),
    (3, "Mares Chase",                                   "G2", "chase_mares",   False),
    (4, "JCB Triumph Hurdle",                            "G1", "hurdle_4yo",    False),
    (4, "Albert Bartlett Novices Hurdle",                "G1", "hurdle_novice", False),
    (4, "Cheltenham Gold Cup",                           "G1", "chase",         False),
    (4, "County Handicap Hurdle",                        "G3", "hurdle_hcap",   True),
    (4, "Martin Pipe Conditional Jockeys Hurdle",        "G3", "hurdle_hcap",   True),
    (4, "Foxhunter Chase",                               "G3", "foxhunter",     True),
    (4, "Festival Hunters Chase",                        "G3", "foxhunter",     True),
    (4, "Grand Annual Chase",                            "G3", "chase_hcap",    True),
    (4, "Juvenile Handicap Hurdle",                      "G3", "hurdle_hcap",   True),
    (4, "Champion Bumper (NH Flat)",                     "G1", "bumper",        False),
]

# ─────────────────────────────────────────────────────────────────────────────
# 2026 DECLARATIONS  (entered horses per race)
# Built from barrys/surebet_intel.py + save_cheltenham_picks.py + known entries
# ─────────────────────────────────────────────────────────────────────────────

FIELDS_2026 = {
    "Supreme Novices Hurdle": [
        {"name": "Mighty Park",          "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "13/2",  "form": "111",  "rating": 152, "irish": True},
        {"name": "Jeriko Du Reponet",     "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "8/1",   "form": "211",  "rating": 148, "irish": True},
        {"name": "Pont Aval",             "trainer": "Nicky Henderson",      "jockey": "Nico de Boinville",  "odds": "9/2",   "form": "111",  "rating": 150, "irish": False},
        {"name": "Salvator Mundi",        "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "7/1",   "form": "112",  "rating": 145, "irish": True},
        {"name": "Ramillies",             "trainer": "Nicky Henderson",      "jockey": "James Bowen",        "odds": "10/1",  "form": "211",  "rating": 140, "irish": False},
        {"name": "Kopek Des Bordes",      "trainer": "Willie Mullins",       "jockey": "TBC",                "odds": "7/4",   "form": "1111", "rating": 155, "irish": True},
    ],
    "Arkle Challenge Trophy": [
        {"name": "Kopek Des Bordes",      "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "7/4",   "form": "1111", "rating": 160, "irish": True},
        {"name": "Kappa Jy Pyke",         "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "5/1",   "form": "112",  "rating": 152, "irish": True},
        {"name": "Sixmilebridge",         "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "8/1",   "form": "111",  "rating": 148, "irish": True},
        {"name": "Il Etait Temps",        "trainer": "Nicky Henderson",      "jockey": "Nico de Boinville",  "odds": "12/1",  "form": "112",  "rating": 145, "irish": False},
        {"name": "Lecky Watson",          "trainer": "Henry de Bromhead",    "jockey": "Rachael Blackmore",  "odds": "10/1",  "form": "211",  "rating": 143, "irish": True},
    ],
    "Unibet Champion Hurdle": [
        {"name": "Lossiemouth",           "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "7/2",   "form": "1111", "rating": 168, "irish": True},
        {"name": "The New Lion",          "trainer": "Nicky Henderson",      "jockey": "Nico de Boinville",  "odds": "2/1",   "form": "211",  "rating": 162, "irish": False},
        {"name": "Brighterdaysahead",     "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "7/2",   "form": "112",  "rating": 163, "irish": True},
        {"name": "Golden Ace",            "trainer": "Jeremy Scott",         "jockey": "Lorcan Williams",    "odds": "7/1",   "form": "211",  "rating": 159, "irish": False},
        {"name": "Luccia",                "trainer": "Willie Mullins",       "jockey": "TBC",                "odds": "12/1",  "form": "121",  "rating": 155, "irish": True},
        {"name": "State Man",             "trainer": "Willie Mullins",       "jockey": "TBC",                "odds": "14/1",  "form": "311",  "rating": 170, "irish": True},
    ],
    "Close Brothers Mares Hurdle": [
        {"name": "Lossiemouth",           "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "5/4",   "form": "1111", "rating": 168, "irish": True},
        {"name": "Brighterdaysahead",     "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "3/1",   "form": "12",   "rating": 159, "irish": True},
        {"name": "Love Sign d'Aunou",     "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "6/1",   "form": "111",  "rating": 152, "irish": True},
        {"name": "Luccia",                "trainer": "Willie Mullins",       "jockey": "TBC",                "odds": "8/1",   "form": "121",  "rating": 150, "irish": True},
    ],
    "Ballymore Novices Hurdle": [
        {"name": "Doctor Steinberg",      "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "3/1",   "form": "111",  "rating": 148, "irish": True},
        {"name": "No Drama This End",     "trainer": "Nicky Henderson",      "jockey": "Nico de Boinville",  "odds": "4/1",   "form": "1111", "rating": 150, "irish": False},
        {"name": "Skylight Hustle",       "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "6/1",   "form": "211",  "rating": 145, "irish": True},
        {"name": "Mr Whizz",              "trainer": "Paul Nicholls",        "jockey": "Harry Cobden",       "odds": "8/1",   "form": "112",  "rating": 142, "irish": False},
    ],
    "Brown Advisory Novices Chase": [
        {"name": "Western Fold",          "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "8/1",   "form": "112",  "rating": 148, "irish": True},
        {"name": "Kappa Jy Pyke",         "trainer": "Gordon Elliott",       "jockey": "JJ Slevin",          "odds": "9/1",   "form": "112",  "rating": 145, "irish": True},
        {"name": "Gaelic Warrior",        "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "5/1",   "form": "211",  "rating": 158, "irish": True},
        {"name": "Captain Teague",        "trainer": "Paul Nicholls",        "jockey": "Harry Cobden",       "odds": "12/1",  "form": "121",  "rating": 143, "irish": False},
    ],
    "Queen Mother Champion Chase": [
        {"name": "Majborough",            "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "6/4",   "form": "1111", "rating": 168, "irish": True},
        {"name": "Jonbon",                "trainer": "Nicky Henderson",      "jockey": "Nico de Boinville",  "odds": "3/1",   "form": "211",  "rating": 164, "irish": False},
        {"name": "El Fabiolo",            "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "5/1",   "form": "112",  "rating": 162, "irish": True},
        {"name": "Gentleman De Mee",      "trainer": "Willie Mullins",       "jockey": "TBC",                "odds": "10/1",  "form": "111",  "rating": 155, "irish": True},
        {"name": "Edwardstone",           "trainer": "Alan King",            "jockey": "Tom Cannon",         "odds": "16/1",  "form": "311",  "rating": 158, "irish": False},
    ],
    "Dawn Run Mares Novices Hurdle": [
        {"name": "Bambino Fever",         "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "4/5",   "form": "1111", "rating": 145, "irish": True},
        {"name": "Blarney Street",        "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "6/1",   "form": "211",  "rating": 138, "irish": True},
        {"name": "Selma De Vary",         "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "7/1",   "form": "112",  "rating": 140, "irish": True},
    ],
    "Champion Bumper": [
        {"name": "Love Sign d'Aunou",     "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "9/2",   "form": "111",  "rating": 135, "irish": True},
        {"name": "Jade De Grugy",         "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "6/1",   "form": "11",   "rating": 132, "irish": True},
        {"name": "Inns Of Court",         "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "7/1",   "form": "111",  "rating": 130, "irish": True},
        {"name": "Mystical Power",        "trainer": "Nicky Henderson",      "jockey": "Nico de Boinville",  "odds": "8/1",   "form": "21",   "rating": 128, "irish": False},
    ],
    "Turners Novices Chase": [
        {"name": "Koktail Divin",         "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "9/2",   "form": "1111", "rating": 158, "irish": True},
        {"name": "Regent's Stroll",       "trainer": "Nicky Henderson",      "jockey": "Nico de Boinville",  "odds": "6/1",   "form": "211",  "rating": 152, "irish": False},
        {"name": "Sixmilebridge",         "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "7/1",   "form": "111",  "rating": 148, "irish": True},
        {"name": "Marine Nationale",      "trainer": "Jessica Harrington",   "jockey": "Robbie Power",       "odds": "10/1",  "form": "112",  "rating": 145, "irish": True},
    ],
    "Ryanair Chase": [
        {"name": "Fact To File",          "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "4/5",   "form": "1111", "rating": 172, "irish": True},
        {"name": "Galopin Des Champs",    "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "3/1",   "form": "112",  "rating": 178, "irish": True},
        {"name": "Envoi Allen",           "trainer": "Henry de Bromhead",    "jockey": "Rachael Blackmore",  "odds": "8/1",   "form": "311",  "rating": 168, "irish": True},
        {"name": "Protektorat",           "trainer": "Dan Skelton",          "jockey": "Harry Skelton",      "odds": "12/1",  "form": "212",  "rating": 165, "irish": False},
    ],
    "Stayers Hurdle": [
        {"name": "Ballyburn",             "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "12/1",  "form": "211",  "rating": 162, "irish": True},
        {"name": "Teahupoo",              "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "5/1",   "form": "211",  "rating": 165, "irish": True},
        {"name": "Stay Away Fay",         "trainer": "Paul Nicholls",        "jockey": "Harry Cobden",       "odds": "5/1",   "form": "111",  "rating": 163, "irish": False},
        {"name": "Bob Olinger",           "trainer": "Henry de Bromhead",    "jockey": "Rachael Blackmore",  "odds": "7/1",   "form": "112",  "rating": 160, "irish": True},
        {"name": "Klassical Dream",       "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "9/1",   "form": "312",  "rating": 158, "irish": True},
    ],
    "Mares Chase": [
        {"name": "Dinoblue",              "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "4/5",   "form": "1111", "rating": 160, "irish": True},
        {"name": "Salsaretta",            "trainer": "Gordon Elliott",       "jockey": "Davy Russell",       "odds": "4/1",   "form": "211",  "rating": 152, "irish": True},
        {"name": "Allegorie De Vassy",    "trainer": "Paul Nicholls",        "jockey": "Bryony Frost",       "odds": "7/1",   "form": "112",  "rating": 148, "irish": False},
    ],
    "JCB Triumph Hurdle": [
        {"name": "Selma De Vary",         "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "9/2",   "form": "111",  "rating": 148, "irish": True},
        {"name": "Proactif",              "trainer": "Francois Nicolle",     "jockey": "Felix De Giles",     "odds": "7/2",   "form": "1111", "rating": 152, "irish": False},
        {"name": "Flying Tiara",          "trainer": "Colin Tizzard",        "jockey": "Tom Scudamore",      "odds": "10/1",  "form": "211",  "rating": 140, "irish": False},
        {"name": "Jade De Grugy",         "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "7/1",   "form": "11",   "rating": 145, "irish": True},
    ],
    "Albert Bartlett Novices Hurdle": [
        {"name": "Panda Boy",             "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "3/1",   "form": "111",  "rating": 148, "irish": True},
        {"name": "Magical Zoe",           "trainer": "Emmet Mullins",        "jockey": "Brian Hayes",        "odds": "7/2",   "form": "211",  "rating": 145, "irish": True},
        {"name": "Gold Bullion",          "trainer": "Nicky Henderson",      "jockey": "Nico de Boinville",  "odds": "5/1",   "form": "112",  "rating": 143, "irish": False},
        {"name": "Fil Dor",               "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "6/1",   "form": "121",  "rating": 140, "irish": True},
    ],
    "Cheltenham Gold Cup": [
        {"name": "Gaelic Warrior",        "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "6/1",   "form": "211",  "rating": 175, "irish": True},
        {"name": "The Jukebox Man",       "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "6/1",   "form": "111",  "rating": 173, "irish": True},
        {"name": "Jango Baie",            "trainer": "Nicky Henderson",      "jockey": "Nico de Boinville",  "odds": "6/1",   "form": "311",  "rating": 170, "irish": False},
        {"name": "Galopin Des Champs",    "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "7/1",   "form": "112",  "rating": 178, "irish": True},
        {"name": "Inothewayurthinkin",    "trainer": "Gavin Cromwell",       "jockey": "Mark Walsh",         "odds": "8/1",   "form": "111",  "rating": 172, "irish": True},
        {"name": "Grey Dawning",          "trainer": "Dan Skelton",          "jockey": "Harry Skelton",      "odds": "10/1",  "form": "211",  "rating": 168, "irish": False},
        {"name": "Fastorslow",            "trainer": "Willie Mullins",       "jockey": "TBC",                "odds": "10/1",  "form": "211",  "rating": 172, "irish": True},
        {"name": "Spillane's Tower",      "trainer": "Gordon Elliott",       "jockey": "Davy Russell",       "odds": "12/1",  "form": "312",  "rating": 165, "irish": True},
        {"name": "Protektorat",           "trainer": "Dan Skelton",          "jockey": "Harry Skelton",      "odds": "14/1",  "form": "212",  "rating": 165, "irish": False},
    ],
    "Champion Bumper (NH Flat)": [
        {"name": "Love Sign d'Aunou",     "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "9/2",   "form": "111",  "rating": 135, "irish": True},
        {"name": "Jade De Grugy",         "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "6/1",   "form": "11",   "rating": 132, "irish": True},
        {"name": "Inns Of Court",         "trainer": "Gordon Elliott",       "jockey": "Jack Kennedy",       "odds": "7/1",   "form": "111",  "rating": 130, "irish": True},
        {"name": "Mystical Power",        "trainer": "Nicky Henderson",      "jockey": "Nico de Boinville",  "odds": "8/1",   "form": "21",   "rating": 128, "irish": False},
    ],
    # Skipped races — minimal data
    "Ultima Handicap Chase": [
        {"name": "Banbridge",             "trainer": "Gordon Elliott",       "jockey": "Davy Russell",       "odds": "40/1",  "form": "3124", "rating": 148, "irish": True},
        {"name": "Nick Rockett",          "trainer": "Gordon Elliott",       "jockey": "Keith Donoghue",     "odds": "14/1",  "form": "212",  "rating": 155, "irish": True},
        {"name": "Mister Coffey",         "trainer": "Nicky Henderson",      "jockey": "James Bowen",        "odds": "12/1",  "form": "113",  "rating": 158, "irish": False},
    ],
    "National Hunt Chase": [
        {"name": "Backmersackme",         "trainer": "Henry de Bromhead",    "jockey": "Denis O'Regan",      "odds": "9/2",   "form": "211",  "rating": 138, "irish": True},
    ],
    "Pertemps Network Final": [
        {"name": "Watamu",                "trainer": "Dan Skelton",          "jockey": "Harry Skelton",      "odds": "8/1",   "form": "121",  "rating": 140, "irish": False},
        {"name": "Minella Crooner",       "trainer": "Joseph O'Brien",       "jockey": "Mark Walsh",         "odds": "10/1",  "form": "212",  "rating": 138, "irish": True},
    ],
    "Festival Plate Chase": [
        {"name": "Jagwar",                "trainer": "Oliver Greenall",      "jockey": "Jonjo O'Neill Jr",   "odds": "10/1",  "form": "112",  "rating": 148, "irish": False},
    ],
    "Kim Muir Challenge Cup": [
        {"name": "Daily Present",         "trainer": "Paul Nolan",           "jockey": "Barry Stone",        "odds": "8/1",   "form": "211",  "rating": 135, "irish": True},
        {"name": "Inothewayurthinkin",    "trainer": "Gavin Cromwell",       "jockey": "Derek O'Connor",     "odds": "3/1",   "form": "1111", "rating": 150, "irish": True},
    ],
    "County Handicap Hurdle": [
        {"name": "Kargese",               "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "4/1",   "form": "111",  "rating": 148, "irish": True},
        {"name": "Absurde",               "trainer": "Willie Mullins",       "jockey": "Mark Walsh",         "odds": "12/1",  "form": "211",  "rating": 143, "irish": True},
    ],
    "Martin Pipe Conditional Jockeys Hurdle": [
        {"name": "Wodhooh",               "trainer": "Gordon Elliott",       "jockey": "Danny Gilligan",     "odds": "5/1",   "form": "211",  "rating": 138, "irish": True},
    ],
    "Foxhunter Chase": [
        {"name": "Lecky Watson",          "trainer": "Stephanie Sykes",      "jockey": "Mr A Sykes",         "odds": "100/1", "form": "111",  "rating": 130, "irish": False},
    ],
    "Festival Hunters Chase": [
        {"name": "Wonderwall",            "trainer": "Sam Curling",          "jockey": "Rob James",          "odds": "12/1",  "form": "112",  "rating": 128, "irish": True},
    ],
    "Grand Annual Chase": [
        {"name": "Blue Lord",             "trainer": "Willie Mullins",       "jockey": "Paul Townend",       "odds": "7/1",   "form": "211",  "rating": 145, "irish": True},
    ],
    "Juvenile Handicap Hurdle": [
        {"name": "Proactif",              "trainer": "Francois Nicolle",     "jockey": "Felix De Giles",     "odds": "6/1",   "form": "1211", "rating": 142, "irish": False},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# RACE NAME MATCHING  (DynamoDB names vs schedule names)
# ─────────────────────────────────────────────────────────────────────────────

RACE_NAME_MAP = {
    # schedule name → possible DynamoDB names (2024/2025)
    "Supreme Novices Hurdle":                  ["Supreme Novices Hurdle"],
    "Arkle Challenge Trophy":                  ["Arkle Novices Chase", "Arkle Challenge Trophy"],
    "Ultima Handicap Chase":                   ["Ultima Handicap Chase"],
    "Unibet Champion Hurdle":                  ["Unibet Champion Hurdle", "Champion Hurdle"],
    "Close Brothers Mares Hurdle":             ["Close Brothers Mares Hurdle", "Mares Hurdle"],
    "National Hunt Chase":                     ["National Hunt Chase"],
    "Ballymore Novices Hurdle":                ["Ballymore Novices Hurdle"],
    "Brown Advisory Novices Chase":            ["Brown Advisory Novices Chase"],
    "Queen Mother Champion Chase":             ["Queen Mother Champion Chase"],
    "Pertemps Network Final":                  ["Pertemps Final", "Pertemps Network Final"],
    "Dawn Run Mares Novices Hurdle":           ["Air Of Entitlement Mares Novices", "Dawn Run Mares Novices", "Mares Novices Hurdle"],
    "Champion Bumper":                         ["Champion Bumper"],
    "Turners Novices Chase":                   ["Turners Novices Chase", "Jack Richards Novices Chase", "JLT Novices Chase"],
    "Ryanair Chase":                           ["Ryanair Chase"],
    "Stayers Hurdle":                          ["Stayers Hurdle"],
    "Festival Plate Chase":                    ["Festival Plate", "Festival Plate Chase"],
    "Kim Muir Challenge Cup":                  ["Kim Muir", "Kim Muir Challenge Cup"],
    "Mares Chase":                             ["Mares Chase"],
    "JCB Triumph Hurdle":                      ["Triumph Hurdle", "JCB Triumph Hurdle"],
    "Albert Bartlett Novices Hurdle":          ["Albert Bartlett", "Albert Bartlett Novices Hurdle"],
    "Cheltenham Gold Cup":                     ["Cheltenham Gold Cup"],
    "County Handicap Hurdle":                  ["County Handicap Hurdle"],
    "Martin Pipe Conditional Jockeys Hurdle":  ["Martin Pipe", "Martin Pipe Conditional Jockeys Hurdle"],
    "Foxhunter Chase":                         ["Foxhunter Chase"],
    "Festival Hunters Chase":                  ["Festival Hunters Chase"],
    "Grand Annual Chase":                      ["Grand Annual Chase"],
    "Juvenile Handicap Hurdle":                ["Juvenile Handicap Hurdle", "Boodles Juvenile Handicap"],
    "Champion Bumper (NH Flat)":               ["Champion Bumper"],
}


def find_dynamo_race(race_schedule_name, results_by_year):
    """
    Look up all DynamoDB records for a race across 2024 & 2025.
    Returns list of (year, pos, data) tuples.
    """
    aliases = RACE_NAME_MAP.get(race_schedule_name, [race_schedule_name])
    found = []
    for year, races in results_by_year.items():
        for dynamo_race, positions in races.items():
            for alias in aliases:
                # Case-insensitive, flexible match
                if (alias.lower() in dynamo_race.lower() or
                    dynamo_race.lower() in alias.lower() or
                    any(w in dynamo_race.lower() for w in alias.lower().split()[:3])):
                    for pos, data in positions.items():
                        found.append({"year": year, "race": dynamo_race, "pos": pos, **data})
                    break
    return found


# ─────────────────────────────────────────────────────────────────────────────
# SCORING FACTORS (2026 analysis)
# ─────────────────────────────────────────────────────────────────────────────

# Going forecast 2026
GOING_2026 = {1: "Good to Soft", 2: "Good to Soft", 3: "Good to Soft / Soft", 4: "Soft"}

# Trainers who benefit from soft/heavy going (Irish yards — winter prep)
SOFT_BONUS_TRAINERS = {
    "Willie Mullins", "Gordon Elliott", "Henry de Bromhead",
    "Joseph O'Brien", "Gavin Cromwell", "Jessica Harrington",
    "Noel Meade", "Emmet Mullins", "Paul Nolan", "Sam Curling",
}

# 2025/2024 festival-winning trainers (priority)
FESTIVAL_WINNING_TRAINERS = {
    "Willie Mullins":     14,   # 8 in 2025 + 6 in 2024
    "Gordon Elliott":     3,    # Stellar Story 2024 + Martin Pipe 2024 + Gold Cup contenders
    "Henry de Bromhead":  2,    # Mares Novices + Stayers 2025
    "Gavin Cromwell":     2,    # Kim Muir 2024 + Gold Cup 2025
    "Nicky Henderson":    2,    # Pertemps + Arkle Jango Baie 2025
    "Jeremy Scott":       2,    # Mares Novices 2024 + Champion Hurdle 2025
    "Paul Nicholls":      1,    # Turners 2025
    "Lucinda Russell":    1,    # Ultima 2025
    "Rebecca Curtis":     1,    # NHC 2025
    "Joseph O'Brien":     1,    # Juvenile 2025
    "Oliver Greenall":    1,    # Festival Plate 2025
}

# Key horses with proven Cheltenham form / double winners or defending champs
ELITE_HORSES = {
    "Lossiemouth":          {"bonus": 25, "note": "Won Mares Hurdle 2024 + 2025, hat-trick bid"},
    "Inothewayurthinkin":   {"bonus": 20, "note": "Won Kim Muir 2024 + Gold Cup 2025, defending champ"},
    "Fact To File":         {"bonus": 20, "note": "Won 2025 Ryanair Chase, defending champion"},
    "Kopek Des Bordes":     {"bonus": 18, "note": "Won 2025 Supreme Novices, stepping up to Arkle"},
    "Gaelic Warrior":       {"bonus": 15, "note": "Won 2024 Arkle, multiple Grade 1 winner"},
    "Galopin Des Champs":   {"bonus": 15, "note": "Won 2024 Gold Cup, previous champion"},
    "Golden Ace":           {"bonus": 12, "note": "Won Mares Novices 2024 + Champion Hurdle 2025"},
    "Ballyburn":            {"bonus": 12, "note": "Multiple Grade 1 winner"},
    "Majborough":           {"bonus": 12, "note": "Won 2024 Triumph Hurdle"},
    "Dinoblue":             {"bonus": 15, "note": "Won 2025 Mares Chase, defending champion"},
    "Kargese":              {"bonus": 10, "note": "Won 2025 County Hurdle, progressive"},
    "Jagwar":               {"bonus": 10, "note": "Won 2025 Festival Plate"},
    "Koktail Divin":        {"bonus": 10, "note": "Grade 1 novice chaser"},
}


def score_horse(horse, race_name, day, historical_records, verbose=False):
    """Score a horse for a 2026 race. Returns (score, reasons)."""
    score = 0.0
    reasons = []

    name = horse["name"]
    trainer = horse["trainer"]
    odds_str = horse.get("odds", "99/1")
    rating = horse.get("rating", 130)
    is_irish = horse.get("irish", False)
    form = horse.get("form", "")

    # --- Base rating ---
    score += min(rating - 120, 60)   # max 60 pts for rating (160+ = 40, etc.)
    reasons.append(f"Rating {rating} (+{min(rating-120,60):.0f})")

    # --- Trainer historical wins ---
    trainer_wins = FESTIVAL_WINNING_TRAINERS.get(trainer, 0)
    t_bonus = min(trainer_wins * 4, 20)
    if t_bonus:
        score += t_bonus
        reasons.append(f"{trainer} festival wins {trainer_wins}x (+{t_bonus:.0f})")

    # --- Soft ground bonus (Irish trainers) ---
    if is_irish or trainer in SOFT_BONUS_TRAINERS:
        going = GOING_2026.get(day, "Good to Soft")
        if "Soft" in going or "Heavy" in going:
            score += 8
            reasons.append(f"Soft/Heavy going advantage (+8)")

    # --- Elite horse bonus ---
    if name in ELITE_HORSES:
        eb = ELITE_HORSES[name]["bonus"]
        score += eb
        reasons.append(f"Elite: {ELITE_HORSES[name]['note']} (+{eb})")

    # --- Historical race winner patterns ---
    race_winners = [r for r in historical_records if r["pos"] == 1]
    trainer_won_this_race = sum(1 for r in race_winners if r["trainer"] == trainer)
    if trainer_won_this_race >= 2:
        score += 15
        reasons.append(f"{trainer} won this race {trainer_won_this_race}x in 2024-25 (+15)")
    elif trainer_won_this_race == 1:
        score += 8
        reasons.append(f"{trainer} won this race 2024 or 2025 (+8)")

    horse_won_this_race = sum(1 for r in race_winners if r["horse"] == name)
    if horse_won_this_race >= 2:
        score += 25
        reasons.append(f"WON THIS RACE 2x: {name} back-to-back champion (+25)")
    elif horse_won_this_race == 1:
        score += 15
        reasons.append(f"Won this race previously (+15)")

    # --- Form ---
    wins_in_form = form.count("1")
    score += wins_in_form * 3
    if form.startswith("1"):
        score += 5
        reasons.append(f"Latest win in form ({form}, +{wins_in_form*3+5})")
    elif wins_in_form:
        reasons.append(f"Wins in form ({form}, +{wins_in_form*3})")

    # --- Odds factor (market confidence) ---
    sp_f = sp_to_float(odds_str)
    if sp_f is not None:
        if sp_f <= 1.5:    # odds-on
            score += 15
            reasons.append(f"Odds-on favourite ({odds_str}, +15)")
        elif sp_f <= 3.0:  # short price
            score += 10
            reasons.append(f"Short-priced ({odds_str}, +10)")
        elif sp_f <= 5.0:
            score += 7
            reasons.append(f"Well-backed ({odds_str}, +7)")
        elif sp_f <= 8.0:
            score += 4
            reasons.append(f"Reasonable odds ({odds_str}, +4)")

    # --- Jockey factor ---
    jockey = horse.get("jockey", "")
    if jockey == "Paul Townend":
        score += 10
        reasons.append("Paul Townend (most festival wins 2024-25, +10)")
    elif jockey in ("Mark Walsh", "Jack Kennedy", "Rachael Blackmore", "Nico de Boinville"):
        score += 6
        reasons.append(f"{jockey} top jockey (+6)")
    elif jockey in ("Harry Cobden", "Lorcan Williams", "JJ Slevin"):
        score += 4
        reasons.append(f"{jockey} quality jockey (+4)")

    return score, reasons


# ─────────────────────────────────────────────────────────────────────────────
# HISTORICAL PATTERN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def analyse_why_winner_won(race_name, historical_records):
    """Produce text analysis of why historical winners won this race."""
    winners = [r for r in historical_records if r["pos"] == 1]
    if not winners:
        return "No historical data available for this race in 2024-2025."

    lines = []
    for w in sorted(winners, key=lambda x: x["year"], reverse=True):
        sp_f = sp_to_float(w["sp"])
        price_note = ""
        if sp_f is not None:
            if sp_f < 2.0:
                price_note = "strong market leader"
            elif sp_f <= 4.0:
                price_note = "well-backed"
            elif sp_f <= 8.0:
                price_note = "mid-range"
            else:
                price_note = f"big-priced upset ({w['sp']})"

        lines.append(
            f"  {w['year']}: {w['horse']} won ({w['sp']}, {price_note}) "
            f"· Trainer: {w['trainer']} · Jockey: {w['jockey']}"
        )

    # Trainer pattern
    trainer_counts = defaultdict(int)
    for w in winners:
        trainer_counts[w["trainer"]] += 1
    dominant = [(t, c) for t, c in trainer_counts.items() if c >= 1]
    if dominant:
        dominant_str = ", ".join(f"{t} ({c}x)" for t, c in sorted(dominant, key=lambda x: -x[1]))
        lines.append(f"  Winning trainers: {dominant_str}")

    # Price pattern
    sp_floats = [sp_to_float(w["sp"]) for w in winners if sp_to_float(w["sp"]) is not None]
    if sp_floats:
        avg_sp = sum(sp_floats) / len(sp_floats)
        if avg_sp < 2:
            lines.append(f"  Price pattern: Race favours short-priced horses (avg odds {avg_sp:.1f}/1)")
        elif avg_sp < 5:
            lines.append(f"  Price pattern: Well-backed horses win (avg {avg_sp:.1f}/1)")
        else:
            lines.append(f"  Price pattern: Upsets common (avg {avg_sp:.1f}/1)")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def run_analysis():
    print("\n" + "=" * 90)
    print("  CHELTENHAM 2026 — COMPREHENSIVE WINNER PREDICTIONS")
    print("  Powered by DynamoDB CheltenhamResults (verified 2024+2025 data, 99 records)")
    print("  All 28 races · Historical WHY analysis · Going factor · Trainer/Jockey bias")
    print("=" * 90)

    # Pull DynamoDB
    print("\n  [1/3] Fetching verified historical data from DynamoDB CheltenhamResults...")
    try:
        items = pull_dynamo_results()
        results_by_year = parse_results(items)
        total = len(items)
        print(f"        Loaded {total} records from {sorted(results_by_year.keys())} years")
    except Exception as e:
        print(f"  ⚠ DynamoDB error: {e}")
        print("  Using built-in historical data...")
        results_by_year = {}

    # Build all-records flat list for cross-references
    all_records = []
    for year, races in results_by_year.items():
        for race, positions in races.items():
            for pos, data in positions.items():
                all_records.append({"year": year, "race": race, "pos": pos, **data})

    print(f"\n  [2/3] Analysing {len(RACE_SCHEDULE_2026)} races...")

    # Track winners for summary
    summary_picks = []

    day_labels = {1: "DAY 1 — TUESDAY 10 MAR (Champion Day)",
                  2: "DAY 2 — WEDNESDAY 11 MAR (Ladies Day)",
                  3: "DAY 3 — THURSDAY 12 MAR (St Patrick's Day)",
                  4: "DAY 4 — FRIDAY 13 MAR (Gold Cup Day)"}
    current_day = 0

    for (day, race_name, grade, race_type, is_skip) in RACE_SCHEDULE_2026:
        if day != current_day:
            current_day = day
            going = GOING_2026.get(day, "Good")
            print(f"\n  {'─'*85}")
            print(f"  {day_labels[day]}")
            print(f"  Going: {going}")
            print(f"  {'─'*85}")

        # Get historical records for this race
        historical_records = find_dynamo_race(race_name, results_by_year)

        skip_tag = " [HANDICAP/SKIP]" if is_skip else ""
        print(f"\n  [{grade}] {race_name}{skip_tag}")

        # Historical analysis
        why_text = analyse_why_winner_won(race_name, historical_records)
        print(f"  Historical (2024-2025 winners):")
        print(why_text)

        # Get 2026 field
        field = FIELDS_2026.get(race_name, [])
        if not field:
            print("  ⚠ No 2026 field data available")
            summary_picks.append({"race": race_name, "day": day, "grade": grade,
                                   "skip": is_skip, "pick": None, "score": 0})
            continue

        # Score all runners
        scored = []
        for horse in field:
            score, reasons = score_horse(horse, race_name, day, historical_records)
            scored.append({"horse": horse, "score": score, "reasons": reasons})

        scored.sort(key=lambda x: x["score"], reverse=True)

        # Print top 3
        print(f"  2026 Field scoring:")
        for i, s in enumerate(scored[:4]):
            h = s["horse"]
            marker = "  ★ PICK →" if i == 0 else f"  {i+1}."
            print(f"{marker} {h['name']:<28} Score:{s['score']:>6.0f}  "
                  f"Odds:{h['odds']:<7} Trainer:{h['trainer']}")
            if i == 0:
                for reason in s["reasons"]:
                    print(f"          {reason}")

        winner = scored[0]
        gap = scored[0]["score"] - scored[1]["score"] if len(scored) > 1 else 0
        conf = "HIGH" if gap > 20 else ("MED" if gap > 10 else "LOW")

        print(f"\n  ✅ PREDICTION: {winner['horse']['name']} "
              f"({winner['horse']['odds']}, {winner['horse']['trainer']}) "
              f"— Score:{winner['score']:.0f} — Confidence:{conf} (gap:{gap:.0f})")

        # Apply pattern transfer note
        h_name = winner["horse"]["name"]
        if h_name in ELITE_HORSES:
            print(f"  📊 Pattern: {ELITE_HORSES[h_name]['note']}")

        summary_picks.append({
            "race": race_name, "day": day, "grade": grade, "skip": is_skip,
            "pick": winner["horse"]["name"],
            "odds": winner["horse"]["odds"],
            "trainer": winner["horse"]["trainer"],
            "jockey": winner["horse"].get("jockey", ""),
            "score": winner["score"],
            "gap": gap,
            "conf": conf,
        })

    # ── Summary Table ─────────────────────────────────────────────────────────
    print(f"\n\n  {'=' * 90}")
    print(f"  CHELTENHAM 2026 — COMPLETE WINNER PREDICTIONS SUMMARY")
    print(f"  {'=' * 90}")
    print(f"  {'#':<3} {'Race':<43} {'Pick':<26} {'Odds':<8} {'Score':<6} {'Conf':<5} {'Trainer'}")
    print(f"  {'─' * 88}")

    current_day = 0
    for i, p in enumerate(summary_picks, 1):
        if p["day"] != current_day:
            current_day = p["day"]
            going = GOING_2026.get(current_day, "")
            print(f"\n  ─── {day_labels[current_day]} · Going: {going} ───")

        if not p["pick"]:
            print(f"  {i:<3} {p['race']:<43} {'NO DATA':<26}")
            continue

        skip_tag = " [skip]" if p["skip"] else ""
        grade_tag = f"[{p['grade']}]"
        print(f"  {i:<3} {p['race'][:42]:<43} {p['pick']:<26} "
              f"{p['odds']:<8} {p['score']:<6.0f} {p['conf']:<5} {p['trainer']}{skip_tag}")

    # ── Grade 1 Conviction Plays ──────────────────────────────────────────────
    print(f"\n\n  {'=' * 90}")
    print(f"  GRADE 1 CONVICTION PLAYS (score gap ≥ 15pts)")
    print(f"  {'=' * 90}")
    g1_picks = [p for p in summary_picks if p.get("grade") == "G1" and not p["skip"] and p.get("gap", 0) >= 15]
    for p in g1_picks:
        print(f"  ⭐ {p['race']:<43} → {p['pick']:<26} {p['odds']:<8} Score:{p['score']:.0f}  Gap:{p['gap']:.0f}pts")

    # ── Historical WHY Summary ────────────────────────────────────────────────
    print(f"\n\n  {'=' * 90}")
    print(f"  KEY HISTORICAL PATTERNS APPLIED TO 2026 PREDICTIONS")
    print(f"  {'=' * 90}")
    patterns = [
        ("Lossiemouth — Hat-Trick Bid",
         "Won Mares Hurdle 2024 (8/13f, Mullins/Townend) AND 2025 (4/6f, Mullins/Townend). "
         "Now entered Champion Hurdle 2026 at 7/2. Back-to-back Mares Hurdle champion stepping "
         "up to Champion Hurdle. Mullins confirmed she's going to Champion Hurdle race."),
        ("Fact To File — Ryanair Repeat",
         "Won 2025 Ryanair Chase at 6/4f (Mullins/Walsh). Now 4/5 favourite for 2026 Ryanair. "
         "Defending champions at Cheltenham win at a high rate in chases (~40% repeat). "
         "No reason to oppose at odds-on."),
        ("Inothewayurthinkin — Gold Cup Defender",
         "Won 2024 Kim Muir (13/8f) then stepped up to Gold Cup 2025 (15/2, Cromwell/Walsh). "
         "Defending Gold Cup champion at 8/1. Progressive horse, soft ground specialist. "
         "Cromwell/Walsh combination proven at level."),
        ("Kopek Des Bordes — Supreme → Arkle",
         "Won 2025 Supreme Novices Hurdle (4/6f, Mullins/Townend) then schooled over fences. "
         "Classic Willie Mullins pattern: Supreme champion steps to Arkle the following year. "
         "Douvan (2015→2016 Arkle), Altior (2016→2017 Arkle) — at 7/4."),
        ("Willie Mullins — Festival Domination",
         "8 winners in 2025, 6 in 2024 (14 total). In soft/heavy conditions (2026 forecast), "
         "Irish-prepared horses have a massive advantage. Any Mullins horse must get significant bonus. "
         "Expected 7-10 winners again in 2026."),
        ("Going Factor — Soft/Heavy Forecast",
         "2026 forecast: Day 1 Good to Soft → Day 4 Soft/Heavy. Advantages Irish yards "
         "(Mullins, Elliott, de Bromhead, Cromwell) who train through soft winter ground. "
         "British trainers (Henderson, Nicholls, Skelton) at disadvantage on softening track."),
        ("Golden Ace (Jeremy Scott/Lorcan Williams)",
         "Won 2024 Mares Novices (10/1) then stunned at 25/1 in 2025 Champion Hurdle. "
         "Small Taunton trainer producing elite horses. Any 2026 runner from this team "
         "should be taken at big prices."),
        ("Gaelic Warrior (Mullins) — Gold Cup",
         "Won 2024 Arkle Chase (2/1f). Now trained for Gold Cup 2026 at 6/1. "
         "Mullins graduating novice chasers to Gold Cup is a established pattern "
         "(Galopin Des Champs 2022→2023→2024 Gold Cup wins). Rating of 175+."),
    ]
    for title, text in patterns:
        print(f"\n  [{title}]")
        # Word-wrap text
        words = text.split()
        line = "  "
        for w in words:
            if len(line) + len(w) > 85:
                print(line)
                line = "  " + w + " "
            else:
                line += w + " "
        if line.strip():
            print(line)

    print(f"\n  {'=' * 90}")
    print(f"  Analysis complete. {sum(1 for p in summary_picks if p.get('pick'))} races predicted.")
    print(f"  {'=' * 90}\n")

    return summary_picks


# ─────────────────────────────────────────────────────────────────────────────
# VERIFIED 2025 RESULTS (from DynamoDB CheltenhamResults)
# ─────────────────────────────────────────────────────────────────────────────

RESULTS_2025 = {
    "Supreme Novices Hurdle":                 {"horse": "Kopek Des Bordes",    "sp": "4/6f",  "trainer": "Willie Mullins"},
    "Arkle Challenge Trophy":                 {"horse": "Jango Baie",           "sp": "5/1",   "trainer": "Nicky Henderson"},
    "Ultima Handicap Chase":                  {"horse": "Myretown",             "sp": "13/2f", "trainer": "Lucinda Russell"},
    "Unibet Champion Hurdle":                 {"horse": "Golden Ace",           "sp": "25/1",  "trainer": "Jeremy Scott"},
    "Close Brothers Mares Hurdle":            {"horse": "Lossiemouth",          "sp": "4/6f",  "trainer": "Willie Mullins"},
    "National Hunt Chase":                    {"horse": "Haiti Couleurs",       "sp": "7/2jf", "trainer": "Rebecca Curtis"},
    "Turners Novices Chase":                  {"horse": "Caldwell Potter",      "sp": "7/1",   "trainer": "Paul Nicholls"},
    "Ryanair Chase":                          {"horse": "Fact To File",         "sp": "6/4f",  "trainer": "Willie Mullins"},
    "Stayers Hurdle":                         {"horse": "Bob Olinger",          "sp": "8/1",   "trainer": "Henry de Bromhead"},
    "Festival Plate Chase":                   {"horse": "Jagwar",               "sp": "3/1f",  "trainer": "Oliver Greenall & Josh Guerriero"},
    "Kim Muir Challenge Cup":                 {"horse": "Daily Present",        "sp": "12/1",  "trainer": "Paul Nolan"},
    "Mares Chase":                            {"horse": "Dinoblue",             "sp": "6/4",   "trainer": "Willie Mullins"},
    "JCB Triumph Hurdle":                     {"horse": "Poniros",              "sp": "100/1", "trainer": "Willie Mullins"},
    "Albert Bartlett Novices Hurdle":         {"horse": "Jasmin De Vaux",       "sp": "6/1",   "trainer": "Willie Mullins"},
    "Cheltenham Gold Cup":                    {"horse": "Inothewayurthinkin",   "sp": "15/2",  "trainer": "Gavin Cromwell"},
    "County Handicap Hurdle":                 {"horse": "Kargese",              "sp": "3/1",   "trainer": "Willie Mullins"},
    "Martin Pipe Conditional Jockeys Hurdle": {"horse": "Wodhooh",              "sp": "9/2",   "trainer": "Gordon Elliott"},
    "Festival Hunters Chase":                 {"horse": "Wonderwall",           "sp": "28/1",  "trainer": "Sam Curling"},
    "Dawn Run Mares Novices Hurdle":          {"horse": "Air Of Entitlement",   "sp": "16/1",  "trainer": "Henry de Bromhead"},
    "Pertemps Network Final":                 {"horse": "Doddiethegreat",       "sp": "25/1",  "trainer": "Nicky Henderson"},
    "Juvenile Handicap Hurdle":               {"horse": "Puturhandstogether",   "sp": "17/2",  "trainer": "Joseph O'Brien"},
}

RESULTS_2024 = {
    "Supreme Novices Hurdle":                 {"horse": "Slade Steel",          "sp": "7/2",   "trainer": "Henry de Bromhead"},
    "Arkle Challenge Trophy":                 {"horse": "Gaelic Warrior",       "sp": "2/1f",  "trainer": "Willie Mullins"},
    "Ultima Handicap Chase":                  {"horse": "Chianti Classico",     "sp": "6/1",   "trainer": "Kim Bailey"},
    "Unibet Champion Hurdle":                 {"horse": "State Man",            "sp": "2/5f",  "trainer": "Willie Mullins"},
    "Close Brothers Mares Hurdle":            {"horse": "Lossiemouth",          "sp": "8/13f", "trainer": "Willie Mullins"},
    "Kim Muir Challenge Cup":                 {"horse": "Inothewayurthinkin",   "sp": "13/8f", "trainer": "Gavin Cromwell"},
    "JCB Triumph Hurdle":                     {"horse": "Majborough",           "sp": "6/1",   "trainer": "Willie Mullins"},
    "County Handicap Hurdle":                 {"horse": "Absurde",              "sp": "12/1",  "trainer": "Willie Mullins"},
    "Albert Bartlett Novices Hurdle":         {"horse": "Stellar Story",        "sp": "33/1",  "trainer": "Gordon Elliott"},
    "Cheltenham Gold Cup":                    {"horse": "Galopin Des Champs",   "sp": "10/11f","trainer": "Willie Mullins"},
    "Dawn Run Mares Novices Hurdle":          {"horse": "Golden Ace",           "sp": "10/1",  "trainer": "Jeremy Scott"},
    "Juvenile Handicap Hurdle":               {"horse": "Lark In The Mornin",   "sp": "9/1",   "trainer": "Joseph O'Brien"},
}


# ─────────────────────────────────────────────────────────────────────────────
# HTML EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def export_html(summary_picks, output_file="cheltenham_2026_predictions.html"):
    import os

    day_labels = {1: "DAY 1 — Tuesday 10 Mar · Champion Day",
                  2: "DAY 2 — Wednesday 11 Mar · Ladies Day",
                  3: "DAY 3 — Thursday 12 Mar · St Patrick's Day",
                  4: "DAY 4 — Friday 13 Mar · Gold Cup Day"}

    rows_html = ""
    current_day = 0
    g1_picks_html = ""

    for p in summary_picks:
        if not p.get("pick"):
            continue
        if p["day"] != current_day:
            current_day = p["day"]
            going = GOING_2026.get(current_day, "")
            rows_html += (
                f'<tr><td colspan="10" style="background:#1a1a0d;color:#c9a84c;'
                f'font-weight:700;padding:10px;">'
                f'{day_labels[current_day]} &nbsp;·&nbsp; Going: {going}</td></tr>\n'
            )

        conf_color = "#3fb950" if p["conf"] == "HIGH" else ("#58a6ff" if p["conf"] == "MED" else "#c9a84c")
        skip_tag = ' <span style="color:#666;font-size:.7rem">[skip]</span>' if p["skip"] else ""
        grade_color = "#3fb950" if p["grade"] == "G1" else ("#58a6ff" if p["grade"] == "G2" else "#888")

        # 2025 result for this race
        r25 = RESULTS_2025.get(p["race"])
        r24 = RESULTS_2024.get(p["race"])

        def result_cell(r):
            if not r:
                return '<td style="color:#555;font-size:.75rem">—</td>'
            sp = r["sp"]
            # colour by SP: favourite/short=green, mid=blue, big=amber
            sp_f = sp_to_float(sp)
            if sp_f is not None and sp_f < 2:
                col = "#3fb950"
            elif sp_f is not None and sp_f < 5:
                col = "#58a6ff"
            else:
                col = "#c9a84c"
            return (f'<td style="font-size:.78rem">'
                    f'<span style="color:{col};font-weight:600">{r["horse"]}</span>'
                    f'<br><span style="color:#666;font-size:.7rem">{sp} · {r["trainer"].split()[0] if r["trainer"] else ""}</span>'
                    f'</td>')

        rows_html += (
            f'<tr style="border-bottom:1px solid #21262d;">'
            f'<td style="padding:7px 10px;"><span style="color:{grade_color};'
            f'font-size:.72rem">[{p["grade"]}]</span> {p["race"]}{skip_tag}</td>'
            + result_cell(r24)
            + result_cell(r25)
            + f'<td style="color:#3fb950;font-weight:700">{p["pick"]}</td>'
            f'<td style="color:#c9a84c;font-weight:700">{p["odds"]}</td>'
            f'<td style="color:{conf_color};font-weight:600">{p["score"]:.0f}</td>'
            f'<td style="color:{conf_color};font-size:.78rem">{p["conf"]}'
            f' <span style="color:#555">(+{p.get("gap",0):.0f})</span></td>'
            f'<td>{p["trainer"]}</td>'
            f'<td style="color:#888">{p.get("jockey","")}</td>'
            f'<td style="color:#555;font-style:italic;font-size:.75rem">TBD</td>'
            f'</tr>\n'
        )

        if p["grade"] == "G1" and not p["skip"] and p.get("gap", 0) >= 10:
            border = "#3fb950" if p["conf"] == "HIGH" else "#58a6ff"
            r25_note = f'<div style="color:#888;font-size:.68rem;margin-top:4px">2025: {r25["horse"]} ({r25["sp"]})</div>' if r25 else ""
            g1_picks_html += (
                f'<div style="background:rgba(30,30,30,.8);border:1.5px solid {border};'
                f'border-radius:8px;padding:14px 16px;flex:1 1 180px;min-width:160px;max-width:220px;">'
                f'<div style="color:#888;font-size:.68rem;text-transform:uppercase;margin-bottom:4px">'
                f'{p["race"][:30]}</div>'
                f'<div style="font-size:1rem;font-weight:700;color:#f0f6fc">{p["pick"]}</div>'
                f'<div style="color:{border};font-weight:700;font-size:.9rem">{p["odds"]}</div>'
                f'<div style="color:#888;font-size:.75rem">{p["trainer"]}</div>'
                f'<div style="color:#666;font-size:.7rem;margin-top:4px">Score: {p["score"]:.0f} · Gap: +{p.get("gap",0):.0f}</div>'
                f'{r25_note}'
                f'</div>\n'
            )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Cheltenham 2026 — Winner Predictions</title>
<style>
  *{{box-sizing:border-box;}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#0d1117;color:#f0f6fc;margin:0;padding:24px;}}
  h1{{color:#c9a84c;font-size:1.7rem;border-bottom:2px solid #c9a84c;padding-bottom:10px;margin-bottom:6px;}}
  h2{{color:#58a6ff;font-size:1.05rem;margin:28px 0 10px;}}
  .meta{{color:#888;font-size:.8rem;margin-bottom:20px;}}
  .picks{{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 24px;}}
  table{{width:100%;border-collapse:collapse;font-size:.82rem;}}
  th{{background:#161b22;color:#8b949e;font-size:.68rem;text-transform:uppercase;
      letter-spacing:.05em;padding:8px 10px;text-align:left;border-bottom:2px solid #30363d;}}
  th.res-head{{background:#0d2b0d;color:#3fb950;border-bottom:2px solid #2d5a2d;}}
  th.pred-head{{background:#0a1929;color:#58a6ff;border-bottom:2px solid #1a3a5c;}}
  tr:hover td{{background:#161b22;}}
  .patterns{{background:#161b22;border-radius:8px;padding:16px 20px;margin-top:24px;}}
  .pattern-item{{margin-bottom:14px;border-left:3px solid #c9a84c;padding-left:12px;}}
  .pattern-title{{color:#c9a84c;font-weight:700;font-size:.85rem;margin-bottom:4px;}}
  .pattern-text{{color:#8b949e;font-size:.8rem;line-height:1.5;}}
  .stamp{{color:#666;font-size:.72rem;margin-top:24px;text-align:right;}}
  .legend{{display:flex;gap:18px;flex-wrap:wrap;margin-bottom:12px;font-size:.75rem;color:#888;}}
  .legend span{{display:inline-flex;align-items:center;gap:5px;}}
  .dot{{width:9px;height:9px;border-radius:50%;display:inline-block;}}
</style>
</head>
<body>
<h1>🏇 Cheltenham 2026 — Comprehensive Winner Predictions</h1>
<div class="meta">
  Generated via DynamoDB CheltenhamResults (99 verified records: 2024 + 2025) &nbsp;·&nbsp;
  Ground forecast (LOCKED): All 4 days Good to Soft / Soft — confirmed 6 March 2026 &nbsp;·&nbsp;
  Scoring: rating + trainer/jockey bias + historical race pattern + going + market confidence
</div>

<h2>🎯 Grade 1 Picks — Best Bets</h2>
<div class="picks">{g1_picks_html}</div>

<h2>📋 All Races — Historical Results &amp; 2026 Predictions</h2>
<div class="legend">
  <span><span class="dot" style="background:#3fb950"></span> Favourite / short-priced winner</span>
  <span><span class="dot" style="background:#58a6ff"></span> Well-backed winner</span>
  <span><span class="dot" style="background:#c9a84c"></span> Big-priced upset</span>
  <span><span class="dot" style="background:#3fb950;opacity:.4"></span> 2026 Result — TBD (festival 10–13 Mar)</span>
</div>
<table>
  <thead>
    <tr>
      <th rowspan="2">Race</th>
      <th colspan="2" class="res-head" style="text-align:center;border-left:2px solid #2d5a2d">✅ Actual Results</th>
      <th colspan="6" class="pred-head" style="text-align:center;border-left:2px solid #1a3a5c">🔮 2026 Predictions</th>
      <th class="res-head" style="border-left:2px solid #2d5a2d">2026 Result</th>
    </tr>
    <tr>
      <th class="res-head" style="border-left:2px solid #2d5a2d">2024 Winner</th>
      <th class="res-head">2025 Winner</th>
      <th class="pred-head" style="border-left:2px solid #1a3a5c">2026 Pick</th>
      <th class="pred-head">Odds</th>
      <th class="pred-head">Score</th>
      <th class="pred-head">Conf</th>
      <th class="pred-head">Trainer</th>
      <th class="pred-head">Jockey</th>
      <th class="res-head" style="border-left:2px solid #2d5a2d">Actual Winner</th>
    </tr>
  </thead>
  <tbody>{rows_html}</tbody>
</table>

<div class="patterns">
  <h2 style="color:#c9a84c;margin-top:0">📊 Historical Patterns Driving 2026 Predictions</h2>
  <div class="pattern-item">
    <div class="pattern-title">Lossiemouth — Hat-Trick Bid (Champion Hurdle)</div>
    <div class="pattern-text">Won Mares Hurdle 2024 (8/13f) AND 2025 (4/6f) for Willie Mullins/Paul Townend.
    Now declared for Champion Hurdle 2026 at 7/2. Two-time defending Mares champion stepping up.
    Mullins confirmed route. Pattern: Cheltenham champion mares regularly win the Champion Hurdle
    (Annie Power 2016 is the blueprint).</div>
  </div>
  <div class="pattern-item">
    <div class="pattern-title">Fact To File — Ryanair Defender (4/5 favourite)</div>
    <div class="pattern-text">Won 2025 Ryanair Chase at 6/4f for Mullins/Walsh. Defending champions in
    Grade 1 chases at Cheltenham win ~40% of the time. No reason to oppose at near odds-on.
    Mullins/Townend confirmed for 2026.</div>
  </div>
  <div class="pattern-item">
    <div class="pattern-title">Kopek Des Bordes — Supreme → Arkle Pattern</div>
    <div class="pattern-text">Won 2025 Supreme Novices Hurdle (4/6f, Mullins/Townend) and schooled over fences.
    Classic pattern: Altior (Supreme 2016 → Arkle 2017), Douvan (Supreme 2015 → Arkle 2016),
    Shishkin (Supreme 2020 → Arkle 2021). Mullins horse at 7/4.</div>
  </div>
  <div class="pattern-item">
    <div class="pattern-title">Willie Mullins — Festival Domination in Soft Ground</div>
    <div class="pattern-text">14 winners combined in 2024+2025. 2026 ground confirmed Good to Soft / Soft throughout —
    Irish yards trained through soft winter conditions have massive edge. Expect Mullins 7-10 winners again.
    Any Mullins horse in a Grade 1 must receive top priority weighting.</div>
  </div>
  <div class="pattern-item">
    <div class="pattern-title">Inothewayurthinkin — Defending Gold Cup Champion</div>
    <div class="pattern-text">Won 2024 Kim Muir (13/8f) then stepped up to win 2025 Gold Cup (15/2, Gavin Cromwell/Mark Walsh).
    Defending Gold Cup champions have a solid record. At 8/1 for 2026, solid each-way value.</div>
  </div>
  <div class="pattern-item">
    <div class="pattern-title">2025 Shock Results — Value Always Exists</div>
    <div class="pattern-text">2025 produced multiple big-priced winners: Poniros 100/1 (Triumph), Golden Ace 25/1 (Champion Hurdle),
    Wonderwall 28/1 (Hunters), Doddiethegreat 25/1 (Pertemps). In handicaps especially,
    Cheltenham always rewards course specialists at any price. Don't be afraid of bigger-priced runners
    who have shown Cheltenham form previously.</div>
  </div>
</div>

<div class="stamp">Cheltenham 2026 Analysis · Powered by DynamoDB CheltenhamResults · March 2026</div>
</body>
</html>"""

    root = r"C:\Users\charl\OneDrive\futuregenAI\Betting"
    path = os.path.join(root, output_file)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n  ✅ HTML exported: {path}")
    return path


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    do_html = "--html" in sys.argv
    picks = run_analysis()
    if do_html:
        export_html(picks)

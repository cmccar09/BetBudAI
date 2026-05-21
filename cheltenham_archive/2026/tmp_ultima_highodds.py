import sys; sys.path.insert(0, '.')
from cheltenham_deep_analysis_2026 import score_horse_2026

# Target big-odds horses with "Won last time out" or interesting profiles
candidates = [
    # name, trainer, jockey, rating, days_off, odds
    ("Myretown",         "Gordon Elliott",      "Jack Kennedy",       154, 28, "10/1"),
    ("Quebecois",        "Henry de Bromhead",   "Rachael Blackmore",  153, 21, "12/1"),
    ("Konfusion",        "Willie Mullins",      "Patrick Mullins",    150, 49, "14/1"),
    ("The Short Go",     "Gordon Elliott",      "J. W. Kennedy",      149, 21, "16/1"),
    ("Knight Of Allen",  "Gavin Cromwell",      "Danny Mullins",      148, 42, "16/1"),
    ("Imperial Saint",   "Emmet Mullins",       "M. P. Walsh",        146, 21, "20/1"),
    ("The Doyen Chief",  "James Moffatt",       "James Bowen",        144, 28, "25/1"),
    ("Leave of Absence", "Gordon Elliott",      "Jack Kennedy",       143, 21, "25/1"),
    ("Search For Glory", "Henry de Bromhead",   "Rachael Blackmore",  142, 28, "25/1"),
    ("Blow Your Wad",    "Philip Hobbs",        "Tom O'Brien",        141, 49, "33/1"),
    ("Stolen Silver",    "Venetia Williams",    "Charlie Deutsch",    136, 70, "50/1"),
]

horse_data = {
    "Myretown":         {"trainer": "Gordon Elliott", "jockey": "Jack Kennedy", "rating": 154, "days_off": 28, "odds": "10/1",
                         "form": "231431", "cheltenham_record": None, "last_run": "Won Hcap Chase Feb 2026"},
    "Quebecois":        {"trainer": "Henry de Bromhead", "jockey": "Rachael Blackmore", "rating": 153, "days_off": 21, "odds": "12/1",
                         "form": "142312", "cheltenham_record": None, "last_run": "2nd Hcap Chase Feb 2026"},
    "Konfusion":        {"trainer": "Willie Mullins", "jockey": "Patrick Mullins", "rating": 150, "days_off": 49, "odds": "14/1",
                         "form": "231412", "cheltenham_record": None},
    "The Short Go":     {"trainer": "Gordon Elliott", "jockey": "J. W. Kennedy", "rating": 149, "days_off": 21, "odds": "16/1",
                         "form": "413231", "cheltenham_record": None, "last_run": "Won Hcap Chase Feb 2026"},
    "Knight Of Allen":  {"trainer": "Gavin Cromwell", "jockey": "Danny Mullins", "rating": 148, "days_off": 42, "odds": "16/1",
                         "form": "323142", "cheltenham_record": None},
    "Imperial Saint":   {"trainer": "Emmet Mullins", "jockey": "M. P. Walsh", "rating": 146, "days_off": 21, "odds": "20/1",
                         "form": "142312", "cheltenham_record": None},
    "The Doyen Chief":  {"trainer": "James Moffatt", "jockey": "James Bowen", "rating": 144, "days_off": 28, "odds": "25/1",
                         "form": "324131", "cheltenham_record": None, "last_run": "Won Hcap Chase Feb 2026"},
    "Leave of Absence": {"trainer": "Gordon Elliott", "jockey": "Jack Kennedy", "rating": 143, "days_off": 21, "odds": "25/1",
                         "form": "412332", "cheltenham_record": None},
    "Search For Glory": {"trainer": "Henry de Bromhead", "jockey": "Rachael Blackmore", "rating": 142, "days_off": 28, "odds": "25/1",
                         "form": "341223", "cheltenham_record": None},
    "Blow Your Wad":    {"trainer": "Philip Hobbs", "jockey": "Tom O'Brien", "rating": 141, "days_off": 49, "odds": "33/1",
                         "form": "234141", "cheltenham_record": None, "last_run": "Won Hcap Chase Jan 2026"},
    "Stolen Silver":    {"trainer": "Venetia Williams", "jockey": "Charlie Deutsch", "rating": 136, "days_off": 70, "odds": "50/1",
                         "form": "324241", "cheltenham_record": None, "last_run": "Won Hcap Chase Dec 2025"},
}

results = []
for name, data in horse_data.items():
    horse = {"name": name, **data}
    score, tips_out, warnings_out, value_rating = score_horse_2026(horse, "Ultima Handicap Chase")
    results.append((name, int(score), data['odds'], tips_out))

results.sort(key=lambda x: -x[1])
print(f"{'Horse':25s} {'Score':>6}  {'Odds':>8}")
print("-"*50)
for name, score, odds, tips in results:
    hcap_tip = next((t for t in tips if 'equalisation' in t.lower()), '')
    won_tip = next((t for t in tips if 'won last' in t.lower()), '')
    extras = []
    if hcap_tip: extras.append(hcap_tip)
    if won_tip: extras.append(won_tip)
    print(f"{name:25s} {score:6d}  {odds:>8}  {' | '.join(extras)}")

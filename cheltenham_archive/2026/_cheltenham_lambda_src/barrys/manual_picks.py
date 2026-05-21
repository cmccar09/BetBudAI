"""
manual_picks.py
Generates and displays the best picks for both entries using HORSE_INTEL
even when Betfair markets aren't open yet.
Assigns horses to races based on race_hint and scores them per strategy.
"""
import sys, os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from barrys.barrys_config import FESTIVAL_RACES, ENTRIES, STRATEGY_WEIGHTS, FESTIVAL_DAYS
from barrys.generate_picks import HORSE_INTEL, score_horse_form, score_horse_festival_specialist

# Manual race-to-horse assignment based on known form and declarations
# Key = race config key from FESTIVAL_RACES, Value = list of likely runners
RACE_CONTENDERS = {
    "day1_race1": ["kopek des bordes","salvator mundi","maughreen","next destination"],      # Supreme Novices
    "day1_race2": ["fact to file","james's gate","jonbon","authorizo"],                       # Arkle
    "day1_race3": [],  # Ultima Handicap - TBC
    "day1_race4": ["state man","lossiemouth","sir gino","nurburgring"],                       # Champion Hurdle
    "day1_race5": ["brighterdaysahead","lossiemouth","wonder laoch","brandy love"],           # Mares Hurdle
    "day1_race6": [],  # National Hunt Chase - TBC
    "day1_race7": [],  # Conditional Jockeys - TBC

    "day2_race1": ["ballyburn","majborough","american mike"],                                  # Ballymore
    "day2_race2": ["james du berlais","dance with debon","dannyday"],                         # Brown Advisory
    "day2_race3": [],  # Coral Cup - TBC
    "day2_race4": ["captain guinness","jonbon","energumene","edwardstone","greaneteen"],      # QM Champion Chase
    "day2_race5": [],  # Cross Country - TBC
    "day2_race6": [],  # Dawn Run Mares Novices - TBC
    "day2_race7": ["lagos all day"],                                                           # NH Flat Day 2

    "day3_race1": ["jungle boogie","lecky watson"],                                            # Turners
    "day3_race2": [],  # Pertemps - TBC
    "day3_race3": ["mister coffey","banbridge","conflated"],                                  # Ryanair
    "day3_race4": ["teahupoo","sire du berlais","klassical dream","paisley park"],            # Stayers Hurdle
    "day3_race5": [],  # Plate Handicap - TBC
    "day3_race6": [],  # Boodles Juvenile - TBC
    "day3_race7": [],  # Martin Pipe - TBC

    "day4_race1": ["dynasty lady","il etait temps","blue arrow"],                             # Triumph Hurdle
    "day4_race2": [],  # County Handicap - TBC
    "day4_race3": ["perceval legallois","onemorefortheroad"],                                  # Albert Bartlett
    "day4_race4": ["galopin des champs","i am maximus","gerri colombe","fastorslow","alliance francaise"],  # Gold Cup
    "day4_race5": [],  # Grand Annual - TBC
    "day4_race6": ["grangeclare west","il est francais","readin tommy wrong"],                # Champion Bumper
    "day4_race7": [],  # Foxhunter - TBC
}

DAY_DATES = {1: "2026-03-10", 2: "2026-03-11", 3: "2026-03-12", 4: "2026-03-13"}
DAY_NAMES = {1: "Champion Day", 2: "Ladies Day", 3: "St Patrick's Thursday", 4: "Gold Cup Day"}


def score_runner(name, strategy):
    intel = HORSE_INTEL.get(name.lower(), {
        "trainer_tier": 2, "form_score": 5, "cheltenham_winner": False,
        "festival_winner": False, "progressive": False
    })
    # Wrap as runner dict for scorer
    runner = {"name": name, "odds": 5.0, "selection_id": 0}
    # Override intel lookup by injecting into HORSE_INTEL temporarily
    HORSE_INTEL[name.lower()] = intel
    if strategy == "form":
        return score_horse_form(runner, [])
    else:
        return score_horse_festival_specialist(runner, [])


def best_pick(contenders, strategy, exclude=None):
    """Return the highest scoring horse for the strategy"""
    if not contenders:
        return "TBC (declarations pending)"
    scored = [(h, score_runner(h, strategy)) for h in contenders if h != exclude]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0] if scored else "TBC"


def generate_manual_picks():
    print(f"\n{'='*90}")
    print(f"  BARRY'S CHELTENHAM 2026 - PICKS")
    print(f"  Surebet (FORM) vs Douglas Stunners (FESTIVAL SPECIALIST)")
    print(f"  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}  |  Betfair markets open ~4 Mar")
    print(f"{'='*90}")
    print(f"  NOTE: 10pts WIN | 5pts 2nd | 3pts 3rd  -  Odds are IRRELEVANT")
    print(f"{'='*90}\n")

    for day_num in [1, 2, 3, 4]:
        day_races = {k: v for k, v in FESTIVAL_RACES.items() if v['day'] == day_num}
        day_date  = DAY_DATES[day_num]

        print(f"  DAY {day_num} - {DAY_NAMES[day_num].upper()} ({day_date})")
        print(f"  {'-'*86}")
        print(f"  {'TIME':<7}{'RACE':<38}{'SUREBET (FORM)':<27}{'DOUGLAS STUNNERS (FEST.)':<27}{'SAME?'}")
        print(f"  {'-'*86}")

        for race_key, race_info in sorted(day_races.items(), key=lambda x: x[1]['time']):
            contenders = RACE_CONTENDERS.get(race_key, [])
            sb_pick = best_pick(contenders, "form")
            ds_pick = best_pick(contenders, "festival_specialist", exclude=sb_pick if sb_pick != "TBC (declarations pending)" else None)

            same_flag = " <<" if sb_pick == ds_pick and sb_pick != "TBC (declarations pending)" else ""

            print(f"  {race_info['time']:<7}{race_info['name'][:36]:<38}{sb_pick[:25]:<27}{ds_pick[:25]:<27}{same_flag}")

        print()

    print(f"  {'='*86}")
    print(f"  HEADLINE PICKS SUMMARY")
    print(f"  {'='*86}")

    highlights = [
        ("Champion Hurdle",      "day1_race4"),
        ("Arkle",                "day1_race2"),
        ("Queen Mother Chase",   "day2_race4"),
        ("Stayers Hurdle",       "day3_race4"),
        ("Ryanair Chase",        "day3_race3"),
        ("Gold Cup",             "day4_race4"),
        ("Champion Bumper",      "day4_race6"),
    ]
    print(f"\n  {'RACE':<30}{'SUREBET':<25}{'DOUGLAS STUNNERS':<25}")
    print(f"  {'-'*78}")
    for race_label, race_key in highlights:
        contenders = RACE_CONTENDERS.get(race_key, [])
        sb = best_pick(contenders, "form")
        ds = best_pick(contenders, "festival_specialist", exclude=sb if sb != "TBC (declarations pending)" else None)
        print(f"  {race_label:<30}{sb[:23]:<25}{ds[:23]:<25}")

    print(f"\n  TBC = declarations not yet published (expected 3-4 Mar)")
    print(f"  Run again after 4 March for full confirmed runner lists.\n")


if __name__ == "__main__":
    generate_manual_picks()

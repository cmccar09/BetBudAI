"""
final_lists.py
Barry's Cheltenham 2026 — Final Competition Pick Lists
=======================================================
Produces two clean pick sheets:
  SUREBET        — form-first, best SureBet raw score
  STUNNERS       — Douglas Stunners, festival specialist / course winners

Both lists share the clear BANKERS (22 races).
Six close calls diverge based on strategy logic:

  Race                    Surebet            Stunners           Reason
  -----------------------------------------------------------------------
  National Hunt Chase     Crosshill          Delta Work         Delta Work won 2019 RSA (Cheltenham experience)
  Conditional Jockeys     Golden Ace         Blazing Khal       1-pt gap; Mullins horse has stronger stable form
  Ryanair Chase           Energumene         Banbridge          Banbridge WON the 2025 Ryanair specifically
  Pertemps Final          Gaillard Du Mesnil Crambo             Crambo WON this exact race (2024 Pertemps Final)
  Turners Novices Chase   Jungle Boogie      Gaelic Warrior     Gaelic Warrior won Arkle at Cheltenham — course winner
  St James Foxhunter      Il Est Francais    Readin Tommy Wrong Readin Tommy Wrong is the REIGNING Foxhunter champ

Usage:
    python barrys/final_lists.py          # print both lists side by side
    python barrys/final_lists.py --solo   # print each list separately on its own
"""

import sys, os, argparse
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# fmt: off
# ─────────────────────────────────────────────────────────────────────────────
# THE PICKS
# Format: (race_key, time, grade, race_name, surebet_pick, stunners_pick, banker)
# banker=True  → same horse, shown with ** marker
# banker=False → close call, lists differ
# ─────────────────────────────────────────────────────────────────────────────
PICKS = [
    # ── DAY 1 - CHAMPION DAY  (Tue 10 Mar) ────────────────────────────────
    ("day1_race1", "13:30", "G1",       "Sky Bet Supreme Novices Hurdle",       "Salvator Mundi",       "Salvator Mundi",       True),
    ("day1_race2", "14:10", "G1",       "Arkle Challenge Trophy Chase",          "Gaelic Warrior",       "Gaelic Warrior",       True),
    ("day1_race3", "14:50", "Hcap",     "Ultima Handicap Chase",                 "Monkfish",             "Monkfish",             True),
    ("day1_race4", "15:30", "G1",       "Unibet Champion Hurdle",                "State Man",            "State Man",            True),
    ("day1_race5", "16:10", "G1",       "Close Brothers Mares Hurdle",           "Lossiemouth",          "Lossiemouth",          True),
    ("day1_race6", "16:50", "G2",       "National Hunt Chase",                   "Crosshill",            "Delta Work",           False),
    ("day1_race7", "17:30", "Hcap",     "Conditional Jockeys Hcap Hurdle",      "Golden Ace",           "Blazing Khal",         False),

    # ── DAY 2 - LADIES DAY  (Wed 11 Mar) ──────────────────────────────────
    ("day2_race1", "13:30", "G1",       "Ballymore Novices Hurdle",              "Ballyburn",            "Ballyburn",            True),
    ("day2_race2", "14:10", "G1",       "Brown Advisory Novices Chase",          "Dance With Debon",     "Dance With Debon",     True),
    ("day2_race3", "14:50", "Hcap",     "Coral Cup Handicap Hurdle",             "Sharp Secret",         "Sharp Secret",         True),
    ("day2_race4", "15:30", "G1",       "Queen Mother Champion Chase",           "El Fabiolo",           "El Fabiolo",           True),
    ("day2_race5", "16:10", "G2",       "Glenfarclas Cross Country Chase",       "Billaway",             "Billaway",             True),
    ("day2_race6", "16:50", "G2",       "Dawn Run Mares Novices Hurdle",         "Sainte Sangria",       "Sainte Sangria",       True),
    ("day2_race7", "17:30", "Flat",     "FBD Hotels NH Flat Race",               "Lagos All Day",        "Lagos All Day",        True),

    # ── DAY 3 - ST PATRICK'S THURSDAY  (Thu 12 Mar) ───────────────────────
    ("day3_race1", "13:30", "G1",       "Turners Novices Chase",                 "Jungle Boogie",        "Gaelic Warrior",       False),
    ("day3_race2", "14:10", "Hcap",     "Pertemps Final Handicap Hurdle",        "Gaillard Du Mesnil",   "Crambo",               False),
    ("day3_race3", "14:50", "G1",       "Ryanair Chase",                         "Energumene",           "Banbridge",            False),
    ("day3_race4", "15:30", "G1",       "Paddy Power Stayers Hurdle",            "Teahupoo",             "Teahupoo",             True),
    ("day3_race5", "16:10", "Hcap",     "Plate Handicap Chase",                  "Run To Freedom",       "Run To Freedom",       True),
    ("day3_race6", "16:50", "Hcap",     "Boodles Juvenile Handicap Hurdle",      "Il Etait Temps",       "Il Etait Temps",       True),
    ("day3_race7", "17:30", "Hcap",     "Martin Pipe Conditional Jockeys",       "Kargese",              "Kargese",              True),

    # ── DAY 4 - GOLD CUP DAY  (Fri 13 Mar) ───────────────────────────────
    ("day4_race1", "13:30", "G1",       "JCB Triumph Hurdle",                    "Il Etait Temps",       "Il Etait Temps",       True),
    ("day4_race2", "14:10", "Hcap",     "County Handicap Hurdle",                "Kopek Des Bordes",     "Kopek Des Bordes",     True),
    ("day4_race3", "14:50", "G1",       "Albert Bartlett Novices Hurdle",        "Perceval Legallois",   "Perceval Legallois",   True),
    ("day4_race4", "15:30", "G1",       "Cheltenham Gold Cup",                   "Galopin Des Champs",   "Galopin Des Champs",   True),
    ("day4_race5", "16:10", "Hcap",     "Grand Annual Handicap Chase",           "Vauban",               "Vauban",               True),
    ("day4_race6", "16:50", "Flat",     "Champion Open NH Flat Race",            "Majborough",           "Majborough",           True),
    ("day4_race7", "17:30", "Hunter",   "St James Place Foxhunter Chase",        "Il Est Francais",      "Readin Tommy Wrong",   False),
]
# fmt: on

DAY_HEADERS = {
    "day1": ("DAY 1 — CHAMPION DAY",        "Tuesday   10 March 2026"),
    "day2": ("DAY 2 — LADIES DAY",          "Wednesday 11 March 2026"),
    "day3": ("DAY 3 — ST PATRICK'S THURS",  "Thursday  12 March 2026"),
    "day4": ("DAY 4 — GOLD CUP DAY",        "Friday    13 March 2026"),
}

CLOSE_CALL_NOTES = {
    "day1_race6": "Delta Work = Won 2019 RSA (Cheltenham festival exp); Crosshill best form score",
    "day1_race7": "1-pt gap; Blazing Khal (Mullins) vs Golden Ace (Henderson) - coin flip",
    "day3_race1": "Gaelic Warrior won 2024 Arkle at Cheltenham; Jungle Boogie best form score",
    "day3_race2": "Crambo WON 2024 Pertemps Final (this race); Gaillard Du Mesnil top SureBet score",
    "day3_race3": "Banbridge WON 2025 Ryanair Chase specifically; Energumene top score (QMCC horse)",
    "day4_race7": "Readin Tommy Wrong = REIGNING Foxhunter champ (2025); Il Est Francais won 2024",
}


def print_side_by_side():
    print(f"\n{'='*100}")
    print(f"  BARRY'S CHELTENHAM 2026 — COMPETITION ENTRY LISTS")
    print(f"  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}")
    print(f"  Points: WIN=10  |  2nd=5  |  3rd=3  |  Prize: GBP 2,500")
    print(f"{'='*100}")
    print(f"  ** = BANKER (both lists agree)   ><= CLOSE CALL (lists differ)")
    print(f"{'='*100}\n")

    current_day = None
    for (rkey, time, grade, race, sb, ds, banker) in PICKS:
        day = rkey[:4]
        if day != current_day:
            current_day = day
            hdr, date = DAY_HEADERS[day]
            print(f"\n  {hdr}  —  {date}")
            print(f"  {'-'*96}")
            print(f"  {'TIME':<7} {'GRADE':<6} {'RACE':<38} {'SUREBET':<26} {'STUNNERS':<26} {'NOTE'}")
            print(f"  {'-'*96}")

        marker  = "**" if banker else "><"
        sb_disp = sb[:24]
        ds_disp = ds[:24]
        note    = "" if banker else CLOSE_CALL_NOTES.get(rkey, "close call")

        print(f"  {time:<7} {grade:<6} {race[:37]:<38} {sb_disp:<26} {ds_disp:<26} {marker} {note[:28]}")

    # ── Surebet list
    _print_solo_list("SUREBET", "sb")
    # ── Stunners list
    _print_solo_list("DOUGLAS STUNNERS", "ds")

    # ── Differences
    diffs = [(t, gr, r, sb, ds, rkey) for (rkey, t, gr, r, sb, ds, bk) in PICKS if not bk]
    print(f"\n{'='*100}")
    print(f"  CLOSE CALLS — WHERE THE LISTS DIFFER ({len(diffs)} races)")
    print(f"{'='*100}")
    print(f"\n  {'RACE':<38} {'SUREBET':<26} {'STUNNERS':<26} {'REASONING'}")
    print(f"  {'-'*100}")
    for (t, gr, r, sb, ds, rkey) in diffs:
        note = CLOSE_CALL_NOTES.get(rkey, "")
        print(f"  {r[:37]:<38} {sb[:24]:<26} {ds[:24]:<26} {note}")

    bankers = [(sb, r) for (_, _, _, r, sb, ds, bk) in PICKS if bk]
    print(f"\n  SHARED BANKERS ({len(bankers)} races — both lists identical):")
    for i, (horse, race) in enumerate(bankers, 1):
        print(f"    {i:>2}. {horse:<28} ({race})")
    print()


def _print_solo_list(title, which):
    """Print a single clean entry card."""
    print(f"\n{'='*70}")
    print(f"  BARRY'S CHELTENHAM 2026  —  {title.upper()}")
    print(f"  Cheltenham Festival  |  10-13 March 2026")
    print(f"  28 picks  |  WIN=10pts  2nd=5pts  3rd=3pts  |  Prize GBP 2,500")
    print(f"{'='*70}")
    current_day = None
    num = 0
    for (rkey, time, grade, race, sb, ds, banker) in PICKS:
        day = rkey[:4]
        if day != current_day:
            current_day = day
            hdr, date = DAY_HEADERS[day]
            print(f"\n  {hdr}  ({date})")
            print(f"  {'-'*66}")
        num += 1
        horse = sb if which == "sb" else ds
        star  = "  BANKER" if banker else "  *close call*"
        print(f"  {num:>2}. {time}  {race[:34]:<35} {horse}")
    total_bankers = sum(1 for *_, bk in PICKS if bk)
    total_diffs   = 28 - total_bankers
    print(f"\n  {total_bankers} shared bankers  |  {total_diffs} exclusive picks")
    print(f"{'='*70}")


def print_solo(title, which):
    """Standalone mode: just one list."""
    _print_solo_list(title, which)


def save_to_dynamodb():
    """Save final picks (with close-call logic) to BarrysCompetition DynamoDB."""
    import boto3
    db    = boto3.resource("dynamodb", region_name="eu-west-1")
    table = db.Table("BarrysCompetition")
    saved = 0
    now   = datetime.now().isoformat()

    for (rkey, time, grade, race, sb_pick, ds_pick, banker) in PICKS:
        day = int(rkey[3])
        for entry, pick in [("Surebet", sb_pick), ("Douglas Stunners", ds_pick)]:
            note = CLOSE_CALL_NOTES.get(rkey, "banker — both entries agree") if not banker else "banker — both entries agree"
            item = {
                "entry":         entry,
                "race_id":       rkey,
                "race_name":     race,
                "day":           day,
                "race_time":     time,
                "grade":         grade,
                "pick":          pick,
                "banker":        banker,
                "pick_reason":   note[:200],
                "strategy":      "form" if entry == "Surebet" else "festival_specialist",
                "source":        "final_lists_close_call_logic",
                "generated_at":  now,
                "outcome":       "pending",
                "points":        Decimal("0"),
            }
            table.put_item(Item=item)
            saved += 1

    print(f"  [DB] Saved {saved} picks to BarrysCompetition (final_lists logic)")
    print(f"  [DB] 22 bankers + 6 close-call splits")
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Barry's final pick lists")
    parser.add_argument("--solo",     action="store_true", help="Print each list solo (no side-by-side)")
    parser.add_argument("--surebet",  action="store_true", help="Print Surebet list only")
    parser.add_argument("--stunners", action="store_true", help="Print Douglas Stunners list only")
    parser.add_argument("--save",     action="store_true", help="Save picks to BarrysCompetition DynamoDB")
    args = parser.parse_args()

    if args.surebet:
        print_solo("SUREBET", "sb")
    elif args.stunners:
        print_solo("DOUGLAS STUNNERS", "ds")
    else:
        print_side_by_side()

    if args.save:
        save_to_dynamodb()

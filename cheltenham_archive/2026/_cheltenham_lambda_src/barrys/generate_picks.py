"""
generate_picks.py
Generates Cheltenham Festival picks for both competition entries:
  - Surebet:          Form-first strategy (favours market leaders with strong form)
  - Douglas Stunners: Value strategy (favours overlooked runners at bigger prices)

Scoring is driven by Betfair odds + known form indicators.
Saves picks to DynamoDB BarrysCompetition table.
"""
import sys
import os
import json
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from barrys.barrys_config import (
    ENTRIES, FESTIVAL_RACES, DYNAMODB_TABLE, DYNAMODB_REGION,
    STRATEGY_WEIGHTS, FESTIVAL_DAYS, POINTS
)

import boto3

dynamodb = boto3.resource('dynamodb', region_name=DYNAMODB_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)

RACES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cheltenham_races.json')

# ============================================================
# MANUAL INTELLIGENCE LAYER
# NOTE: Odds are IRRELEVANT - 10pts for win regardless of price.
# All scoring is purely about who is most likely to WIN/PLACE.
#
# trainer_tier:      1=elite (Mullins/Henderson/O'Brien/de Bromhead)
#                    2=strong (Nicholls/Pipe/Hobbs/Skelton)
#                    3=other
# form_score:        0-10  (10 = won last 3, 0 = poor/no form)
# cheltenham_winner: won AT Cheltenham racecourse (any meeting)
# festival_winner:   won specifically at the Cheltenham Festival
# progressive:       True if consistently improving run-on-run
# ============================================================
HORSE_INTEL = {
    # ================================================================
    # CHELTENHAM FESTIVAL 2026 - FORM INTELLIGENCE
    # Last updated: March 1, 2026 (pre-declarations)
    # NOTE: Constitution Hill RULED OUT (confirmed 25 Feb 2026)
    #
    # trainer_tier: 1=elite (Mullins/Henderson/O'Brien/de Bromhead)
    #               2=strong (Nicholls/Pipe/Skelton/Hobbs/King)
    #               3=other
    # form_score:   0-10 (10=won last 3 in high-class company)
    # cheltenham_winner: won AT Cheltenham racecourse
    # festival_winner:   won AT the Festival specifically
    # progressive:  True if improving run-on-run (unexposed)
    # race_hint:    Expected race assignment
    # ================================================================

    # ---- CHAMPION HURDLE (Day 1) ----
    "state man":            {"trainer_tier": 1, "form_score": 10, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Champion Hurdle"},
    "lossiemouth":          {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": True,  "festival_winner": True,  "progressive": True,  "race_hint": "Champion Hurdle or Mares Hurdle"},
    "sir gino":             {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Champion Hurdle"},
    "nurburgring":          {"trainer_tier": 2, "form_score":  7, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Champion Hurdle"},

    # ---- SUPREME NOVICES HURDLE (Day 1) ----
    "kopek des bordes":     {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Supreme Novices"},
    "maughreen":            {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Supreme Novices"},
    "salvator mundi":       {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Supreme Novices"},
    "next destination":     {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Supreme Novices"},

    # ---- ARKLE (Day 1) ----
    "fact to file":         {"trainer_tier": 1, "form_score": 10, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Arkle"},
    "jonbon":               {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Arkle or QM Champion Chase"},
    "james's gate":         {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Arkle"},
    "authorizo":            {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Arkle"},

    # ---- QUEEN MOTHER CHAMPION CHASE (Day 2) ----
    "captain guinness":     {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Queen Mother Champion Chase"},
    "energumene":           {"trainer_tier": 1, "form_score":  7, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Queen Mother Champion Chase"},
    "edwardstone":          {"trainer_tier": 2, "form_score":  8, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Queen Mother Champion Chase"},
    "greaneteen":           {"trainer_tier": 2, "form_score":  7, "cheltenham_winner": True,  "festival_winner": False, "progressive": False, "race_hint": "Queen Mother Champion Chase"},

    # ---- GOLD CUP (Day 4) ----
    "galopin des champs":   {"trainer_tier": 1, "form_score": 10, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Gold Cup"},
    "i am maximus":         {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Gold Cup"},
    "gerri colombe":        {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": True,  "festival_winner": False, "progressive": False, "race_hint": "Gold Cup"},
    "fastorslow":           {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": True,  "festival_winner": False, "progressive": False, "race_hint": "Gold Cup"},
    "alliance francaise":   {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Gold Cup"},

    # ---- STAYERS HURDLE (Day 3) ----
    "teahupoo":             {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Stayers Hurdle"},
    "paisley park":         {"trainer_tier": 2, "form_score":  6, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Stayers Hurdle"},
    "klassical dream":      {"trainer_tier": 1, "form_score":  7, "cheltenham_winner": False, "festival_winner": False, "progressive": False, "race_hint": "Stayers Hurdle"},
    "sire du berlais":      {"trainer_tier": 1, "form_score":  7, "cheltenham_winner": True,  "festival_winner": False, "progressive": False, "race_hint": "Stayers Hurdle"},

    # ---- RYANAIR CHASE (Day 3) ----
    "mister coffey":        {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": True,  "festival_winner": False, "progressive": True,  "race_hint": "Ryanair"},
    "banbridge":            {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": True,  "festival_winner": False, "progressive": False, "race_hint": "Ryanair"},
    "conflated":            {"trainer_tier": 1, "form_score":  7, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Ryanair or Gold Cup"},

    # ---- BALLYMORE NOVICES HURDLE (Day 2) ----
    "ballyburn":            {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Ballymore"},
    "majborough":           {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Ballymore"},
    "american mike":        {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Ballymore"},

    # ---- BROWN ADVISORY (RSBA) NOVICES CHASE (Day 2) ----
    "james du berlais":     {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Brown Advisory"},
    "dance with debon":     {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Brown Advisory"},
    "dannyday":             {"trainer_tier": 2, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Brown Advisory"},

    # ---- TURNERS NOVICES CHASE (Day 3) ----
    "jungle boogie":        {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Turners"},
    "lecky watson":         {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Turners"},

    # ---- TRIUMPH HURDLE (Day 4) ----
    "dynasty lady":         {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Triumph Hurdle"},
    "il etait temps":       {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Triumph Hurdle"},
    "blue arrow":           {"trainer_tier": 2, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Triumph Hurdle"},

    # ---- ALBERT BARTLETT (Day 4) ----
    "perceval legallois":   {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Albert Bartlett"},
    "onemorefortheroad":    {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Albert Bartlett"},

    # ---- MARES HURDLE (Day 1) ----
    "brighterdaysahead":    {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Mares Hurdle"},
    "wonder laoch":         {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Mares Hurdle"},
    "brandy love":          {"trainer_tier": 1, "form_score":  7, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Mares Hurdle"},

    # ---- NH FLAT RACES (Bumper Day 2 & Champion Bumper Day 4) ----
    "grangeclare west":     {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": True,  "festival_winner": True,  "progressive": False, "race_hint": "Champion Bumper"},
    "il est francais":      {"trainer_tier": 1, "form_score":  9, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Champion Bumper"},
    "readin tommy wrong":    {"trainer_tier": 2, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "Champion Bumper"},
    "lagos all day":        {"trainer_tier": 1, "form_score":  8, "cheltenham_winner": False, "festival_winner": False, "progressive": True,  "race_hint": "NH Flat Day 2"},
}


def load_race_data():
    """Load fetched race data from JSON file"""
    if not os.path.exists(RACES_FILE):
        return []
    with open(RACES_FILE) as f:
        return json.load(f)


def score_horse_form(runner, race_runners):
    """
    SUREBET STRATEGY: Form-first scoring.
    Purely about who is in the BEST FORM right now.
    Odds are irrelevant - 10pts for win regardless of price.
    Weights: recent form > trainer > jockey > course/distance > class.
    """
    name = runner['name'].lower()
    intel = HORSE_INTEL.get(name, {})

    form_score    = intel.get('form_score', 5.0)
    trainer_score = {1: 10.0, 2: 6.0, 3: 3.0}.get(intel.get('trainer_tier', 2), 5.0)
    jockey_score  = trainer_score * 0.8   # Proxy: top trainers book top jockeys
    course_score  = 8.0 if intel.get('cheltenham_winner') else 4.0
    festival_bonus = 2.0 if intel.get('festival_winner') else 0.0

    w = STRATEGY_WEIGHTS['form']
    total = (
        w['recent_form']    * form_score +
        w['trainer_form']   * trainer_score +
        w['jockey_form']    * jockey_score +
        w['course_distance']* course_score +
        w['class_level']    * form_score * 0.8
    ) + festival_bonus

    return round(total, 3)


def score_horse_festival_specialist(runner, race_runners):
    """
    DOUGLAS STUNNERS STRATEGY: Festival specialist scoring.
    Targets horses that SPECIFICALLY excel at Cheltenham:
    - Won at the course before
    - Trainer with strong Cheltenham Festival record
    - Progressive improvers who could be peaking at the festival
    Odds are irrelevant - 10pts for win regardless of price.
    """
    name = runner['name'].lower()
    intel = HORSE_INTEL.get(name, {})

    # Cheltenham course win = massive credibility
    course_win_score  = 10.0 if intel.get('cheltenham_winner') else 3.0
    festival_win_score = 10.0 if intel.get('festival_winner') else 4.0

    # Trainer Cheltenham record
    trainer_chelt = {1: 10.0, 2: 6.0, 3: 2.0}.get(intel.get('trainer_tier', 2), 4.0)

    # Progressive improver (unexposed horse peaking at right time)
    progressive_score = 9.0 if intel.get('progressive') else 5.0

    form_score = intel.get('form_score', 5.0)

    w = STRATEGY_WEIGHTS['festival_specialist']
    total = (
        w['festival_course_win'] * course_win_score +
        w['trainer_chelt_record']* trainer_chelt +
        w['progressive_form']    * progressive_score +
        w['recent_form']         * form_score +
        w['class_level']         * form_score * 0.7
    ) + (2.0 if intel.get('festival_winner') else 0.0)

    return round(total, 3)


def pick_for_entry(entry_name, race, all_race_runners):
    """Select the best horse for an entry in a given race"""
    strategy = ENTRIES[entry_name]['strategy']
    runners = [r for r in all_race_runners if r.get('status') == 'ACTIVE' and r.get('odds')]

    if not runners:
        return None

    score_fn = score_horse_form if strategy == 'form' else score_horse_festival_specialist
    scored = [(r, score_fn(r, runners)) for r in runners]
    scored.sort(key=lambda x: x[1], reverse=True)

    best_runner, best_score = scored[0]

    # Prevent both entries picking identical horses in same race if possible
    return {
        'horse': best_runner['name'],
        'odds': best_runner['odds'],
        'score': best_score,
        'selection_id': best_runner['selection_id'],
        'all_scores': [(r['name'], s) for r, s in scored[:5]]
    }


def save_pick(entry_name, race, pick):
    """Save a pick to DynamoDB"""
    race_id = f"{race['date']}_{race.get('race_key', race['market_id'])}"

    table.update_item(
        Key={
            'entry': entry_name,
            'race_id': race_id
        },
        UpdateExpression='''SET horse = :horse, odds = :odds, score = :score,
                            selection_id = :sel_id, market_id = :mid,
                            result = :result, points = :pts, updated_at = :ts''',
        ExpressionAttributeValues={
            ':horse':   pick['horse'],
            ':odds':    Decimal(str(pick['odds'])),
            ':score':   Decimal(str(pick['score'])),
            ':sel_id':  str(pick['selection_id']),
            ':mid':     race.get('market_id', ''),
            ':result':  'pending',
            ':pts':     0,
            ':ts':      datetime.now().isoformat()
        }
    )


def generate_all_picks():
    """Main picks generation loop"""
    print(f"\n{'='*70}")
    print("GENERATING CHELTENHAM PICKS FOR BOTH ENTRIES")
    print(f"{'='*70}\n")

    races = load_race_data()

    if not races:
        print("[WARNING] No race data found. Run fetch_cheltenham_races.py first.")
        print("          Using festival race schedule only (no odds yet).\n")
        generate_picks_from_schedule()
        return

    picks_summary = {entry: [] for entry in ENTRIES}

    for race in sorted(races, key=lambda x: (x['day'], x['start_time'])):
        race_name = race['market_name']
        runners  = race['runners']
        day      = race['day']
        race_date = race['date']

        if not runners:
            continue

        print(f"\nDay {day} | {race['start_time'][11:16] if len(race.get('start_time',''))>5 else race_date} | {race_name}")
        print(f"  Runners: {len(runners)} | Fav: {runners[0]['name']} @ {runners[0]['odds']}")

        for entry_name in ENTRIES:
            pick = pick_for_entry(entry_name, race, runners)
            if pick:
                # If both picked the same horse and Douglas Stunners uses value strategy, pick their 2nd choice
                if (entry_name == "Douglas Stunners" and
                        picks_summary["Surebet"] and
                        picks_summary["Surebet"][-1].get('race') == race_name and
                        picks_summary["Surebet"][-1].get('horse') == pick['horse'] and
                        len(pick['all_scores']) > 1):
                    alt_name, alt_score = pick['all_scores'][1]
                    alt_runner = next((r for r in runners if r['name'] == alt_name), None)
                    if alt_runner:
                        pick['horse'] = alt_name
                        pick['odds'] = alt_runner['odds']
                        pick['score'] = alt_score
                        pick['selection_id'] = alt_runner['selection_id']

                try:
                    save_pick(entry_name, race, pick)
                    saved = "[SAVED]"
                except Exception as e:
                    saved = f"[ERROR: {e}]"

                strategy_label = "FORM " if ENTRIES[entry_name]['strategy'] == 'form' else "FEST "
                print(f"  [{strategy_label}] {entry_name:<20}: {pick['horse']:<35} (score: {pick['score']})  {saved}")
                picks_summary[entry_name].append({
                    'race': race_name,
                    'horse': pick['horse']
                })

    print(f"\n{'='*70}")
    print("PICKS GENERATION COMPLETE")
    print(f"{'='*70}\n")
    print_picks_table(picks_summary)


def generate_picks_from_schedule():
    """Fallback: generate picks skeleton from config when no odds available yet"""
    print("[INFO] Generating skeleton picks from race schedule (no odds data yet)...")
    print("       Update HORSE_INTEL in this file as declarations are published.\n")

    for race_key, race_info in FESTIVAL_RACES.items():
        day = race_info['day']
        race_date = {1: "2026-03-10", 2: "2026-03-11", 3: "2026-03-12", 4: "2026-03-13"}[day]
        print(f"  Day {day} | {race_info['time']} | {race_info['name']} - picks TBC (no data yet)")


def print_picks_table(picks_summary):
    """Print formatted picks for all entries"""
    all_races = list(range(1, 29))

    print(f"{'#':<4} {'RACE NAME':<42} {'SUREBET (FORM)':<30} {'DOUGLAS STUNNERS (FESTIVAL)':<30}")
    print("-" * 110)

    surebet_picks = picks_summary.get("Surebet", [])
    douglas_picks = picks_summary.get("Douglas Stunners", [])
    max_len = max(len(surebet_picks), len(douglas_picks))

    for i in range(max_len):
        sp = surebet_picks[i] if i < len(surebet_picks) else {}
        dp = douglas_picks[i] if i < len(douglas_picks) else {}
        race_name = sp.get('race', dp.get('race', f'Race {i+1}'))[:40]
        sh = sp.get('horse', 'TBC')[:30] if sp else "TBC"
        dh = dp.get('horse', 'TBC')[:30] if dp else "TBC"
        same = " <-- SAME PICK" if sh == dh and sh != "TBC" else ""
        print(f"  {i+1:<3} {race_name:<42} {sh:<30} {dh:<30}{same}")


if __name__ == '__main__':
    generate_all_picks()

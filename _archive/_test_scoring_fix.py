"""Test the going suitability and unexposed horse fixes."""
import sys
sys.path.insert(0, '.')
import comprehensive_pick_logic as cpl
from comprehensive_pick_logic import analyze_horse_comprehensive

# Inject yesterday's Naas/Carlisle going conditions
_mock_going = {
    'Naas': {'going': 'Soft (Soft to Heavy in places)', 'adjustment': -3, 'surface': 'turf'},
    'Carlisle': {'going': 'Good to Soft (Good in places)', 'adjustment': -2, 'surface': 'turf'},
}
cpl._going_cache['going_data'] = _mock_going
from datetime import datetime
cpl._going_cache['timestamp'] = datetime.now()

# ---- Quatre Bras: 6 consecutive Dundalk AW runs ----
qb_prev = [
    {'date':'2026-02-20','course':'Dundalk','going':'Standard (Slow)','position':'4','distance':'1m'},
    {'date':'2025-12-19','course':'Dundalk','going':'Standard (Slow)','position':'3','distance':'1m2f'},
    {'date':'2025-12-05','course':'Dundalk','going':'Standard (Slow)','position':'2','distance':'1m4f'},
    {'date':'2025-11-14','course':'Dundalk','going':'Standard (Slow)','position':'1','distance':'1m2f'},
    {'date':'2025-10-31','course':'Dundalk','going':'Standard (Slow)','position':'2','distance':'1m4f'},
    {'date':'2025-10-17','course':'Dundalk','going':'Standard (Slow)','position':'1','distance':'1m2f'},
]
qb = {'horse':'Quatre Bras','form':'12123-4','odds':9,'jockey':'Billy Lee','trainer':'R OBrien','age':'5',
      'race_name':'15:12 Naas 7f Hcap','prev_results': qb_prev}

# ---- Causeway: 2 runs - Curragh 7f Soft-to-Heavy (1st), Gowran 1m Soft (4th) ----
caus_prev = [
    {'date':'2025-10-04','course':'Curragh','going':'Soft to Heavy','position':'1','distance':'7f'},
    {'date':'2025-09-20','course':'Gowran Park','going':'Soft','position':'4','distance':'1m'},
]
caus = {'horse':'Causeway','form':'41-','odds':2.5,'jockey':'Ryan Moore','trainer':'A OBrien','age':'3',
        'race_name':'15:47 Naas 7f Hcap','prev_results': caus_prev}

# ---- Flanker Jet: 6 Dundalk AW runs including 2 wins ----
fj_prev = [
    {'date':'2026-03-13','course':'Dundalk','going':'Standard','position':'1','distance':'6f'},
    {'date':'2026-02-27','course':'Dundalk','going':'Standard (Slow)','position':'4','distance':'1m'},
    {'date':'2026-02-06','course':'Dundalk','going':'Standard (Slow)','position':'2','distance':'7f'},
    {'date':'2026-01-23','course':'Dundalk','going':'Standard (Slow)','position':'1','distance':'7f'},
    {'date':'2026-01-09','course':'Dundalk','going':'Standard (Slow)','position':'3','distance':'1m'},
    {'date':'2025-11-26','course':'Dundalk','going':'Standard (Slow)','position':'2','distance':'7f'},
]
fj = {'horse':'Flanker Jet','form':'2-31241','odds':11,'jockey':'David Egan','trainer':'Robson Aguiar','age':'3',
      'race_name':'15:47 Naas 7f Hcap','prev_results': fj_prev}

# ---- Collecting Coin: turf horse, soft-ground form ----
cc_prev = [
    {'date':'2025-09-27','course':'Curragh','going':'Soft','position':'5','distance':'7f'},
    {'date':'2025-08-22','course':'Killarney','going':'Good','position':'3','distance':'1m'},
    {'date':'2025-07-29','course':'Galway','going':'Good to Soft','position':'1','distance':'7f'},
    {'date':'2025-05-23','course':'Curragh','going':'Good','position':'2','distance':'7f'},
    {'date':'2025-04-19','course':'Cork','going':'Soft','position':'3','distance':'1m'},
]
cc = {'horse':'Collecting Coin','form':'32135-','odds':5,'jockey':'Shane Foley','trainer':'Mrs J Harrington','age':'4',
      'race_name':'15:12 Naas 7f Hcap','prev_results': cc_prev}

print("=== NAAS 15:12 / 15:47 SCORING TEST (post-fix) ===\n")
print(f"{'Horse':<20} {'Score':>5}  {'Going':>8}  {'Unexposed':>9}  {'TotalWins':>9}  Verdict")
print("-" * 75)

for horse_data in [qb, caus, fj, cc]:
    score, breakdown, reasons = analyze_horse_comprehensive(horse_data, course='Naas', avg_winner_odds=5.0, course_winners_today=0)
    going_suit = breakdown.get('going_suitability', 0)
    unexposed = breakdown.get('unexposed_bonus', 0)
    total_wins = breakdown.get('total_wins', 0)
    verdict = "PICK" if score >= 80 else ("consider" if score >= 65 else "skip")
    print(f"{horse_data['horse']:<20} {score:>5}  {going_suit:>8}  {unexposed:>9}  {total_wins:>9}  {verdict}")

print("\n--- Key reasoning for Causeway ---")
score, breakdown, reasons = analyze_horse_comprehensive(caus, course='Naas', avg_winner_odds=5.0, course_winners_today=0)
for r in reasons:
    print(" ", r)

print("\n--- Key reasoning for Quatre Bras ---")
score, breakdown, reasons = analyze_horse_comprehensive(qb, course='Naas', avg_winner_odds=5.0, course_winners_today=0)
for r in reasons:
    print(" ", r)

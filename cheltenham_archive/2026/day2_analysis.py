import sys, json
sys.path.insert(0, '.'); sys.path.insert(0, 'barrys')
from barrys.surebet_intel import EXTRA_RACES
from cheltenham_deep_analysis_2026 import score_horse_2026

all_races = [
    # key               display name                     1st                   2nd                   3rd
    # Day 1 races (Tuesday) — keys discovered from actual runner data
    ('day2_race1',  'Supreme Novices Hurdle',          'Old Park Star',      'Sober Glory',        'Mydaddypaddy'),
    ('day2_race2',  'Arkle Challenge Trophy Chase',    'Kargese',            'Kopek Des Bordes',   'Lulamba'),
    ('day1_race3',  'Fred Winter Handicap Hurdle',     'Saratoga',           'Winston Junior',     'Madness Delle'),
    ('day1_race4',  'Ultima Handicap Chase',           'Johnnywho',          'Jagwar',             'Quebecois'),
    (None,          'Champion Hurdle (no data)',        'Lossiemouth',        'Brighterdaysahead',  'The New Lion'),
    ('day1_race6_plate', 'Cheltenham Plate Chase',     'Madara',             'Will The Wise',      'Moon Dorange'),
    ('day1_race7',  'Challenge Cup Chase',             'Holloway Queen',     'King Of Answers',    'One Big Bang'),
    # Day 2 races (Wednesday)
    (None,          'Turners Novices Hurdle (no data)', 'King Rasko Grey',   'Act Of Innocence',   'Zeus Power'),
    (None,          'Brown Advisory Chase (no data)',  'Kitzbuhel',          'Final Demand',       'Now Is The Hour'),
    (None,          'BetMGM Cup Hurdle (no data)',     'Jingko Blue',        'Franciscan Rock',    'Storm Heart'),
    ('day2_race4',  'Glenfarclas Cross Country Chase', 'Final Orders',       'Favori De Champdou', 'Vanillier'),
    ('day2_race5',  'Queen Mother Champion Chase',     'Il Etait Temps',     'Libberty Hunter',    "L'Eau du Sud"),
    ('day2_race6',  'Grand Annual Handicap Chase',     'Martator',           'Jazzy Matty',        'Break My Soul'),
    ('day2_race7',  'Champion Bumper',                 'The Mourne Rambler', 'Mets Ta Ceinture',   'Bass Hunter'),
]

print("=" * 110)
print("FULL DAY 1+2 RESULTS ANALYSIS")
print("=" * 110)
print(f"{'Race':<40} {'Our Pick':<22} {'SP':<6} {'Winner':<22} {'W. Rank':<10} {'Pts':<5} Result")
print("-" * 110)

total_pts = 0
misses = []

for key, rname, w1, w2, w3 in all_races:
    if key is None or key not in EXTRA_RACES:
        print(f"{rname:<40}  *** NO DATA — winner: {w1} ***")
        continue
    entries = EXTRA_RACES[key]['entries']
    results = []
    for h in entries:
        score, tips, warnings, vr = score_horse_2026(h, rname)
        results.append((score, h['name'], h['odds']))
    results.sort(reverse=True)

    top_nm = results[0][1] if results else 'N/A'
    top_sc = results[0][0] if results else 0
    top_od = results[0][2] if results else '?'

    # Find where 1st/2nd/3rd ranked
    def find_rank(name):
        for rank, (sc, nm, odds) in enumerate(results, 1):
            if name.lower()[:8] in nm.lower() or nm.lower()[:8] in name.lower():
                return rank, sc, odds
        return None, 0, '?'

    wr, wsc, wod = find_rank(w1)

    # Pts
    pts = 0
    tnl = top_nm.lower()
    if w1.lower()[:8] in tnl or tnl[:8] in w1.lower(): pts = 10
    elif w2.lower()[:8] in tnl or tnl[:8] in w2.lower(): pts = 5
    elif w3.lower()[:8] in tnl or tnl[:8] in w3.lower(): pts = 3
    total_pts += pts

    wr_str = f"#{wr} ({wsc}pts)" if wr else "???"
    result_str = "WIN" if pts == 10 else ("2nd" if pts == 5 else ("3rd" if pts == 3 else "MISS"))
    print(f"{rname:<40} {top_nm[:22]:<22} {top_od:<6} {w1[:22]:<22} {wr_str:<10} {pts:<5} {result_str}")
    if pts == 0:
        gap = top_sc - wsc if wr else top_sc
        misses.append((rname, top_nm, top_sc, w1, wr, wsc, gap))

print("-" * 110)
print(f"Total pts (pure top-1 picks): {total_pts}/140")
print()
print("=" * 110)
print("MISS ANALYSIS — Winner ranked vs Our pick")
print("=" * 110)
for rname, pick, pick_sc, winner, wr, wsc, gap in misses:
    print(f"\n  Race:   {rname}")
    print(f"  Pick:   {pick} ({pick_sc}pts)")
    print(f"  Winner: {winner} — ranked #{wr} at {wsc}pts  |  gap = {gap}pts")

print()
print("=" * 110)
print("MODEL ACCURACY SUMMARY")
print("=" * 110)
wins = len([m for m in all_races if True])
hit_top1 = total_pts / 10
print(f"  Races analysed:  {len(all_races)}")
print(f"  Top-1 was winner: {hit_top1:.0f}/{len(all_races)}")
print(f"  Misses:          {len(misses)}")

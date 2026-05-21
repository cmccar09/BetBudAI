"""
Analyse favourite concentration in current picks + historical Day 1 fav performance.
"""
import boto3, json
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
from collections import defaultdict

ddb = boto3.resource('dynamodb', region_name='eu-west-1')

# ── 1. CURRENT PICKS ────────────────────────────────────────────────────────
table = ddb.Table('CheltenhamPicks')
resp = table.scan(FilterExpression=Attr('pick_date').eq('2026-03-09'))
picks = sorted(resp['Items'], key=lambda x: float(x.get('score', 0)), reverse=True)

def odds_to_dec(odds_str):
    """Convert fractional odds string to decimal, return None if can't parse."""
    try:
        if '/' in str(odds_str):
            n, d = odds_str.strip().split('/')
            return round(int(n)/int(d) + 1, 2)
        if odds_str and odds_str != '?' and odds_str != '—':
            return float(odds_str)
    except:
        pass
    return None

print("=== CURRENT PICKS ODDS ===")
print(f"{'Score':>5} | {'Horse':<28} | {'Odds':<8} | {'Dec':>5} | Race")
print("-" * 90)

fav_count = 0
near_fav_count = 0
total_with_odds = 0

for p in picks:
    odds = p.get('odds', '?')
    dec = odds_to_dec(odds)
    dec_str = f"{dec:.2f}" if dec else "  ?  "
    is_fav = dec and dec <= 2.5   # evens or shorter = favourite territory
    is_near_fav = dec and dec <= 4.0  # up to 3/1 = near favourite
    marker = " ★FAV" if is_fav else (" ~fav" if is_near_fav else "")
    if is_fav:
        fav_count += 1
    if is_near_fav:
        near_fav_count += 1
    if dec:
        total_with_odds += 1
    race = p.get('race_name', '?')[:35]
    print(f"{str(p.get('score','?')):>5} | {p.get('horse','?'):<28} | {str(odds):<8} | {dec_str:>5} | {race}{marker}")

print()
print(f"  Races with known odds : {total_with_odds}/28")
print(f"  Favourites (<=5/2)    : {fav_count}")
print(f"  Near-favs  (<=3/1)    : {near_fav_count}")


# ── 2. WHY SO MANY FAVS — scoring factor audit ──────────────────────────────
print()
print("=== WHY FAVOURITES SCORE HIGH — SCORING FACTORS ===")
print("Our system adds pts for: short price directly. Let's check which factors")
print("correlate with favourite status in the scoring engine...")

# Pull all_horses for a couple of races to see the odds bonus
sample_races = ['Arkle', 'Champion Hurdle', 'Ryanair']
resp2 = table.scan(FilterExpression=Attr('pick_date').eq('2026-03-09'))
for item in resp2['Items']:
    if any(r in item.get('race_name','') for r in sample_races):
        reasons = item.get('reasons', '')
        try:
            r_list = eval(reasons) if isinstance(reasons, str) else reasons
            odds_reasons = [r for r in r_list if 'price' in r.lower() or 'odds' in r.lower() or 'favourite' in r.lower()]
            if odds_reasons:
                print(f"  {item['race_name']}: {item['horse']} @ {item.get('odds','?')} — {odds_reasons}")
        except:
            pass


# ── 3. HISTORICAL DAY 1 FAVOURITES ──────────────────────────────────────────
print()
print("=== HISTORICAL DAY 1 CHELTENHAM — FAVOURITE PERFORMANCE ===")

hist_table = ddb.Table('CheltenhamHistoricalResults')
resp3 = hist_table.scan()
hist = resp3['Items']
while 'LastEvaluatedKey' in resp3:
    resp3 = hist_table.scan(ExclusiveStartKey=resp3['LastEvaluatedKey'])
    hist.extend(resp3['Items'])

print(f"  Total historical records: {len(hist)}")

# Find Day 1 races (Champion Day races)
DAY1_RACES = [
    'Supreme', 'Arkle', 'Ultima', 'Champion Hurdle', 'Mares Hurdle',
    'Mares\' Hurdle', 'Close Brothers', 'National Hunt Chase', 'NH Chase',
    'Bumper', 'Champion Bumper', 'Fred Winter', 'BetMGM'
]

day1 = []
for r in hist:
    race = r.get('race_name', '') or r.get('race', '')
    if any(d in race for d in DAY1_RACES):
        day1.append(r)

print(f"  Day 1 race records found: {len(day1)}")
print()

# Analyse favourite performance
fav_wins = 0
fav_total = 0
non_fav_wins = 0
non_fav_total = 0
results_by_race = defaultdict(list)

for r in day1:
    race = r.get('race_name', r.get('race', 'Unknown'))
    winner = r.get('winner', '') or r.get('horse_name', '') or r.get('horse', '')
    sp = r.get('sp', '') or r.get('starting_price', '') or r.get('odds', '')
    position = r.get('position', '') or r.get('finish_position', '')
    year = r.get('year', '') or r.get('race_year', '')
    
    dec = odds_to_dec(str(sp))
    
    results_by_race[race[:40]].append({
        'year': year,
        'winner': winner,
        'sp': sp,
        'dec': dec,
        'position': position
    })

# Look for favourite win rate patterns
print("Day 1 Results by Race (winners/favourites):")
for race, entries in sorted(results_by_race.items()):
    winners = [e for e in entries if str(e.get('position','')).strip() in ['1','1st','W','Win','won']]
    favs = [e for e in entries if e['dec'] and e['dec'] <= 3.0]
    fav_winners = [e for e in winners if e['dec'] and e['dec'] <= 3.0]
    print(f"  {race[:40]}")
    for e in sorted(entries, key=lambda x: str(x.get('year',''))):
        dec_str = f"{e['dec']:.1f}" if e['dec'] else "?"
        pos_str = str(e.get('position','?'))
        print(f"    {e.get('year','?')} | {str(e.get('winner','?')):<25} | SP:{str(e.get('sp','?')):<8} ({dec_str}) | pos:{pos_str}")
    print()


# ── 4. BROAD SP ANALYSIS across all historical ──────────────────────────────
print("=== ALL HISTORICAL CHELTENHAM: WIN RATE BY PRICE BAND ===")
bands = {
    'Fav (<=2.0)':    (0, 2.0),
    'Near-fav (2-3)': (2.0, 3.0),
    'Short (3-5)':    (3.0, 5.0),
    'Mid (5-10)':     (5.0, 10.0),
    'Longer (10+)':   (10.0, 9999),
}

band_stats = {k: {'wins':0,'runs':0} for k in bands}

for r in hist:
    sp = r.get('sp','') or r.get('starting_price','') or r.get('odds','')
    pos = str(r.get('position','') or r.get('finish_position','')).strip()
    dec = odds_to_dec(str(sp))
    if dec is None:
        continue
    won = pos in ['1','1st','W','Win','won']
    for band, (lo, hi) in bands.items():
        if lo < dec <= hi:
            band_stats[band]['runs'] += 1
            if won:
                band_stats[band]['wins'] += 1

print(f"  {'Band':<20} {'Runs':>6} {'Wins':>6} {'Win%':>7}")
print("  " + "-"*42)
for band, stats in band_stats.items():
    runs = stats['runs']
    wins = stats['wins']
    pct = f"{wins/runs*100:.1f}%" if runs else "n/a"
    print(f"  {band:<20} {runs:>6} {wins:>6} {pct:>7}")

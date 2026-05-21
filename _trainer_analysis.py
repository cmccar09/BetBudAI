"""
Historical trainer analysis — Willie Mullins vs Gordon Elliott vs others.
Examines: win rate, ROI, score calibration, race types, and scoring bias.
"""
import json, statistics
from collections import defaultdict

with open('backtest_dataset.json') as f:
    data = json.load(f)

# Also try to load cheltenham archive data
extra = []
try:
    import os, glob
    for p in glob.glob('cheltenham_archive/*.json') + glob.glob('history/*.json'):
        with open(p) as f:
            d = json.load(f)
            if isinstance(d, list):
                extra.extend(d)
except Exception:
    pass

all_data = data + extra
print(f"Total records: {len(all_data)} (backtest: {len(data)}, extra: {len(extra)})")

def roi(records):
    if not records:
        return 0
    total_staked = len(records) * 1.0
    returns = sum(r.get('odds', 2) for r in records if r.get('outcome') == 'WON')
    return (returns - total_staked) / total_staked * 100

def analyse(recs):
    wins = [r for r in recs if r.get('outcome') == 'WON']
    losses = [r for r in recs if r.get('outcome') == 'LOST']
    scores_all = [r.get('comprehensive_score', 0) for r in recs]
    scores_w   = [r.get('comprehensive_score', 0) for r in wins]
    scores_l   = [r.get('comprehensive_score', 0) for r in losses]
    odds_w = [r.get('odds', 2) for r in wins]
    return {
        'picks':          len(recs),
        'wins':           len(wins),
        'wr':             len(wins) / len(recs) * 100 if recs else 0,
        'roi':            roi(recs),
        'avg_score':      statistics.mean(scores_all) if scores_all else 0,
        'avg_score_w':    statistics.mean(scores_w)   if scores_w   else 0,
        'avg_score_l':    statistics.mean(scores_l)   if scores_l   else 0,
        'avg_odds_w':     statistics.mean(odds_w)     if odds_w     else 0,
        'max_score':      max(scores_all)              if scores_all else 0,
        'min_score':      min(scores_all)              if scores_all else 0,
    }

score_bands = [
    (90, 999, '90+  '),
    (80,  89, '80-89'),
    (70,  79, '70-79'),
    (60,  69, '60-69'),
    (50,  59, '50-59'),
    (40,  49, '40-49'),
    ( 0,  39, '<40  '),
]

# ── 1. Overall trainer leaderboard ──────────────────────────────────────────
print()
print('=' * 70)
print('  TRAINER LEADERBOARD (min 3 picks)')
print('=' * 70)
print(f"  {'Trainer':<30}  {'Picks':>5}  {'Wins':>4}  {'WR%':>5}  {'ROI%':>7}  {'Avg Score':>9}")
print('  ' + '-' * 67)

from collections import Counter
all_trainers = Counter(r.get('trainer', '') for r in all_data)
rows = []
for t, cnt in all_trainers.items():
    if cnt < 3:
        continue
    recs = [r for r in all_data if r.get('trainer', '') == t]
    s = analyse(recs)
    rows.append((t, s))

rows.sort(key=lambda x: x[1]['roi'], reverse=True)
for t, s in rows:
    marker = ''
    if 'Mullins' in t:
        marker = ' ← MULLINS'
    elif 'Elliott' in t:
        marker = ' ← ELLIOTT'
    elif 'Skelton' in t:
        marker = ' ← SKELTON'
    print(f"  {t:<30}  {s['picks']:>5}  {s['wins']:>4}  {s['wr']:>4.0f}%  {s['roi']:>+6.0f}%  {s['avg_score']:>8.0f}{marker}")

# ── 2. Mullins + Elliott deep dive ──────────────────────────────────────────
print()
print('=' * 70)
print('  DEEP DIVE: W.P. Mullins vs Gordon Elliott vs Dan Skelton')
print('=' * 70)

focus = {
    'W.P. Mullins':    [r for r in all_data if 'Mullins' in r.get('trainer', '')],
    'Gordon Elliott':  [r for r in all_data if r.get('trainer', '') == 'Gordon Elliott'],
    'Dan Skelton':     [r for r in all_data if r.get('trainer', '') == 'D Skelton'],
    'Nicky Henderson': [r for r in all_data if 'Henderson' in r.get('trainer', '')],
    'Paul Nicholls':   [r for r in all_data if 'Nicholls' in r.get('trainer', '')],
}

for name, recs in focus.items():
    if not recs:
        continue
    s = analyse(recs)
    print(f"\n  {name} ({s['picks']} picks):")
    print(f"    Win Rate:   {s['wr']:.0f}%  |  ROI: {s['roi']:+.0f}%")
    print(f"    Avg Score:  {s['avg_score']:.0f}  (wins: {s['avg_score_w']:.0f}  losses: {s['avg_score_l']:.0f})")
    print(f"    Score spread: {s['min_score']} – {s['max_score']}")
    print(f"    Avg winning odds: {s['avg_odds_w']-1:.1f}/1")
    print(f"    By score band:")
    for lo, hi, label in score_bands:
        sub = [r for r in recs if lo <= r.get('comprehensive_score', 0) <= hi]
        wins = [r for r in sub if r.get('outcome') == 'WON']
        if sub:
            print(f"      {label}: {len(sub):2d} picks  {len(wins):2d} wins  {len(wins)/len(sub)*100:.0f}%  ROI {roi(sub):+.0f}%")

# ── 3. Score calibration (all picks) ────────────────────────────────────────
print()
print('=' * 70)
print('  SCORE CALIBRATION — Does a higher score = more winners?')
print('=' * 70)
print(f"  {'Band':<8}  {'Picks':>5}  {'Wins':>5}  {'WR%':>6}  {'ROI%':>7}  Description")
print('  ' + '-' * 60)
for lo, hi, label in score_bands:
    recs = [r for r in all_data if lo <= r.get('comprehensive_score', 0) <= hi]
    wins = [r for r in recs if r.get('outcome') == 'WON']
    if recs:
        desc = '▓▓▓▓' if len(wins)/len(recs) >= 0.3 else ('▓▓  ' if len(wins)/len(recs) >= 0.2 else '░   ')
        print(f"  {label}  {len(recs):>5}  {len(wins):>5}  {len(wins)/len(recs)*100:>5.0f}%  {roi(recs):>+6.0f}%  {desc}")

# ── 4. Trainer picks by score — are Mullins/Elliott inflating the top bands? ─
print()
print('=' * 70)
print('  TRAINER CONCENTRATION at top score bands (80+)')
print('  Who is the scoring engine picking at the highest scores?')
print('=' * 70)
top_recs = [r for r in all_data if r.get('comprehensive_score', 0) >= 80]
top_trainers = Counter(r.get('trainer', '') for r in top_recs)
top_wins = defaultdict(int)
for r in top_recs:
    if r.get('outcome') == 'WON':
        top_wins[r.get('trainer', '')] += 1
print(f"  {len(top_recs)} picks with score 80+:")
for t, cnt in top_trainers.most_common(15):
    if cnt < 2:
        continue
    w = top_wins[t]
    print(f"    {cnt:3d} picks  {w:2d} wins  {w/cnt*100:.0f}%  {t}")

# ── 5. Race type breakdown for Mullins/Elliott ──────────────────────────────
print()
print('=' * 70)
print('  RACE TYPE BREAKDOWN — Mullins & Elliott')
print('  Are we picking them in the wrong race types?')
print('=' * 70)
for trainer_key, recs in [('W.P. Mullins', focus['W.P. Mullins']),
                           ('Gordon Elliott', focus['Gordon Elliott'])]:
    if not recs:
        continue
    by_course = Counter(r.get('course') for r in recs)
    print(f"\n  {trainer_key} — by course:")
    for course, cnt in by_course.most_common(10):
        rr = [r for r in recs if r.get('course') == course]
        ww = [r for r in rr if r.get('outcome') == 'WON']
        print(f"    {course:<25}: {cnt} picks  {len(ww)} wins  ({len(ww)/cnt*100:.0f}%)")

# ── 6. KEY FINDING SUMMARY ──────────────────────────────────────────────────
print()
print('=' * 70)
print('  KEY FINDINGS & RECOMMENDATIONS')
print('=' * 70)
all_wr = sum(1 for r in all_data if r.get('outcome') == 'WON') / len(all_data) * 100
print(f"\n  Overall win rate across all {len(all_data)} picks: {all_wr:.0f}%")
print(f"  Overall ROI: {roi(all_data):+.0f}%")

mullins_recs = focus['W.P. Mullins']
elliott_recs = focus['Gordon Elliott']
m_wr = sum(1 for r in mullins_recs if r.get('outcome') == 'WON') / len(mullins_recs) * 100 if mullins_recs else 0
e_wr = sum(1 for r in elliott_recs if r.get('outcome') == 'WON') / len(elliott_recs) * 100 if elliott_recs else 0

print(f"\n  Mullins pick concentration: {len(mullins_recs)}/{len(all_data)} = {len(mullins_recs)/len(all_data)*100:.0f}% of all picks  WR={m_wr:.0f}%")
print(f"  Elliott pick concentration: {len(elliott_recs)}/{len(all_data)} = {len(elliott_recs)/len(all_data)*100:.0f}% of all picks  WR={e_wr:.0f}%")

# Score inflation check
mullins_high = [r for r in mullins_recs if r.get('comprehensive_score', 0) >= 70]
non_mullins_high = [r for r in all_data if r.get('comprehensive_score', 0) >= 70 and 'Mullins' not in r.get('trainer', '')]
m_high_wr = sum(1 for r in mullins_high if r.get('outcome') == 'WON') / len(mullins_high) * 100 if mullins_high else 0
nm_high_wr = sum(1 for r in non_mullins_high if r.get('outcome') == 'WON') / len(non_mullins_high) * 100 if non_mullins_high else 0
print(f"\n  Mullins horses scoring 70+:     {len(mullins_high)} picks  WR={m_high_wr:.0f}%  (expected ~{m_wr:.0f}%)")
print(f"  Non-Mullins horses scoring 70+: {len(non_mullins_high)} picks  WR={nm_high_wr:.0f}%")
if mullins_high and m_high_wr < all_wr:
    print(f"\n  ⚠ WARNING: Mullins horses at 70+ score win at {m_high_wr:.0f}% — below overall {all_wr:.0f}%")
    print(f"     This suggests the TRAINER BONUS is inflating scores without improving predictions.")
elif mullins_high and m_high_wr >= all_wr * 1.2:
    print(f"\n  ✓ Mullins premium justified — high-score Mullins horses win at {m_high_wr:.0f}% vs {all_wr:.0f}% average")

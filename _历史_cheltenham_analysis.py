"""
Definitive historical analysis of Mullins/Elliott at Cheltenham.
Uses: CheltenhamHistoricalResults DynamoDB table + backtest_dataset.json
"""
import json, statistics, boto3
from collections import Counter, defaultdict

# ── Pull historical festival data ────────────────────────────────────────────
ddb = boto3.resource('dynamodb', region_name='eu-west-1')
hist_rows = ddb.Table('CheltenhamHistoricalResults').scan().get('Items', [])
print(f"Historical Cheltenham rows: {len(hist_rows)}")

years = sorted(set(str(i.get('year','?')) for i in hist_rows))
print(f"Years covered: {years}")

# ── Trainer festival stats ───────────────────────────────────────────────────
trainer_stats = defaultdict(lambda: {'runs':0,'wins':0,'places':0,'sp_sum':0.0})
for r in hist_rows:
    t   = str(r.get('trainer','?'))
    pos = str(r.get('position','?'))
    sp  = str(r.get('sp_dec','0'))
    trainer_stats[t]['runs'] += 1
    if pos == '1st':
        trainer_stats[t]['wins'] += 1
    if pos in ('1st','2nd','3rd'):
        trainer_stats[t]['places'] += 1
    try:
        trainer_stats[t]['sp_sum'] += float(sp)
    except Exception:
        pass

print()
print('=' * 75)
print('  CHELTENHAM FESTIVAL HISTORICAL WIN RATES (actual results)')
print('=' * 75)
print(f"  {'Trainer':<30}  {'Runs':>5}  {'Wins':>4}  {'Win%':>5}  {'Place%':>7}  {'Avg SP':>7}")
print('  ' + '-' * 60)
rows = sorted(trainer_stats.items(), key=lambda x: x[1]['wins'], reverse=True)
for t, s in rows:
    if s['runs'] < 3:
        continue
    wr = s['wins'] / s['runs'] * 100
    pr = s['places'] / s['runs'] * 100
    avg_sp = s['sp_sum'] / s['runs'] if s['runs'] else 0
    marker = ''
    if 'Mullins' in t:  marker = ' ← MULLINS'
    if 'Elliott' in t:  marker = ' ← ELLIOTT'
    if 'Henderson' in t: marker = ' ← HENDERSON'
    if 'Skelton' in t:  marker = ' ← SKELTON'
    print(f"  {t:<30}  {s['runs']:>5}  {s['wins']:>4}  {wr:>4.0f}%  {pr:>6.0f}%  {avg_sp:>6.1f}{marker}")

# ── By year breakdown for Mullins & Elliott ──────────────────────────────────
print()
print('=' * 75)
print('  MULLINS vs ELLIOTT — YEAR BY YEAR CHELTENHAM RECORD')
print('=' * 75)
for trainer_key, label in [('W P Mullins','W.P. Mullins'), ('G Elliott','Gordon Elliott')]:
    trecs = [r for r in hist_rows if str(r.get('trainer','')) == trainer_key]
    if not trecs:
        continue
    by_year = defaultdict(lambda: {'runs':0,'wins':0})
    for r in trecs:
        y = str(r.get('year','?'))
        by_year[y]['runs'] += 1
        if str(r.get('position','')) == '1st':
            by_year[y]['wins'] += 1
    print(f"\n  {label}:")
    total_r = total_w = 0
    for y in sorted(by_year.keys()):
        ry = by_year[y]
        print(f"    {y}: {ry['runs']:2d} runs  {ry['wins']:2d} wins  ({ry['wins']/ry['runs']*100:.0f}%)")
        total_r += ry['runs'];  total_w += ry['wins']
    print(f"    TOTAL: {total_r} runs  {total_w} wins  ({total_w/total_r*100:.0f}%)")

# ── Race-type breakdown for Mullins at festival ──────────────────────────────
print()
print('=' * 75)
print('  MULLINS — WHICH RACE TYPES WIN at CHELTENHAM?')
print('=' * 75)
mullins_recs = [r for r in hist_rows if 'Mullins' in str(r.get('trainer',''))]
race_types = defaultdict(lambda: {'runs':0,'wins':0})
for r in mullins_recs:
    rname = str(r.get('race_name','?'))
    # Classify by race type keyword
    if 'Hurdle' in rname and 'Nov' in rname:    rt = 'Novice Hurdle'
    elif 'Hurdle' in rname and 'Champion' in rname: rt = 'Champion Hurdle'
    elif 'Hurdle' in rname:                     rt = 'Hurdle (other)'
    elif 'Chase' in rname and 'Nov' in rname:   rt = 'Novice Chase'
    elif 'Chase' in rname and 'Champion' in rname: rt = 'Champion Chase'
    elif 'Chase' in rname and 'Gold' in rname:  rt = 'Gold Cup'
    elif 'Chase' in rname:                      rt = 'Chase (other)'
    elif 'Bumper' in rname or 'NHF' in rname:   rt = 'Champion Bumper'
    else:                                        rt = rname[:30]
    race_types[rt]['runs'] += 1
    if str(r.get('position','')) == '1st':
        race_types[rt]['wins'] += 1

for rt, s in sorted(race_types.items(), key=lambda x: x[1]['runs'], reverse=True):
    wr = s['wins']/s['runs']*100 if s['runs'] else 0
    indicator = '★' if wr >= 25 else ('✓' if wr >= 15 else '✗')
    print(f"  {indicator} {rt:<30}: {s['runs']} runs  {s['wins']} wins  ({wr:.0f}%)")

# ── Cross-reference with scoring engine ─────────────────────────────────────
print()
print('=' * 75)
print('  SCORING ENGINE vs HISTORICAL REALITY CHECK')
print('=' * 75)
# Load backtest
with open('backtest_dataset.json') as f:
    bt = json.load(f)

# Historical festival WR
all_runs  = len(hist_rows)
all_wins  = sum(1 for r in hist_rows if str(r.get('position',''))=='1st')
m_runs    = trainer_stats.get('W P Mullins',{}).get('runs',0)
m_wins    = trainer_stats.get('W P Mullins',{}).get('wins',0)
e_runs    = trainer_stats.get('G Elliott',{}).get('runs',0)
e_wins    = trainer_stats.get('G Elliott',{}).get('wins',0)
hend_runs = trainer_stats.get('N J Henderson',{}).get('runs',0)
hend_wins = trainer_stats.get('N J Henderson',{}).get('wins',0)

overall_wr = all_wins / all_runs * 100 if all_runs else 0
m_wr       = m_wins / m_runs * 100 if m_runs else 0
e_wr       = e_wins / e_runs * 100 if e_runs else 0
hend_wr    = hend_wins / hend_runs * 100 if hend_runs else 0

print(f"\n  Historical Cheltenham win rates (across {all_runs} runners, {years[0]}-{years[-1]}):")
print(f"    Festival average:   {overall_wr:.0f}%  ({all_wins}/{all_runs})")
print(f"    W.P. Mullins:       {m_wr:.0f}%  ({m_wins}/{m_runs})  — {m_wr/overall_wr:.1f}x average")
print(f"    G. Elliott:         {e_wr:.0f}%  ({e_wins}/{e_runs})  — {e_wr/overall_wr:.1f}x average")
print(f"    N.J. Henderson:     {hend_wr:.0f}%  ({hend_wins}/{hend_runs})  — {hend_wr/overall_wr:.1f}x average")

# Current pick concentration
picks_resp = ddb.Table('CheltenhamPicks').scan().get('Items', [])
m_picks  = len([p for p in picks_resp if 'Mullins' in str(p.get('trainer',''))])
e_picks  = len([p for p in picks_resp if 'Elliott' in str(p.get('trainer',''))])
tot_picks = len(picks_resp)
print(f"\n  Current 2026 pick concentration:")
print(f"    Total picks: {tot_picks}")
print(f"    Mullins:  {m_picks} picks = {m_picks/tot_picks*100:.0f}% of database  (historical runners: {m_runs/all_runs*100:.0f}%)")
print(f"    Elliott:  {e_picks} picks = {e_picks/tot_picks*100:.0f}% of database  (historical runners: {e_runs/all_runs*100:.0f}%)")

# Expected representation based on historical run rates
m_expected_pct = m_runs / all_runs * 100
e_expected_pct = e_runs / all_runs * 100
m_over = (m_picks/tot_picks*100) / m_expected_pct if m_expected_pct else 0
e_over = (e_picks/tot_picks*100) / e_expected_pct if e_expected_pct else 0

print(f"\n  Over-representation vs expected:")
print(f"    Mullins: runs {m_expected_pct:.0f}% of horses historically → {m_picks/tot_picks*100:.0f}% of our picks ({m_over:.1f}x OVER)")
print(f"    Elliott: runs {e_expected_pct:.0f}% of horses historically → {e_picks/tot_picks*100:.0f}% of our picks ({e_over:.1f}x OVER)")

# ── RECOMMENDATIONS ──────────────────────────────────────────────────────────
print()
print('=' * 75)
print('  RECOMMENDATIONS FOR SCORING ENGINE')
print('=' * 75)
print()
print(f"  FINDING 1: Mullins historical WR at Cheltenham = {m_wr:.0f}% (festival avg {overall_wr:.0f}%)")
print(f"  → Mullins IS genuinely ~{m_wr/overall_wr:.0f}x better than average. Trainer bonus is justified.")
print(f"  → BUT: our picks are {m_over:.1f}x over-concentrated. The bonus creates score inflation")
print(f"    that sweeps EVERY Mullins horse to the top, even weak ones.")
print()
print(f"  FINDING 2: Elliott WR = {e_wr:.0f}% ({e_wr/overall_wr:.1f}x average)")
print(f"  → Elliott is a positive but smaller edge. Should score lower than Mullins.")
print()
print(f"  FINDING 3: Backtest win rate across all picks = only {sum(1 for r in bt if r.get('outcome')=='WON')/len(bt)*100:.0f}%")
print(f"  → Non-Cheltenham picks are very poorly calibrated. Cheltenham scoring is separate but")
print(f"    the trainer bonus alone is insufficient to justify a pick.")
print()
print("  SUGGESTED SCORING ADJUSTMENTS:")
print("  ┌─────────────────────────────────────────────────────────┐")
print("  │ TRAINER BONUS — add GUARD RAILS, not reduce the total   │")
print("  │                                                         │")
print("  │  Current: Mullins +15, Elliott +12 (flat bonus)         │")
print("  │                                                         │")
print("  │  Proposed: Tiered by supporting evidence                │")
print("  │    Mullins + strong form + festival class:   +15 (keep) │")
print("  │    Mullins alone (no other evidence):        +8  (halve)│")
print("  │    Elliott + strong form:                    +12 (keep) │")
print("  │    Elliott alone:                            +6  (halve)│")
print("  │                                                         │")
print("  │  ADD DEDUCTION for trainers with 0 wins at festival:    │")
print("  │    Trainer with 0 Cheltenham wins in 5+ runs: -5        │")
print("  └─────────────────────────────────────────────────────────┘")
print()
print("  RACE TYPES where Mullins premium is most justified:")
mullins_best = [(rt, s) for rt, s in race_types.items() if s['wins'] > 0]
mullins_best.sort(key=lambda x: x[1]['wins']/x[1]['runs'], reverse=True)
for rt, s in mullins_best:
    print(f"    ★ {rt}: {s['wins']}/{s['runs']} = {s['wins']/s['runs']*100:.0f}%  ←  premium justified")
print()
print("  RACE TYPES where Mullins premium is NOT justified (0 wins):")
mullins_zero = [(rt, s) for rt, s in race_types.items() if s['wins'] == 0 and s['runs'] >= 3]
for rt, s in mullins_zero:
    print(f"    ✗ {rt}: 0/{s['runs']} = 0%  ←  trainer bonus over-inflating weak picks")

"""
Analyse what we'd need to hit 2-3 winners per day.
- How many picks/day currently?
- Where are the missed winners?
- What signals fire for winners vs losers?
"""
import boto3
from boto3.dynamodb.conditions import Attr
from collections import defaultdict

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

WIN_OUTCOMES     = {'win', 'won'}
SETTLED_OUTCOMES = {'win', 'won', 'loss', 'lost', 'placed'}

# ── 1. UI picks with settled outcomes ───────────────────────────────────────
def scan_all(filt):
    items = []
    kwargs = {'FilterExpression': filt}
    while True:
        resp = table.scan(**kwargs)
        items += resp['Items']
        if not resp.get('LastEvaluatedKey'):
            break
        kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']
    return [i for i in items if i.get('bet_id') != 'SYSTEM_ANALYSIS_MANIFEST']

ui_items = scan_all(
    Attr('bet_date').between('2026-03-22', '2026-03-30') & Attr('show_in_ui').eq(True)
)
settled_picks = [
    i for i in ui_items
    if str(i.get('outcome', '')).lower().strip() in SETTLED_OUTCOMES
]

print(f"Settled UI picks Mar 22-30: {len(settled_picks)}")
if not settled_picks:
    print("  [no data - check bet_date / show_in_ui fields]")
else:
    day_groups = defaultdict(list)
    for i in settled_picks:
        day_groups[i.get('bet_date', '')[:10]].append(i)

    print('\nDate          Picks  Wins  Strike  Horses')
    for d in sorted(day_groups):
        picks = day_groups[d]
        wins = [p for p in picks if str(p.get('outcome', '')).lower().strip() in WIN_OUTCOMES]
        horses = ', '.join(
            p.get('horse', '?')
            for p in sorted(picks, key=lambda x: x.get('race_time', ''))
        )
        print(f'{d}  {len(picks):5}  {len(wins):4}  {len(wins)/len(picks)*100:5.0f}%  {horses[:90]}')

    winners = [i for i in settled_picks if str(i.get('outcome', '')).lower().strip() in WIN_OUTCOMES]
    losers  = [i for i in settled_picks if str(i.get('outcome', '')).lower().strip() not in WIN_OUTCOMES]
    print(f'\nTotal: {len(settled_picks)} picks, {len(winners)} wins ({len(winners)/len(settled_picks)*100:.1f}%)')

    if winners:
        w_scores = [float(i.get('comprehensive_score', 0)) for i in winners]
        l_scores = [float(i.get('comprehensive_score', 0)) for i in losers] if losers else [0]
        print(f'Avg winner score: {sum(w_scores)/len(w_scores):.1f}')
        print(f'Avg loser score:  {sum(l_scores)/len(l_scores):.1f}')

# ── 2. All settled records — find missed winners ─────────────────────────────
print('\n--- LOADING ALL SETTLED RECORDS ---')
all_items = scan_all(Attr('bet_date').between('2026-03-22', '2026-03-30'))
all_settled = [i for i in all_items if str(i.get('outcome', '')).lower().strip() in SETTLED_OUTCOMES]
print(f'Total settled records: {len(all_settled)}')

races = defaultdict(list)
for i in all_settled:
    rkey = (
        i.get('race_key')
        or f"{i.get('bet_date','')[:10]}_{i.get('course','')}_{str(i.get('race_time',''))[:5]}"
    )
    races[rkey].append(i)

missed = []
for rkey, runners in races.items():
    our_picks = [r for r in runners if r.get('show_in_ui')]
    if not our_picks:
        continue
    our_pick = sorted(our_picks, key=lambda x: -float(x.get('comprehensive_score', 0)))[0]
    if str(our_pick.get('outcome', '')).lower().strip() in WIN_OUTCOMES:
        continue  # we won
    winner = next(
        (r for r in runners if str(r.get('outcome', '')).lower().strip() in WIN_OUTCOMES),
        None
    )
    if not winner:
        continue
    missed.append({
        'date':          our_pick.get('bet_date', '')[:10],
        'course':        our_pick.get('course', '?'),
        'race_time':     str(our_pick.get('race_time', ''))[:16],
        'our_pick':      our_pick.get('horse', '?'),
        'our_score':     float(our_pick.get('comprehensive_score', 0)),
        'our_odds':      float(our_pick.get('odds', 0)),
        'winner':        winner.get('horse', '?'),
        'winner_score':  float(winner.get('comprehensive_score', 0)),
        'winner_odds':   float(winner.get('odds', 0)),
        'winner_form':   winner.get('form', ''),
        'winner_sb':     winner.get('score_breakdown') or {},
        'our_sb':        our_pick.get('score_breakdown') or {},
    })

missed.sort(key=lambda x: x['date'])
print(f'\nRaces we lost where winner was in the field: {len(missed)}')
print()
hdr = f'{"Date":12} {"Course":12} {"Time":5} {"Our Pick":22} {"Sc":4} {"Od":5}  |  {"WINNER":22} {"Sc":4} {"Od":5}  form   gap'
print(hdr)
print('-' * len(hdr))
for r in missed:
    gap = r['winner_score'] - r['our_score']
    gap_str = f'+{gap:.0f}' if gap >= 0 else f'{gap:.0f}'
    t = r['race_time'][11:16] if len(r['race_time']) > 10 else r['race_time'][:5]
    print(
        f'{r["date"]:12} {r["course"][:12]:12} {t:5} '
        f'{r["our_pick"][:22]:22} {r["our_score"]:4.0f} {r["our_odds"]:5.1f}  |  '
        f'{r["winner"][:22]:22} {r["winner_score"]:4.0f} {r["winner_odds"]:5.1f}  '
        f'{r["winner_form"][:6]:<6}  {gap_str}'
    )

# ── 3. Signal delta analysis ─────────────────────────────────────────────────
print('\n\n--- SIGNALS WHERE WINNER OUTSCORED OUR PICK ---')
signal_deltas = defaultdict(list)
for r in missed:
    all_keys = set(list(r['winner_sb'].keys()) + list(r['our_sb'].keys()))
    for k in all_keys:
        w_val = float(r['winner_sb'].get(k, 0))
        o_val = float(r['our_sb'].get(k, 0))
        delta = w_val - o_val
        if abs(delta) > 1:
            signal_deltas[k].append(delta)

print(f'\nWhere winner outscored us (avg delta > +3):')
for sig, deltas in sorted(signal_deltas.items(), key=lambda x: -sum(x[1])/len(x[1])):
    avg = sum(deltas) / len(deltas)
    if avg > 3:
        print(f'  {sig:30}  avg +{avg:.1f}  (n={len(deltas)})')

print(f'\nWhere we outscored winner (avg delta < -3):')
for sig, deltas in sorted(signal_deltas.items(), key=lambda x: sum(x[1])/len(x[1])):
    avg = sum(deltas) / len(deltas)
    if avg < -3:
        print(f'  {sig:30}  avg {avg:.1f}  (n={len(deltas)})')

# ── 4. What were the winners' odds? ─────────────────────────────────────────
print('\n\n--- MISSED WINNER ODDS DISTRIBUTION ---')
from collections import Counter
bands = Counter()
for r in missed:
    o = r['winner_odds']
    if o <= 3.0:
        bands['1.0-3.0 (fav)'] += 1
    elif o <= 6.0:
        bands['3.1-6.0'] += 1
    elif o <= 10.0:
        bands['6.1-10.0'] += 1
    elif o <= 20.0:
        bands['10.1-20.0'] += 1
    else:
        bands['20+'] += 1
for band, count in sorted(bands.items()):
    print(f'  {band}: {count}')
print(f'\nAvg missed winner odds: {sum(r["winner_odds"] for r in missed)/len(missed):.1f}' if missed else '')

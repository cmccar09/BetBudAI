"""
Backtest: Top-3 by score_gap vs Top-3 by raw score — last 7 days
=================================================================
Pulls all show_in_ui picks from DynamoDB for the past 7 days (ending yesterday).
For each day:
  - METHOD A (old): top 3 picks sorted by comprehensive_score descending
  - METHOD B (new): top 3 picks sorted by score_gap descending
Compares win/loss/P&L for both methods using stake * odds for wins.
Only settled picks (outcome in win/loss/placed) are included.
"""

import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import date, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table    = dynamodb.Table('SureBetBets')

TODAY     = date.today()
START     = TODAY - timedelta(days=7)
STAKE_DEFAULT = 1.0   # 1 unit per pick for fair comparison

def fetch_day(d: date):
    """Return all show_in_ui=True settled picks for a given date."""
    resp = table.query(
        KeyConditionExpression=Key('bet_date').eq(str(d)),
        FilterExpression=Attr('show_in_ui').eq(True),
    )
    items = resp.get('Items', [])
    # Only settled picks
    settled = [
        p for p in items
        if p.get('outcome') in ('win', 'loss', 'placed')
    ]
    return settled

def pick_profit(p, stake=STAKE_DEFAULT):
    """Calculate P&L for one pick at given stake."""
    outcome = p.get('outcome', '')
    odds    = float(p.get('odds', 0))
    if outcome == 'win':
        return round(stake * (odds - 1), 2)
    elif outcome == 'placed':
        # Each Way — count as place return at 1/4 odds
        place_odds = round((odds - 1) / 4, 4)
        return round(stake * place_odds - stake, 2)
    else:
        return -stake

def method_score(picks):
    """Select top-3 by comprehensive_score descending."""
    return sorted(picks, key=lambda p: float(p.get('comprehensive_score', 0)), reverse=True)[:3]

def method_combo(picks):
    """Select top-3 by combo rank: score * 0.7 + gap * 0.3."""
    for p in picks:
        if p.get('score_gap') is None or float(p.get('score_gap', -1)) < 0:
            all_h = p.get('all_horses', [])
            my_s  = float(p.get('comprehensive_score', 0))
            if len(all_h) >= 2:
                scores = sorted([float(h.get('score', 0) or 0) for h in all_h], reverse=True)
                second = scores[1] if len(scores) > 1 else scores[0]
                p['_computed_gap'] = max(0, my_s - second)
            else:
                p['_computed_gap'] = 0
        else:
            p['_computed_gap'] = float(p.get('score_gap', 0))
    def _rank(p):
        s = float(p.get('comprehensive_score', 0))
        g = p.get('_computed_gap', 0)
        return s * 0.7 + g * 0.3
    return sorted(picks, key=_rank, reverse=True)[:3]

def method_gap(picks):
    """Select top-3 by score_gap descending (widest margin over 2nd horse)."""
    # score_gap may be stored in DB, or we compute it from all_horses
    for p in picks:
        if p.get('score_gap') is None or float(p.get('score_gap', -1)) < 0:
            all_h  = p.get('all_horses', [])
            my_s   = float(p.get('comprehensive_score', 0))
            if len(all_h) >= 2:
                scores = sorted([float(h.get('score', 0) or 0) for h in all_h], reverse=True)
                second = scores[1] if scores[1] < my_s else scores[0]
                p['_computed_gap'] = max(0, my_s - second)
            else:
                p['_computed_gap'] = 0
        else:
            p['_computed_gap'] = float(p.get('score_gap', 0))
    return sorted(picks, key=lambda p: p.get('_computed_gap', 0), reverse=True)[:3]

# ── Main ──────────────────────────────────────────────────────────────────────
print("=" * 110)
print(f"BACKTEST: Top-3 by Score  vs  Top-3 by Gap  vs  Top-3 by Combo (score*0.7+gap*0.3) — {START} → {TODAY - timedelta(days=1)}")
print("=" * 110)
print(f"{'Date':<12}  {'METHOD A (score)':<28}  {'METHOD B (gap)':<28}  {'METHOD C (combo)':<28}")
print(f"{'':12}  {'W/L':6} {'P&L':8}  {'W/L':6} {'P&L':8}  {'W/L':6} {'P&L':8}")
print("-" * 110)

totals = {'A': {'picks':0,'wins':0,'profit':0.0,'settled':0},
          'B': {'picks':0,'wins':0,'profit':0.0,'settled':0},
          'C': {'picks':0,'wins':0,'profit':0.0,'settled':0}}

day_rows = []

for i in range(7):
    d = START + timedelta(days=i)
    if d >= TODAY:
        break
    all_picks = fetch_day(d)
    if not all_picks:
        continue

    sel_A = method_score(all_picks)
    sel_B = method_gap(all_picks)
    sel_C = method_combo(all_picks)

    def summarise(sel, label):
        settled = [p for p in sel if p.get('outcome') in ('win','loss','placed')]
        wins    = sum(1 for p in settled if p.get('outcome') == 'win')
        profit  = sum(pick_profit(p) for p in settled)
        return settled, wins, profit

    sA, wA, pA = summarise(sel_A, 'A')
    sB, wB, pB = summarise(sel_B, 'B')
    sC, wC, pC = summarise(sel_C, 'C')

    for k, sel, s, w, p in [('A',sel_A,sA,wA,pA),('B',sel_B,sB,wB,pB),('C',sel_C,sC,wC,pC)]:
        totals[k]['picks']   += len(sel)
        totals[k]['settled'] += len(s)
        totals[k]['wins']    += w
        totals[k]['profit']  += p

    wl_A = f"{wA}W/{len(sA)-wA}L"
    wl_B = f"{wB}W/{len(sB)-wB}L"
    wl_C = f"{wC}W/{len(sC)-wC}L"

    print(f"{str(d):<12}  {wl_A:<6} {pA:+8.2f}  {wl_B:<6} {pB:+8.2f}  {wl_C:<6} {pC:+8.2f}")

    day_rows.append((d, sel_A, sel_B, sel_C))

print("-" * 110)
pnl_A = totals['A']['profit']
pnl_B = totals['B']['profit']
pnl_C = totals['C']['profit']
roi_A = pnl_A / (totals['A']['settled'] * STAKE_DEFAULT) * 100 if totals['A']['settled'] else 0
roi_B = pnl_B / (totals['B']['settled'] * STAKE_DEFAULT) * 100 if totals['B']['settled'] else 0
roi_C = pnl_C / (totals['C']['settled'] * STAKE_DEFAULT) * 100 if totals['C']['settled'] else 0
wl_A  = f"{totals['A']['wins']}W/{totals['A']['settled']-totals['A']['wins']}L"
wl_B  = f"{totals['B']['wins']}W/{totals['B']['settled']-totals['B']['wins']}L"
wl_C  = f"{totals['C']['wins']}W/{totals['C']['settled']-totals['C']['wins']}L"
print(f"{'TOTAL':<12}  {wl_A:<6} {pnl_A:+8.2f}  {wl_B:<6} {pnl_B:+8.2f}  {wl_C:<6} {pnl_C:+8.2f}")
print(f"{'ROI':<12}  {'':6} {roi_A:+7.1f}%  {'':6} {roi_B:+7.1f}%  {'':6} {roi_C:+7.1f}%")
print("=" * 110)
best_name = max([('A (score)', pnl_A), ('B (gap)', pnl_B), ('C (combo)', pnl_C)], key=lambda x: x[1])
print(f"\nVERDICT: Method {best_name[0]} wins with {best_name[1]:+.2f} units P&L")

# ── Per-day detail ────────────────────────────────────────────────────────────
print("\n\nDETAIL — where the two methods diverge (different picks chosen)\n")
for d, sel_A, sel_B, sel_C in day_rows:
    horses_A = {p['horse'] for p in sel_A}
    horses_B = {p['horse'] for p in sel_B}
    horses_C = {p['horse'] for p in sel_C}
    all_horses = horses_A | horses_B | horses_C
    if horses_A == horses_B == horses_C:
        print(f"{d}: Identical picks all methods")
        continue
    print(f"{d}: Methods diverged")
    all_picks_dict = {}
    for p in sel_A + sel_B + sel_C:
        all_picks_dict[p['horse']] = p
    for horse, p in all_picks_dict.items():
        methods = []
        if horse in horses_A: methods.append('A')
        if horse in horses_B: methods.append('B')
        if horse in horses_C: methods.append('C')
        gap   = p.get('_computed_gap', float(p.get('score_gap', 0)))
        score = float(p.get('comprehensive_score', 0))
        out   = p.get('outcome','?')
        odds  = float(p.get('odds',0))
        icon  = '✅' if out=='win' else '❌' if out=='loss' else '🔶' if out=='placed' else '⏳'
        label = '+'.join(methods)
        print(f"  [{label:<5}]: {icon} {horse:<28} score={score:.0f}  gap={gap:.1f}  @{odds:.2f}  {out}")
    print()

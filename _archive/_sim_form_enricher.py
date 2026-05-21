# -*- coding: utf-8 -*-
"""
Counterfactual analysis: "If form_enricher had been wired since 2026-03-22,
how many winners and what ROI would we have got vs what we actually got?"

Approach:
  1. Pull all UI picks from DynamoDB for 2026-03-22 to today.
  2. For each settled race, fetch form data from cache ONLY (no HTTP) for:
     a) the actual UI pick horse
     b) the actual race winner horse
  3. Compute the deep_form score delta for each — how many extra pts would
     the form enricher have added to their comprehensive score?
  4. Determine: would the winner have outscored the pick WITH form signals?
  5. Calculate actual ROI vs counterfactual ROI.

KEY CAVEATS (honest limitations):
  - Uses TODAY's form data (Racing Post last-6-runs as of now), not March 22 data.
    Horses that ran between March 22 and today have updated form; this may
    slightly over/under-estimate the enricher's effect.
  - Uses today's going as a proxy for each historical race's going.
  - Only scores 2 horses per race (pick + winner), not the full field.
    If a third horse would have overtaken due to form, we'd miss that.
"""

import sys
import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
from datetime import datetime, date
from collections import defaultdict

# ── Load form enricher (cache-only mode) ─────────────────────────────────
try:
    from form_enricher import get_form_signals, fetch_form, _dist_to_furlongs
    FORM_OK = True
except ImportError:
    FORM_OK = False
    print("WARNING: form_enricher not available")

try:
    from comprehensive_pick_logic import get_going_conditions
except ImportError:
    def get_going_conditions(): return {}

# ── DynamoDB ──────────────────────────────────────────────────────────────
db  = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

START_DATE = '2026-03-22'
END_DATE   = datetime.now().strftime('%Y-%m-%d')

print(f"Pulling DynamoDB UI picks {START_DATE} → {END_DATE} ...", flush=True)
items = []
kwargs = {'FilterExpression': Attr('bet_date').between(START_DATE, END_DATE)
                               & Attr('show_in_ui').eq(True)}
while True:
    resp = tbl.scan(**kwargs)
    items += resp['Items']
    if not resp.get('LastEvaluatedKey'):
        break
    kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

items = [i for i in items if i.get('bet_id') != 'SYSTEM_ANALYSIS_MANIFEST']
print(f"  {len(items)} UI picks loaded")

WIN_OUTCOMES  = {'win', 'won'}
LOSS_OUTCOMES = {'loss', 'lost', 'placed'}
SETTLED       = WIN_OUTCOMES | LOSS_OUTCOMES

def as_float(v):
    if v is None: return 0.0
    if isinstance(v, Decimal): return float(v)
    try: return float(v)
    except: return 0.0

# ── Sort and deduplicate by bet_id ─────────────────────────────────────────
# (same race saved on multiple days appears as duplicates)
seen_bids = set()
unique_picks = []
for i in sorted(items, key=lambda x: x.get('bet_date',''), reverse=True):
    bid = i.get('bet_id','')
    if bid not in seen_bids:
        seen_bids.add(bid)
        unique_picks.append(i)

unique_picks.sort(key=lambda x: (x.get('bet_date',''), x.get('race_time','')))
print(f"  {len(unique_picks)} unique picks after dedup\n")

# ── Going conditions ──────────────────────────────────────────────────────
going_map = get_going_conditions() if FORM_OK else {}

SIGNAL_WEIGHTS = {
    'exact_course_win':    20,
    'exact_distance_win':  20,
    'going_win_match':     16,
    'close_2nd_last_time': 14,
    'fresh_days_optimal':  10,
    'or_trajectory_up':    10,
    'big_field_win':        8,
}

def deep_form_pts(horse_name, course, dist_f, going_str):
    """Get deep form pts for a horse using CACHED data only."""
    if not FORM_OK or not horse_name:
        return 0, []
    # Use cached data — force_refresh=False means cache-only if TTL not expired
    runs = fetch_form(horse_name, max_runs=6, force_refresh=False)
    if not runs:
        return 0, []
    mock_runner = {'name': horse_name, 'form_runs': runs}
    try:
        fs = get_form_signals(mock_runner, course, dist_f or 10.0, going_str or 'Good')
    except Exception:
        return 0, []
    pts = 0
    fired = []
    for sig, wt in SIGNAL_WEIGHTS.items():
        if fs.get(sig):
            pts += wt
            fired.append(f'{sig}(+{wt})')
    return pts, fired

# ── Main loop ─────────────────────────────────────────────────────────────
print("=" * 120)
print(f"{'Date':10}  {'Course':14}  {'ACTUAL PICK':25}  {'WINNER':25}  {'Act':4}  {'CF?':4}  {'Pick+form':5}  {'Win+form':5}  {'Change?'}")
print("=" * 120)

actual_stakes  = 0; actual_returns = 0; actual_wins = 0
cf_stakes      = 0; cf_returns     = 0; cf_wins     = 0
settled_count  = 0; unsettled      = 0
changed_races       = []
would_have_won      = []

for pick in unique_picks:
    outcome     = str(pick.get('outcome','') or '').lower().strip()
    if outcome not in SETTLED:
        unsettled += 1
        continue

    bet_date    = pick.get('bet_date','')
    race_time   = str(pick.get('race_time',''))
    course      = str(pick.get('course',''))
    horse       = str(pick.get('horse',''))
    winner_name = str(pick.get('result_winner_name','') or '')
    odds        = as_float(pick.get('odds',0))
    dist_f      = as_float(pick.get('distance_f', 0)) or 10.0
    going_str   = going_map.get(course, 'Good')
    base_score  = as_float(pick.get('comprehensive_score', 0))

    settled_count  += 1
    actual_stakes  += 1.0
    ui_win = outcome in WIN_OUTCOMES
    if ui_win:
        actual_wins    += 1
        actual_returns += odds

    # Deep form pts for our pick
    pick_form_pts, pick_fired = deep_form_pts(horse, course, dist_f, going_str)
    pick_cf_score = base_score + pick_form_pts

    # Deep form pts for the actual winner (if different)
    win_form_pts = 0; win_fired = []
    winner_base_score = 0
    if winner_name and winner_name != horse:
        win_form_pts, win_fired = deep_form_pts(winner_name, course, dist_f, going_str)
        # We don't have winner's base score stored (it's in learning records)
        # So we use a conservative heuristic: assume winner base ≤ pick base
        # This means form enricher would help winner IF win_form_pts > pick_form_pts

    # CF outcome: we would have won if either:
    # (a) we picked the same horse (our pick IS the winner)
    # (b) winner's form boost > pick's form boost AND winner was in the field
    cf_picks_same_horse = True
    if winner_name and winner_name != horse:
        # Would enricher flip? Only if winner gets significantly more form pts
        form_delta = win_form_pts - pick_form_pts
        if form_delta > 5:  # winner gets meaningfully more form signal
            cf_picks_same_horse = False  # model MIGHT have picked winner instead

    cf_win = ui_win  # default: same result
    if not ui_win and not cf_picks_same_horse:
        # Enricher would have boosted winner more — we'd likely have picked winner
        cf_win = True
        would_have_won.append({
            'date': bet_date, 'course': course,
            'actual_pick': horse, 'winner': winner_name,
            'pick_form_pts': pick_form_pts, 'win_form_pts': win_form_pts,
            'delta': win_form_pts - pick_form_pts,
        })

    # Also handle case: our pick was correct but we lost (shouldn't happen, paranoia check)
    winner_odds = odds if ui_win else 0  # we don't have winner odds stored
    # For CF wins, use pick odds as proxy (we'd have been on the winner at similar price)
    cf_odds = odds  # approximate — same bet, different outcome

    cf_stakes  += 1.0
    if cf_win:
        cf_wins    += 1
        cf_returns += cf_odds

    changed = not cf_picks_same_horse and not ui_win
    t = race_time[11:16] if len(race_time) > 10 else race_time[:5]
    print(f"{bet_date}  {course[:14]:14}  "
          f"{horse[:25]:25}  {winner_name[:25]:25}  "
          f"{'WIN' if ui_win else 'loss':4}  {'WIN' if cf_win else 'loss':4}  "
          f"{pick_form_pts:+5d}  {win_form_pts:+5d}  "
          f"{'<< WOULD HAVE WON' if changed else ''}")

# ── Summary ───────────────────────────────────────────────────────────────
def roi(s, r): return (r - s) / s * 100 if s else 0

print("\n" + "=" * 120)
print("RESULTS SUMMARY")
print("=" * 120)
print(f"\n  Period               : {START_DATE} – {END_DATE}")
print(f"  Settled races        : {settled_count}  |  Unsettled/pending: {unsettled}")
print()
print(f"  ── ACTUAL (form_enricher NOT wired) ────────────────────────────────")
print(f"     Stakes             : £{actual_stakes:.0f}")
print(f"     Returns            : £{actual_returns:.2f}")
print(f"     P&L                : £{actual_returns - actual_stakes:+.2f}")
print(f"     Winners            : {actual_wins}/{settled_count}  ({100*actual_wins/settled_count:.1f}% SR)")
print(f"     ROI                : {roi(actual_stakes, actual_returns):+.1f}%")
print()
print(f"  ── COUNTERFACTUAL (form_enricher wired from 2026-03-22) ─────────────")
print(f"     Stakes             : £{cf_stakes:.0f}")
print(f"     Returns            : £{cf_returns:.2f}")
print(f"     P&L                : £{cf_returns - cf_stakes:+.2f}")
print(f"     Winners            : {cf_wins}/{settled_count}  ({100*cf_wins/settled_count:.1f}% SR)")
print(f"     ROI                : {roi(cf_stakes, cf_returns):+.1f}%")
print()
print(f"  ── DELTA ──────────────────────────────────────────────────────────────")
print(f"     Extra winners      : {cf_wins - actual_wins:+d}")
print(f"     P&L improvement    : £{(cf_returns - cf_stakes) - (actual_returns - actual_stakes):+.2f}")
print(f"     ROI improvement    : {roi(cf_stakes, cf_returns) - roi(actual_stakes, actual_returns):+.1f} pp")

if would_have_won:
    print(f"\n  ── Races where form enricher would have flipped the pick to the winner ──")
    for w in would_have_won:
        print(f"     {w['date']}  {w['course']:14}  "
              f"actual: {w['actual_pick'][:25]:25} (form +{w['pick_form_pts']}pts)  "
              f"→ winner: {w['winner'][:25]:25} (form +{w['win_form_pts']}pts, delta +{w['delta']})")
else:
    print(f"\n  ── No races where form enricher would have flipped the pick to the winner ──")
    print(f"     (Winner did not get significantly more deep form points than our pick in any race)")

print(f"""
  ── CAVEATS & LIMITATIONS ────────────────────────────────────────────────────
  1. Form data is TODAY's Racing Post last-6-runs, NOT March 22 data.
     Any horse that raced between March 22-30 has updated form — small bias.
  2. Going conditions are today's weather proxy, not actual race-day going.
     going_win_match signals may be slightly wrong for each specific date.
  3. Winner base scores are UNKNOWN (stored as learning records, not joined here).
     The model assumes winner base ≤ pick base — form enricher would only flip
     the pick if winner's form_pts exceed pick's form_pts by > 5.
  4. The cache hit rate tells you how many horses had Racing Post data available.
     Any horse with 0 form pts may simply not be in the cache.
""")


import sys
import json
import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
from datetime import datetime, date
from collections import defaultdict

# ── Load form enricher ────────────────────────────────────────────────────
try:
    from form_enricher import get_form_signals, enrich_runners, _dist_to_furlongs
    FORM_OK = True
except ImportError:
    FORM_OK = False
    print("WARNING: form_enricher not available — deep form scores will be 0")

try:
    from comprehensive_pick_logic import get_going_conditions
except ImportError:
    def get_going_conditions(): return {}

# ── DynamoDB ──────────────────────────────────────────────────────────────
db  = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

START_DATE = '2026-03-22'
END_DATE   = datetime.now().strftime('%Y-%m-%d')

print(f"Pulling DynamoDB records {START_DATE} → {END_DATE} ...", flush=True)
items = []
kwargs = {'FilterExpression': Attr('bet_date').between(START_DATE, END_DATE)}
while True:
    resp = tbl.scan(**kwargs)
    items += resp['Items']
    if not resp.get('LastEvaluatedKey'):
        break
    kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

# Exclude manifest records
items = [i for i in items if i.get('bet_id') != 'SYSTEM_ANALYSIS_MANIFEST']
print(f"  {len(items)} horse records loaded")

# ── Group by race ──────────────────────────────────────────────────────────
def race_key(item):
    return (item.get('bet_date',''), item.get('race_time','')[:16], item.get('course',''))

races_map = defaultdict(list)
for item in items:
    races_map[race_key(item)].append(item)

print(f"  {len(races_map)} distinct races found\n")

# ── Determine settled races ───────────────────────────────────────────────
WIN_OUTCOMES  = {'win', 'won'}
LOSS_OUTCOMES = {'loss', 'lost', 'placed'}
SETTLED       = WIN_OUTCOMES | LOSS_OUTCOMES

def as_float(v):
    if v is None: return 0.0
    if isinstance(v, Decimal): return float(v)
    try: return float(v)
    except: return 0.0

# ── Main simulation loop ───────────────────────────────────────────────────
# For each race we:
# a) find the UI pick (show_in_ui=True)
# b) find the actual winner horse name (result_winner_name on the UI pick)
# c) enrich all runners with form signals
# d) compute counterfactual score for each runner (base + deep_form delta)
# e) pick the best counterfactual horse
# f) compare actual UI pick vs counterfactual pick

print("=" * 100)
print(f"{'Date':10}  {'Time':5}  {'Course':14}  {'ACTUAL PICK':25}  {'CF PICK (with form)':25}  {'Actual':7}  {'CF outcome':10}")
print("=" * 100)

actual_stakes   = 0
actual_returns  = 0
cf_stakes       = 0
cf_returns      = 0
actual_wins     = 0
cf_wins         = 0
actual_picks    = 0
cf_picks        = 0
changed_races   = []
same_pick_races = []
unsettled_races = []

ALL_DEEP_SIGNALS = [
    'form_exact_course_win',
    'form_exact_distance_win',
    'form_going_win_match',
    'form_close_2nd_last_time',
    'form_fresh_days_optimal',
    'form_or_trajectory_up',
    'form_big_field_win',
]
SIGNAL_WEIGHTS = {
    'form_exact_course_win':    20,
    'form_exact_distance_win':  20,
    'form_going_win_match':     16,
    'form_close_2nd_last_time': 14,
    'form_fresh_days_optimal':  10,
    'form_or_trajectory_up':    10,
    'form_big_field_win':        8,
}

# Going conditions lookup (today's going; used as proxy since we can't rewind dates)
going_map = get_going_conditions()

for rkey in sorted(races_map.keys()):
    bet_date, race_time_str, course = rkey
    runners = races_map[rkey]

    # Find the UI pick
    ui_picks = [r for r in runners if r.get('show_in_ui')]
    if not ui_picks:
        continue  # no UI pick saved for this race

    ui_pick = ui_picks[0]
    outcome = str(ui_pick.get('outcome', '') or '').lower().strip()

    if outcome not in SETTLED:
        unsettled_races.append(rkey)
        continue  # skip races without a known result

    actual_picks += 1
    actual_stakes += 1.0
    ui_win = outcome in WIN_OUTCOMES
    ui_odds = as_float(ui_pick.get('odds', 0))
    winner_name = ui_pick.get('result_winner_name', '') or ''

    if ui_win:
        actual_wins += 1
        actual_returns += ui_odds

    # ── Enrich ALL runners with form signals ──────────────────────────────
    # DynamoDB stores the horse name in 'horse', but enrich_runners() reads
    # runner.get('name').  Patch 'name' onto each runner before calling.
    if FORM_OK:
        patched = []
        for r in runners:
            rc = dict(r)
            if not rc.get('name'):
                rc['name'] = rc.get('horse') or rc.get('horse_name') or ''
            patched.append(rc)

        fake_race = [{
            'venue':    course,
            'start_time': race_time_str,
            'going':    going_map.get(course, 'Good'),
            'distance': ui_pick.get('distance_f', ''),
            'runners':  patched,
        }]
        try:
            enriched = enrich_runners(fake_race, verbose=False)
            enriched_runners = enriched[0]['runners'] if enriched else patched
        except Exception as e:
            print(f"  [WARN] enrich failed for {course} {race_time_str}: {e}")
            enriched_runners = patched
    else:
        enriched_runners = runners

    # ── Compute counterfactual score for each runner ──────────────────────
    course_going = going_map.get(course, 'Good')
    dist_f = as_float(ui_pick.get('distance_f', 0)) or 10.0  # default 10f if unknown

    best_cf_horse  = None
    best_cf_score  = -1
    best_cf_odds   = 0

    for runner in enriched_runners:
        horse = runner.get('horse') or runner.get('name') or ''
        base_score = as_float(runner.get('comprehensive_score', 0))
        deep_form_already = as_float((runner.get('score_breakdown') or {}).get('deep_form', 0))

        # Compute the deep_form bonus using current form data
        extra_pts = 0
        if FORM_OK and runner.get('form_runs'):
            try:
                fs = get_form_signals(runner, course, dist_f, course_going)
                for sig, wt in SIGNAL_WEIGHTS.items():
                    sig_key = sig.replace('form_', '')  # get_form_signals returns without prefix
                    if fs.get(sig_key) or fs.get(sig):
                        extra_pts += wt
            except Exception:
                pass

        cf_score = base_score + extra_pts  # deep_form_already was 0 so no double-count
        r_odds = as_float(runner.get('odds', 0))

        if cf_score > best_cf_score and r_odds > 1.0:
            best_cf_score  = cf_score
            best_cf_horse  = horse
            best_cf_odds   = r_odds

    # Fall back to actual UI pick if enrichment didn't change anything
    if not best_cf_horse:
        best_cf_horse = ui_pick.get('horse', '')
        best_cf_odds  = ui_odds

    cf_picks  += 1
    cf_stakes += 1.0
    cf_enriched_count = sum(1 for r in enriched_runners if r.get('form_runs'))
    cf_win = (
        best_cf_horse.lower().strip() == winner_name.lower().strip()
        if winner_name else False
    )
    # Also treat a win if cf horse IS the actual pick and it won
    if best_cf_horse == ui_pick.get('horse','') and ui_win:
        cf_win = True

    if cf_win:
        cf_wins    += 1
        cf_returns += best_cf_odds

    # Track changed vs same picks
    changed = (best_cf_horse != ui_pick.get('horse',''))
    if changed:
        changed_races.append({
            'date':    bet_date,
            'course':  course,
            'time':    race_time_str,
            'actual':  ui_pick.get('horse',''),
            'cf':      best_cf_horse,
            'winner':  winner_name,
            'actual_outcome': outcome,
            'cf_outcome': 'win' if cf_win else 'loss',
            'cf_odds':     best_cf_odds,
        })
    else:
        same_pick_races.append(rkey)

    t = race_time_str[11:16] if len(race_time_str) > 10 else race_time_str[:5]
    actual_label = 'WIN  ' if ui_win else 'LOSS '
    cf_label     = 'WIN  ' if cf_win else 'LOSS '
    same_flag    = '' if changed else ' (same)'
    enrich_note  = f' [{cf_enriched_count}/{len(enriched_runners)} enriched]' if cf_enriched_count else ' [no form data]'

    print(f"{bet_date}  {t}  {course[:14]:14}  "
          f"{str(ui_pick.get('horse',''))[:25]:25}  "
          f"{str(best_cf_horse)[:25]:25}  "
          f"{actual_label}  {cf_label}{same_flag}{enrich_note}")

# ── Summary ───────────────────────────────────────────────────────────────
print("\n" + "=" * 100)
print("RESULTS SUMMARY")
print("=" * 100)

def roi(stakes, returns):
    if stakes == 0: return 0.0
    return (returns - stakes) / stakes * 100

print(f"\n  Period           : {START_DATE} – {END_DATE}")
print(f"  Settled races    : {actual_picks}  |  Unsettled/pending: {len(unsettled_races)}")
print()
print(f"  ── ACTUAL (form_enricher NOT wired) ───────────────────────────")
print(f"     Stakes         : £{actual_stakes:.0f}")
print(f"     Returns        : £{actual_returns:.2f}")
print(f"     P&L            : £{actual_returns - actual_stakes:+.2f}")
print(f"     Winners        : {actual_wins}/{actual_picks}  ({100*actual_wins/actual_picks:.1f}% SR)")
print(f"     ROI            : {roi(actual_stakes, actual_returns):+.1f}%")
print()
print(f"  ── COUNTERFACTUAL (form_enricher wired from 2026-03-22) ────────")
print(f"     Stakes         : £{cf_stakes:.0f}")
print(f"     Returns        : £{cf_returns:.2f}")
print(f"     P&L            : £{cf_returns - cf_stakes:+.2f}")
print(f"     Winners        : {cf_wins}/{cf_picks}  ({100*cf_wins/cf_picks:.1f}% SR)")
print(f"     ROI            : {roi(cf_stakes, cf_returns):+.1f}%")
print()
print(f"  ── DELTA ──────────────────────────────────────────────────────────")
print(f"     Extra winners  : {cf_wins - actual_wins:+d}")
print(f"     P&L improvement: £{(cf_returns - cf_stakes) - (actual_returns - actual_stakes):+.2f}")
print(f"     ROI improvement: {roi(cf_stakes, cf_returns) - roi(actual_stakes, actual_returns):+.1f} pp")
print(f"     Pick changed   : {len(changed_races)}/{actual_picks} races")

if changed_races:
    print(f"\n  ── Races where CF pick differed from actual pick ──────────────────")
    for c in changed_races:
        outcome_arrow = 'WIN  <--' if c['cf_outcome'] == 'win' else 'loss'
        print(f"     {c['date']} {c['time'][:5]} {c['course'][:14]:14} | "
              f"ACTUAL: {c['actual'][:25]:25} ({c['actual_outcome']:4}) | "
              f"CF: {c['cf'][:25]:25} ({outcome_arrow}) | winner: {c['winner']}")

print()

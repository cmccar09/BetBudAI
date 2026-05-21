"""
Lay-the-Fav backtest — last 8 days
Scores each race favourite with the vulnerability model and checks % that actually lost.
"""
import boto3, json
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = ddb.Table('SureBetBets')

dates = [(datetime.now(timezone.utc) - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(8)]

all_items = []
for d in dates:
    resp = tbl.query(KeyConditionExpression=Key('bet_date').eq(d))
    all_items.extend(resp['Items'])
    while resp.get('LastEvaluatedKey'):
        resp = tbl.query(
            KeyConditionExpression=Key('bet_date').eq(d),
            ExclusiveStartKey=resp['LastEvaluatedKey']
        )
        all_items.extend(resp['Items'])

def _dec(o):
    if isinstance(o, Decimal): return float(o)
    if isinstance(o, dict): return {k: _dec(v) for k, v in o.items()}
    if isinstance(o, list): return [_dec(v) for v in o]
    return o

def to_f(v, default=0.0):
    try: return float(v)
    except: return default

WEIGHTS = {
    'class_up': 4, 'trip_new': 2, 'going_unproven': 2, 'draw_poor': 1,
    'layoff': 1, 'pace_doubt': 1, 'rivals_close': 2, 'drift': 1, 'short_price': 1,
    'trainer_track': 1, 'trainer_cold': 1, 'trainer_multiple': 1, 'current_form_no_wins': 1,
}
FLAG_LABELS = {
    'short_price': 'Short Price', 'rivals_close': 'Rivals Close', 'trip_new': 'Trip Unproven',
    'going_unproven': 'Going Unproven', 'draw_poor': 'Poor Draw', 'layoff': 'Layoff',
    'pace_doubt': 'Pace Doubt', 'drift': 'Low Score Gap', 'class_up': 'Class Up',
    'trainer_track': 'Trainer @ Track', 'trainer_cold': 'Trainer Cold', 'trainer_multiple': 'Multi Runner',
    'current_form_no_wins': 'Form No Wins',
}

def score_fav(fav, runners_sorted):
    sb = fav.get('score_breakdown') or {}
    flags = {}
    fav_score = to_f(fav.get('comprehensive_score') or fav.get('score', 0))
    fav_odds  = to_f(fav.get('odds') or fav.get('decimal_odds'))
    if fav_odds and fav_odds <= 2.25:
        flags['short_price'] = True
    rivals = [h for h in runners_sorted if h.get('horse') != fav.get('horse')]
    if rivals:
        r2 = to_f(rivals[0].get('comprehensive_score') or rivals[0].get('score', 0))
        if fav_score > 0 and (r2 / fav_score) >= 0.75:
            flags['rivals_close'] = True
    if to_f(sb.get('going_suitability', 0)) == 0 and to_f(sb.get('heavy_going_penalty', 0)) == 0:
        flags['going_unproven'] = True
    if to_f(sb.get('distance_suitability', 0)) == 0 and to_f(sb.get('cd_bonus', 0)) == 0:
        flags['trip_new'] = True
    if (to_f(sb.get('official_rating_bonus', 0)) > 0
            and to_f(sb.get('cd_bonus', 0)) == 0
            and to_f(sb.get('course_performance', 0)) == 0):
        flags['class_up'] = True
    form_str = str(fav.get('form') or '')
    if form_str.count('-') >= 2:
        flags['layoff'] = True
    score_gap = to_f(fav.get('score_gap', 0))
    if 0 < score_gap < 10:
        flags['drift'] = True
    elif score_gap == 0 and fav_score > 0:
        flags['drift'] = True
    if to_f(sb.get('going_suitability', 0)) == 0 and to_f(sb.get('recent_win', 0)) == 0:
        flags['pace_doubt'] = True
    # --- Current form – no wins (+1) ---
    form_str = str(fav.get('form') or '')
    form_digits = []
    for ch in form_str.replace('-', '').replace('/', ''):
        if ch.isdigit():
            form_digits.append(int(ch))
        elif ch.upper() in ('U', 'F', 'P', 'R'):
            form_digits.append(99)
    last_4 = form_digits[-4:] if len(form_digits) >= 4 else form_digits
    if last_4 and all(pos >= 2 for pos in last_4):
        flags['current_form_no_wins'] = True
    total = sum(WEIGHTS.get(f, 1) for f in flags)
    return total, list(flags.keys())

# ── Group by race ────────────────────────────────────────────────────────────
races = {}
for it in all_items:
    it = _dec(it)
    rt     = str(it.get('race_time', ''))[:16]
    course = it.get('course', '') or it.get('race_course', '')
    key    = rt + '|' + course
    races.setdefault(key, []).append(it)

results = []
for key, runners in sorted(races.items()):
    has_settled = any(
        str(r.get('outcome', '')).upper() in ('WIN', 'LOSS', 'PLACED', 'WON', 'LOST')
        for r in runners
    )
    if not has_settled:
        continue
    sorted_r    = sorted(runners, key=lambda r: to_f(r.get('odds') or r.get('decimal_odds') or 99))
    fav         = sorted_r[0]
    fav_outcome = str(fav.get('outcome', '')).upper()
    if fav_outcome not in ('WIN', 'LOSS', 'PLACED', 'WON', 'LOST'):
        continue
    lay_score, flags = score_fav(fav, sorted_r)
    rt, course = key.split('|', 1)
    results.append({
        'date':      rt[:10],
        'time':      rt[11:16],
        'course':    course,
        'fav':       fav.get('horse', '?'),
        'odds':      to_f(fav.get('odds') or fav.get('decimal_odds')),
        'lay_score': lay_score,
        'flags':     flags,
        'outcome':   fav_outcome,
        'fav_lost':  fav_outcome in ('LOSS', 'LOST'),
        'our_pick':  fav.get('show_in_ui', False),
    })

results.sort(key=lambda x: x['date'] + x['time'])

# ── Stats ────────────────────────────────────────────────────────────────────
total     = len(results)
thresholds = [4, 6, 8, 9, 13]
stats = {}
for t in thresholds:
    subset = [r for r in results if r['lay_score'] >= t]
    lost   = [r for r in subset if r['fav_lost']]
    pct    = len(lost) / len(subset) * 100 if subset else 0
    stats[t] = {'count': len(subset), 'lost': len(lost), 'pct': round(pct, 1)}

# ── Print summary ─────────────────────────────────────────────────────────────
print(f"Total settled races: {total}")
print()
for t, s in stats.items():
    print(f"Lay score >= {t:2d}: {s['count']:2d} races | {s['lost']:2d} fav lost | {s['pct']}% success rate")
print()
print("Detail (score >= 4):")
for r in [x for x in results if x['lay_score'] >= 4]:
    mark = "✓ LOST" if r['fav_lost'] else "✗ WON"
    print(f"  {r['date']} {r['time']} {r['course']:22s} {r['fav']:25s} {r['odds']:.2f} score={r['lay_score']:2d} [{mark}]  {','.join(r['flags'])}")

print(json.dumps({'results': results, 'stats': {str(k): v for k, v in stats.items()}, 'total': total}, indent=2))

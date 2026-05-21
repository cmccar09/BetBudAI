"""Patch lambda_function.py with winner analysis and learning endpoint."""
import zipfile, re

# Read extracted source
content = open('_lambda_function_extracted.py', encoding='utf-8').read()

# 1. Allow POST in CORS headers
content = content.replace(
    "'Access-Control-Allow-Methods': 'GET,OPTIONS'",
    "'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'"
)

# 2. Add learning/apply route before the 'picks' catch-all in lambda_handler
content = content.replace(
    "elif 'picks' in path:\n\n            return get_all_picks(headers)",
    "elif 'learning/apply' in path:\n\n            return apply_learning_lambda(headers, event)\n\n        elif 'picks' in path:\n\n            return get_all_picks(headers)"
)

# 3. Inject winner_analysis attachment just before the final return statement
# of check_yesterday_results
inject = """
    # Attach winner_analysis to non-winning picks
    for pick in picks:
        oc = (pick.get('outcome') or '').lower()
        if oc in ('loss', 'placed'):
            pick['winner_analysis'] = compute_winner_analysis(pick)

"""
# Find the return statement in check_yesterday_results (second occurrence - the main return, not the empty-picks early return)
target = "    return {\n\n        'statusCode': 200,\n\n        'headers': headers,\n\n        'body': json.dumps({\n\n            'success': True,\n\n            'date': yesterday,"
content = content.replace(target, inject + target, 1)

# 4. Append new functions at the end
new_funcs = r'''

def to_fractional(decimal_odds):
    if not decimal_odds or float(decimal_odds) <= 1.0:
        return 'SP'
    d = float(decimal_odds)
    tbl = [
        (1.1,'1/10'),(1.13,'1/9'),(1.2,'1/5'),(1.25,'1/4'),(1.33,'1/3'),
        (1.4,'2/5'),(1.5,'1/2'),(1.6,'3/5'),(1.67,'4/6'),(1.8,'4/5'),
        (1.9,'9/10'),(2.0,'1/1'),(2.1,'11/10'),(2.2,'6/5'),(2.25,'5/4'),
        (2.5,'6/4'),(2.62,'13/8'),(2.75,'7/4'),(3.0,'2/1'),(3.25,'9/4'),
        (3.5,'5/2'),(3.75,'11/4'),(4.0,'3/1'),(4.5,'7/2'),(5.0,'4/1'),
        (5.5,'9/2'),(6.0,'5/1'),(7.0,'6/1'),(8.0,'7/1'),(9.0,'8/1'),
        (10.0,'9/1'),(11.0,'10/1'),(13.0,'12/1'),(16.0,'15/1'),(21.0,'20/1'),
        (26.0,'25/1'),(34.0,'33/1'),(51.0,'50/1'),(101.0,'100/1'),
    ]
    for threshold, label in tbl:
        if d <= threshold:
            return label
    return f'{int(d-1)}/1'


def compute_winner_analysis(pick):
    our_score   = float(pick.get('comprehensive_score') or pick.get('analysis_score') or 0)
    our_odds    = float(pick.get('odds') or 0)
    our_horse   = (pick.get('horse') or '').strip().lower()
    winner_name = (pick.get('result_winner_name') or '').strip()
    all_horses  = pick.get('all_horses') or []
    sb          = pick.get('score_breakdown') or {}

    if not winner_name:
        return {'winner_found': False, 'why_missed': ['Winner not yet recorded']}

    sorted_field = sorted(
        [h for h in all_horses if h.get('horse')],
        key=lambda h: float(h.get('score', 0)), reverse=True
    )

    winner_horse = next(
        (h for h in sorted_field if h.get('horse', '').strip().lower() == winner_name.lower()),
        None
    )
    winner_score = float(winner_horse.get('score', 0)) if winner_horse else 0
    winner_odds  = float(winner_horse.get('odds', 0)) if winner_horse else 0
    winner_rank  = next(
        (i + 1 for i, h in enumerate(sorted_field)
         if h.get('horse', '').strip().lower() == winner_name.lower()),
        0
    )
    score_gap    = our_score - winner_score
    why_missed   = []
    weight_nudges = {}

    if not winner_horse:
        why_missed.append(f'Winner "{winner_name}" was not in our scored Betfair field — model could not see them')
        return {'winner_found': False, 'winner_score': 0, 'winner_rank': 0,
                'winner_odds': 0, 'score_gap': score_gap,
                'why_missed': why_missed, 'weight_nudges': weight_nudges}

    if winner_odds > 0 and our_odds > 0 and winner_odds < our_odds * 0.80:
        why_missed.append(
            f'Market disagreed: winner went off at {to_fractional(winner_odds)} '
            f'vs our pick at {to_fractional(our_odds)} — odds signal should have flagged this'
        )
        weight_nudges['optimal_odds'] = weight_nudges.get('optimal_odds', 0) + 1.0

    if score_gap > 15:
        why_missed.append(
            f'Model over-confidence: we scored {our_horse.title()} {our_score:.0f}/100 '
            f'vs {winner_name} {winner_score:.0f}/100 — {score_gap:.0f}pt gap too large'
        )

    if 0 < winner_rank <= 3 and score_gap <= 10:
        ord_suffix = 'st' if winner_rank == 1 else 'nd' if winner_rank == 2 else 'rd'
        why_missed.append(
            f'{winner_name} ranked {winner_rank}{ord_suffix} '
            f'in our model at {winner_score:.0f}/100 — narrow margin, pick was defensible'
        )

    if winner_rank > 5:
        why_missed.append(
            f'{winner_name} ranked {winner_rank}th of {len(sorted_field)} in our model '
            f'({winner_score:.0f}/100) — significant model blind spot'
        )

    going_pts = float(sb.get('going_suitability', 0))
    if going_pts > 0 and our_score > 0 and (going_pts / our_score) > 0.25:
        why_missed.append(
            f'Going suitability dominated our score ({going_pts:.0f}pts = '
            f'{going_pts/our_score*100:.0f}% of total) — may have been misleading'
        )
        weight_nudges['going_suitability'] = weight_nudges.get('going_suitability', 0) - 0.5

    cd_pts = float(sb.get('cd_bonus', 0)) + float(sb.get('course_performance', 0))
    if cd_pts > 20:
        why_missed.append(
            f'Course & distance bonus inflated score ({cd_pts:.0f}pts) — '
            f'winner may have had stronger recent form on the day'
        )
        weight_nudges['cd_bonus'] = weight_nudges.get('cd_bonus', 0) - 0.3

    if winner_score < our_score * 0.85:
        weight_nudges['recent_win'] = weight_nudges.get('recent_win', 0) + 0.5

    field_size = len(sorted_field)
    if field_size <= 5 and winner_odds > 0 and winner_odds < 2.5:
        why_missed.append(
            f'Small field ({field_size} runners) with a well-backed winner — '
            f'in small fields the market price is highly predictive'
        )
        weight_nudges['optimal_odds'] = weight_nudges.get('optimal_odds', 0) + 0.5

    # Why the winner won
    winner_sb = winner_horse.get('score_breakdown') or {}
    winner_reasons = []
    if winner_odds > 0 and our_odds > 0 and winner_odds < our_odds:
        winner_reasons.append(
            f'better market confidence ({to_fractional(winner_odds)} vs our pick at {to_fractional(our_odds)})'
        )
    w_form = float(winner_sb.get('form', 0) or winner_sb.get('form_score', 0) or winner_sb.get('recent_win', 0))
    o_form = float(sb.get('form', 0) or sb.get('form_score', 0) or sb.get('recent_win', 0))
    if w_form > o_form + 3:
        winner_reasons.append(f"stronger recent form score ({w_form:.0f}pts vs our pick's {o_form:.0f}pts)")
    w_cd = float(winner_sb.get('cd_bonus', 0) or winner_sb.get('course_performance', 0))
    o_cd = float(sb.get('cd_bonus', 0) or sb.get('course_performance', 0))
    if w_cd > o_cd + 5:
        winner_reasons.append(f"superior C&D record ({w_cd:.0f}pts vs our pick's {o_cd:.0f}pts)")
    w_going = float(winner_sb.get('going_suitability', 0))
    o_going = float(sb.get('going_suitability', 0))
    if w_going > o_going + 5:
        winner_reasons.append(f'better going suitability ({w_going:.0f}pts vs {o_going:.0f}pts)')
    w_tr = float(winner_sb.get('trainer_strike_rate', 0) or winner_sb.get('meeting_focus_trainer', 0))
    o_tr = float(sb.get('trainer_strike_rate', 0) or sb.get('meeting_focus_trainer', 0))
    if w_tr > o_tr + 5:
        winner_reasons.append(f"trainer in better form ({w_tr:.0f}pts vs our pick's {o_tr:.0f}pts)")

    if winner_reasons:
        why_missed.append(f'{winner_name} won on: {"; ".join(winner_reasons)}')
    elif winner_score > 0:
        why_missed.append(
            f'{winner_name} (scored {winner_score:.0f}/100, rank {winner_rank}) outperformed expectations on the day'
        )

    if not why_missed:
        why_missed.append(
            f'{winner_name} scored {winner_score:.0f}/100 (rank {winner_rank}) — result within normal variance'
        )

    return {
        'winner_found':   True,
        'winner_name':    winner_name,
        'winner_score':   int(winner_score),
        'winner_rank':    winner_rank,
        'winner_rank_of': len(sorted_field),
        'winner_odds':    winner_odds,
        'winner_odds_fractional': to_fractional(winner_odds) if winner_odds > 0 else '?',
        'score_gap':      round(score_gap, 1),
        'why_missed':     why_missed,
        'weight_nudges':  weight_nudges,
    }


def apply_learning_lambda(headers, event):
    import json as _json
    from datetime import timedelta
    from decimal import Decimal
    from boto3.dynamodb.conditions import Key

    method = (event.get('requestContext') or {}).get('http', {}).get('method', event.get('httpMethod', 'GET'))
    if method == 'OPTIONS':
        return {'statusCode': 204, 'headers': headers, 'body': ''}

    try:
        body = event.get('body') or '{}'
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        data = _json.loads(body) if body else {}
        target_date = data.get('date') or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        resp = table.query(KeyConditionExpression=Key('bet_date').eq(target_date))
        all_items = [decimal_to_float(i) for i in resp.get('Items', [])]

        picks = [p for p in all_items
                 if p.get('show_in_ui') == True
                 and p.get('result_winner_name')
                 and (p.get('outcome') or '').lower() in ('loss', 'placed')]

        if not picks:
            return {'statusCode': 200, 'headers': headers,
                    'body': _json.dumps({'success': True,
                                         'message': 'No settled losses found — nothing to learn from',
                                         'changes': {}})}

        WEIGHT_MIN, WEIGHT_MAX, MAX_NUDGE = 2.0, 40.0, 1.5
        try:
            wt_resp = table.get_item(Key={'bet_id': 'SYSTEM_WEIGHTS', 'bet_date': 'CONFIG'})
            raw_wt  = wt_resp.get('Item', {}).get('weights', {}) if 'Item' in wt_resp else {}
            weights = {k: float(v) for k, v in raw_wt.items()} if raw_wt else {}
        except Exception:
            weights = {}

        all_nudges, race_summaries = [], []
        for pick in picks:
            wa     = compute_winner_analysis(pick)
            nudges = wa.get('weight_nudges', {})
            if nudges:
                all_nudges.append(nudges)
            race_summaries.append({
                'horse':  pick.get('horse'),
                'winner': wa.get('winner_name', '?'),
                'why':    wa.get('why_missed', []),
            })

        changes = {}
        if all_nudges and weights:
            totals = {}
            for nd in all_nudges:
                for k, v in nd.items():
                    totals[k] = totals.get(k, 0) + v
            n = len(all_nudges)
            for factor, total in totals.items():
                if factor not in weights:
                    continue
                nudge = max(-MAX_NUDGE, min(MAX_NUDGE, total / n))
                old_v = weights[factor]
                new_v = round(max(WEIGHT_MIN, min(WEIGHT_MAX, old_v + nudge)), 2)
                if abs(new_v - old_v) > 0.01:
                    weights[factor] = new_v
                    changes[factor] = {'from': old_v, 'to': new_v, 'nudge': round(nudge, 2)}
            if changes:
                table.put_item(Item={
                    'bet_id':        'SYSTEM_WEIGHTS',
                    'bet_date':      'CONFIG',
                    'weights':       {k: Decimal(str(v)) for k, v in weights.items()},
                    'updated_at':    datetime.now().isoformat(),
                    'source':        'lambda_learning_apply',
                    'learning_date': target_date,
                })

        msg = (f"Applied {len(changes)} weight update(s) from {len(picks)} missed winner(s)"
               if changes else "No weight changes needed")
        return {'statusCode': 200, 'headers': headers, 'body': _json.dumps({
            'success': True, 'date': target_date, 'picks_analysed': len(picks),
            'changes': changes, 'races': race_summaries, 'message': msg,
        })}
    except Exception as e:
        return {'statusCode': 500, 'headers': headers,
                'body': _json.dumps({'success': False, 'error': str(e)})}
'''

content = content + new_funcs

# Write patched file
with open('_lambda_function_updated.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Written: {len(content.splitlines())} lines')

# Verify syntax
import py_compile, sys
try:
    py_compile.compile('_lambda_function_updated.py', doraise=True)
    print('Syntax: OK')
except py_compile.PyCompileError as e:
    print('SYNTAX ERROR:', e)
    sys.exit(1)

# Verify key patches landed
checks = [
    ("GET,POST,OPTIONS" in content, "CORS POST method added"),
    ("learning/apply" in content,   "learning/apply route added"),
    ("compute_winner_analysis" in content, "compute_winner_analysis function added"),
    ("apply_learning_lambda" in content,   "apply_learning_lambda function added"),
    ("winner_analysis" in content,         "winner_analysis attachment added"),
]
for ok, label in checks:
    print(f"{'OK' if ok else 'FAIL'}: {label}")

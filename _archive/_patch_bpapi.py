"""Patch BettingPicksAPI lambda_function.py with CORS fixes and learning/apply route"""
import re

with open('_bpapi_deployed.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: CORS Allow-Methods - add POST
old1 = "'Access-Control-Allow-Methods': 'GET,OPTIONS',"
new1 = "'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',"
assert old1 in content, "Fix1 not found"
content = content.replace(old1, new1, 1)
print("Fix 1 (CORS methods): OK")

# Fix 2: Replace OPTIONS detection to handle HTTP API v2 event format
# The old code uses event.get('httpMethod') which is v1-only
# HTTP API v2 uses event['requestContext']['http']['method']
old2 = "    # Handle OPTIONS preflight"
# Insert the method extraction before the OPTIONS check
old_block = re.search(
    r"    # Handle OPTIONS preflight\s+if event\.get\('httpMethod'\) == 'OPTIONS':",
    content
)
if old_block:
    content = content[:old_block.start()] + \
        "    # Handle OPTIONS preflight - works for REST API v1 and HTTP API v2\n" + \
        "    _req_method = event.get('requestContext', {}).get('http', {}).get('method', event.get('httpMethod', ''))\n" + \
        "    if _req_method == 'OPTIONS':" + \
        content[old_block.end():]
    print("Fix 2 (OPTIONS v2 check): OK")
else:
    print("Fix 2 FAILED - pattern not found")

# Fix 3: Add learning/apply route before results/auto-record
old3 = "        elif 'results/auto-record' in path:"
new3 = "        elif 'learning/apply' in path:\n            return apply_learning_lambda(headers, event)\n        elif 'results/auto-record' in path:"
assert old3 in content, "Fix3 anchor not found"
content = content.replace(old3, new3, 1)
print("Fix 3 (learning/apply route): OK")

# Fix 4: Append the three new functions at the end of the file
new_functions = '''

# ── Learning / Apply helpers ──────────────────────────────────────────────────

def toFractional_py(decimal):
    if not decimal or float(decimal) <= 1.0:
        return 'SP'
    d = float(decimal)
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
    score_gap     = our_score - winner_score
    why_missed    = []
    weight_nudges = {}

    if not winner_horse:
        why_missed.append(f'Winner "{winner_name}" was not in our scored field')
        return {'winner_found': False, 'winner_score': 0, 'winner_rank': 0,
                'winner_odds': 0, 'score_gap': score_gap,
                'why_missed': why_missed, 'weight_nudges': weight_nudges}

    if winner_odds > 0 and our_odds > 0 and winner_odds < our_odds * 0.80:
        why_missed.append(f'Market disagreed: winner at {toFractional_py(winner_odds)} vs our pick at {toFractional_py(our_odds)}')
        weight_nudges['optimal_odds'] = weight_nudges.get('optimal_odds', 0) + 1.0

    if score_gap > 15:
        why_missed.append(f'Model over-confidence: {our_horse.title()} scored {our_score:.0f} vs {winner_name} {winner_score:.0f} — {score_gap:.0f}pt gap')

    if 0 < winner_rank <= 3 and score_gap <= 10:
        why_missed.append(f'{winner_name} ranked {winner_rank} in our model at {winner_score:.0f}/100 — narrow margin')

    if winner_rank > 5:
        why_missed.append(f'{winner_name} ranked {winner_rank} of {len(sorted_field)} in our model — model blind spot')

    going_pts = float(sb.get('going_suitability', 0))
    if going_pts > 0 and our_score > 0 and (going_pts / our_score) > 0.25:
        why_missed.append(f'Going suitability over-weighted ({going_pts:.0f}pts = {going_pts/our_score*100:.0f}% of score)')
        weight_nudges['going_suitability'] = weight_nudges.get('going_suitability', 0) - 0.5

    cd_pts = float(sb.get('cd_bonus', 0)) + float(sb.get('course_performance', 0))
    if cd_pts > 20:
        why_missed.append(f'C&D bonus inflated score ({cd_pts:.0f}pts)')
        weight_nudges['cd_bonus'] = weight_nudges.get('cd_bonus', 0) - 0.3

    if winner_score < our_score * 0.85:
        weight_nudges['recent_win'] = weight_nudges.get('recent_win', 0) + 0.5

    if len(sorted_field) <= 5 and winner_odds > 0 and winner_odds < 2.5:
        why_missed.append(f'Small field ({len(sorted_field)} runners) with well-backed winner')
        weight_nudges['optimal_odds'] = weight_nudges.get('optimal_odds', 0) + 0.5

    if not why_missed:
        why_missed.append(f'{winner_name} scored {winner_score:.0f}/100 rank {winner_rank} — within normal variance')

    return {
        'winner_found':   True,
        'winner_name':    winner_name,
        'winner_score':   int(winner_score),
        'winner_rank':    winner_rank,
        'winner_rank_of': len(sorted_field),
        'winner_odds':    winner_odds,
        'score_gap':      round(score_gap, 1),
        'why_missed':     why_missed,
        'weight_nudges':  weight_nudges,
    }


def apply_learning_lambda(headers, event):
    """POST /api/learning/apply — nudge SYSTEM_WEIGHTS from missed winners."""
    from decimal import Decimal
    from boto3.dynamodb.conditions import Key

    try:
        body = event.get('body') or '{}'
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        data = json.loads(body) if body else {}
        target_date = data.get('date') or (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        resp = table.query(KeyConditionExpression=Key('bet_date').eq(target_date))
        all_items = [decimal_to_float(i) for i in resp.get('Items', [])]

        picks = [p for p in all_items
                 if p.get('show_in_ui') is True
                 and p.get('result_winner_name')
                 and (p.get('outcome') or '').lower() in ('loss', 'placed')]

        if not picks:
            return {'statusCode': 200, 'headers': headers,
                    'body': json.dumps({'success': True,
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
                'winner': wa.get('winner_name', pick.get('result_winner_name', '?')),
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
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps({
            'success': True, 'date': target_date, 'picks_analysed': len(picks),
            'changes': changes, 'races': race_summaries, 'message': msg,
        })}
    except Exception as e:
        return {'statusCode': 500, 'headers': headers,
                'body': json.dumps({'success': False, 'error': str(e)})}
'''

content = content + new_functions
print("Fix 4 (new functions appended): OK")

with open('_bpapi_patched.py', 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Written: {len(content.splitlines())} lines")

# Validate syntax
import py_compile
py_compile.compile('_bpapi_patched.py', doraise=True)
print("Syntax: OK")

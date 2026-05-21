"""
Audit the last 2 weeks of DynamoDB picks.
For each date, simulate the top-5 cap + S1/S2/S3 gates that Today's Picks enforces.
Any show_in_ui=True pick that wouldn't have made the cut gets demoted to show_in_ui=False.
This automatically fixes the cumulative ROI endpoint (which uses show_in_ui=True).
"""
import boto3
import datetime
from boto3.dynamodb.conditions import Key
from decimal import Decimal

def dec(obj):
    if isinstance(obj, dict): return {k: dec(v) for k,v in obj.items()}
    if isinstance(obj, list): return [dec(v) for v in obj]
    if isinstance(obj, Decimal): return float(obj)
    return obj

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

def query_all(date):
    items = []
    kwargs = {'KeyConditionExpression': Key('bet_date').eq(date)}
    while True:
        resp = tbl.query(**kwargs)
        items.extend([dec(it) for it in resp.get('Items', [])])
        lek = resp.get('LastEvaluatedKey')
        if not lek:
            break
        kwargs['ExclusiveStartKey'] = lek
    return items

def passes_gates(p):
    """Return True if pick passes S1/S2/S3 quality gates (same logic as api_server picks endpoint)."""
    comp_score = float(p.get('comprehensive_score') or p.get('analysis_score') or 0)
    comb_conf  = float(p.get('combined_confidence') or 0)
    if comp_score < 75:
        return False, "score < 75"
    if comb_conf > 0 and comb_conf < 55:
        return False, f"combined_confidence {comb_conf} < 55"
    bd  = p.get('score_breakdown') or {}
    ml  = float(bd.get('market_leader', 0))
    tr  = float(bd.get('trainer_reputation', 0))
    cd  = float(bd.get('cd_bonus', 0))
    age = float(bd.get('age_bonus', 0))
    if ml == 0 and tr == 0 and cd == 0:
        return False, "S2: no contextual anchor"
    if ml == 0 and comp_score < 90:
        return False, f"S1: no market leader + score {comp_score:.0f} < 90"
    if age >= 10 and ml == 0 and tr == 0 and comp_score < 92:
        return False, f"S3: age-padded, no market/trainer support, score {comp_score:.0f} < 92"
    return True, "ok"

def top5_for_date(all_items, date):
    """
    Return the set of bet_ids that would have been the top-5 picks for a date.
    date: YYYY-MM-DD (used to filter race_time)
    """
    # Only show_in_ui=True picks with today's race_time
    candidates = [
        it for it in all_items
        if it.get('show_in_ui') == True
        and str(it.get('race_time', '')).startswith(date)
        and it.get('course') and it.get('course') != 'Unknown'
        and it.get('horse') and it.get('horse') != 'Unknown'
        and not it.get('is_learning_pick', False)
    ]

    # Apply S1/S2/S3 gates
    gated = []
    for p in candidates:
        ok, reason = passes_gates(p)
        if ok:
            gated.append(p)

    # One-pick-per-race dedup (keep highest scorer)
    seen = {}
    for p in gated:
        key = (p.get('course', ''), str(p.get('race_time', ''))[:16])
        existing = seen.get(key)
        if not existing or float(p.get('comprehensive_score', 0)) > float(existing.get('comprehensive_score', 0)):
            seen[key] = p
    deduped = list(seen.values())

    # Top 5 by score
    deduped.sort(key=lambda x: float(x.get('comprehensive_score') or x.get('analysis_score') or 0), reverse=True)
    top5 = deduped[:5]
    return {p['bet_id'] for p in top5}

# ── Main audit ──────────────────────────────────────────────────────────────
today = datetime.date.today()
start = today - datetime.timedelta(days=14)

to_demote = []   # (bet_date, bet_id, horse, score, reason)
total_shown = 0

print(f"Auditing {start} → {today}\n")

cur = start
while cur <= today:
    date_str = str(cur)
    items = query_all(date_str)

    # All show_in_ui=True picks whose race_time is on this date
    shown = [
        it for it in items
        if it.get('show_in_ui') == True
        and str(it.get('race_time', '')).startswith(date_str)
        and not it.get('is_learning_pick', False)
    ]
    total_shown += len(shown)

    if not shown:
        cur += datetime.timedelta(days=1)
        continue

    valid_ids = top5_for_date(items, date_str)

    excess = [p for p in shown if p['bet_id'] not in valid_ids]
    if excess:
        print(f"{date_str}: {len(shown)} shown → top-5 keeps {len(valid_ids)}, demoting {len(excess)}:")
        for p in excess:
            ok, reason = passes_gates(p)
            score = p.get('comprehensive_score', 0)
            rank_note = "outside top-5" if ok else f"gate fail: {reason}"
            print(f"    - {p.get('horse')} ({p.get('course')}) score:{score} | {rank_note}")
            to_demote.append({
                'bet_date': p['bet_date'],
                'bet_id':   p['bet_id'],
                'horse':    p.get('horse', ''),
                'score':    score,
                'reason':   rank_note,
            })
    else:
        valid_count = len(valid_ids & {p['bet_id'] for p in shown})
        print(f"{date_str}: {len(shown)} shown — all {valid_count} pass top-5 check ✓")

    cur += datetime.timedelta(days=1)

print(f"\nTotal show_in_ui=True picks audited: {total_shown}")
print(f"Picks to demote: {len(to_demote)}")

if not to_demote:
    print("\nNothing to fix — all historical picks were correctly capped.")
else:
    print("\nProceeding to demote...")
    for item in to_demote:
        tbl.update_item(
            Key={'bet_date': item['bet_date'], 'bet_id': item['bet_id']},
            UpdateExpression='SET show_in_ui = :f, recommended_bet = :f',
            ExpressionAttributeValues={':f': False}
        )
        print(f"  Demoted: {item['horse']} ({item['bet_date']}) — {item['reason']}")
    print(f"\nDone. {len(to_demote)} picks demoted. Cumulative ROI will recalculate on next API call.")

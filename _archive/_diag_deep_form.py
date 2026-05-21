"""Show deep_form impact on today's UI picks."""
import re
import boto3
from boto3.dynamodb.conditions import Key, Attr

db = boto3.resource('dynamodb', region_name='eu-west-1')
t  = db.Table('SureBetBets')

resp  = t.query(KeyConditionExpression=Key('bet_date').eq('2026-03-30'),
                FilterExpression=Attr('show_in_ui').eq(True))
picks = sorted(resp['Items'], key=lambda x: x.get('race_time', ''))

print(f"Today UI picks: {len(picks)}\n")
print(f"{'Horse':<22} {'Course':<14} {'Time':5}  {'Score':>5}  {'deep_form':>9}  {'New score':>9}  {'Outcome':<10}  Deep-form reasons")
print("-" * 120)

for p in picks:
    bd      = {k: float(v) for k, v in p.get('score_breakdown', {}).items()}
    total   = sum(bd.values())
    df      = bd.get('deep_form', 0)
    reasons = p.get('selection_reasons', [])
    df_reasons = [r for r in reasons if any(kw in r.lower() for kw in
                  ['ground', 'going', 'trajectory', 'course winner', 'distance evidence', 'close', 'field'])]

    # Simulate fix: suppress AW going_win_match and OR trajectory on long layoff
    # We can detect from the reasons text which sub-signals fired
    simulated_cut = 0
    suppressed = []
    for r in df_reasons:
        if 'ground (proven going suitability)' in r.lower():
            m = re.search(r'\+(\d+)pts', r)
            pts = int(m.group(1)) if m else 0
            suppressed.append(f"AW going win: -{pts}")
            simulated_cut += pts
        if 'rising or trajectory' in r.lower():
            m = re.search(r'\+(\d+)pts', r)
            pts = int(m.group(1)) if m else 0
            suppressed.append(f"OR trajectory (long layoff): -{pts}")
            simulated_cut += pts

    new_score = total - simulated_cut
    horse     = p.get('horse', '?')
    course    = p.get('course', '?')
    time_     = p.get('race_time', '')
    time_hhmm = time_[11:16] if len(time_) >= 16 else '?'
    outcome   = p.get('outcome', 'pending')

    print(f"{horse:<22} {course:<14} {time_hhmm}  {total:>5.0f}  {df:>+9.0f}  {new_score:>+9.0f}  {outcome:<10}  {'; '.join(suppressed) or 'no change'}")

print()
print("Suppressed signals:")
print("  1. AW going_win_match: fires when horse won on Standard/AW — not selective (all AW races same 'going')")
print("  2. OR trajectory rising: fires when recent OR higher — suppressed if last run was >90 days ago")

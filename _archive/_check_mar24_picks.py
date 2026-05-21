import boto3, json
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def d2f(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: d2f(v) for k, v in obj.items()}
    if isinstance(obj, list): return [d2f(i) for i in obj]
    return obj

# Get Mar 24 picks
resp = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': '2026-03-24'}
)
items = [d2f(i) for i in resp.get('Items', [])]
ui_picks = [p for p in items if p.get('show_in_ui') == True and not p.get('is_learning_pick')]
print(f"Total items Mar 24: {len(items)}, UI picks: {len(ui_picks)}")
print()

for p in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
    score = p.get('comprehensive_score') or p.get('analysis_score') or 0
    odds  = p.get('odds', '?')
    horse = p.get('horse', '?')
    course = p.get('course', '?')
    rt = str(p.get('race_time', ''))[:16]
    outcome = p.get('outcome', 'pending')
    combined_conf = p.get('combined_confidence', 0)
    print(f"  {rt} | {horse} | {course} | odds={odds} | score={score} | conf={combined_conf} | outcome={outcome}")
    sb = p.get('score_breakdown') or {}
    if sb:
        print(f"    score_breakdown: {json.dumps(sb, default=str)}")
    # Show all_horses for context
    all_h = p.get('all_horses') or []
    if all_h:
        print(f"    field ({len(all_h)} horses):")
        for h in sorted(all_h, key=lambda x: -float(x.get('score', 0))):
            hname = h.get('horse') or h.get('name', '?')
            hscore = h.get('score', '?')
            hodds = h.get('odds', '?')
            print(f"      #{hname} score={hscore} odds={hodds}")
    print()

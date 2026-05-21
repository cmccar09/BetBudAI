import boto3
from decimal import Decimal
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def d2f(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: d2f(v) for k, v in obj.items()}
    if isinstance(obj, list): return [d2f(i) for i in obj]
    return obj

# Get ALL Mar 24 horses (learning picks) with outcomes
resp = table.query(
    KeyConditionExpression='bet_date = :d',
    FilterExpression='is_learning_pick = :lp',
    ExpressionAttributeValues={':d': '2026-03-24', ':lp': True}
)
items = [d2f(i) for i in resp.get('Items', [])]

# Group by race
races = defaultdict(list)
for p in items:
    rt = str(p.get('race_time', ''))
    if rt.startswith('2026-03-24'):
        rk = (rt[:16], p.get('course', ''))
        races[rk].append(p)

print("=== MARCH 24 RACE WINNERS (from learning picks) ===\n")
for race_key in sorted(races.keys()):
    rt, course = race_key
    horses = races[race_key]
    winners = [h for h in horses if h.get('outcome') == 'win']
    placed  = [h for h in horses if h.get('outcome') == 'placed']
    horses_sorted = sorted(horses, key=lambda x: -float(x.get('comprehensive_score') or 0))
    
    if winners or placed:
        print(f"{rt[11:16]} {course}")
        for h in winners:
            score = h.get('comprehensive_score') or 0
            sb = h.get('score_breakdown') or {}
            odds = h.get('odds', '?')
            rank = next((i+1 for i, x in enumerate(horses_sorted) if x.get('horse') == h.get('horse')), '?')
            print(f"  WIN:    {h.get('horse'):30s} score={score:5.1f} odds={odds} model_rank={rank}/{len(horses)}")
            if sb:
                top = sorted(sb.items(), key=lambda x: -float(x[1] or 0))
                print(f"          top signals: {', '.join(f'{k}={v:.0f}' for k,v in top[:6] if float(v or 0) > 0)}")
        for h in placed:
            score = h.get('comprehensive_score') or 0
            sb = h.get('score_breakdown') or {}
            odds = h.get('odds', '?')
            rank = next((i+1 for i, x in enumerate(horses_sorted) if x.get('horse') == h.get('horse')), '?')
            print(f"  PLACED: {h.get('horse'):30s} score={score:5.1f} odds={odds} model_rank={rank}/{len(horses)}")
        # Show top 3 our model picked
        print(f"  MODEL TOP 3: ", end='')
        for h in horses_sorted[:3]:
            print(f"{h.get('horse')} ({h.get('comprehensive_score'):.0f})", end='  ')
        print()
        print()

import boto3
from decimal import Decimal
import json
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def d2f(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: d2f(v) for k, v in obj.items()}
    if isinstance(obj, list): return [d2f(i) for i in obj]
    return obj

# Get all Mar 24 scored horses (learning picks = all analysed horses)
resp = table.query(
    KeyConditionExpression='bet_date = :d',
    FilterExpression='is_learning_pick = :lp',
    ExpressionAttributeValues={':d': '2026-03-24', ':lp': True}
)
items = [d2f(i) for i in resp.get('Items', [])]
print(f"Total learning_picks Mar 24: {len(items)}")

# Group by race
races = defaultdict(list)
for p in items:
    rk = (p.get('race_time', ''), p.get('course', ''))
    races[rk].append(p)

print(f"\n=== ALL RACES (showing full field with score breakdowns) ===")
for race_key in sorted(races.keys()):
    rt, course = race_key
    horses = races[race_key]
    horses_sorted = sorted(horses, key=lambda x: -float(x.get('comprehensive_score') or x.get('analysis_score') or 0))
    
    print(f"\n{rt[:16]} | {course}")
    for h in horses_sorted:
        score = h.get('comprehensive_score') or h.get('analysis_score') or 0
        odds  = h.get('odds', '?')
        horse = h.get('horse', '?')
        outcome = h.get('outcome', 'n/a')
        sb = h.get('score_breakdown') or {}
        # Key fields from new features
        meet_focus = sb.get('meeting_focus', 0)
        unexposed  = sb.get('unexposed_bonus', 0)
        cd_b       = sb.get('cd_bonus', 0)
        # Old score = new score - unexposed_bonus - (meeting_focus above what old additive would sum to)
        # Simple approximation: old score without unexposed_bonus
        old_score_approx = float(score) - float(unexposed) 
        # Also remove cd_bonus fallback additions if they're from the new fallback
        # We'll show both
        print(f"  {horse:30s} score={score:5.1f} old_approx={old_score_approx:5.1f} odds={odds} | meet_focus={meet_focus} unexposed={unexposed} cd_bonus={cd_b} | outcome={outcome}")

import boto3
from decimal import Decimal
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def d2f(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: d2f(v) for k, v in obj.items()}
    if isinstance(obj, list): return [d2f(i) for i in obj]
    return obj

resp = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': '2026-03-24'}
)
items = [d2f(i) for i in resp.get('Items', [])]

with_outcome = [i for i in items if i.get('outcome') and i.get('outcome') not in ('pending', '-')]
print(f"Items with real outcomes: {len(with_outcome)}")
print()

for p in sorted(with_outcome, key=lambda x: str(x.get('race_time', ''))):
    rt = str(p.get('race_time', ''))[:16]
    print(f"{'='*60}")
    print(f"{rt} | {p.get('course')} | {p.get('horse')}")
    print(f"  outcome={p.get('outcome')}  score={p.get('comprehensive_score')}  odds={p.get('odds')}")
    print(f"  show_in_ui={p.get('show_in_ui')}  is_learning_pick={p.get('is_learning_pick')}")
    bd = p.get('score_breakdown') or {}
    if bd:
        sig_bd = {k: v for k, v in bd.items() if isinstance(v, (int, float)) and v != 0}
        print(f"  score_breakdown (non-zero):")
        for k, v in sorted(sig_bd.items(), key=lambda x: -abs(x[1])):
            print(f"    {k:35s} {v:+.1f}")
    print()

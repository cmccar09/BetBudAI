import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

def dec(obj):
    if isinstance(obj, dict): return {k: dec(v) for k,v in obj.items()}
    if isinstance(obj, list): return [dec(v) for v in obj]
    if isinstance(obj, Decimal): return float(obj)
    return obj

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-10'))
items = [dec(it) for it in resp.get('Items', [])]

for it in items:
    h = it.get('horse', '')
    if 'celtic' in h.lower() or 'druid' in h.lower():
        print("=== Celtic Druid ===")
        for k, v in sorted(it.items()):
            if k not in ('all_horses', 'score_breakdown', 'selection_reasons'):
                print(f"  {k}: {v}")
        print("\n  score_breakdown:", it.get('score_breakdown', {}))
        print("  pick_rank:", it.get('pick_rank'))
        print("  show_in_ui:", it.get('show_in_ui'))
        print("  bet_id:", it.get('bet_id'))

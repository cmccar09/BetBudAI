import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

def dec(obj):
    if isinstance(obj, dict): return {k: dec(v) for k,v in obj.items()}
    if isinstance(obj, list): return [dec(v) for v in obj]
    if isinstance(obj, Decimal): return float(obj)
    return obj

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
for date in ['2026-04-10', '2026-04-09', '2026-04-08']:
    resp = tbl.query(KeyConditionExpression=Key('bet_date').eq(date))
    items = [dec(it) for it in resp.get('Items', [])]
    matches = [it for it in items if 'celtic' in it.get('horse','').lower() or 'druid' in it.get('horse','').lower()]
    if matches:
        for it in matches:
            print(f"DATE:{date} horse:{it.get('horse')} bet_id:{it.get('bet_id')} pick_rank:{it.get('pick_rank')} show_in_ui:{it.get('show_in_ui')} race_time:{it.get('race_time')}")
    else:
        print(f"DATE:{date} - no Celtic Druid found (total items: {len(items)})")

# Also check what the /api/results endpoint returns for 'today'
print("\n--- All picks with pick_rank set for 2026-04-10 ---")
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-10'))
items = [dec(it) for it in resp.get('Items', [])]
picks = [it for it in items if it.get('pick_rank') and float(it.get('pick_rank') or 0) >= 1]
picks.sort(key=lambda x: float(x.get('pick_rank') or 99))
for p in picks:
    print(f"  rank:{p.get('pick_rank')} {p.get('horse')} @ {p.get('race_time','')[:16]} {p.get('course','')} score:{p.get('comprehensive_score',0)} outcome:{p.get('outcome','')}")

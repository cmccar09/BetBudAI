import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

def dec(obj):
    if isinstance(obj, dict): return {k: dec(v) for k,v in obj.items()}
    if isinstance(obj, list): return [dec(v) for v in obj]
    if isinstance(obj, Decimal): return float(obj)
    return obj

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

def query_all(date):
    """Paginate through ALL items for a date."""
    items = []
    kwargs = {'KeyConditionExpression': Key('bet_date').eq(date)}
    while True:
        resp = tbl.query(**kwargs)
        items.extend([dec(it) for it in resp.get('Items', [])])
        lek = resp.get('LastEvaluatedKey')
        if not lek:
            break
        kwargs['ExclusiveStartKey'] = lek
        print(f"  Paginating... got {len(items)} so far")
    return items

for date in ['2026-04-10', '2026-04-09']:
    print(f"\n=== {date} ===")
    items = query_all(date)
    print(f"Total items (paginated): {len(items)}")
    matches = [it for it in items if 'celtic' in (it.get('horse','') or '').lower() or 'druid' in (it.get('horse','') or '').lower()]
    print(f"Celtic Druid matches: {len(matches)}")
    for it in matches:
        print(f"  horse: {it.get('horse')} | bet_id: {it.get('bet_id')} | score: {it.get('comprehensive_score')} | show_in_ui: {it.get('show_in_ui')} | race_time: {it.get('race_time')}")

# Also check all Dundalk items for today
print("\n=== Dundalk items for 2026-04-10 (paginated) ===")
items_today = query_all('2026-04-10')
dundalk = [it for it in items_today if 'dundalk' in (it.get('course','') or '').lower()]
print(f"Dundalk items: {len(dundalk)}")
# Group by race_time
from collections import defaultdict
by_race = defaultdict(list)
for it in dundalk:
    rt = str(it.get('race_time',''))[:16]
    by_race[rt].append(it.get('horse','?'))
for rt in sorted(by_race):
    horses = by_race[rt]
    print(f"  {rt}: {len(horses)} runners — {horses[:5]}")

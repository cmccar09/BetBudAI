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

print("--- Searching for Grey Dawning / Solness ---")
for it in items:
    h = it.get('horse', '')
    if 'grey' in h.lower() or 'solness' in h.lower() or 'dawning' in h.lower():
        rt = str(it.get('race_time', ''))[:16]
        score = it.get('comprehensive_score', 0)
        odds = it.get('odds', '?')
        print(f"  {rt} | {it.get('course','')} | {h} | score:{score} | odds:{odds}")

print("\n--- All Aintree race times in DB ---")
aintree_times = {}
for it in items:
    course = it.get('course', '')
    if 'aintree' in course.lower():
        rt = str(it.get('race_time', ''))[:16]
        if rt not in aintree_times:
            aintree_times[rt] = []
        aintree_times[rt].append(it.get('horse', ''))

for t in sorted(aintree_times):
    horses = aintree_times[t]
    print(f"  {t}: {len(horses)} runners")

print("\n--- Top scorers each Aintree race ---")
for t in sorted(aintree_times):
    race_items = [it for it in items if 'aintree' in it.get('course','').lower() and str(it.get('race_time',''))[:16] == t]
    race_items.sort(key=lambda x: float(x.get('comprehensive_score',0) or 0), reverse=True)
    top3 = race_items[:3]
    print(f"\n  {t} Aintree:")
    for h in top3:
        score = h.get('comprehensive_score', 0)
        odds = h.get('odds', '?')
        pick_rank = h.get('pick_rank', '')
        outcome = h.get('outcome', '')
        print(f"    {h.get('horse','')} | score:{score} | odds:{odds} | rank:{pick_rank} | outcome:{outcome}")

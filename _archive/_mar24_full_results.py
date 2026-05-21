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

# Scan all Mar 24 items to find any with outcomes
resp = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': '2026-03-24'}
)
items = [d2f(i) for i in resp.get('Items', [])]

print(f"Total Mar 24 items: {len(items)}")

# Find items with outcomes set
with_outcome = [i for i in items if i.get('outcome') and i.get('outcome') != 'pending']
print(f"Items with outcomes: {len(with_outcome)}")

races = defaultdict(list)
for p in items:
    rt = str(p.get('race_time', ''))
    course = p.get('course', '')
    if course and course != 'Unknown' and p.get('horse'):
        rk = (rt[:16], course)
        races[rk].append(p)

print(f"Races found: {len(races)}")
print()

for race_key in sorted(races.keys()):
    rt, course = race_key
    horses = races[race_key]
    # deduplicate by horse
    seen = {}
    for h in horses:
        hn = h.get('horse','')
        cs = float(h.get('comprehensive_score') or 0)
        if hn not in seen or cs > float(seen[hn].get('comprehensive_score') or 0):
            seen[hn] = h
    horses = sorted(seen.values(), key=lambda x: -float(x.get('comprehensive_score') or 0))
    
    outcomes = {h.get('horse'): h.get('outcome') for h in horses if h.get('outcome')}
    winner = next((h for h in horses if h.get('outcome') == 'win'), None)
    
    print(f"{rt[11:16] if rt else '?'} {course} ({len(horses)} horses) | outcomes recorded: {len(outcomes)}")
    for h in horses[:4]:
        oc = h.get('outcome', '-')
        print(f"  {h.get('horse','?'):30s} score={float(h.get('comprehensive_score') or 0):5.1f} odds={h.get('odds','?'):<6} outcome={oc}")
    if winner:
        rank = next((i+1 for i, h in enumerate(horses) if h.get('horse') == winner.get('horse')), '?')
        print(f"  >>> WINNER was rank {rank}")
    print()

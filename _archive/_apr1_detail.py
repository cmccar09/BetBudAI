import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

dynamo = boto3.resource('dynamodb', region_name='eu-west-1')
table  = dynamo.Table('SureBetBets')
resp   = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-01'))
items  = resp['Items']

def get_race(rt_prefix, course_kw):
    hits = [i for i in items
            if str(i.get('race_time','')).startswith(rt_prefix)
            and course_kw.lower() in str(i.get('course','')).lower()]
    hits.sort(key=lambda x: -float(x.get('comprehensive_score') or 0))
    seen = {}
    for h in hits:
        n = h.get('horse','?')
        if n not in seen:
            seen[n] = h
    return list(seen.values())

races = [
    ('2026-04-01T14:20', 'Wincanton', '15:20 IST Wincanton — Golan Loop (won by Broomfields Cave 3/1)'),
    ('2026-04-01T15:20', 'Wincanton', '16:20 IST Wincanton — Kingcormac (won by Broomfields Cave 9/4)'),
    ('2026-04-01T16:45', 'Dundalk',   "17:45 IST Dundalk   — I'm Spartacus (won by Clonmacash 5/1)"),
]

for rt, course, label in races:
    print(f'\n{"="*70}')
    print(f'  {label}')
    print(f'  {"Horse":<28} {"Score":>6}  {"OR":>4}  {"Form":>10}  {"Trainer":<20}')
    print(f'  {"-"*75}')
    for h in get_race(rt, course):
        sc  = float(h.get('comprehensive_score') or 0)
        OR  = h.get('official_rating', '?')
        frm = h.get('form', '?')
        tr  = h.get('trainer', '?')
        nm  = h.get('horse', '?')
        print(f'  {nm:<28} {sc:6.0f}  {str(OR):>4}  {str(frm):>10}  {str(tr)[:20]}')
    print()

# Also check selection_reasons for our picks
picks_of_interest = ['Golan Loop', "I'm Spartacus", 'Kingcormac', 'Broomfields Cave', 'Clonmacash']
print('\n\n=== Key Pick Selection Reasons ===')
for item in items:
    horse = item.get('horse','')
    if horse in picks_of_interest:
        score = float(item.get('comprehensive_score') or 0)
        reasons = item.get('selection_reasons') or []
        if reasons:
            print(f'\n  {horse} (score={score:.0f}):')
            for r in reasons[:8]:
                print(f'    · {r}')
            break_analysis = item.get('breakdown') or {}

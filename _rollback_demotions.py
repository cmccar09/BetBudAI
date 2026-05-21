"""Roll back the 31 show_in_ui demotions made by _audit_top5_cap.py."""
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

def dec(obj):
    if isinstance(obj, dict): return {k: dec(v) for k,v in obj.items()}
    if isinstance(obj, list): return [dec(v) for v in obj]
    if isinstance(obj, Decimal): return float(obj)
    return obj

tbl = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# Exact list of (bet_date, horse_name) that were demoted
TO_RESTORE = [
    ('2026-03-27', 'Daylatedollarshort'),
    ('2026-03-28', 'Dmaniac'),
    ('2026-03-28', 'Belgravian'),
    ('2026-03-28', 'Triple Double A'),
    ('2026-03-28', 'Eternal Force'),
    ('2026-03-28', 'Ellusive Butterfly'),
    ('2026-03-29', 'Jimmy Speaking'),
    ('2026-03-29', 'Fine Interview'),
    ('2026-04-01', 'Kingcormac'),
    ('2026-04-01', 'Baila Conmigo'),
    ('2026-04-02', 'Jaipaletemps'),
    ('2026-04-03', 'Faiyum'),
    ('2026-04-03', 'Berkshire Sundance'),
    ('2026-04-03', 'Happy Pharoah'),
    ('2026-04-04', 'Dutch Corner'),
    ('2026-04-04', 'Mount Atlas'),
    ('2026-04-04', 'Blue Carpet'),
    ('2026-04-04', 'Team Player'),
    ('2026-04-04', 'Tropical Storm'),
    ('2026-04-04', 'Calimystic'),
    ('2026-04-04', 'Guet Apens'),
    ('2026-04-04', 'Karbau'),
    ('2026-04-04', 'Major Fortune'),
    ('2026-04-04', 'Solar System'),
    ('2026-04-04', 'Codiak'),
    ('2026-04-04', 'Saladins Son'),  # two entries same date/horse
    ('2026-04-05', 'Leader Dallier'),
    ('2026-04-05', 'Ballynaheer'),
    ('2026-04-05', 'Zanoosh'),
    ('2026-04-05', 'Western Fold'),
]

def query_all(date):
    items = []
    kwargs = {'KeyConditionExpression': Key('bet_date').eq(date)}
    while True:
        resp = tbl.query(**kwargs)
        items.extend([dec(it) for it in resp.get('Items', [])])
        lek = resp.get('LastEvaluatedKey')
        if not lek:
            break
        kwargs['ExclusiveStartKey'] = lek
    return items

# Group by date to minimise queries
from collections import defaultdict
by_date = defaultdict(list)
for date, horse in TO_RESTORE:
    by_date[date].append(horse.lower())

restored = 0
not_found = []

for date, horses in sorted(by_date.items()):
    items = query_all(date)
    for it in items:
        h = (it.get('horse') or '').lower()
        if h in horses:
            tbl.update_item(
                Key={'bet_date': it['bet_date'], 'bet_id': it['bet_id']},
                UpdateExpression='SET show_in_ui = :t, recommended_bet = :t',
                ExpressionAttributeValues={':t': True}
            )
            print(f"  Restored: {it.get('horse')} ({date})")
            restored += 1
            horses.remove(h)
    for leftover in horses:
        not_found.append((date, leftover))

print(f"\nRestored: {restored}")
if not_found:
    print(f"Not found ({len(not_found)}):")
    for d, h in not_found:
        print(f"  {d}: {h}")
else:
    print("All picks restored successfully.")

import boto3
from datetime import date, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

start_d = date.fromisoformat('2026-03-22')
today_d = date.today()

all_items = []
cur = start_d
while cur <= today_d:
    kwargs = {
        'KeyConditionExpression': 'bet_date = :d',
        'ExpressionAttributeValues': {':d': str(cur)},
        'ProjectionExpression': 'bet_date, bet_id, horse, course, race_time, show_in_ui, is_learning_pick, outcome, sp_odds, odds'
    }
    while True:
        resp = table.query(**kwargs)
        all_items.extend(resp.get('Items', []))
        lek = resp.get('LastEvaluatedKey')
        if not lek:
            break
        kwargs['ExclusiveStartKey'] = lek
    cur += timedelta(days=1)

picks = [p for p in all_items
         if p.get('course') and p.get('course') != 'Unknown'
         and p.get('horse') and p.get('horse') != 'Unknown'
         and p.get('show_in_ui') is True
         and not p.get('is_learning_pick', False)]

# Deduplicate (same as ROI endpoint)
seen = {}
for p in picks:
    key = (p.get('course', ''), str(p.get('race_time', ''))[:16])
    existing = seen.get(key)
    if not existing or p.get('bet_date', '') > existing.get('bet_date', ''):
        seen[key] = p
picks = list(seen.values())

settled = [p for p in picks if (p.get('outcome') or '').lower() in ('win', 'placed', 'loss')]
pending = [p for p in picks if (p.get('outcome') or '').lower() not in ('win', 'placed', 'loss')]

print(f'Total show_in_ui picks (deduped): {len(picks)}')
print(f'Settled: {len(settled)}  Pending: {len(pending)}')
print()
print('=== SETTLED ===')
for p in sorted(settled, key=lambda x: str(x.get('race_time', ''))):
    rt = str(p.get('race_time', ''))[:16]
    print(f"{p.get('bet_date')} {rt} | {p.get('course')} | {p.get('horse')} | {p.get('outcome')}")
print()
print('=== PENDING (not settled) ===')
for p in sorted(pending, key=lambda x: str(x.get('race_time', ''))):
    rt = str(p.get('race_time', ''))[:16]
    print(f"{p.get('bet_date')} {rt} | {p.get('course')} | {p.get('horse')}")

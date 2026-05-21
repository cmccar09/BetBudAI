"""Simulate the non-paginated ROI endpoint exactly as api_server.py does it,
to see settled count and compare with paginated version."""
import boto3
from datetime import date, timedelta
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

CUMULATIVE_ROI_START = '2026-03-22'
start_d = date.fromisoformat(CUMULATIVE_ROI_START)
today_d = date.today()

# === NON-PAGINATED (exactly as the API endpoint does it) ===
all_items_np = []
cur = start_d
while cur <= today_d:
    response = table.query(
        KeyConditionExpression=Key('bet_date').eq(str(cur)),
        ProjectionExpression='bet_date, bet_id, horse, course, race_time, show_in_ui, is_learning_pick, outcome, sp_odds, odds, ew_fraction, bet_type',
    )
    all_items_np.extend(response.get('Items', []))
    lek = response.get('LastEvaluatedKey')
    if lek:
        print(f"  !! PAGINATION NEEDED for {cur}: got {len(response.get('Items',[]))} items, more available")
    cur += timedelta(days=1)

picks_np = [p for p in all_items_np
            if p.get('course') and p.get('course') != 'Unknown'
            and p.get('horse') and p.get('horse') != 'Unknown'
            and p.get('show_in_ui') is True
            and not p.get('is_learning_pick', False)]

seen = {}
for p in picks_np:
    key = (p.get('course', ''), str(p.get('race_time', ''))[:16])
    existing = seen.get(key)
    if not existing or p.get('bet_date', '') > existing.get('bet_date', ''):
        seen[key] = p
picks_np = list(seen.values())

settled_np = [p for p in picks_np if (p.get('outcome') or '').lower() in ('win', 'placed', 'loss')]
pending_np = [p for p in picks_np if (p.get('outcome') or '').lower() not in ('win', 'placed', 'loss')]

print(f"\n=== NON-PAGINATED (API endpoint) ===")
print(f"Total items fetched: {len(all_items_np)}")
print(f"After filter+dedup: {len(picks_np)}")
print(f"Settled: {len(settled_np)}  Pending: {len(pending_np)}")

# === PAGINATED (full truth) ===
all_items_p = []
cur = start_d
while cur <= today_d:
    kwargs = {
        'KeyConditionExpression': Key('bet_date').eq(str(cur)),
        'ProjectionExpression': 'bet_date, bet_id, horse, course, race_time, show_in_ui, is_learning_pick, outcome, sp_odds, odds, ew_fraction, bet_type',
    }
    while True:
        resp = table.query(**kwargs)
        all_items_p.extend(resp.get('Items', []))
        lek = resp.get('LastEvaluatedKey')
        if not lek:
            break
        kwargs['ExclusiveStartKey'] = lek
    cur += timedelta(days=1)

picks_p = [p for p in all_items_p
           if p.get('course') and p.get('course') != 'Unknown'
           and p.get('horse') and p.get('horse') != 'Unknown'
           and p.get('show_in_ui') is True
           and not p.get('is_learning_pick', False)]

seen2 = {}
for p in picks_p:
    key = (p.get('course', ''), str(p.get('race_time', ''))[:16])
    existing = seen2.get(key)
    if not existing or p.get('bet_date', '') > existing.get('bet_date', ''):
        seen2[key] = p
picks_p = list(seen2.values())

settled_p = [p for p in picks_p if (p.get('outcome') or '').lower() in ('win', 'placed', 'loss')]
pending_p = [p for p in picks_p if (p.get('outcome') or '').lower() not in ('win', 'placed', 'loss')]

print(f"\n=== PAGINATED (truth) ===")
print(f"Total items fetched: {len(all_items_p)}")
print(f"After filter+dedup: {len(picks_p)}")
print(f"Settled: {len(settled_p)}  Pending: {len(pending_p)}")

# Find what paginated has but non-paginated missed
np_race_keys = {(p.get('course',''), str(p.get('race_time',''))[:16]) for p in picks_np}
missed = [p for p in picks_p if (p.get('course',''), str(p.get('race_time',''))[:16]) not in np_race_keys]
print(f"\n=== PICKS IN PAGINATED BUT MISSING FROM NON-PAGINATED ===")
for p in sorted(missed, key=lambda x: str(x.get('race_time',''))):
    print(f"  {p.get('bet_date')} {str(p.get('race_time',''))[:16]} | {p.get('course')} | {p.get('horse')} | outcome={p.get('outcome')}")

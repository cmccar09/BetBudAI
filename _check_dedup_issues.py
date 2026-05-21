"""Find races where deduplication is hiding a settled record behind a pending one."""
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
        'ProjectionExpression': 'bet_date, bet_id, horse, course, race_time, show_in_ui, is_learning_pick, outcome'
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

# Group by race key — find races with multiple records
from collections import defaultdict
by_race = defaultdict(list)
for p in picks:
    key = (p.get('course', ''), str(p.get('race_time', ''))[:16])
    by_race[key].append(p)

print("=== RACES WITH DUPLICATE RECORDS ===")
problem_count = 0
for key, records in by_race.items():
    if len(records) > 1:
        records.sort(key=lambda x: x.get('bet_date', ''), reverse=True)
        winner = records[0]  # kept by dedup (latest bet_date)
        losers = records[1:]
        # Problem: winner has no outcome but a loser does
        settled_losers = [r for r in losers if (r.get('outcome') or '').lower() in ('win', 'placed', 'loss')]
        if settled_losers and not (winner.get('outcome') or '').lower() in ('win', 'placed', 'loss'):
            print(f"\nPROBLEM at {key[0]} {key[1]}:")
            print(f"  KEPT (no outcome, latest): {winner.get('bet_date')} {winner.get('horse')} bet_id={winner.get('bet_id')}")
            for r in settled_losers:
                print(f"  HIDDEN (settled): {r.get('bet_date')} {r.get('horse')} outcome={r.get('outcome')} bet_id={r.get('bet_id')}")
            problem_count += 1
        elif len(records) > 1:
            print(f"\nDUPLICATE at {key[0]} {key[1]}:")
            for r in records:
                print(f"  {r.get('bet_date')} {r.get('horse')} outcome={r.get('outcome')} bet_id={r.get('bet_id')}")

print(f"\nTotal dedup problems (settled hidden): {problem_count}")

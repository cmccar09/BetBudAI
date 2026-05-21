"""
Analyze whether the gap between our pick's score and the next best horse
in the same race is predictive of winning.

If a big gap = more likely to win, we should weight this as a factor.
"""
import boto3
from boto3.dynamodb.conditions import Attr, Key
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# ---------------------------------------------------------------
# 1. Load all picks with comprehensive_score (both settled & ALL)
# ---------------------------------------------------------------
print("Loading all picks with comprehensive_score...")
all_items = []
resp = table.scan(FilterExpression=Attr('comprehensive_score').exists())
all_items.extend(resp['Items'])
while 'LastEvaluatedKey' in resp:
    resp = table.scan(
        FilterExpression=Attr('comprehensive_score').exists(),
        ExclusiveStartKey=resp['LastEvaluatedKey']
    )
    all_items.extend(resp['Items'])

print(f"Total picks with comprehensive_score: {len(all_items)}")

# ---------------------------------------------------------------
# 2. Group all horses by race (bet_date + course + race_time)
# ---------------------------------------------------------------
races = defaultdict(list)
for item in all_items:
    date = item.get('bet_date', '')
    course = item.get('course', '')
    race_time = str(item.get('race_time', ''))[:16]
    if date and course and race_time:
        race_key = (date, course, race_time)
        races[race_key].append(item)

print(f"Total distinct races: {len(races)}")

# ---------------------------------------------------------------
# 3. For each race, find our recommended pick & compute score gap
# ---------------------------------------------------------------
gap_results = []

for race_key, horses in races.items():
    # Sort by score descending
    scored = [(h, float(h.get('comprehensive_score', 0) or 0)) for h in horses]
    scored.sort(key=lambda x: x[1], reverse=True)

    best_horse, best_score = scored[0]
    outcome = best_horse.get('outcome', '')

    # Only analyse settled races where best horse has a result
    if outcome not in ('won', 'lost', 'placed'):
        continue

    # Score gap = difference between our pick and second best
    if len(scored) >= 2:
        second_score = scored[1][1]
        gap = best_score - second_score
    else:
        gap = None  # Only one horse in data

    gap_results.append({
        'race_key': race_key,
        'horse': best_horse.get('horse', '?'),
        'score': best_score,
        'second_score': scored[1][1] if len(scored) >= 2 else None,
        'gap': gap,
        'outcome': outcome,
        'pl': float(best_horse.get('profit_loss', 0) or 0),
        'odds': float(best_horse.get('odds', 0) or 0),
    })

print(f"\nSettled races with full data: {len(gap_results)}")

# ---------------------------------------------------------------
# 4. Bucket by gap size
# ---------------------------------------------------------------
print()
print("=" * 70)
print("SCORE GAP vs OUTCOME ANALYSIS")
print("=" * 70)
print("Gap = (our pick's score) - (next best horse's score)")
print()

gap_buckets = {
    'Large gap (>15pts)':  [r for r in gap_results if r['gap'] is not None and r['gap'] > 15],
    'Medium gap (5-15pts)': [r for r in gap_results if r['gap'] is not None and 5 <= r['gap'] <= 15],
    'Small gap (0-5pts)':  [r for r in gap_results if r['gap'] is not None and 0 <= r['gap'] < 5],
    'Negative gap (<0)':   [r for r in gap_results if r['gap'] is not None and r['gap'] < 0],
    'Single horse data':   [r for r in gap_results if r['gap'] is None],
}

print(f"{'Bucket':<25} {'Races':>7} {'Wins':>6} {'Placed':>7} {'SR%':>7} {'Avg Odds':>10} {'P/L':>9}")
print("-" * 75)

for bucket_name, races_in_bucket in gap_buckets.items():
    if not races_in_bucket:
        continue
    total = len(races_in_bucket)
    wins = sum(1 for r in races_in_bucket if r['outcome'] == 'won')
    places = sum(1 for r in races_in_bucket if r['outcome'] == 'placed')
    total_pl = sum(r['pl'] for r in races_in_bucket)
    avg_odds = sum(r['odds'] for r in races_in_bucket) / total if total > 0 else 0
    sr = ((wins + places) / total * 100) if total > 0 else 0
    print(f"{bucket_name:<25} {total:>7} {wins:>6} {places:>7} {sr:>6.1f}% {avg_odds:>10.2f} {total_pl:>9.2f}")

# ---------------------------------------------------------------
# 5. Show specific examples sorted by gap size (large gaps)
# ---------------------------------------------------------------
print()
print("=" * 70)
print("LARGE GAP RACES (>15pts) - Individual breakdown")
print("=" * 70)
large_gaps = sorted(
    [r for r in gap_results if r['gap'] is not None and r['gap'] > 15],
    key=lambda x: x['gap'],
    reverse=True
)
for r in large_gaps[:20]:
    date, course, rt = r['race_key']
    outcome_sym = 'W' if r['outcome'] == 'won' else 'P' if r['outcome'] == 'placed' else 'L'
    print(f"  [{outcome_sym}] {date} {course:20} {r['horse']:25} "
          f"score={r['score']:.0f} vs next={r['second_score']:.0f} "
          f"(gap=+{r['gap']:.0f}) @ {r['odds']:.2f}  P/L={r['pl']:+.2f}")

print()
print("=" * 70)
print("NEGATIVE GAP RACES - We backed the LOWER-scored horse")
print("=" * 70)
neg_gaps = sorted(
    [r for r in gap_results if r['gap'] is not None and r['gap'] < 0],
    key=lambda x: x['gap']
)
for r in neg_gaps[:20]:
    date, course, rt = r['race_key']
    outcome_sym = 'W' if r['outcome'] == 'won' else 'P' if r['outcome'] == 'placed' else 'L'
    print(f"  [{outcome_sym}] {date} {course:20} {r['horse']:25} "
          f"score={r['score']:.0f} vs next={r['second_score']:.0f} "
          f"(gap={r['gap']:.0f}) @ {r['odds']:.2f}  P/L={r['pl']:+.2f}")

# ---------------------------------------------------------------
# 6. Verdict
# ---------------------------------------------------------------
print()
print("=" * 70)
print("VERDICT")
print("=" * 70)

large = gap_buckets['Large gap (>15pts)']
medium = gap_buckets['Medium gap (5-15pts)']
small = gap_buckets['Small gap (0-5pts)']
neg = gap_buckets['Negative gap (<0)']

def sr(bucket):
    if not bucket:
        return 0
    wins = sum(1 for r in bucket if r['outcome'] in ('won', 'placed'))
    return wins / len(bucket) * 100

def roi(bucket):
    if not bucket:
        return 0
    pl = sum(r['pl'] for r in bucket)
    total_stake = len(bucket) * 6
    return pl / total_stake * 100

print(f"Large gap (>15):   SR={sr(large):.1f}%  ROI={roi(large):.1f}%  n={len(large)}")
print(f"Medium gap (5-15): SR={sr(medium):.1f}%  ROI={roi(medium):.1f}%  n={len(medium)}")
print(f"Small gap (0-5):   SR={sr(small):.1f}%  ROI={roi(small):.1f}%  n={len(small)}")
print(f"Negative gap (<0): SR={sr(neg):.1f}%  ROI={roi(neg):.1f}%  n={len(neg)}")

print()
if len(large) >= 3 and roi(large) > roi(small):
    print("FINDING: Large score gap IS predictive - higher gap = better performance")
    print("RECOMMENDATION: Add score_gap as a scoring bonus factor")
    large_roi = roi(large)
    small_roi = roi(small)
    print(f"  Large gap ROI: {large_roi:.1f}% vs Small gap ROI: {small_roi:.1f}%")
elif len(large) >= 3 and roi(large) < roi(small):
    print("FINDING: Small gap actually performs better - gap not useful as positive signal")
else:
    print("FINDING: Not enough data yet to draw strong conclusions")
    print("  Keep collecting results - gap analysis needs 10+ races per bucket")

print()

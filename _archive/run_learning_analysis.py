"""
Learning Analysis - Comprehensive Score Performance
Analyzes all historical picks to find what score thresholds and patterns work best
"""
import boto3
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print()
print("=" * 70)
print("COMPREHENSIVE LEARNING ANALYSIS")
print("=" * 70)

# Scan all items using high-level resource (auto-deserializes)
from boto3.dynamodb.conditions import Attr
all_items = []
resp = table.scan(
    FilterExpression=Attr('comprehensive_score').exists() & Attr('outcome').is_in(['won', 'lost', 'placed'])
)
all_items.extend(resp['Items'])
while 'LastEvaluatedKey' in resp:
    resp = table.scan(
        FilterExpression=Attr('comprehensive_score').exists() & Attr('outcome').is_in(['won', 'lost', 'placed']),
        ExclusiveStartKey=resp['LastEvaluatedKey']
    )
    all_items.extend(resp['Items'])

print(f"\nTotal settled picks with comprehensive_score: {len(all_items)}")

def get_val(item, key, default=0):
    """Get value from DynamoDB item (high-level SDK returns Python types)"""
    val = item.get(key, default)
    if val is None:
        return default
    return val

# ========================
# 1. Score Bucket Analysis
# ========================
buckets = defaultdict(lambda: {'count': 0, 'wins': 0, 'places': 0, 'pl': 0.0})

for item in all_items:
    score = float(get_val(item, 'comprehensive_score', 0) or 0)
    outcome = str(get_val(item, 'outcome', ''))
    pl = float(get_val(item, 'profit_loss', 0) or 0)
    stake = float(get_val(item, 'stake', 6) or 6)

    if score >= 90:
        bucket = '90-100'
    elif score >= 85:
        bucket = '85-89'
    elif score >= 80:
        bucket = '80-84'
    elif score >= 75:
        bucket = '75-79'
    else:
        bucket = '<75'

    buckets[bucket]['count'] += 1
    buckets[bucket]['stake'] = buckets[bucket].get('stake', 0) + stake
    if outcome == 'won':
        buckets[bucket]['wins'] += 1
    if outcome == 'placed':
        buckets[bucket]['places'] += 1
    buckets[bucket]['pl'] += pl

print()
print("SCORE BUCKET PERFORMANCE")
print("-" * 80)
print(f"{'Score':<10} {'Bets':>6} {'Wins':>6} {'Placed':>7} {'SR%':>7} {'P/L':>10} {'ROI%':>8}")
print("-" * 80)

for bucket in ['90-100', '85-89', '80-84', '75-79', '<75']:
    b = buckets[bucket]
    if b['count'] == 0:
        continue
    sr = (b['wins'] / b['count']) * 100
    total_stake = b.get('stake', b['count'] * 6)
    roi = (b['pl'] / total_stake) * 100 if total_stake > 0 else 0
    print(f"{bucket:<10} {b['count']:>6} {b['wins']:>6} {b['places']:>7} {sr:>6.1f}% {b['pl']:>10.2f} {roi:>7.1f}%")

total_count = sum(b['count'] for b in buckets.values())
total_wins = sum(b['wins'] for b in buckets.values())
total_places = sum(b['places'] for b in buckets.values())
total_pl = sum(b['pl'] for b in buckets.values())
total_stake = sum(b.get('stake', b['count'] * 6) for b in buckets.values())

print("-" * 80)
sr_overall = (total_wins / total_count * 100) if total_count > 0 else 0
roi_overall = (total_pl / total_stake * 100) if total_stake > 0 else 0
print(f"{'TOTAL':<10} {total_count:>6} {total_wins:>6} {total_places:>7} {sr_overall:>6.1f}% {total_pl:>10.2f} {roi_overall:>7.1f}%")

# ========================
# 2. By Date / Recent Trend
# ========================
from collections import OrderedDict
daily = defaultdict(lambda: {'count': 0, 'wins': 0, 'places': 0, 'pl': 0.0})

for item in all_items:
    score = float(get_val(item, 'comprehensive_score', 0) or 0)
    if score < 80:
        continue  # Only UI-level picks
    date = str(get_val(item, 'date', '') or get_val(item, 'bet_date', '') or '')[:10]
    outcome = str(get_val(item, 'outcome', ''))
    pl = float(get_val(item, 'profit_loss', 0) or 0)

    if date:
        daily[date]['count'] += 1
        if outcome == 'won':
            daily[date]['wins'] += 1
        if outcome == 'placed':
            daily[date]['places'] += 1
        daily[date]['pl'] += pl

print()
print("DAILY PERFORMANCE (80+ score picks)")
print("-" * 70)
print(f"{'Date':<12} {'Picks':>6} {'W':>4} {'P':>4} {'SR%':>7} {'P/L':>9}")
print("-" * 70)

running_pl = 0.0
for date in sorted(daily.keys()):
    d = daily[date]
    if d['count'] == 0:
        continue
    sr = ((d['wins'] + d['places']) / d['count']) * 100
    running_pl += d['pl']
    print(f"{date:<12} {d['count']:>6} {d['wins']:>4} {d['places']:>4} {sr:>6.1f}% {d['pl']:>9.2f}")

print(f"\nRunning P/L across all tracked days: {running_pl:.2f}")

# ========================
# 3. By Course Performance (85+)
# ========================
course_stats = defaultdict(lambda: {'count': 0, 'wins': 0, 'places': 0, 'pl': 0.0})

for item in all_items:
    score = float(get_val(item, 'comprehensive_score', 0) or 0)
    if score < 85:
        continue
    course = str(get_val(item, 'course', 'Unknown') or 'Unknown')
    outcome = str(get_val(item, 'outcome', ''))
    pl = float(get_val(item, 'profit_loss', 0) or 0)

    course_stats[course]['count'] += 1
    if outcome == 'won':
        course_stats[course]['wins'] += 1
    if outcome == 'placed':
        course_stats[course]['places'] += 1
    course_stats[course]['pl'] += pl

print()
print("COURSE PERFORMANCE (85+ score picks, 3+ bets)")
print("-" * 70)
print(f"{'Course':<20} {'Bets':>6} {'W':>4} {'P':>4} {'SR%':>7} {'P/L':>9}")
print("-" * 70)

sorted_courses = sorted(
    [(k, v) for k, v in course_stats.items() if v['count'] >= 3],
    key=lambda x: x[1]['pl'],
    reverse=True
)

for course, c in sorted_courses:
    sr = ((c['wins'] + c['places']) / c['count']) * 100
    print(f"{course:<20} {c['count']:>6} {c['wins']:>4} {c['places']:>4} {sr:>6.1f}% {c['pl']:>9.2f}")

# ========================
# 4. Odds Range Analysis (85+)
# ========================
odds_buckets = defaultdict(lambda: {'count': 0, 'wins': 0, 'places': 0, 'pl': 0.0})

for item in all_items:
    score = float(get_val(item, 'comprehensive_score', 0) or 0)
    if score < 85:
        continue
    odds_raw = get_val(item, 'odds', 0)
    try:
        odds = float(odds_raw)
    except:
        continue
    outcome = str(get_val(item, 'outcome', ''))
    pl = float(get_val(item, 'profit_loss', 0) or 0)

    if odds < 2.0:
        ob = 'Odds-on (<2.0)'
    elif odds < 3.0:
        ob = 'Evens-2/1 (2-3)'
    elif odds < 5.0:
        ob = '3/1-4/1 (3-5)'
    elif odds < 8.0:
        ob = '5/1-7/1 (5-8)'
    else:
        ob = '8/1+ (8+)'

    odds_buckets[ob]['count'] += 1
    if outcome == 'won':
        odds_buckets[ob]['wins'] += 1
    if outcome == 'placed':
        odds_buckets[ob]['places'] += 1
    odds_buckets[ob]['pl'] += pl

print()
print("ODDS RANGE PERFORMANCE (85+ score picks)")
print("-" * 70)
print(f"{'Odds Range':<20} {'Bets':>6} {'W':>4} {'P':>4} {'SR%':>7} {'P/L':>9}")
print("-" * 70)

for ob in ['Odds-on (<2.0)', 'Evens-2/1 (2-3)', '3/1-4/1 (3-5)', '5/1-7/1 (5-8)', '8/1+ (8+)']:
    b = odds_buckets[ob]
    if b['count'] == 0:
        continue
    sr = ((b['wins'] + b['places']) / b['count']) * 100
    print(f"{ob:<20} {b['count']:>6} {b['wins']:>4} {b['places']:>4} {sr:>6.1f}% {b['pl']:>9.2f}")

# ========================
# 5. Key Takeaways
# ========================
print()
print("=" * 70)
print("KEY TAKEAWAYS & IMPROVEMENT RECOMMENDATIONS")
print("=" * 70)

# Find best score threshold
best_roi = -999
best_thresh = None
for bucket in ['90-100', '85-89']:
    b = buckets[bucket]
    if b['count'] >= 3:
        stake = b.get('stake', b['count'] * 6)
        roi = (b['pl'] / stake * 100) if stake > 0 else 0
        if roi > best_roi:
            best_roi = roi
            best_thresh = bucket

if best_thresh:
    print(f"\n1. Best scoring threshold: {best_thresh} (ROI: {best_roi:.1f}%)")

# Best course
if sorted_courses:
    best_course = sorted_courses[0]
    print(f"2. Best performing course: {best_course[0]} (P/L: {best_course[1]['pl']:.2f})")
    worst_course = sorted_courses[-1]
    print(f"3. Worst performing course: {worst_course[0]} (P/L: {worst_course[1]['pl']:.2f})")

# Odds range insight
profitable_odds = [(ob, b) for ob, b in odds_buckets.items() if b['pl'] > 0]
losing_odds = [(ob, b) for ob, b in odds_buckets.items() if b['pl'] < 0]
if profitable_odds:
    best_odds = max(profitable_odds, key=lambda x: x[1]['pl'])
    print(f"4. Best odds range: {best_odds[0]} (P/L: {best_odds[1]['pl']:.2f})")
if losing_odds:
    worst_odds = min(losing_odds, key=lambda x: x[1]['pl'])
    print(f"5. Worst odds range: {worst_odds[0]} (P/L: {worst_odds[1]['pl']:.2f})")

# Check if 90+ is better than 85+
b90 = buckets['90-100']
b85 = buckets['85-89']
if b90['count'] >= 3 and b85['count'] >= 3:
    roi_90 = (b90['pl'] / b90.get('stake', b90['count']*6)) * 100
    roi_85 = (b85['pl'] / b85.get('stake', b85['count']*6)) * 100
    if roi_90 > roi_85:
        print(f"6. RAISE threshold to 90+ (90+ ROI: {roi_90:.1f}% vs 85-89 ROI: {roi_85:.1f}%)")
    else:
        print(f"6. Keep 85+ threshold (85-89 ROI: {roi_85:.1f}% vs 90+ ROI: {roi_90:.1f}%)")

print()

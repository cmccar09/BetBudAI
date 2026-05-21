import boto3
from boto3.dynamodb.conditions import Attr
from collections import defaultdict
import math

def pearson_r(x, y):
    n = len(x)
    mx, my = sum(x)/n, sum(y)/n
    num = sum((xi-mx)*(yi-my) for xi, yi in zip(x, y))
    den = math.sqrt(sum((xi-mx)**2 for xi in x) * sum((yi-my)**2 for yi in y))
    if den == 0:
        return 0, 1.0
    r = num / den
    if abs(r) == 1:
        return r, 0.0
    t = r * math.sqrt(n-2) / math.sqrt(1 - r**2)
    z = abs(t)
    p = 2 * (1 - 0.5 * (1 + math.erf(z / math.sqrt(2))))
    return r, p

def fisher_exact_2x2(a, b, c, d):
    n = a + b + c + d
    r1 = a + b
    c1 = a + c

    def log_choose(n, k):
        if k < 0 or k > n:
            return float('-inf')
        return math.lgamma(n+1) - math.lgamma(k+1) - math.lgamma(n-k+1)

    def hypergeom_pmf(k):
        return math.exp(log_choose(r1, k) + log_choose(n-r1, c1-k) - log_choose(n, c1))

    p_obs = hypergeom_pmf(a)
    lo = max(0, c1 - (n - r1))
    hi = min(r1, c1)

    p_val = sum(hypergeom_pmf(k) for k in range(lo, hi+1) if hypergeom_pmf(k) <= p_obs * 1.0000001)

    if b == 0 or c == 0:
        odds_ratio = float('inf') if (a > 0 and d > 0) else 0
    else:
        odds_ratio = (a * d) / (b * c)

    return min(p_val, 1.0), odds_ratio

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print("Fetching data from DynamoDB...")
all_items = []
resp = table.scan(FilterExpression=Attr('comprehensive_score').exists())
all_items.extend(resp['Items'])
while 'LastEvaluatedKey' in resp:
    resp = table.scan(
        FilterExpression=Attr('comprehensive_score').exists(),
        ExclusiveStartKey=resp['LastEvaluatedKey']
    )
    all_items.extend(resp['Items'])

print(f"Loaded {len(all_items)} items")

races = defaultdict(list)
for item in all_items:
    date = item.get('bet_date', '')
    course = item.get('course', '')
    rt = str(item.get('race_time', ''))[:16]
    if date and course and rt:
        races[(date, course, rt)].append(item)

results = []
for race_key, horses in races.items():
    scored = sorted(horses, key=lambda h: float(h.get('comprehensive_score', 0) or 0), reverse=True)
    best = scored[0]
    best_score = float(best.get('comprehensive_score', 0) or 0)
    outcome = best.get('outcome', '')
    if outcome not in ('won', 'lost', 'placed'):
        continue
    if len(scored) < 2:
        continue
    second_score = float(scored[1].get('comprehensive_score', 0) or 0)
    gap = best_score - second_score
    won = 1 if outcome in ('won', 'placed') else 0
    results.append({'gap': gap, 'won': won, 'score': best_score})

if not results:
    print("No results found!")
    exit()

gaps = [r['gap'] for r in results]
wins = [r['won'] for r in results]
n = len(results)

print(f"\nDataset: {n} settled races with 2+ horses scored")
print()

gaps_sorted = sorted(gaps)
median_gap = gaps_sorted[n // 2]
print(f"Median gap: {median_gap:.1f} pts")
print()

big_idx   = [i for i, g in enumerate(gaps) if g > median_gap]
small_idx = [i for i, g in enumerate(gaps) if g <= median_gap]

win_big   = sum(wins[i] for i in big_idx)
loss_big  = len(big_idx) - win_big
win_small = sum(wins[i] for i in small_idx)
loss_small= len(small_idx) - win_small

print("Contingency table (big gap vs small gap):")
print("              Win   Loss  Total  Win%")
print(f"  Big gap:    {win_big:>4}  {loss_big:>4}  {len(big_idx):>5}  {win_big/len(big_idx)*100:.1f}%")
print(f"  Small gap:  {win_small:>4}  {loss_small:>4}  {len(small_idx):>5}  {win_small/len(small_idx)*100:.1f}%")
print()

p_fisher, odds_ratio = fisher_exact_2x2(win_big, loss_big, win_small, loss_small)
print(f"Fisher exact test: p={p_fisher:.4f}  odds_ratio={odds_ratio:.3f}")

r, p_r = pearson_r(gaps, wins)
print(f"Point-biserial correlation: r={r:.4f}  p={p_r:.4f}")
print()

if p_fisher < 0.05:
    print("*** SIGNIFICANT: Gap IS a statistically significant predictor (p < 0.05) ***")
    direction = "MORE" if odds_ratio > 1 else "LESS"
    print(f"  Direction: Larger gap = {direction} likely to win")
else:
    print(f"NOT SIGNIFICANT: Fisher p={p_fisher:.4f} (threshold: p < 0.05)")
    print("  Gap does NOT significantly predict outcome")
    print("  Conclusion: Do not add score gap as a betting signal")

print()

wins_gaps  = [gaps[i] for i in range(n) if wins[i] == 1]
losses_gaps = [gaps[i] for i in range(n) if wins[i] == 0]
print(f"Mean gap when WIN:  {sum(wins_gaps)/len(wins_gaps):.1f} pts  (n={len(wins_gaps)})")
print(f"Mean gap when LOSS: {sum(losses_gaps)/len(losses_gaps):.1f} pts  (n={len(losses_gaps)})")
print()

third = n // 3
sorted_by_gap = sorted(range(n), key=lambda i: gaps[i])
buckets = [
    ("Bottom 3rd (smallest gap)", sorted_by_gap[:third]),
    ("Middle 3rd              ", sorted_by_gap[third:2*third]),
    ("Top 3rd (largest gap)   ", sorted_by_gap[2*third:]),
]
print("Win rate by gap tertile:")
for label, indices in buckets:
    w = sum(wins[i] for i in indices)
    avg_g = sum(gaps[i] for i in indices) / len(indices)
    print(f"  {label}: {w}/{len(indices)} wins = {w/len(indices)*100:.1f}%  avg_gap={avg_g:.1f}")

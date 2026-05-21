import boto3
from boto3.dynamodb.conditions import Key
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-02-26'))
items = resp['Items']

# Pending UI picks only
pending = [i for i in items if i.get('show_in_ui') == True and not i.get('outcome')]

# Group by race (dedup to best per race)
by_race = defaultdict(list)
for p in pending:
    rt = str(p.get('race_time',''))[11:16]
    by_race[(p.get('course',''), rt)].append(p)

print("PENDING UI PICKS - RANKED BY SCORE\n")
print(f"{'Course':<20} {'Time':<6} {'Horse':<25} {'Score':<7} {'Odds':<8} {'Key Reasons'}")
print("-" * 100)

all_best = []
for (course, rt), picks in sorted(by_race.items()):
    best = max(picks, key=lambda x: int(x.get('comprehensive_score', 0) or 0))
    all_best.append(best)

all_best.sort(key=lambda x: int(x.get('comprehensive_score', 0) or 0), reverse=True)

for h in all_best:
    rt = str(h.get('race_time',''))[11:16]
    score = int(h.get('comprehensive_score', 0) or 0)
    odds = h.get('odds', '')
    reasons = h.get('selection_reasons', [])
    # Top 2 reasons
    top_reasons = ' | '.join(str(r) for r in reasons[:2]) if reasons else ''
    print(f"{h.get('course',''):<20} {rt:<6} {h.get('horse',''):<25} {score:<7} {str(odds):<8} {top_reasons}")

print()

# Get score_breakdown for top 3
print("\nTOP 3 BREAKDOWN:")
for h in all_best[:3]:
    rt = str(h.get('race_time',''))[11:16]
    score = int(h.get('comprehensive_score', 0) or 0)
    bd = h.get('score_breakdown', {})
    odds = float(h.get('odds', 0) or 0)
    
    # Fractional odds display
    frac = f"{int(odds-1)}/1" if odds > 2 else f"{odds-1:.2f}/1"
    
    print(f"\n{'='*60}")
    print(f"  {h.get('course','')} {rt} | {h.get('horse','')} | Score: {score} | Odds: {odds} ({frac})")
    print(f"  Going: {h.get('course','')} going today")
    # Score components
    components = [(k, int(v)) for k, v in bd.items() if int(v or 0) > 0]
    components.sort(key=lambda x: x[1], reverse=True)
    for k, v in components:
        bar = '#' * (v // 2)
        print(f"    {k:<25} {v:>3}pts  {bar}")
    all_reasons = h.get('selection_reasons', [])
    print(f"  Reasons: {'; '.join(str(r) for r in all_reasons)}")

import boto3
from datetime import date

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = str(date.today())
resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today))
items = resp['Items']

# Group by race
races = {}
for item in items:
    key = (item.get('course',''), item.get('race_time',''))
    if key not in races:
        races[key] = []
    s = float(item.get('comprehensive_score', 0) or 0)
    if s > 0:
        races[key].append(item)

# Rank races by: score gap, top score, exclude past races
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
candidates = []

for key, horses in races.items():
    course, race_time_str = key
    if not horses:
        continue
    
    # Parse race time
    try:
        rt = datetime.fromisoformat(race_time_str.replace('Z','+00:00'))
    except:
        continue
    
    # Skip races that have already run (more than 10 min ago)
    if rt < now:
        continue
    
    horses_sorted = sorted(horses, key=lambda x: -float(x.get('comprehensive_score',0) or 0))
    top = horses_sorted[0]
    top_score = float(top.get('comprehensive_score',0) or 0)
    second_score = float(horses_sorted[1].get('comprehensive_score',0) or 0) if len(horses_sorted) > 1 else 0
    gap = top_score - second_score
    
    # Only include races with decent top score (>= 60)
    if top_score < 60:
        continue
    
    candidates.append({
        'course': course,
        'race_time': race_time_str,
        'rt': rt,
        'horse': top.get('horse','?'),
        'score': top_score,
        'gap': gap,
        'odds': top.get('odds','?'),
        'trainer': top.get('trainer','?'),
        'form': top.get('form','?'),
        'second_horse': horses_sorted[1].get('horse','?') if len(horses_sorted) > 1 else '-',
        'second_score': second_score,
        'runners': len(horses_sorted),
        'is_pick': str(top.get('show_in_ui','')).lower() == 'true'
    })

# Sort by gap descending (most dominant pick first)
candidates.sort(key=lambda x: -x['gap'])

print("TOP CANDIDATES BY DOMINANCE (score gap over 2nd place):")
print("="*80)
for i, c in enumerate(candidates[:15]):
    pick_flag = " *** CURRENT PICK ***" if c['is_pick'] else ""
    decimal_odds = float(c['odds']) if c['odds'] != '?' else 0
    sp_approx = f"{decimal_odds-1:.0f}/1" if decimal_odds >= 2 else "evs"
    print(f"\n#{i+1} {c['race_time'][11:16]} {c['course']}")
    print(f"   Horse:  {c['horse']} @ {c['odds']} ({sp_approx})")  
    print(f"   Score:  {c['score']:.0f}/100  |  Gap: +{c['gap']:.0f}pts over {c['second_horse']} ({c['second_score']:.0f})")
    print(f"   Field:  {c['runners']} runners analyzed{pick_flag}")

print()
print("="*80)
print("TOP 3 RECOMMENDED BETS:")
print("="*80)
# Best 3 = highest gap, score >= 75, gap >= 15
top3 = [c for c in candidates if c['score'] >= 75 and c['gap'] >= 15][:3]
for i, c in enumerate(top3):
    decimal_odds = float(c['odds']) if c['odds'] != '?' else 0
    print(f"\nBET #{i+1}: {c['horse']}")
    print(f"  Race:  {c['race_time'][11:16]} {c['course']}")
    print(f"  Odds:  {c['odds']} (≈{decimal_odds-1:.0f}/1)")
    print(f"  Score: {c['score']:.0f}/100 | Dominance: +{c['gap']:.0f}pts clear")

print()
print("VERDICT ON FAHRENHEIT SEVEN (16:38 Southwell):")
f7 = next((c for c in candidates if 'Southwell' in c['course'] and '16:38' in c['race_time']), None)
if f7:
    print(f"  Score: {f7['score']:.0f}/100 but only +{f7['gap']:.0f}pt gap")
    print(f"  2nd place: {f7['second_horse']} ({f7['second_score']:.0f}pts)")
    print(f"  VERDICT: TOO CLOSE - model cannot separate these two horses with confidence")
else:
    print("  Southwell 16:38 already run or no data")

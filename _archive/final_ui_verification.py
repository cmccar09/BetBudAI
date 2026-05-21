import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-07')
)

items = resp.get('Items', [])
ui_picks = [i for i in items if i.get('show_in_ui')]

print("="*80)
print(f"FINAL UI PICKS VERIFICATION - {len(ui_picks)} picks")
print("="*80)

# Group by race
races = {}
for pick in ui_picks:
    race_key = f"{pick.get('race_time')}_{pick.get('course')}"
    if race_key not in races:
        races[race_key] = []
    races[race_key].append(pick)

# Check for duplicates
errors = []
for race_key, picks in sorted(races.items()):
    if len(picks) > 1:
        errors.append((race_key, picks))

if errors:
    print("\n⚠️  ERRORS FOUND - Multiple picks in same race:\n")
    for race_key, picks in errors:
        time = picks[0].get('race_time', '')[:16]
        course = picks[0].get('course')
        print(f"{time} {course} - {len(picks)} picks:")
        for p in sorted(picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
            print(f"  - {p.get('horse'):25} {float(p.get('comprehensive_score', 0)):3.0f}/100 UI:{p.get('show_in_ui')} Rec:{p.get('recommended_bet')}")
else:
    print("\n✅ SUCCESS - All races have exactly 1 pick\n")

print(f"Total races with picks: {len(races)}")
print(f"Total UI picks: {len(ui_picks)}\n")

# Show top 10 by score
print("="*80)
print("TOP 10 UI PICKS BY SCORE")
print("="*80)

for i, pick in enumerate(sorted(ui_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:10], 1):
    horse = pick.get('horse')
    score = float(pick.get('comprehensive_score', 0))
    course = pick.get('course')
    time = pick.get('race_time', '')[:16]
    odds = pick.get('odds', 'N/A')
    rec = '★' if pick.get('recommended_bet') else ' '
    
    print(f"{i:2}. {rec} {horse:25} {score:3.0f}/100 @ {odds:4} odds - {course:15} {time}")

print("\n" + "="*80)

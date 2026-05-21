import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# Check 13:00 Newbury race
print("="*80)
print("13:00 NEWBURY RACE - KADASTRAL VS SOBER GLORY")
print("="*80)

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-07'),
    FilterExpression='course = :course AND race_time = :time',
    ExpressionAttributeValues={
        ':course': 'Newbury',
        ':time': '2026-02-07T13:00:00.000Z'
    }
)

items = resp.get('Items', [])

for i, horse in enumerate(sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True), 1):
    name = horse.get('horse', 'Unknown')
    score = float(horse.get('comprehensive_score', 0))
    odds = horse.get('odds', 'N/A')
    show_ui = horse.get('show_in_ui', False)
    recommended = horse.get('recommended_bet', False)
    form = horse.get('form', 'N/A')
    trainer = horse.get('trainer', 'N/A')
    
    ui_mark = '✓' if show_ui else ' '
    rec_mark = '★' if recommended else ' '
    
    print(f"\n{i}. {ui_mark} {rec_mark} {name}")
    print(f"   Score: {score}/100")
    print(f"   Odds: {odds}")
    print(f"   Form: {form}")
    print(f"   Trainer: {trainer}")
    print(f"   UI: {show_ui}, Recommended: {recommended}")

# Check Risky Obsession
print("\n" + "="*80)
print("RISKY OBSESSION CHECK")
print("="*80)

resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-07')
)

items = resp.get('Items', [])
risky = [i for i in items if 'Risky' in i.get('horse', '')]

if risky:
    r = risky[0]
    print(f"\nHorse: {r.get('horse')}")
    print(f"Score: {r.get('comprehensive_score')}")
    print(f"Odds: {r.get('odds', 'N/A')}")
    print(f"Course: {r.get('course')}")
    print(f"Race Time: {r.get('race_time')}")
    print(f"show_in_ui: {r.get('show_in_ui')}")
    print(f"recommended_bet: {r.get('recommended_bet')}")
    print(f"Form: {r.get('form', 'N/A')}")
    print(f"Trainer: {r.get('trainer', 'N/A')}")
    print(f"Confidence Grade: {r.get('confidence_grade', 'N/A')}")
    print(f"Analysis Method: {r.get('analysis_method', 'N/A')}")
else:
    print("NOT FOUND!")

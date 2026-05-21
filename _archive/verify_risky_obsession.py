import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

# Get Risky Obsession
resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-07')
)

items = resp.get('Items', [])
risky = [i for i in items if 'Risky' in i.get('horse', '')][0]

print("="*80)
print("RISKY OBSESSION - FINAL VERIFICATION")
print("="*80)
print(f"Horse: {risky.get('horse')}")
print(f"Score: {risky.get('comprehensive_score')}/100")
print(f"Odds: {risky.get('odds')}")
print(f"Course: {risky.get('course')}")
print(f"Time: {risky.get('race_time')}")
print(f"show_in_ui: {risky.get('show_in_ui')}")
print(f"recommended_bet: {risky.get('recommended_bet')}")
print(f"Trainer: {risky.get('trainer')}")
print(f"Form: {risky.get('form')}")
print(f"Confidence Grade: {risky.get('confidence_grade')}")

print("\n" + "="*80)
print("ALL FIELDS REQUIRED BY UI:")
print("="*80)
required_fields = ['horse', 'course', 'race_time', 'odds', 'comprehensive_score', 'show_in_ui']
for field in required_fields:
    value = risky.get(field, 'MISSING')
    status = '✓' if value and str(value) != 'MISSING' else '✗'
    print(f"{status} {field:25} = {value}")

print("\n" + "="*80)
print("TOP 7 RECOMMENDED BETS WITH ODDS:")
print("="*80)

recommended = [i for i in items if i.get('recommended_bet')]
for i, pick in enumerate(sorted(recommended, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True), 1):
    horse = pick.get('horse')
    score = float(pick.get('comprehensive_score', 0))
    odds = pick.get('odds', 'N/A')
    course = pick.get('course')
    time = pick.get('race_time', '')[11:16]
    
    print(f"{i}. {horse:25} {score:3.0f}/100 @ {odds} odds - {course:15} {time}")

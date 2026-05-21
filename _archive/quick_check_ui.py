import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-07'))
items = resp.get('Items', [])

recommended = [i for i in items if i.get('recommended_bet')]

print(f"\n{'='*80}")
print(f"RECOMMENDED BETS FOR TODAY: {len(recommended)}")
print(f"{'='*80}\n")

for i, pick in enumerate(sorted(recommended, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True), 1):
    horse = pick.get('horse')
    score = float(pick.get('comprehensive_score', 0))
    course = pick.get('course')
    time = pick.get('race_time', '')[11:16]
    
    print(f"{i:2}. {horse:25} {score:3.0f}/100 @ {course:15} {time}")

print(f"\n{'='*80}\n")

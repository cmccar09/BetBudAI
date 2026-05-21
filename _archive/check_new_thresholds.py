"""Check today's scores with new thresholds"""
import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='show_in_ui = :ui',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':ui': True
    }
)

print("\nTODAY'S UI PICKS WITH NEW THRESHOLDS:")
print("="*80)
print("EXCELLENT (85+): Mortgage bet - 40-50% win chance - 2.0x stake")
print("GOOD (70-84): Solid pick - 25-35% win chance - 1.5x stake")
print("FAIR (55-69): Risky - 15-25% win chance - 1.0x stake")
print("POOR (<55): Avoid - <15% win chance - 0.5x stake")
print("="*80)
print()

grades = {'EXCELLENT': 0, 'GOOD': 0, 'FAIR': 0, 'POOR': 0}

for item in sorted(response['Items'], key=lambda x: -(x.get('comprehensive_score') or x.get('combined_confidence', 0))):
    horse = item.get('horse', 'Unknown')
    score = item.get('comprehensive_score') or item.get('combined_confidence', 0)
    odds = item.get('odds', 0)
    
    if score >= 85:
        grade = 'EXCELLENT'
        color = 'GREEN'
    elif score >= 70:
        grade = 'GOOD'
        color = 'AMBER'
    elif score >= 55:
        grade = 'FAIR'
        color = 'ORANGE'
    else:
        grade = 'POOR'
        color = 'RED'
    
    grades[grade] += 1
    
    print(f"{horse:25} {score:3}/100  {grade:10} ({color:6})  Odds: {odds}")

print(f"\n{'='*80}")
print("DISTRIBUTION:")
for grade, count in grades.items():
    print(f"  {grade}: {count} picks")

import boto3
from decimal import Decimal

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-06'))
items = resp.get('Items', [])

print(f'\n=== TODAY (Feb 6, 2026) IN-DEPTH ANALYSIS ===')
print(f'Total horses analyzed: {len(items)}')

# Group by course
courses = {}
for item in items:
    course = item.get('course', 'Unknown')
    if course not in courses:
        courses[course] = []
    courses[course].append(item)

print(f'\nRaces analyzed by course:')
for course in sorted(courses.keys()):
    count = len(courses[course])
    print(f'  {course:20} - {count:2d} horses')

# Show 70+ scorers (UI picks)
scores_70plus = [i for i in items if float(i.get('comprehensive_score', 0)) >= 70]
print(f'\n=== UI PICKS (70+ Score) ===')
print(f'Total UI picks: {len(scores_70plus)}')
for item in sorted(scores_70plus, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
    score = float(item.get('comprehensive_score', 0))
    rec = ' [RECOMMENDED]' if item.get('recommended_bet') else ''
    time = item.get('race_time', 'Unknown')
    print(f'  {score:.0f}/100{rec:15} - {item.get("horse"):30} @ {item.get("course")} {time}')

# Show all horses with details
print(f'\n=== ALL HORSES ANALYZED (Top 20 by score) ===')
all_sorted = sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)
for item in all_sorted[:20]:
    score = float(item.get('comprehensive_score', 0))
    trainer = item.get('trainer', 'Unknown')
    odds = item.get('decimal_odds', 0)
    print(f'  {score:3.0f}/100 - {item.get("horse"):30} @ {item.get("course"):15} - Trainer: {trainer:20} - Odds: {odds}')

# Show analysis breakdown
print(f'\n=== SCORE DISTRIBUTION ===')
ranges = {
    '85+ (Recommended)': len([i for i in items if float(i.get('comprehensive_score', 0)) >= 85]),
    '70-84 (UI Display)': len([i for i in items if 70 <= float(i.get('comprehensive_score', 0)) < 85]),
    '50-69': len([i for i in items if 50 <= float(i.get('comprehensive_score', 0)) < 70]),
    '30-49': len([i for i in items if 30 <= float(i.get('comprehensive_score', 0)) < 50]),
    'Below 30': len([i for i in items if float(i.get('comprehensive_score', 0)) < 30])
}
for range_name, count in ranges.items():
    print(f'  {range_name:25} - {count:2d} horses')

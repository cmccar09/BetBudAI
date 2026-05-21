"""Show top scored horses for today"""
import boto3
from decimal import Decimal

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = '2026-02-04'
resp = table.query(
    KeyConditionExpression='bet_date = :d',
    ExpressionAttributeValues={':d': today}
)

items = resp['Items']
items.sort(key=lambda x: float(x.get('combined_confidence', 0)), reverse=True)

print('\n' + '='*100)
print('TOP 20 HIGHEST SCORED HORSES TODAY')
print('='*100)
print(f'Total horses analyzed: {len(items)}\n')

for i, item in enumerate(items[:20], 1):
    horse = item.get('horse', '?')
    course = item.get('race_course', '?')
    time = item.get('race_time', '?')
    score = float(item.get('combined_confidence', 0))
    odds = float(item.get('decimal_odds', 0))
    grade = item.get('confidence_grade', '?')
    
    print(f'{i:2}. {horse:25} {course:20} {time:8} Score: {score:5.1f} Odds: {odds:6.2f} Grade: {grade}')

print('\n' + '='*100)
print('RECOMMENDATION:')
print('='*100)

top10 = items[:10]
avg_top10 = sum(float(i.get('combined_confidence', 0)) for i in top10) / len(top10) if top10 else 0

print(f'\nAverage score of top 10: {avg_top10:.1f}')

if avg_top10 >= 70:
    print('✓ Strong picks available - promote top picks to UI')
elif avg_top10 >= 60:
    print('⚠️ Moderate picks - consider top 3-5 for UI')
elif avg_top10 >= 50:
    print('⚠️ Weak day - suggest lowering threshold or skipping')
else:
    print('✗ No confident picks - recommend not betting today')

print('\nTo promote top picks to UI manually:')
print('  python promote_top_picks.py --threshold 60 --limit 10')
print('='*100 + '\n')

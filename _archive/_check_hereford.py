import boto3, json
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get all Hereford picks for bet_date 2026-03-25
resp = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-03-25'),
    FilterExpression=Attr('course').eq('Hereford')
)
items = resp['Items']
print(f'Total Hereford picks: {len(items)}')

# Find 15:30 race
for it in sorted(items, key=lambda x: x.get('race_time', '')):
    rt = it.get('race_time', '')
    horse = it.get('horse', '?')
    score = it.get('comprehensive_score', '?')
    grade = it.get('confidence_grade', '?')
    odds = it.get('odds', '?')
    rec = it.get('recommended_bet', False)
    outcome = it.get('outcome', '-')
    trainer = it.get('trainer', '?')
    
    print(f'{str(rt)[11:16]} | {horse:30} | score={score:5} | grade={grade[:20]:20} | odds={odds} | rec={rec} | outcome={outcome}  trainer={trainer}')
    if '15:30' in str(rt):
        reasons = it.get('selection_reasons', [])
        breakdown = it.get('score_breakdown', {})
        print(f'  REASONS: {reasons}')
        print(f'  BREAKDOWN: {json.dumps(dict(breakdown), default=str)}')
        print()

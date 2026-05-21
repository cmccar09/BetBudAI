import boto3
from datetime import date

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
today = date.today().isoformat()

items = []
last_key = None
while True:
    kwargs = {'KeyConditionExpression': boto3.dynamodb.conditions.Key('bet_date').eq(today)}
    if last_key:
        kwargs['ExclusiveStartKey'] = last_key
    resp = table.query(**kwargs)
    items += resp.get('Items', [])
    last_key = resp.get('LastEvaluatedKey')
    if not last_key:
        break

print(f'Total items today: {len(items)}')
show_true = [i for i in items if i.get('show_in_ui') is True]
print(f'show_in_ui=True: {len(show_true)}')

real_picks = [i for i in items if i.get('horse') and 'SYSTEM' not in str(i.get('bet_id', ''))]
real_picks.sort(key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)
print('\nTop 15 by score:')
for p in real_picks[:15]:
    score = p.get('comprehensive_score', '?')
    show = p.get('show_in_ui')
    grade = p.get('grade', '?')
    tier = p.get('tier', '?')
    horse = p.get('horse', '?')
    course = p.get('course', '?')
    conf = p.get('confidence', '?')
    min_conf = p.get('min_confidence_used', '?')
    print(f"  score={score!s:>5} conf={conf!s:>4} min_conf={min_conf!s:>4} show={show} grade={grade} tier={tier} | {horse} @ {course}")

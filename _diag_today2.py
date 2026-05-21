import boto3
from datetime import date, datetime, timezone

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
today = date.today().isoformat()
now_utc = datetime.now(timezone.utc)
print(f'Now UTC: {now_utc.strftime("%H:%M")}')

all_items = []
last_key = None
while True:
    kwargs = {'KeyConditionExpression': boto3.dynamodb.conditions.Key('bet_date').eq(today)}
    if last_key:
        kwargs['ExclusiveStartKey'] = last_key
    r = table.query(**kwargs)
    all_items += r.get('Items', [])
    last_key = r.get('LastEvaluatedKey')
    if not last_key:
        break

print('\n--- show_in_ui=True picks ---')
for it in sorted(all_items, key=lambda x: x.get('race_time','') or ''):
    if it.get('show_in_ui') is True:
        rt = it.get('race_time','')
        horse = it.get('horse','?')
        course = it.get('course','?')
        score = it.get('comprehensive_score','?')
        pick_type = it.get('pick_type','?')
        rec = it.get('recommended_bet','?')
        print(f"  {rt} | {horse} @ {course} | score={score} | pick_type={pick_type} | recommended_bet={rec}")

print('\n--- show_in_ui=False, score>=78 ---')
for it in sorted(all_items, key=lambda x: float(x.get('comprehensive_score',0)), reverse=True):
    if it.get('show_in_ui') is not True and float(it.get('comprehensive_score',0)) >= 78:
        rt = it.get('race_time','')
        horse = it.get('horse','?')
        course = it.get('course','?')
        score = it.get('comprehensive_score','?')
        pick_type = it.get('pick_type','?')
        rec = it.get('recommended_bet','?')
        is_learning = it.get('is_learning_pick','?')
        print(f"  {rt} | {horse} @ {course} | score={score} | pick_type={pick_type} | rec={rec} | learning={is_learning}")

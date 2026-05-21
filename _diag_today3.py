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

print('\n--- All 4 show_in_ui=True picks with stake & race_time details ---')
for it in sorted(all_items, key=lambda x: x.get('race_time','') or ''):
    if it.get('show_in_ui') is True:
        rt = it.get('race_time','')
        stake = it.get('stake', 'MISSING')
        horse = it.get('horse','?')
        course = it.get('course','?')
        score = it.get('comprehensive_score','?')
        # Check stake filter
        stake_val = float(stake) if stake != 'MISSING' else 0
        stake_passes = stake_val <= 10
        # Check time filter
        try:
            race_dt = datetime.fromisoformat(str(rt).replace('Z','+00:00'))
            time_passes = race_dt.astimezone(timezone.utc) > now_utc
        except:
            time_passes = 'parse error'
        print(f"  {rt} | {horse} @ {course} | score={score} | stake={stake} | stake_passes={stake_passes} | time_passes={time_passes}")

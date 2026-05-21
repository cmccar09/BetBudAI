import boto3
from boto3.dynamodb.conditions import Attr
from decimal import Decimal
db = boto3.resource('dynamodb', region_name='eu-west-1')
t = db.Table('SureBetBets')
resp = t.scan(FilterExpression=Attr('bet_date').eq('2026-04-16'))
items = resp.get('Items', [])
print(f"Total items for today: {len(items)}")
ui_items = [i for i in items if i.get('show_in_ui') == True]
print(f"UI items: {len(ui_items)}")
ui_items.sort(key=lambda x: x.get('race_time', ''))
for i in ui_items:
    rt = str(i.get('race_time', ''))[11:16]
    course = str(i.get('course', ''))
    horse = str(i.get('horse', ''))
    outcome = str(i.get('outcome', ''))
    fp = i.get('finish_position', '?')
    np = i.get('number_of_places', 'MISSING')
    recorded = str(i.get('result_recorded_at', ''))[:19]
    if isinstance(fp, Decimal): fp = int(fp)
    if isinstance(np, Decimal): np = int(np)
    print(f"{rt}  {course:15s}  {horse:25s}  outcome={outcome:8s}  pos={fp}  places={np}  recorded={recorded}")

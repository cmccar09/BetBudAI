import boto3
from boto3.dynamodb.conditions import Attr

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

resp = tbl.scan(FilterExpression=Attr('bet_date').begins_with('2026-03-24'), Limit=500)
items = resp['Items']
print(f'Items with 2026-03-24: {len(items)}')

ui_picks = [i for i in items if i.get('show_in_ui')]
print(f'show_in_ui=True: {len(ui_picks)}')

# Show all scored items
scored = sorted([i for i in items if i.get('comprehensive_score')],
                key=lambda x: float(x.get('comprehensive_score', 0) or 0), reverse=True)
print(f'\nTop scored horses (any stake):')
for i in scored[:10]:
    sb = i.get('score_breakdown', {})
    cd = float(sb.get('cd_bonus', 0) or 0)
    going = float(sb.get('going_suitability', 0) or 0)
    rwin = float(sb.get('recent_win', 0) or 0)
    horse = i.get('horse', '?')
    course = i.get('course', '?')
    score = float(i.get('comprehensive_score', 0) or 0)
    ui = i.get('show_in_ui', False)
    stake = i.get('stake', '?')
    grade = i.get('confidence_grade', '?')
    print(f'  {horse:25} | {course:12} | score={score:.0f} grade={grade} ui={ui} stake={stake}')
    print(f'    cd={cd:.0f}  going={going:.0f}  recent_win={rwin:.0f}')

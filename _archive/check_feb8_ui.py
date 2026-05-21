import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = response.get('Items', [])
ui_picks = [item for item in items if item.get('show_in_ui', False)]
recommended = [item for item in items if item.get('recommended_bet', False)]

print(f"Total picks for {today}: {len(items)}")
print(f"UI picks (show_in_ui=True): {len(ui_picks)}")
print(f"Recommended bets: {len(recommended)}")
print()

print("All picks with show_in_ui status:")
for item in sorted(items, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
    show = "UI" if item.get('show_in_ui') else "HIDDEN"
    rec = "REC" if item.get('recommended_bet') else ""
    score = float(item.get('comprehensive_score', 0))
    print(f"  {show:6} {rec:3} {score:3.0f}/100  {item.get('horse'):25} @ {item.get('course')}")

"""Check what the 6 picks actually are"""
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

print(f"\n{'='*70}")
print(f"CHECKING THE 6 FILTERED PICKS")
print(f"{'='*70}\n")

# Query both today and yesterday with the same filter as Lambda
all_picks = []
for date in [today, yesterday]:
    response = table.query(
        KeyConditionExpression='bet_date = :date',
        FilterExpression='(attribute_not_exists(is_learning_pick) OR is_learning_pick = :not_learning) AND attribute_not_exists(analysis_type) AND attribute_not_exists(learning_type) AND attribute_exists(course) AND attribute_exists(horse)',
        ExpressionAttributeValues={
            ':date': date,
            ':not_learning': False
        }
    )
    all_picks.extend(response.get('Items', []))

# Filter by today's race_time
today_race_picks = [item for item in all_picks if item.get('race_time', '').startswith(today)]

print(f"Total picks: {len(today_race_picks)}\n")

for i, item in enumerate(today_race_picks, 1):
    print(f"{i}. {item.get('horse', 'Unknown'):25} | {item.get('course', 'Unknown'):15} | {item.get('race_time', 'Unknown')}")
    print(f"   bet_id: {item.get('bet_id')}")
    print(f"   bet_date: {item.get('bet_date')}")
    print(f"   show_in_ui: {item.get('show_in_ui')}")
    print(f"   comprehensive_score: {item.get('comprehensive_score')}")
    print(f"   is_learning_pick: {item.get('is_learning_pick', 'not set')}")
    print(f"   analysis_type: {item.get('analysis_type', 'not set')}")
    print(f"   learning_type: {item.get('learning_type', 'not set')}")
    print()

# Now check what we get WITHOUT the complex filter
print(f"\n{'='*70}")
print(f"CHECKING WITH SIMPLE FILTER (just bet_date)")
print(f"{'='*70}\n")

response = table.query(
    KeyConditionExpression='bet_date = :today',
    ExpressionAttributeValues={':today': today}
)

simple_picks = response.get('Items', [])
print(f"Total picks with bet_date={today}: {len(simple_picks)}")

# Count show_in_ui
ui_picks = [p for p in simple_picks if p.get('show_in_ui') == True]
print(f"Picks with show_in_ui=True: {len(ui_picks)}")

print(f"\nTop 10 by score:")
for item in sorted(simple_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:10]:
    horse = item.get('horse', 'Unknown')
    score = float(item.get('comprehensive_score', 0))
    show_ui = item.get('show_in_ui')
    print(f"  {horse:25} | Score: {score:5.1f} | show_in_ui: {show_ui}")

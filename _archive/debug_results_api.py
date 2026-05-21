"""Debug why results API shows 0 picks"""
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

print(f"\n{'='*70}")
print(f"DEBUGGING RESULTS API - {today}")
print(f"{'='*70}\n")

# Query both today and yesterday
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
    print(f"Date {date}: {len(response.get('Items', []))} picks")

print(f"Total picks from both dates: {len(all_picks)}")

# Filter by today's race_time
today_race_picks = [item for item in all_picks if item.get('race_time', '').startswith(today)]
print(f"Picks with today's race_time: {len(today_race_picks)}")

# Filter by course/horse
valid_picks = [item for item in today_race_picks 
               if item.get('course') and item.get('course') != 'Unknown' 
               and item.get('horse') and item.get('horse') != 'Unknown']
print(f"Picks with valid course/horse: {len(valid_picks)}")

# Check show_in_ui
ui_picks = [item for item in valid_picks if item.get('show_in_ui') == True]
print(f"Picks with show_in_ui=True: {len(ui_picks)}")

# Show sample picks
print(f"\n{'='*70}")
print(f"SAMPLE UI PICKS (first 10):")
print(f"{'='*70}\n")

for item in sorted(ui_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:10]:
    horse = item.get('horse', 'Unknown')
    course = item.get('course', 'Unknown')
    race_time = item.get('race_time', 'Unknown')
    score = float(item.get('comprehensive_score', 0))
    show_ui = item.get('show_in_ui')
    outcome = item.get('outcome', 'NO OUTCOME')
    
    print(f"{horse:25} | {course:15} | Score: {score:5.1f} | show_in_ui: {show_ui} | outcome: {outcome}")

print(f"\n{'='*70}\n")

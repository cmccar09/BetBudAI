"""Verify which picks should be showing on the UI"""
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get today's picks
today = datetime.now().strftime('%Y-%m-%d')
response = table.query(
    KeyConditionExpression='bet_date = :today',
    ExpressionAttributeValues={':today': today}
)

items = response['Items']
print(f"\n=== DATABASE STATUS ===")
print(f"Total picks today: {len(items)}")

# Filter by show_in_ui
ui_picks = [item for item in items if item.get('show_in_ui') == True]
print(f"UI picks (show_in_ui=True): {len(ui_picks)}")

# Filter by recommended_bet
recommended = [item for item in ui_picks if item.get('recommended_bet') == True]
print(f"Recommended bets (85+): {len(recommended)}")

print(f"\n=== TOP PICKS THAT SHOULD SHOW ON UI ===")
for item in sorted(ui_picks, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
    score = float(item.get('comprehensive_score', 0))
    horse = item.get('horse', 'Unknown')
    course = item.get('course', 'Unknown')
    race_time = item.get('race_time', 'Unknown')
    odds = item.get('odds', 'N/A')
    show_ui = item.get('show_in_ui')
    rec_bet = item.get('recommended_bet', False)
    
    marker = "⭐" if rec_bet else "  "
    print(f"{marker} {horse:25} | {course:15} {race_time:5} | Score: {score:5.1f} | Odds: {odds} | UI:{show_ui} | Rec:{rec_bet}")

print(f"\n=== THESE SHOULD BE HIDDEN (show_in_ui=False) ===")
hidden = [item for item in items if item.get('show_in_ui') == False]
for item in sorted(hidden, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:10]:
    score = float(item.get('comprehensive_score', 0))
    horse = item.get('horse', 'Unknown')
    course = item.get('course', 'Unknown')
    race_time = item.get('race_time', 'Unknown')
    
    print(f"   {horse:25} | {course:15} {race_time:5} | Score: {score:5.1f} | show_in_ui: {item.get('show_in_ui')}")

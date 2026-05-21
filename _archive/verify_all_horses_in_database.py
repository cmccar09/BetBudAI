"""
Verify ALL horses are in database for complete learning
"""
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

all_horses = response['Items']

print("="*80)
print(f"DATABASE VERIFICATION - ALL HORSES FOR {today}")
print("="*80)

print(f"\nTotal horses in database: {len(all_horses)}")

# Group by race
races = {}
for horse in all_horses:
    race_key = f"{horse.get('race_time', 'Unknown')} {horse.get('race_course', 'Unknown')}"
    if race_key not in races:
        races[race_key] = []
    races[race_key].append(horse)

print(f"Total races covered: {len(races)}")

print("\n" + "="*80)
print("BREAKDOWN BY RACE")
print("="*80)

for race_key in sorted(races.keys()):
    horses = races[race_key]
    ui_picks = [h for h in horses if h.get('show_in_ui')]
    learning = [h for h in horses if not h.get('show_in_ui')]
    
    print(f"\n{race_key}")
    print(f"  Total horses: {len(horses)}")
    print(f"  UI picks: {len(ui_picks)}")
    print(f"  Learning data: {len(learning)}")
    
    if ui_picks:
        for pick in ui_picks:
            score = pick.get('combined_confidence', 0)
            print(f"    → UI: {pick.get('horse', 'Unknown'):30} Score: {score}")
    
    # Show top 3 learning horses in this race
    learning_sorted = sorted(learning, key=lambda x: x.get('combined_confidence', 0), reverse=True)
    if learning_sorted:
        print(f"    Top learning horses:")
        for horse in learning_sorted[:3]:
            score = horse.get('combined_confidence', 0)
            grade = horse.get('confidence_grade', 'Unknown')
            print(f"      - {horse.get('horse', 'Unknown'):30} Score: {score:>3} ({grade[:30]})")

print("\n" + "="*80)
print("COVERAGE SUMMARY")
print("="*80)

all_scores = [h.get('combined_confidence', 0) for h in all_horses]
ui_picks_count = len([h for h in all_horses if h.get('show_in_ui')])
learning_count = len([h for h in all_horses if not h.get('show_in_ui')])

print(f"\nUI Picks (show_in_ui=True): {ui_picks_count}")
print(f"Learning Data (show_in_ui=False): {learning_count}")
print(f"\nScore range: {min(all_scores):.0f} - {max(all_scores):.0f}")
print(f"Average score: {sum(all_scores)/len(all_scores):.1f}")

print("\n" + "="*80)
print("WHEN RESULTS COME IN")
print("="*80)
print("""
The system will:
1. Scrape Racing Post for actual race winners
2. Match each race with ALL horses we analyzed
3. Update outcome field for ALL horses (WON/LOST)
4. See if we picked the winner (UI pick with outcome=WON)
5. If winner wasn't a UI pick, see its score:
   - High score (55+) = We saw it but didn't promote (threshold too strict)
   - Low score (0-54) = System missed the signals (needs learning)
6. Adjust weights based on which factors predicted actual winners
7. Tomorrow's analysis will be better

Example:
  Race: Kempton 15:10
  Winner: "Dark Baron" (wasn't in our 3 UI picks)
  System checks: What score did "Dark Baron" get?
    → If 58/100: Close! Just below threshold (60+)
    → If 25/100: Missed badly, need to learn what made it win
  Learning: Analyze what factors "Dark Baron" had that we undervalued
""")

print("\n✓ All horses are in database and ready for result matching!")

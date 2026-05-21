"""
Hide old races that have already run
Set show_in_ui=False for races with time < now
"""
import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Get all today's picks
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

picks = [item for item in response['Items'] 
         if not item.get('analysis_type') 
         and not item.get('learning_type')]

now = datetime.now().isoformat()
print(f"\nCurrent time: {now}")
print("\nUpdating show_in_ui flags for past races...\n")

updated_count = 0
for pick in picks:
    race_time = pick.get('race_time', '')
    horse = pick.get('horse', '')
    show_in_ui = pick.get('show_in_ui')
    
    # If race time has passed, set show_in_ui=False
    if race_time and race_time < now:
        if show_in_ui != False:  # Only update if not already hidden
            print(f"Hiding: {horse} @ {race_time} (race finished)")
            table.update_item(
                Key={
                    'bet_date': '2026-02-02',
                    'bet_id': pick['bet_id']
                },
                UpdateExpression='SET show_in_ui = :show',
                ExpressionAttributeValues={
                    ':show': False
                }
            )
            updated_count += 1
    else:
        print(f"Keeping visible: {horse} @ {race_time} (future race)")

print(f"\n✓ Updated {updated_count} past races to hide from UI")

# Show current state
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

picks = [item for item in response['Items'] 
         if not item.get('analysis_type') 
         and not item.get('learning_type')]

visible = [p for p in picks if p.get('show_in_ui') == True]
hidden = [p for p in picks if p.get('show_in_ui') == False]

print(f"\nDatabase state:")
print(f"  Visible in UI: {len(visible)}")
print(f"  Hidden from UI: {len(hidden)}")

if visible:
    print("\nVisible picks (future races):")
    for p in sorted(visible, key=lambda x: x.get('race_time', '')):
        print(f"  ✓ {p.get('horse')} @ {p.get('race_time', 'Unknown')}")

"""
Remove duplicate picks from same race where multiple horses scored 85+
This fixes races that had 2+ recommended picks (too close to call)
"""
import boto3
from datetime import datetime
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

# Get all today's items
resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

items = resp.get('Items', [])

print(f"Checking for duplicate recommended picks - {today}")
print(f"="*70)

# Group by race (course + race_time)
races = defaultdict(list)
for item in items:
    if item.get('show_in_ui') and item.get('recommended_bet'):
        race_key = f"{item.get('course')}_{item.get('race_time')}"
        races[race_key].append(item)

# Find races with multiple 85+ picks
duplicates_found = []
for race_key, picks in races.items():
    if len(picks) > 1:
        duplicates_found.append((race_key, picks))

if not duplicates_found:
    print("\n✓ No duplicate picks found - all races have max 1 recommended pick")
else:
    print(f"\n⚠️  Found {len(duplicates_found)} races with multiple 85+ picks:\n")
    
    for race_key, picks in duplicates_found:
        course = picks[0].get('course')
        race_time = picks[0].get('race_time')
        print(f"\n{course} - {race_time[11:16]}:")
        print(f"  TOO CLOSE TO CALL - removing all picks from this race")
        
        for pick in picks:
            horse = pick.get('horse')
            score = float(pick.get('comprehensive_score', 0))
            print(f"    - {horse}: {score}/100")
        
        # Remove all picks from this race (too close to call)
        for pick in picks:
            table.update_item(
                Key={
                    'bet_date': pick['bet_date'],
                    'bet_id': pick['bet_id']
                },
                UpdateExpression='SET show_in_ui = :show, recommended_bet = :rec',
                ExpressionAttributeValues={
                    ':show': False,  # Hide from UI
                    ':rec': False    # Not recommended
                }
            )
            print(f"      ✓ Removed {pick.get('horse')} from UI")

print(f"\n" + "="*70)
print(f"Cleanup complete")

# Show final counts
resp2 = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)
items2 = resp2.get('Items', [])
ui_picks = [i for i in items2 if i.get('show_in_ui')]

print(f"\nFinal UI picks: {len(ui_picks)}")
print(f"✓ Each race now has max 1 recommended pick (or 0 if too close)")

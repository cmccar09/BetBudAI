"""Check exact database state for UI picks"""
import boto3
from datetime import datetime

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')
print(f"\nChecking database for {today}...\n")

# Query all items for today
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

items = response.get('Items', [])
print(f"Total items for today: {len(items)}")

# Filter for show_in_ui
ui_items = [i for i in items if i.get('show_in_ui') == True]
print(f"Items with show_in_ui=True: {len(ui_items)}\n")

if ui_items:
    # Check first UI item in detail
    sample = ui_items[0]
    print("Sample UI Pick Details:")
    print(f"  horse: {sample.get('horse')}")
    print(f"  course: {sample.get('course')}")
    print(f"  sport: {sample.get('sport')}")
    print(f"  race_time: {sample.get('race_time')}")
    print(f"  show_in_ui: {sample.get('show_in_ui')}")
    print(f"  confidence: {sample.get('confidence')}")
    print(f"  odds: {sample.get('odds')}")
    
    # Check what Lambda would filter
    print(f"\nLambda filtering checks:")
    print(f"  sport == 'horses': {sample.get('sport') == 'horses'}")
    print(f"  sport value: '{sample.get('sport')}'")
    
    # Parse race time
    race_time_str = sample.get('race_time', '')
    if race_time_str:
        from datetime import datetime
        try:
            race_time = datetime.fromisoformat(race_time_str.replace('Z', '+00:00'))
            now = datetime.utcnow()
            print(f"  race_time: {race_time}")
            print(f"  now (UTC): {now}")
            print(f"  Future race: {race_time.replace(tzinfo=None) > now}")
        except Exception as e:
            print(f"  Error parsing time: {e}")

print("\n")

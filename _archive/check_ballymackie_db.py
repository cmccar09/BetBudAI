import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
today = '2026-02-10'

# Query for Ballymackie
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(today)
)

all_items = response.get('Items', [])
ballymackie = [i for i in all_items if 'Ballymackie' in i.get('horse', '')]

print("BALLYMACKIE IN DATABASE")
print("="*80)

if ballymackie:
    b = ballymackie[0]
    print(f"Horse: {b.get('horse')}")
    print(f"Course: {b.get('course')}")
    print(f"Race time: {b.get('race_time')}")
    print(f"Score: {b.get('comprehensive_score')}")
    print(f"show_in_ui: {b.get('show_in_ui')}")
    print(f"outcome: {b.get('outcome')}")
    print(f"finish_position: {b.get('finish_position')}")
    print(f"starting_price: {b.get('starting_price')}")
else:
    print("❌ Not found")

# Check all UI picks today
ui_picks = [i for i in all_items if i.get('show_in_ui') == True]
print(f"\n\nTotal UI picks for {today}: {len(ui_picks)}")

for pick in ui_picks:
    print(f"  {pick.get('horse'):30} {pick.get('course'):12} {pick.get('comprehensive_score'):3.0f}/100  outcome: {pick.get('outcome', 'pending')}")

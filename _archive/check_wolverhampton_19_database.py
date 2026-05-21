import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('BettingPicks')

print("\n" + "="*80)
print("CHECKING DATABASE FOR 19:00 WOLVERHAMPTON")
print("="*80)

response = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-02-02')
)

wolverhampton_19 = [item for item in response['Items'] 
                    if 'Wolverhampton' in item.get('course', '') 
                    and '19:00' in item.get('bet_id', '')]

print(f"\nFound {len(wolverhampton_19)} items for Wolverhampton 19:00")

for item in wolverhampton_19:
    print(f"\n  bet_id: {item.get('bet_id')}")
    print(f"  horse: {item.get('horse')}")
    print(f"  odds: {item.get('odds')}")
    print(f"  outcome: {item.get('outcome', 'pending')}")
    print(f"  show_in_ui: {item.get('show_in_ui', 'not set')}")

# Check all today's items
all_picks = response['Items']
print(f"\n\nALL TODAY'S PICKS ({len(all_picks)} total):")
for item in all_picks:
    print(f"  {item.get('horse', 'Unknown')} @ {item.get('course', 'Unknown')} - {item.get('bet_id', 'Unknown')[:16]}")

print("\n" + "="*80)

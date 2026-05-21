import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Get today's picks
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-01-11'}
)

items = response.get('Items', [])
greyhounds = [i for i in items if i.get('sport') == 'greyhounds']
horses = [i for i in items if i.get('sport') == 'horses']

print(f"=== DATABASE PICKS FOR 2026-01-11 ===")
print(f"Total picks: {len(items)}")
print(f"  Horses: {len(horses)}")
print(f"  Greyhounds: {len(greyhounds)}")

print(f"\n=== GREYHOUND PICKS ===")
for pick in greyhounds:
    result = pick.get('actual_result', 'PENDING')
    name = pick.get('horse_name') or pick.get('selection_name') or pick.get('name', 'Unknown')
    venue = pick.get('venue', 'Unknown')
    print(f"  {name} @ {venue}")
    print(f"    Predicted: {float(pick.get('p_win', 0))*100:.1f}%")
    print(f"    Result: {result}")
    print()

print(f"\n=== RESULTS STATUS ===")
print(f"Greyhounds with results: {len([i for i in greyhounds if i.get('actual_result')])}/{len(greyhounds)}")
print(f"Horses with results: {len([i for i in horses if i.get('actual_result')])}/{len(horses)}")

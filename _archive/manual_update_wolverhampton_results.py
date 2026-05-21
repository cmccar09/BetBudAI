import boto3
from decimal import Decimal

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')

print("\n=== MANUAL RESULTS UPDATE - FEBRUARY 6, 2026 ===\n")

# Known Wolverhampton results
wolverhampton_results = [
    {'time': '13:12', 'winner': 'Cargin Bhui', '2nd': 'Albert Cee', '3rd': 'Woodhay Whisper'},
    {'time': '13:42', 'winner': 'Mr Dreamseller', '2nd': 'Correspondence', '3rd': 'Raveena'},
    {'time': '14:12', 'winner': 'Oldbury Lad', '2nd': 'Woodrafff', '3rd': 'Legendsoftheland'},
    {'time': '14:42', 'winner': 'Von Krolock', '2nd': 'Homer Stokes', '3rd': 'Galette'},
    {'time': '15:17', 'winner': 'Royal Jet', '2nd': 'Bad Habits', '3rd': 'Court Of Session'},
]

# Get all Feb 6 items
resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-06'))
items = resp.get('Items', [])

wolverhampton_horses = [i for i in items if i.get('course') == 'Wolverhampton']

print(f"Found {len(wolverhampton_horses)} Wolverhampton horses in database\n")

updated_count = 0

for result in wolverhampton_results:
    race_time = result['time']
    winner_name = result['winner']
    second_name = result['2nd']
    third_name = result['3rd']
    
    print(f"\nUpdating {race_time} Wolverhampton...")
    
    # Find horses in this race
    race_horses = [h for h in wolverhampton_horses if race_time in h.get('race_time', '')]
    
    for horse in race_horses:
        horse_name = horse.get('horse')
        bet_id = horse.get('bet_id')
        
        if horse_name == winner_name:
            outcome = 'Won'
        elif horse_name == second_name:
            outcome = 'Placed'
        elif horse_name == third_name:
            outcome = 'Placed'
        else:
            outcome = 'Lost'
        
        # Update in database
        try:
            table.update_item(
                Key={
                    'bet_date': '2026-02-06',
                    'bet_id': bet_id
                },
                UpdateExpression='SET outcome = :outcome',
                ExpressionAttributeValues={
                    ':outcome': outcome
                }
            )
            updated_count += 1
            print(f"  ✓ {horse_name:30} - {outcome}")
        except Exception as e:
            print(f"  ✗ {horse_name:30} - Error: {e}")

print(f"\n=== SUMMARY ===")
print(f"Updated: {updated_count} horses")
print(f"Races: {len(wolverhampton_results)}")

# Verify updates
print(f"\nVerifying...")
resp = table.query(KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-06'))
items = resp.get('Items', [])

outcomes = {}
for item in items:
    outcome = item.get('outcome', 'UNKNOWN')
    if outcome is None:
        outcome = 'None'
    outcomes[outcome] = outcomes.get(outcome, 0) + 1

print(f"\nOutcome Status:")
for status, count in sorted(outcomes.items(), key=lambda x: (x[0] is None, x[0])):
    print(f"  {status:20} - {count} horses")

print(f"\n✅ Wolverhampton results updated successfully!")

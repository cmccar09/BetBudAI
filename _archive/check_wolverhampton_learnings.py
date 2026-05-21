import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-02'

# Get all Wolverhampton items
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

print('\n' + '='*80)
print('ALL WOLVERHAMPTON ITEMS IN DATABASE')
print('='*80)

wolv_items = [item for item in response['Items'] if item.get('course') == 'Wolverhampton']

for item in sorted(wolv_items, key=lambda x: x.get('race_time', '')):
    print(f"\nRace Time: {item.get('race_time')}")
    print(f"  Horse: {item.get('horse')}")
    print(f"  Odds: {item.get('odds')}")
    print(f"  Outcome: {item.get('outcome')}")
    print(f"  Bet ID: {item.get('bet_id')}")
    print(f"  is_learning_pick: {item.get('is_learning_pick', 'Not set')}")
    print(f"  learning_type: {item.get('learning_type', 'Not set')}")
    print(f"  analysis_type: {item.get('analysis_type', 'Not set')}")

# Check for learning records with WOLVERHAMPTON in bet_id
print('\n' + '='*80)
print('LEARNING RECORDS WITH "WOLVERHAMPTON" IN BET_ID')
print('='*80)

learning_items = [item for item in response['Items'] if 'WOLVERHAMPTON' in item.get('bet_id', '').upper() and item.get('learning_type')]

if learning_items:
    for item in learning_items:
        print(f"\nBet ID: {item.get('bet_id')}")
        print(f"  Learning Type: {item.get('learning_type')}")
        print(f"  Race Time: {item.get('race_time')}")
        print(f"  Horse: {item.get('horse', 'N/A')}")
else:
    print('\nNo learning records found with WOLVERHAMPTON in bet_id')
    print('\nLet me check if 17:00 learning was saved with different format...')
    
    all_learnings = [item for item in response['Items'] if item.get('learning_type') and '17' in item.get('bet_id', '')]
    if all_learnings:
        print(f'\nFound {len(all_learnings)} learning records with "17" in bet_id:')
        for item in all_learnings:
            print(f"  {item.get('bet_id')}: {item.get('learning_type')}")

print('\n' + '='*80)
print('NEED TO ANALYZE')
print('='*80)

# Check which races need analysis
wolv_picks = [item for item in wolv_items if not item.get('learning_type') and not item.get('analysis_type')]

for pick in sorted(wolv_picks, key=lambda x: x.get('race_time', '')):
    race_time = pick.get('race_time', '')
    outcome = pick.get('outcome')
    
    # Check if we have a learning for this race
    has_learning = any(item.get('learning_type') and item.get('race_time') == race_time for item in wolv_items)
    
    if race_time:
        # Extract time (HH:MM format)
        if 'T' in race_time:
            time_part = race_time.split('T')[1][:5]  # Get HH:MM
        else:
            time_part = race_time
            
        status = '✓ HAS LEARNING' if has_learning else '✗ NEEDS ANALYSIS'
        result_status = 'COMPLETE' if outcome and outcome != 'pending' else 'PENDING RESULT'
        
        print(f"\n{time_part}: {pick.get('horse')} @ {pick.get('odds')} - {outcome}")
        print(f"  Status: {status}")
        print(f"  Result: {result_status}")

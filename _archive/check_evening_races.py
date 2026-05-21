import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = '2026-02-02'
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': today}
)

# Find all picks (not learning/analysis)
picks = [item for item in response['Items'] 
         if not item.get('learning_type') 
         and not item.get('analysis_type')
         and not item.get('is_learning_pick')]

# Filter evening picks
print('\n' + '='*80)
print('EVENING PICKS (17:00 ONWARDS)')
print('='*80)

for pick in sorted(picks, key=lambda x: x.get('race_time', '')):
    time = pick.get('race_time', '')
    if '17:' in time or '18:' in time or '19:' in time or '20:' in time:
        # Extract hour
        if 'T' in time:
            hour_min = time.split('T')[1][:5]
        else:
            hour_min = time
        
        outcome = pick.get('outcome') or 'pending'
        
        # Check if we have learning for this race
        has_learning = False
        for item in response['Items']:
            if item.get('learning_type'):
                item_time = str(item.get('race_time', ''))
                if hour_min in item_time or time in item_time:
                    has_learning = True
                    break
        
        status = '✓ Analyzed' if has_learning else '✗ Not analyzed'
        
        print(f'\n{hour_min}: {pick.get("horse")} @ {pick.get("odds")} - {outcome}')
        print(f'  Course: {pick.get("course")}')
        print(f'  Status: {status}')

print('\n' + '='*80)
print('SUMMARY')
print('='*80)
print('\nCurrent time: 18:00 (6:00 PM)')
print('\nCompleted races:')
print('  ✓ 17:00 - Take The Boat WON @ 4.0')
print('  ✓ 17:30 - Leonetto LOST @ 1.2')
print('\nUpcoming races:')
print('  ⏰ 18:30 - Latin @ 3.85 (in 30 minutes)')

"""
Show where and how analysis records are saved in DynamoDB
"""

import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

print('\n' + '='*80)
print('ANALYSIS RECORDS IN DYNAMODB')
print('='*80)

# Get sample analysis records
response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-02'}
)

# Filter to analysis records only
analysis_items = [item for item in response['Items'] if item.get('analysis_type')]

print(f'\nTotal analysis records today: {len(analysis_items)}')

print('\n' + '='*80)
print('SAMPLE ANALYSIS RECORD STRUCTURE')
print('='*80)

if analysis_items:
    sample = analysis_items[0]
    
    print('\nKeys and identifying fields:')
    print(f'  bet_date: {sample.get("bet_date")}')
    print(f'  bet_id: {sample.get("bet_id")}')
    print(f'  analysis_type: {sample.get("analysis_type")}')
    print(f'  analysis_purpose: {sample.get("analysis_purpose", "NOT SET")}')
    
    print('\nRace information:')
    print(f'  venue: {sample.get("venue", "NOT SET")}')
    print(f'  course: {sample.get("course", "NOT SET")}')
    print(f'  race_time: {sample.get("race_time")}')
    print(f'  market_id: {sample.get("market_id", "NOT SET")}')
    print(f'  going: {sample.get("going", "NOT SET")}')
    
    print('\nHorse information:')
    print(f'  horse: {sample.get("horse", "NOT SET")}')
    print(f'  selection_id: {sample.get("selection_id", "NOT SET")}')
    print(f'  odds: {sample.get("odds", "NOT SET")}')
    print(f'  form: {sample.get("form", "NOT SET")}')
    
    print('\nAnalysis data fields:')
    fields = [k for k in sample.keys() if k not in ['bet_date', 'bet_id', 'analysis_type', 'venue', 'course', 'race_time', 'horse', 'odds']]
    for field in sorted(fields)[:15]:
        value = sample.get(field)
        if isinstance(value, (str, int, float, Decimal)) and len(str(value)) < 50:
            print(f'  {field}: {value}')

print('\n' + '='*80)
print('WHERE ANALYSES ARE SAVED')
print('='*80)

print('\n1. analyze_all_races_comprehensive.py (lines 230-300)')
print('   - Creates ANALYSIS_{market_id}_{selection_id} records')
print('   - Sets analysis_type = "PRE_RACE_COMPLETE"')
print('   - Sets analysis_purpose = "CONTINUOUS_LEARNING"')
print('   - Saves to SureBetBets table')

print('\n2. Record structure:')
print('   - Partition Key: bet_date (e.g., "2026-02-02")')
print('   - Sort Key: bet_id (e.g., "ANALYSIS_unknown_12126672")')
print('   - Contains: All race/horse data + comprehensive analysis')

print('\n3. Purpose:')
print('   - Store pre-race analysis for ALL horses')
print('   - Build database for continuous learning')
print('   - Compare predictions vs actual results later')

print('\n4. Why "Unknown" course:')
print('   - Market data uses "venue" not "course"')
print('   - Course field not populated during analysis')
print('   - These are filtered from UI (not actual picks)')

print('\n' + '='*80)
print('ACTUAL PICKS vs ANALYSES')
print('='*80)

actual_picks = [item for item in response['Items'] 
                if not item.get('analysis_type') 
                and not item.get('learning_type')
                and not item.get('is_learning_pick')]

print(f'\nActual betting picks: {len(actual_picks)}')
print(f'Analysis records: {len(analysis_items)}')
print(f'Total in database: {len(response["Items"])}')

print('\nDifference:')
print('  - PICKS: Selected horses to bet on (bet_id = timestamp_course_horse)')
print('  - ANALYSES: All horses analyzed (bet_id = ANALYSIS_marketid_selectionid)')
print('  - PICKS shown in UI, ANALYSES hidden (for learning)')

print('='*80)

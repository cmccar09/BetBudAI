import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

response = table.scan(
    FilterExpression='contains(horse, :h)',
    ExpressionAttributeValues={':h': 'Many A Star'}
)

if response['Items']:
    item = response['Items'][0]
    print('\n' + '='*80)
    print('MANY A STAR - MISSING WINNER ANALYSIS')
    print('='*80)
    print(f"\nanalysis_type: {item.get('analysis_type')}")
    print(f"comprehensive_score: {item.get('comprehensive_score')}")
    print(f"confidence_grade: {item.get('confidence_grade')}")
    print(f"form: {item.get('form')}")
    print(f"odds: {item.get('odds')}")
    print(f"jockey: {item.get('jockey')}")
    print(f"trainer: {item.get('trainer')}")
    
    print('\n' + '-'*80)
    print('ROOT CAUSE:')
    print('-'*80)
    
    analysis_type = item.get('analysis_type')
    score = item.get('comprehensive_score')
    
    if not analysis_type:
        print('✗ PROBLEM: No analysis_type field')
        print('  calculate_all_confidence_scores.py filters for:')
        print('  - PRE_RACE_COMPLETE (from comprehensive analyzer)')
        print('  - COMPLETE_ANALYSIS (from force_complete_analysis)')
        print('  This horse has neither!')
    elif analysis_type not in ['PRE_RACE_COMPLETE', 'COMPLETE_ANALYSIS']:
        print(f'✗ PROBLEM: Wrong analysis_type: {analysis_type}')
        print(f'  Should be PRE_RACE_COMPLETE or COMPLETE_ANALYSIS')
    elif not score:
        print('✗ PROBLEM: analysis_type correct but score not calculated')
        print('  Issue in calculate_all_confidence_scores.py')
    
    # Check form quality
    form = item.get('form', '')
    if form:
        print('\n' + '-'*80)
        print('FORM ANALYSIS:')
        print('-'*80)
        print(f'Form: {form}')
        print('Recent positions: ', end='')
        for c in form[:5]:
            if c.isdigit():
                print(c, end=' ')
        print()
        
        if '1' in form:
            print('✓ Has a win in form')
        if '2' in form[:3]:
            print('✓ Has place in last 3 runs')
            
    # Calculate what score SHOULD be
    print('\n' + '-'*80)
    print('WHAT SCORE SHOULD HAVE BEEN:')
    print('-'*80)
    print(f'Base: 30')
    print(f'Form: 651524- (moderate)')
    print(f'Odds: 8.4/1 (in value zone 3-7, should get +8 bonus)')
    print(f'Expected score: ~40-50 range')
    print(f'Grade: Likely FAIR or GOOD')
    print(f'Threshold: 45 (would likely make UI picks!)')

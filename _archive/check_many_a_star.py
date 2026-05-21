"""
Analyze why Many A Star (8/1 winner) wasn't picked
"""
import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

# Query for Many A Star
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='contains(horse, :horse) AND contains(race_time, :time)',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':horse': 'Many A Star',
        ':time': '18:00'
    }
)

items = response.get('Items', [])

print('\n' + '='*80)
print('WHY DID WE MISS MANY A STAR @ 8/1 WINNER?')
print('='*80)

if items:
    for item in items:
        print(f'\nHorse: {item.get("horse")}')
        print(f'Comprehensive Score: {item.get("comprehensive_score", "N/A")}/100')
        print(f'Confidence Grade: {item.get("confidence_grade", "N/A")}')
        print(f'Odds: {item.get("odds", "N/A")}')
        print(f'Show in UI: {item.get("show_in_ui", False)}')
        print(f'Form: {item.get("form", "N/A")}')
        print(f'Analysis Type: {item.get("analysis_type", "N/A")}')
        print(f'Course: {item.get("course", "N/A")}')
        
        score = item.get('comprehensive_score', 'N/A')
        show_ui = item.get('show_in_ui', False)
        
        print('\n' + '-'*80)
        print('ANALYSIS:')
        print('-'*80)
        
        if score == 'N/A':
            print('✗ PROBLEM: No comprehensive score calculated')
            print('  Likely not analyzed by analyze_all_races_comprehensive.py')
        elif score < 45:
            print(f'✗ PROBLEM: Score {score}/100 below UI threshold (45)')
            print(f'  Form: {item.get("form", "N/A")}')
            print(f'  At 8/1 odds (in value zone), should have gotten bonuses')
            print(f'  Need to investigate form scoring')
        elif score >= 45 and not show_ui:
            print(f'✗ PROBLEM: Score {score}/100 above threshold but show_in_ui=False')
            print('  Issue in set_ui_picks_from_validated.py')
        else:
            print(f'✓ Score: {score}/100, show_in_ui: {show_ui}')
            
else:
    print('\n✗ CRITICAL: Many A Star NOT FOUND in database!')
    print('  Was not analyzed at all')
    print('  Check analyze_all_races_comprehensive.py coverage')

# Now check all horses in the race
print('\n' + '='*80)
print('ALL HORSES IN WOLVERHAMPTON 18:00')
print('='*80)

response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='contains(race_time, :time) AND contains(venue, :venue)',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':time': '18:00',
        ':venue': 'Wolverhampton'
    }
)

all_items = response.get('Items', [])
print(f'\nTotal horses found: {len(all_items)}')

# Show sorted by score
scored = [x for x in all_items if x.get('comprehensive_score') not in [None, 'N/A']]
print(f'Horses with scores: {len(scored)}')

if scored:
    print('\nRanking:')
    for item in sorted(scored, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
        horse = item.get('horse', 'Unknown')
        score = item.get('comprehensive_score', 0)
        grade = item.get('confidence_grade', 'N/A')
        odds = item.get('odds', 'N/A')
        show_ui = item.get('show_in_ui', False)
        form = item.get('form', 'N/A')
        
        marker = '✓ UI' if show_ui else '   '
        print(f'{marker} {horse:20s} {score:5.1f}/100 {grade:10s} @ {odds:5s} Form: {form}')

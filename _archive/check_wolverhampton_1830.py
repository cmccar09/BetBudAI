"""
Record Wolverhampton 18:30 result and check our pick
1st: Lucky Sevens
2nd: Harlequin Bay
3rd: Sparksmith
5th: Lovethiswayagain (our pick?)
"""
import boto3

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# Check our pick for 18:30
response = table.query(
    KeyConditionExpression='bet_date = :date',
    FilterExpression='contains(race_time, :time) AND contains(venue, :venue)',
    ExpressionAttributeValues={
        ':date': '2026-02-03',
        ':time': '18:30',
        ':venue': 'Wolverhampton'
    }
)

items = response['Items']
print('\n' + '='*80)
print('WOLVERHAMPTON 18:30 - 6f Mdn Stks')
print('='*80)

print('\nRACE RESULT:')
print('1st: Lucky Sevens (no form shown)')
print('2nd: Harlequin Bay @ F: 522-')
print('3rd: Sparksmith @ F: 3-2')
print('4th: Analeesa @ F: 0-5')
print('5th: Lovethiswayagain @ F: 3246-2')

print('\n' + '-'*80)
print('DATABASE CHECK:')
print('-'*80)

ui_pick = None
lovethis = None

for item in items:
    horse = item.get('horse', '')
    score = item.get('comprehensive_score') or item.get('combined_confidence', 0)
    show_ui = item.get('show_in_ui', False)
    
    print(f'{horse:25} Score: {score:6} show_in_ui: {show_ui}')
    
    if show_ui:
        ui_pick = item
    if 'Lovethiswayagain' in horse:
        lovethis = item

print('\n' + '-'*80)
print('OUR PICK vs RESULT:')
print('-'*80)

if ui_pick:
    print(f'✓ UI Pick: {ui_pick.get("horse")}')
    print(f'  Score: {ui_pick.get("comprehensive_score") or ui_pick.get("combined_confidence")}/100')
    print(f'  Grade: {ui_pick.get("confidence_grade")}')
    print(f'  Form: {ui_pick.get("form")}')
    
    if ui_pick.get('horse') == 'Lovethiswayagain':
        print(f'\n  RESULT: 5th place - LOST')
        print(f'  Analysis: Scored 69/100 (GOOD) but finished 5th')
    else:
        print(f'\n  RESULT: Not Lovethiswayagain - check result')
else:
    print('✗ NO UI PICK for this race')
    print('  This race may not have been selected in TOP 10')
    if lovethis:
        print(f'\n  Lovethiswayagain was in database:')
        print(f'  Score: {lovethis.get("comprehensive_score") or lovethis.get("combined_confidence")}/100')
        print(f'  But show_in_ui = {lovethis.get("show_in_ui")}')
        print(f'  Not selected in TOP 10 picks')

print('\n' + '-'*80)
print('WINNER ANALYSIS:')
print('-'*80)
print('Lucky Sevens WON')
print('  No form shown (possibly first run)')
print('  Not in our database (new horse or no prior data)')
print('  System cannot predict horses with no form history')

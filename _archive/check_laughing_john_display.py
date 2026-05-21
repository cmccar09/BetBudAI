"""
Check Laughing John's next_best_score specifically
"""
import boto3
from datetime import datetime
import sys
sys.path.append('.')
from api_server import decimal_to_float

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

today = datetime.now().strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression='bet_date = :today',
    ExpressionAttributeValues={':today': today}
)

items = [decimal_to_float(i) for i in response['Items']]

# Find Laughing John
laughing_john = next((i for i in items if i.get('horse') == 'Laughing John'), None)

if laughing_john:
    print('='*80)
    print('LAUGHING JOHN - NEXT BEST ANALYSIS')
    print('='*80)
    
    pick_score = float(laughing_john.get('comprehensive_score', 0))
    pick_course = laughing_john.get('course', '')
    pick_race_time = laughing_john.get('race_time', '')
    
    print(f'\nOur Pick:')
    print(f'  Horse: Laughing John')
    print(f'  Score: {pick_score}')
    print(f'  Course: {pick_course}')
    print(f'  Race time: {pick_race_time}')
    
    # Find other horses in same race
    same_race = [
        i for i in items 
        if i.get('course') == pick_course 
        and i.get('race_time') == pick_race_time
        and i.get('horse') != 'Laughing John'
        and i.get('comprehensive_score')
    ]
    
    print(f'\n\nAll horses in this race:')
    print('-'*80)
    
    all_horses = [(laughing_john.get('horse'), pick_score)] + \
                 [(h.get('horse'), float(h.get('comprehensive_score', 0))) for h in same_race]
    all_horses.sort(key=lambda x: x[1], reverse=True)
    
    for i, (horse, score) in enumerate(all_horses, 1):
        marker = '👑 ' if horse == 'Laughing John' else '   '
        print(f'{marker}{i}. {horse:30} Score: {score}')
    
    if same_race:
        scores = [float(h.get('comprehensive_score', 0)) for h in same_race]
        scores.sort(reverse=True)
        
        next_best = scores[0]
        gap = pick_score - next_best
        
        print(f'\n\nUI Display:')
        print('='*80)
        print(f'Main score badge: "✓ Scored ({pick_score:.0f}/100)"')
        print(f'Next best badge:  "Next best: {next_best:.0f} (+{gap:.0f} gap)"')
        
        if gap > 10:
            color = '🟢 GREEN (Dominant - large advantage)'
        elif gap > 5:
            color = '🟡 YELLOW (Moderate advantage)'
        else:
            color = '🔴 RED (Tight competition)'
        
        print(f'Badge color:      {color}')
        
        print(f'\n\nInterpretation:')
        print('-'*80)
        if gap > 10:
            print('✅ STRONG PICK - Significantly better than next best competitor')
            print('   This horse is the clear favorite by our analysis')
        elif gap > 5:
            print('✅ GOOD PICK - Noticeable advantage over competition')
            print('   This horse has an edge but isn\'t dominant')
        else:
            print('⚠️  COMPETITIVE RACE - Close scores with next best')
            print('   Multiple horses are rated similarly - higher risk')
else:
    print('Laughing John not found in today\'s picks')

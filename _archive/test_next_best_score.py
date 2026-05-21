"""
Test that next_best_score is calculated correctly
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
ui_picks = [i for i in items if i.get('show_in_ui')]

print(f'Found {len(ui_picks)} UI picks today')
print()

if ui_picks:
    # Take one pick and calculate next_best_score
    pick = ui_picks[0]
    
    print(f'Testing with: {pick.get("horse")}')
    print(f'Score: {pick.get("comprehensive_score")}')
    print(f'Course: {pick.get("course")}')
    print(f'Race time: {pick.get("race_time")}')
    print()
    
    # Find other horses in same race
    pick_course = pick.get('course', '')
    pick_race_time = pick.get('race_time', '')
    pick_score = float(pick.get('comprehensive_score', 0))
    
    same_race = [
        i for i in items 
        if i.get('course') == pick_course 
        and i.get('race_time') == pick_race_time
        and i.get('horse') != pick.get('horse')
        and i.get('comprehensive_score')
    ]
    
    print(f'Other horses in same race: {len(same_race)}')
    
    if same_race:
        scores = [float(h.get('comprehensive_score', 0)) for h in same_race]
        scores.sort(reverse=True)
        
        print(f'\nScores in this race:')
        print(f'  Our pick ({pick.get("horse")}): {pick_score}')
        for i, s in enumerate(scores[:3], 1):
            print(f'  {i}. Next: {s}')
        
        next_best = scores[0]
        gap = pick_score - next_best
        
        print(f'\nCalculated values:')
        print(f'  next_best_score: {next_best}')
        print(f'  score_gap: {gap}')
        print(f'  Badge color: {"Green" if gap > 10 else "Yellow" if gap > 5 else "Red"}')
    else:
        print('No other horses in this race (unusual!)')
else:
    print('No UI picks found for today')

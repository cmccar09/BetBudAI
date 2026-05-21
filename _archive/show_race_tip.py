import boto3
import sys

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

course = sys.argv[1] if len(sys.argv) > 1 else 'Kempton'
time = sys.argv[2] if len(sys.argv) > 2 else '12:50'

response = table.scan()
items = response.get('Items', [])

race_horses = [item for item in items if course in item.get('course', '') and time in item.get('race_time', '')]

if race_horses:
    sorted_horses = sorted(race_horses, key=lambda x: float(x.get('combined_confidence', 0)), reverse=True)
    
    print(f'\n{time} {course} - Top 5 Horses:')
    print('='*80)
    
    for i, horse in enumerate(sorted_horses[:5], 1):
        score = float(horse.get('combined_confidence', 0))
        name = horse.get('horse', 'Unknown')
        odds = horse.get('odds', 'N/A')
        ui = ' [UI PICK]' if horse.get('show_in_ui') else ''
        print(f'{i}. {score:5.1f}/100  {name:<30} @{odds:<6}{ui}')
    
    top = sorted_horses[0]
    print('\n' + '='*80)
    print(f'TOP TIP: {top.get("horse")} @{top.get("odds")}')
    print(f'Score: {float(top.get("combined_confidence", 0)):.1f}/100 - {top.get("confidence_grade", "N/A")}')
    print('='*80)
    print('\nScoring Breakdown:')
    for factor in ['sweet_spot', 'optimal_odds', 'recent_win', 'total_wins', 'consistency', 'course_bonus', 'database_history', 'going_suitability', 'track_pattern_bonus']:
        if factor in top and int(top.get(factor, 0)) > 0:
            pts = int(top[factor])
            print(f'  {factor:<25}: +{pts} pts')
    print('')
else:
    print(f'No data found for {time} {course}')

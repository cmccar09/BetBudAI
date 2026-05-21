"""
Check all of yesterday's picks with high scores to see what should be recommended
"""
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq(yesterday)
)

items = response.get('Items', [])

print(f'All picks for {yesterday}')
print('=' * 100)

# Group by score ranges
score_85_plus = [i for i in items if float(i.get('comprehensive_score', 0)) >= 85]
score_75_84 = [i for i in items if 75 <= float(i.get('comprehensive_score', 0)) < 85]
score_below_75 = [i for i in items if float(i.get('comprehensive_score', 0)) < 75]

print(f'\nTotal picks: {len(items)}')
print(f'Score 85+: {len(score_85_plus)}')
print(f'Score 75-84: {len(score_75_84)}')
print(f'Score <75: {len(score_below_75)}')

# Check outcomes for 85+ scores
if score_85_plus:
    print(f'\n{"="*100}')
    print(f'SCORE 85+ PICKS (RECOMMENDED THRESHOLD):')
    print('=' * 100)
    
    with_results = [i for i in score_85_plus if i.get('outcome')]
    without_results = [i for i in score_85_plus if not i.get('outcome')]
    
    print(f'\nWith results: {len(with_results)}')
    print(f'Without results: {len(without_results)}')
    
    if with_results:
        wins = [i for i in with_results if i.get('outcome', '').lower() == 'won']
        losses = [i for i in with_results if i.get('outcome', '').lower() == 'lost']
        
        print(f'\n  Wins: {len(wins)}')
        print(f'  Losses: {len(losses)}')
        
        if wins or losses:
            print(f'\n  Results:')
            for pick in sorted(with_results, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True):
                horse = pick.get('horse', 'Unknown')
                course = pick.get('course', 'Unknown')
                score = float(pick.get('comprehensive_score', 0))
                odds = float(pick.get('odds', 0))
                outcome = pick.get('outcome', 'pending')
                show_ui = pick.get('show_in_ui', False)
                
                prefix = '✓' if outcome.lower() == 'won' else '✗'
                ui_marker = '[UI]' if show_ui else '    '
                
                print(f'    {ui_marker} {prefix} {horse:30} @ {course:20} Score: {score:3.0f} Odds: {odds:.2f} - {outcome.upper()}')
    
    if without_results:
        print(f'\n  Picks without results (top 10 by score):')
        for pick in sorted(without_results, key=lambda x: float(x.get('comprehensive_score', 0)), reverse=True)[:10]:
            horse = pick.get('horse', 'Unknown')
            course = pick.get('course', 'Unknown')
            score = float(pick.get('comprehensive_score', 0))
            odds = float(pick.get('odds', 0))
            show_ui = pick.get('show_in_ui', False)
            
            ui_marker = '[UI]' if show_ui else '    '
            print(f'    {ui_marker} {horse:30} @ {course:20} Score: {score:3.0f} Odds: {odds:.2f}')

print('\n' + '=' * 100)

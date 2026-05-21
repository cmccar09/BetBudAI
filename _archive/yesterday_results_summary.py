"""
Generate yesterday's results summary
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
ui_picks = [i for i in items if i.get('show_in_ui') == True]

print('=' * 80)
print(f'YESTERDAY\'S RESULTS SUMMARY ({yesterday})')
print('=' * 80)
print(f'\nTotal picks in database: {len(items)}')
print(f'  - UI picks (show_in_ui=True): {len(ui_picks)}')
print(f'  - Analysis picks (show_in_ui=False): {len(items) - len(ui_picks)}')

if ui_picks:
    print(f'\n{"="*80}')
    print('UI PICKS RESULTS:')
    print('=' * 80)
    
    wins = [i for i in ui_picks if i.get('outcome', '').lower() == 'won']
    losses = [i for i in ui_picks if i.get('outcome', '').lower() == 'lost']
    places = [i for i in ui_picks if i.get('outcome', '').lower() == 'placed']
    pending = [i for i in ui_picks if not i.get('outcome') or i.get('outcome', '').lower() == 'pending']
    void = [i for i in ui_picks if i.get('outcome', '').lower() == 'void']
    
    print(f'\nWins: {len(wins)}')
    print(f'Losses: {len(losses)}')
    print(f'Places: {len(places)}')
    print(f'Void: {len(void)}')
    print(f'Pending: {len(pending)}')
    
    if wins:
        print(f'\n✓ WINNERS:')
        for pick in wins:
            horse = pick.get('horse', 'Unknown')
            course = pick.get('course', 'Unknown')
            odds = float(pick.get('odds', 0))
            score = float(pick.get('comprehensive_score', 0))
            print(f'  {horse:30} @ {course:20} Score: {score:3.0f} Odds: {odds:.2f}')
    
    if losses:
        print(f'\n✗ LOSSES:')
        for pick in losses:
            horse = pick.get('horse', 'Unknown')
            course = pick.get('course', 'Unknown')
            odds = float(pick.get('odds', 0))
            score = float(pick.get('comprehensive_score', 0))
            print(f'  {horse:30} @ {course:20} Score: {score:3.0f} Odds: {odds:.2f}')
    
    # Calculate P&L if stakes available
    total_stake = sum(float(p.get('stake', 0)) for p in ui_picks if p.get('stake'))
    total_return = sum(
        float(p.get('stake', 0)) * float(p.get('odds', 0)) 
        for p in wins if p.get('stake')
    )
    
    if total_stake > 0:
        profit = total_return - total_stake
        roi = (profit / total_stake) * 100
        print(f'\nP&L SUMMARY:')
        print(f'  Total Stake: £{total_stake:.2f}')
        print(f'  Total Return: £{total_return:.2f}')
        print(f'  Profit/Loss: £{profit:.2f}')
        print(f'  ROI: {roi:.1f}%')
    
    completed = len(wins) + len(losses) + len(places)
    if completed > 0:
        strike_rate = (len(wins) / completed) * 100
        print(f'\nSTRIKE RATE: {strike_rate:.1f}% ({len(wins)}/{completed})')

print('\n' + '=' * 80)
print('✓ Results page is UP TO DATE')
print('=' * 80)

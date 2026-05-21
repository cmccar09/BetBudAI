import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-18'}
)

items = response['Items']

print('\n' + '='*80)
print('SYSTEM A (Actual Bets - stake <= £10)')
print('='*80)
system_a = [i for i in items if float(i.get('stake', 0)) <= 10]
print(f'Total picks: {len(system_a)}')

won_a = [i for i in system_a if i.get('outcome') == 'won']
lost_a = [i for i in system_a if i.get('outcome') == 'lost']
pending_a = [i for i in system_a if i.get('outcome') == 'pending']

print(f'Won: {len(won_a)}, Lost: {len(lost_a)}, Pending: {len(pending_a)}')

stake_a = sum(float(i.get('stake', 0)) for i in system_a)
profit_a = sum(float(i.get('profit_loss', 0)) for i in system_a if i.get('outcome') in ['won', 'lost'])
roi_a = (profit_a / stake_a * 100) if stake_a > 0 else 0

print(f'Total stake: £{stake_a:.2f}')
print(f'Profit/Loss: £{profit_a:.2f}')
print(f'ROI: {roi_a:.1f}%')

print(f'\nDetailed Results:')
for pick in sorted(system_a, key=lambda x: x.get('race_time', '')):
    time = pick.get('race_time', '')[:16] if pick.get('race_time') else 'N/A'
    score = pick.get('comprehensive_score', 'N/A')
    outcome = pick.get('outcome', 'pending').upper()
    pl = pick.get('profit_loss', 0)
    horse = pick.get('horse', 'Unknown')
    odds = pick.get('odds', 0)
    course = pick.get('course', 'Unknown')
    print(f'  {outcome:8} {horse:25} @ {odds:<5.2f} ({score}/100) '
          f'{course:15} {time} {pl:+7.2f}')

print('\n' + '='*80)
print('SYSTEM B (Learning Data - stake > £10)')
print('='*80)
system_b = [i for i in items if float(i.get('stake', 0)) > 10]
print(f'Total picks: {len(system_b)}')

won_b = [i for i in system_b if i.get('outcome') == 'won']
lost_b = [i for i in system_b if i.get('outcome') == 'lost']
pending_b = [i for i in system_b if i.get('outcome') == 'pending']

print(f'Won: {len(won_b)}, Lost: {len(lost_b)}, Pending: {len(pending_b)}')

stake_b = sum(float(i.get('stake', 0)) for i in system_b)
profit_b = sum(float(i.get('profit_loss', 0)) for i in system_b if i.get('outcome') in ['won', 'lost'])
roi_b = (profit_b / stake_b * 100) if stake_b > 0 else 0

print(f'Total stake: £{stake_b:.2f}')
print(f'Profit/Loss: £{profit_b:.2f}')
print(f'ROI: {roi_b:.1f}%')

print(f'\nDetailed Results:')
for pick in sorted(system_b, key=lambda x: x.get('race_time', '')):
    time = pick.get('race_time', '')[:16] if pick.get('race_time') else 'N/A'
    outcome = pick.get('outcome', 'pending').upper()
    pl = pick.get('profit_loss', 0)
    is_fallback = pick.get('is_fallback', False)
    conf = pick.get('confidence_grade', 'N/A')
    horse = pick.get('horse', 'Unknown')
    odds = pick.get('odds', 0)
    course = pick.get('course', 'Unknown')
    print(f'  {outcome:8} {horse:25} @ {odds:<5.2f} '
          f'(fallback={is_fallback}) {course:15} {time} {pl:+7.2f}')

print('\n' + '='*80)
print('COMPARISON')
print('='*80)
print(f'System A: {len(won_a)}/{len(system_a)} wins, ROI {roi_a:.1f}%, Profit £{profit_a:.2f}')
print(f'System B: {len(won_b)}/{len(system_b)} wins, ROI {roi_b:.1f}%, Profit £{profit_b:.2f}')
print('='*80)

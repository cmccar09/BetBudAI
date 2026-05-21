import boto3

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

response = table.query(
    KeyConditionExpression='bet_date = :date',
    ExpressionAttributeValues={':date': '2026-02-18'}
)

items = response['Items']

# Filter to only picks with comprehensive_score (actual selections from workflows)
actual_picks = [i for i in items if i.get('comprehensive_score') and float(i.get('comprehensive_score', 0)) >= 60]

print('\n' + '='*80)
print('TODAY\'S ACTUAL PICKS (comprehensive_score >= 60)')
print('='*80)

# System A: stake <= 10
system_a = [p for p in actual_picks if float(p.get('stake', 0)) <= 10]
# System B: stake > 10  
system_b = [p for p in actual_picks if float(p.get('stake', 0)) > 10]

print(f'\n🎯 SYSTEM A (Actual Bets - £5-6 stakes)')
print('-' * 80)
print(f'Total picks: {len(system_a)}')

for pick in sorted(system_a, key=lambda x: x.get('race_time', '')):
    horse = pick.get('horse', 'Unknown')
    odds = pick.get('odds', 0)
    score = pick.get('comprehensive_score', 0)
    course = pick.get('course', 'Unknown')
    time = pick.get('race_time', '')[:16] if pick.get('race_time') else ''
    outcome = pick.get('outcome', 'pending')
    stake = pick.get('stake', 0)
    pl = pick.get('profit_loss', 0)
    
    status = '✅ WON' if outcome == 'won' else ('❌ LOST' if outcome == 'lost' else '⏳ PENDING')
    
    print(f'{status:12} {horse:25} @ {odds:5.2f} ({int(score)}/100) - {course:15} {time[11:16]} - £{stake} {pl:+.2f}')

won_a = len([p for p in system_a if p.get('outcome') == 'won'])
lost_a = len([p for p in system_a if p.get('outcome') == 'lost'])
pending_a = len([p for p in system_a if p.get('outcome') == 'pending'])
stake_a = sum(float(p.get('stake', 0)) for p in system_a)
profit_a = sum(float(p.get('profit_loss', 0)) for p in system_a if p.get('outcome') in ['won', 'lost'])

print(f'\n📊 System A Summary:')
print(f'   Results: {won_a} wins, {lost_a} losses, {pending_a} pending')
print(f'   Stake: £{stake_a:.2f}, Profit: £{profit_a:.2f}, ROI: {(profit_a/stake_a*100) if stake_a > 0 else 0:.1f}%')

print(f'\n\n📚 SYSTEM B (Learning Data - £12-30 stakes)')
print('-' * 80)
print(f'Total picks: {len(system_b)}')

for pick in sorted(system_b, key=lambda x: x.get('race_time', '')):
    horse = pick.get('horse', 'Unknown')
    odds = pick.get('odds', 0)
    score = pick.get('comprehensive_score', 0)
    course = pick.get('course', 'Unknown')
    time = pick.get('race_time', '')[:16] if pick.get('race_time') else ''
    outcome = pick.get('outcome', 'pending')
    stake = pick.get('stake', 0)
    pl = pick.get('profit_loss', 0)
    is_fallback = pick.get('is_fallback', False)
    
    status = '✅ WON' if outcome == 'won' else ('❌ LOST' if outcome == 'lost' else '⏳ PENDING')
    fallback_mark = ' [FALLBACK]' if is_fallback else ''
    
    print(f'{status:12} {horse:25} @ {odds:5.2f} ({int(score)}/100){fallback_mark} - {course:15} {time[11:16]} - £{stake} {pl:+.2f}')

won_b = len([p for p in system_b if p.get('outcome') == 'won'])
lost_b = len([p for p in system_b if p.get('outcome') == 'lost'])
pending_b = len([p for p in system_b if p.get('outcome') == 'pending'])
stake_b = sum(float(p.get('stake', 0)) for p in system_b)
profit_b = sum(float(p.get('profit_loss', 0)) for p in system_b if p.get('outcome') in ['won', 'lost'])

print(f'\n📊 System B Summary:')
print(f'   Results: {won_b} wins, {lost_b} losses, {pending_b} pending')
print(f'   Stake: £{stake_b:.2f}, Profit: £{profit_b:.2f}, ROI: {(profit_b/stake_b*100) if stake_b > 0 else 0:.1f}%')

print('\n' + '='*80)
print('OVERALL COMPARISON')
print('='*80)
print(f'System A (Actual):  {won_a}/{len(system_a)} wins ({(won_a/len(system_a)*100) if len(system_a) > 0 else 0:.0f}%), ROI {(profit_a/stake_a*100) if stake_a > 0 else 0:+.1f}%')
print(f'System B (Learning): {won_b}/{len(system_b)} wins ({(won_b/len(system_b)*100) if len(system_b) > 0 else 0:.0f}%), ROI {(profit_b/stake_b*100) if stake_b > 0 else 0:+.1f}%')
print('='*80)

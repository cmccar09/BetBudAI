import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

resp = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-04-07'),
    FilterExpression='show_in_ui = :t',
    ExpressionAttributeValues={':t': True}
)
items = resp['Items']
items.sort(key=lambda x: int(float(str(x.get('pick_rank', 99)))))

print(f'Total UI picks today (2026-04-07): {len(items)}')
print('=' * 90)

for p in items:
    score   = float(p.get('comprehensive_score', 0))
    odds    = float(p.get('odds', 0))
    ev      = float(p.get('expected_value', -99))
    kf      = float(p.get('kelly_fraction', 0))
    wp      = p.get('win_probability', '?')
    stake   = p.get('stake', '?')
    outcome = p.get('outcome', 'pending')
    profit  = p.get('profit', '?')
    sp      = p.get('sp_odds', '?')
    clv     = p.get('clv_delta', '?')
    bd      = p.get('score_breakdown', {})
    rank    = p.get('pick_rank', '?')
    icon    = '✅' if outcome == 'win' else '❌' if outcome == 'loss' else '🔶' if outcome == 'placed' else '⏳'

    print(f"{icon} #{rank}  {p['horse']:<30}  @{odds:5.2f}  Score:{score:4.0f}  EV:{ev:+.3f}  WinProb:{wp}%  Stake:{stake}u")
    print(f"     Venue: {p.get('course',''):<18}  Race: {p.get('race_time','')[:16]}  Mkt: {p.get('market_name','')}")
    print(f"     Outcome:{outcome:<10}  SP:{str(sp):<8}  Profit:{str(profit):<8}  CLV:{clv}  Kelly:{kf:.4f}")
    key_bd = {k: round(float(str(v) or 0), 1) for k, v in bd.items() if float(str(v) or 0) != 0}
    print(f"     Breakdown: {key_bd}")
    reasons = p.get('selection_reasons', [])
    for r in reasons[:4]:
        print(f"       · {r}")
    print()

print('=' * 90)
# Summary
wins   = sum(1 for p in items if p.get('outcome') == 'win')
losses = sum(1 for p in items if p.get('outcome') == 'loss')
placed = sum(1 for p in items if p.get('outcome') == 'placed')
pending= sum(1 for p in items if p.get('outcome') not in ('win','loss','placed'))
total_profit = sum(float(str(p.get('profit', 0) or 0)) for p in items)
print(f"Results: {wins}W / {placed}P / {losses}L / {pending} pending  |  Total P&L: {total_profit:+.2f} units")
avg_ev = sum(float(p.get('expected_value', 0)) for p in items) / len(items) if items else 0
print(f"Avg EV across picks: {avg_ev:+.3f}")

# Also show all learning picks count
resp2 = table.query(
    KeyConditionExpression=Key('bet_date').eq('2026-04-07')
)
total_scored = len(resp2['Items'])
print(f"\nTotal horses scored today: {total_scored}  |  UI picks: {len(items)}")

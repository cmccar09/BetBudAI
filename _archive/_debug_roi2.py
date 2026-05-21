import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Attr

def d2f(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: d2f(v) for k, v in obj.items()}
    if isinstance(obj, list): return [d2f(i) for i in obj]
    return obj

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

all_items = []
scan_kwargs = {'FilterExpression': Attr('bet_date').gte('2026-03-22')}
while True:
    response = table.scan(**scan_kwargs)
    all_items.extend(response.get('Items', []))
    if 'LastEvaluatedKey' not in response:
        break
    scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

picks = [d2f(i) for i in all_items]
ui_picks = [p for p in picks
            if p.get('show_in_ui') is True
            and not p.get('is_learning_pick', False)
            and p.get('course') and p.get('horse')]

# Dedup by (course, race_time) — keep most recently dated record
seen = {}
for p in ui_picks:
    k = (p.get('course',''), p.get('race_time',''))
    if k not in seen or p.get('bet_date','') > seen[k].get('bet_date',''):
        seen[k] = p
unique = sorted(seen.values(), key=lambda p: p.get('race_time',''))

print(f"Unique races after dedup (course+race_time): {len(unique)}")
print()

UNIT = 1.0
total_stake = total_return = 0.0
wins = places = losses = pending = 0

for p in unique:
    outcome = (p.get('outcome') or '').lower()
    odds    = float(p.get('odds', 0))
    ef      = float(p.get('ew_fraction') or 0.25)
    if outcome == 'win':
        wins += 1; total_stake += UNIT; total_return += UNIT * odds
    elif outcome == 'placed':
        places += 1; total_stake += UNIT
        total_return += (UNIT/2) * (1 + (odds-1) * ef)
    elif outcome == 'loss':
        losses += 1; total_stake += UNIT
    else:
        pending += 1
    print(f"  {p.get('bet_date')} {str(p.get('race_time',''))[:16]:16s} {p.get('course',''):20s} {p.get('horse',''):25s} @{odds:.2f} → {outcome or 'pending'}")

profit = total_return - total_stake
roi = round((profit / total_stake * 100) if total_stake > 0 else 0, 1)

print()
print(f"Wins: {wins}  Places: {places}  Losses: {losses}  Pending: {pending}")
print(f"Total stake (units): {total_stake:.0f}  Return: {total_return:.2f}  Profit: {profit:.2f}")
print(f"Cumulative ROI = {roi}%")

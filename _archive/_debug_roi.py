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

print(f"Total items scanned: {len(picks)}")
print(f"UI picks (show_in_ui=True, not learning): {len(ui_picks)}")

# Dedup per race per day
seen = {}
for p in ui_picks:
    k = (p.get('bet_date',''), p.get('course',''), p.get('race_time',''))
    if k not in seen or float(p.get('comprehensive_score',0)) > float(seen[k].get('comprehensive_score',0)):
        seen[k] = p
picks = list(seen.values())
picks.sort(key=lambda p: (p.get('bet_date',''), p.get('race_time','')))
print(f"After dedup: {len(picks)}")
print()

total_stake = total_return = 0.0
wins = places = losses = pending = 0
for p in picks:
    outcome = (p.get('outcome') or '').lower()
    stake = float(p.get('stake', 0))
    odds  = float(p.get('odds', 0))
    print(f"  {p.get('bet_date')} {str(p.get('race_time',''))[:16]:16s} {p.get('course',''):20s} {p.get('horse',''):25s} odds={odds:.2f} stake={stake:.2f} outcome={outcome or 'pending'}")
    if outcome == 'win':
        wins += 1; total_stake += stake; total_return += stake * odds
    elif outcome == 'placed':
        places += 1; total_stake += stake
        ef = float(p.get('ew_fraction', 0.2))
        total_return += (stake/2) * (1 + (odds-1) * ef)
    elif outcome == 'loss':
        losses += 1; total_stake += stake
    else:
        pending += 1

profit = total_return - total_stake
roi = round((profit / total_stake * 100) if total_stake > 0 else 0, 1)
settled = wins + places + losses
print()
print(f"Wins={wins}  Places={places}  Losses={losses}  Pending={pending}  Settled={settled}")
print(f"Total stake={total_stake:.2f}  Return={total_return:.2f}  Profit={profit:.2f}")
print(f"ROI = {roi}%")

import boto3, json
from boto3.dynamodb.conditions import Attr
from decimal import Decimal

# Simulate exactly what the lambda does
ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

CUMULATIVE_ROI_START = '2026-03-22'

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    return obj

all_items = []
scan_kwargs = {'FilterExpression': Attr('bet_date').gte(CUMULATIVE_ROI_START)}
while True:
    resp = table.scan(**scan_kwargs)
    all_items.extend(resp.get('Items', []))
    if 'LastEvaluatedKey' not in resp:
        break
    scan_kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

print(f'Raw items scanned: {len(all_items)}')

picks = [decimal_to_float(i) for i in all_items]
picks = [
    p for p in picks
    if p.get('course') and p.get('course') != 'Unknown'
    and p.get('horse') and p.get('horse') != 'Unknown'
    and p.get('show_in_ui') is True
    and not p.get('is_learning_pick', False)
]
print(f'After show_in_ui filter: {len(picks)}')
print('\nAll UI picks:')
for p in sorted(picks, key=lambda x: x.get('race_time', '')):
    print(f"  {p.get('bet_date')}  {p.get('horse','?'):30}  outcome={p.get('outcome','?'):8}  rt={str(p.get('race_time',''))[:16]}  score={p.get('comprehensive_score','?')}")

# Check for Jimmy/Fine across ALL scanned items, show_in_ui regardless
print('\nAll items for Jimmy Speaking / Fine Interview (any bet_date, any show_in_ui):')
for i in all_items:
    h = (i.get('horse') or '')
    if h in ('Jimmy Speaking', 'Fine Interview'):
        ui = i.get('show_in_ui')
        print(f"  bet_date={i.get('bet_date')}  horse={h}  show_in_ui={ui!r}  outcome={i.get('outcome')}  score={i.get('comprehensive_score')}")

# Dedup
seen = {}
for p in picks:
    k = (p.get('course', ''), p.get('race_time', ''))
    if k not in seen or p.get('bet_date', '') > seen[k].get('bet_date', ''):
        seen[k] = p
picks = list(seen.values())
print(f'After dedup: {len(picks)}')

# Normalise
for p in picks:
    oc = (p.get('outcome') or '').lower()
    if oc in ('won',):    p['outcome'] = 'win'
    elif oc in ('lost',): p['outcome'] = 'loss'

# Count
UNIT = 1.0
wins = places = losses = pending = 0
for p in picks:
    outcome = (p.get('outcome') or '').lower()
    if outcome == 'win':    wins += 1
    elif outcome == 'placed': places += 1
    elif outcome == 'loss':  losses += 1
    else:                    pending += 1

print(f'\nFinal: {wins}W {places}P {losses}L {pending} pending')

# By-day
by_day = {}
for p in sorted(picks, key=lambda x: x.get('race_time', '') or x.get('bet_date', '')):
    outcome = (p.get('outcome') or '').lower()
    if outcome not in ('win', 'placed', 'loss'):
        continue
    dn = ((p.get('race_time') or '')[:10] or p.get('bet_date') or '')
    if dn not in by_day:
        by_day[dn] = {'date': dn, 'wins': 0, 'places': 0, 'losses': 0}
    if outcome == 'win':    by_day[dn]['wins'] += 1
    elif outcome == 'placed': by_day[dn]['places'] += 1
    else:                  by_day[dn]['losses'] += 1

print('\nBy day:')
for dn in sorted(by_day.keys()):
    d = by_day[dn]
    print(f"  {dn}  {d['wins']}W {d['places']}P {d['losses']}L")

"""
Quick summary of yesterday's (16-Mar-2026) results vs our picks
"""
import boto3

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

items = []
kwargs = {'FilterExpression': 'bet_date = :d', 'ExpressionAttributeValues': {':d': '2026-03-16'}}
while True:
    r = table.scan(**kwargs)
    items.extend(r['Items'])
    if 'LastEvaluatedKey' not in r:
        break
    kwargs['ExclusiveStartKey'] = r['LastEvaluatedKey']

# Group by race
races = {}
for i in items:
    t = i.get('race_time') or ''
    key = f"{i.get('course','?')} {t}"
    races.setdefault(key, []).append(i)

print('='*65)
print('RESULTS SUMMARY — 16 MARCH 2026')
print('='*65)
print(f'Total horses in DynamoDB : {len(items)}')
print(f'Total races              : {len(races)}')
print()

# Our top picks (score >= 90)
print('OUR TOP PICKS:')
print('-'*65)
top_picks = sorted(items, key=lambda x: -float(x.get('comprehensive_score', 0)))[:5]
for i in top_picks:
    sc   = float(i.get('comprehensive_score', 0))
    if sc < 90:
        break
    pos  = i.get('finish_position', '?')
    settled = i.get('result_settled', False)
    won  = i.get('result_won', False)
    winner = i.get('result_winner_name', '?')
    odds = float(i.get('odds', 0))
    course = i.get('course', '?')

    if settled:
        if won:
            tag = '✓ WIN'
        elif str(pos) == '2':
            tag = '2nd (near miss)'
        elif str(pos) == '3':
            tag = '3rd'
        else:
            tag = f'pos={pos}'
        result_str = f'{tag}  (winner: {winner})'
    else:
        result_str = 'RESULT NOT RECORDED YET'

    print(f"  {i['horse']:30} score={sc:.0f}  odds={odds:.2f}  {course}")
    print(f"    -> {result_str}")
print()

# All settled races
print('ALL SETTLED RACES:')
print('-'*65)
correct = 0
total_settled = 0

for race_key in sorted(races.keys()):
    race_horses = races[race_key]
    if not any(i.get('result_settled') for i in race_horses):
        continue
    total_settled += 1

    winner_item = next((i for i in race_horses if i.get('result_won')), None)
    winner_name  = winner_item['horse'] if winner_item else 'Unknown'
    winner_score = float(winner_item.get('comprehensive_score', 0)) if winner_item else 0
    winner_odds  = float(winner_item.get('odds', 0)) if winner_item else 0

    our_top = max(race_horses, key=lambda x: float(x.get('comprehensive_score', 0)))
    our_score = float(our_top.get('comprehensive_score', 0))
    our_pos   = our_top.get('finish_position', '?')

    if our_top['horse'] == winner_name:
        correct += 1
        flag = '[CORRECT]'
    else:
        flag = '[WRONG  ]'

    print(f"  {flag} {race_key}")
    print(f"    Winner : {winner_name:30} score={winner_score:.0f}  odds={winner_odds:.2f}")
    if our_top['horse'] != winner_name:
        print(f"    Our top: {our_top['horse']:30} score={our_score:.0f}  pos={our_pos}")

print()
if total_settled > 0:
    print(f'STRIKE RATE: {correct}/{total_settled} races = {correct/total_settled*100:.0f}%')
    print()

# Races NOT yet settled
pending = [k for k, v in races.items() if not any(i.get('result_settled') for i in v)]
if pending:
    print(f'RACES WITHOUT RESULTS RECORDED ({len(pending)}):')
    for p in sorted(pending):
        race_h = races[p]
        our_top = max(race_h, key=lambda x: float(x.get('comprehensive_score', 0)))
        top_sc  = float(our_top.get('comprehensive_score', 0))
        print(f'  {p:35}  top pick: {our_top["horse"]} (score={top_sc:.0f})')

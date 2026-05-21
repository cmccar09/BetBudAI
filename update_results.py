"""
Manual result updater – matches provided race results against today's DynamoDB picks
and updates result / course / profit_loss fields.
"""
import boto3
from boto3.dynamodb.conditions import Key
from decimal import Decimal

db    = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

# All results provided by the user today
RESULTS = {
    'Al Qareem':      {'result': 'WIN', 'course': 'Musselburgh', 'odds_frac': '5/4',  'decimal': Decimal('2.25')},
    'Team Player':    {'result': 'WIN', 'course': 'Musselburgh', 'odds_frac': '11/1', 'decimal': Decimal('12.0')},
    'Moyganny Phil':  {'result': 'WIN', 'course': 'Carlisle',    'odds_frac': '7/4',  'decimal': Decimal('2.875')},
    'Alliteration':   {'result': 'WIN', 'course': 'Fairyhouse',  'odds_frac': '9/2',  'decimal': Decimal('5.5')},
}

resp      = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-04'))
all_items = resp.get('Items', [])
ui_picks  = [x for x in all_items if x.get('show_in_ui')]

print(f'Total UI picks today: {len(ui_picks)}\n')
for p in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
    horse   = (p.get('horse') or '').strip()
    matched = next((k for k in RESULTS if k.lower() in horse.lower() or horse.lower() in k.lower()), None)
    tag     = f'MATCH: {matched}' if matched else 'no match'
    print(f"  {str(p.get('race_time','?'))[:22]:22} | {horse:30} | course={str(p.get('course','?')):15} | result={str(p.get('result','?')):10} | {tag}")

print()
updates = []
for p in ui_picks:
    horse   = (p.get('horse') or '').strip()
    matched = next((k for k in RESULTS if k.lower() in horse.lower() or horse.lower() in k.lower()), None)
    if matched:
        r     = RESULTS[matched]
        stake = float(p.get('stake') or 2)
        dec   = float(r['decimal'])
        if r['result'] == 'WIN':
            profit = round(stake * (dec - 1), 2)
        elif r['result'] == 'PLACED':
            profit = round(stake * ((dec - 1) / 4), 2)
        else:
            profit = -stake
        updates.append((p['bet_date'], p['bet_id'], horse, r, profit))

print(f'Updates to apply: {len(updates)}')
for bd, bid, horse, r, profit in updates:
    print(f"  {horse}: {r['result']} @ {r['odds_frac']} -> course={r['course']}, profit=+£{profit:.2f}")

confirm = input('\nApply updates? (y/n): ').strip().lower()
if confirm != 'y':
    print('Aborted.')
else:
    for bd, bid, horse, r, profit in updates:
        table.update_item(
            Key={'bet_date': bd, 'bet_id': bid},
            UpdateExpression=(
                'SET #res = :res, outcome = :oc, result_emoji = :re, '
                'course = :c, profit_loss = :pl'
            ),
            ExpressionAttributeNames={'#res': 'result'},
            ExpressionAttributeValues={
                ':res': r['result'],
                ':oc':  r['result'],
                ':re':  r['result'],
                ':c':   r['course'],
                ':pl':  Decimal(str(profit)),
            }
        )
        print(f"  ✓ Updated {horse} -> {r['result']} @ {r['odds_frac']} (course: {r['course']}, profit: +£{profit:.2f})")
    print('\nDone. Refresh the results page.')

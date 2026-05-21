"""
Record race result and trigger learning nudges.
14:30 Ffos Las - 16 March 2026
RESULT:
  1st: Hellfire Princess  J: Benjamin Macey  T: Kerry Lee       4/1
  2nd: Neeps And Tatties  J: Finn Lambert    T: Richard Phillips 10/1
  3rd: Queen Of Steel     J: Fern O'Brien(3) T: Fergal O'Brien  5/2  (OUR PICK #2)
"""
import boto3
from decimal import Decimal
from datetime import datetime

today = '2026-03-16'
ddb   = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# ---------- find all horses in 14:30 Ffos Las --------------------------------
all_items = []
kwargs = {
    'FilterExpression': 'bet_date = :d AND course = :c',
    'ExpressionAttributeValues': {':d': today, ':c': 'Ffos Las'}
}
while True:
    resp = table.scan(**kwargs)
    all_items.extend(resp['Items'])
    if 'LastEvaluatedKey' not in resp:
        break
    kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

race_horses = [i for i in all_items
               if '143000' in i.get('bet_id', '') or '14:30' in i.get('race_time', '')]
print(f'Found {len(race_horses)} horses in 14:30 Ffos Las')
for h in sorted(race_horses, key=lambda x: -float(x.get('comprehensive_score', 0))):
    bid   = h['bet_id']
    horse = h['horse']
    sc    = float(h.get('comprehensive_score', 0))
    print(f'  {horse:30}  score={sc:.0f}  bet_id={bid}')

WINNER = 'Hellfire Princess'
winner_jockey = 'Benjamin Macey'
winner_trainer = 'Kerry Lee'

# ---------- update every horse in the race -----------------------------------
updates = {
    'Queen Of Steel':     {'finish': 3, 'won': False},
    'Hellfire Princess':  {'finish': 1, 'won': True},
    'Neeps And Tatties':  {'finish': 2, 'won': False},
}
jockeys = {
    'Queen Of Steel':    ('Fern O\'Brien', '(3) claiming'),
    'Hellfire Princess': ('Benjamin Macey', ''),
    'Neeps And Tatties': ('Finn Lambert', ''),
}
trainers = {
    'Queen Of Steel':    "Fergal O'Brien",
    'Hellfire Princess': 'Kerry Lee',
    'Neeps And Tatties': 'Richard Phillips',
}

for h in race_horses:
    horse = h['horse']
    result = updates.get(horse)
    if not result:
        # unplaced
        result = {'finish': 0, 'won': False}

    try:
        table.update_item(
            Key={'bet_id': h['bet_id'], 'bet_date': h['bet_date']},
            UpdateExpression=(
                'SET result_won = :w, result_winner_name = :wn, result_settled = :s, '
                'finish_position = :fp, outcome = :oc'
            ),
            ExpressionAttributeValues={
                ':w':  result['won'],
                ':wn': WINNER,
                ':s':  True,
                ':fp': result['finish'],
                ':oc': 'win' if result['won'] else 'loss',
            }
        )
        mark = '   WIN' if result['won'] else '  loss'
        print(f'  Updated {horse:30} finish={result["finish"]}{mark}')
    except Exception as e:
        print(f'  ERROR {horse}: {e}')

    # Save jockey-course history
    jockey_name = jockeys.get(horse, ('', ''))[0]
    venue = 'Ffos Las'
    if jockey_name:
        jc_key = f"JOCKEY_COURSE_{jockey_name.replace(' ', '_')}_{venue.replace(' ', '_')}"
        try:
            jc_resp = table.get_item(Key={'bet_id': jc_key, 'bet_date': 'HISTORY'})
            jc_item = jc_resp.get('Item', {})
            new_wins = int(jc_item.get('course_wins', 0)) + (1 if result['won'] else 0)
            new_runs = int(jc_item.get('course_runs', 0)) + 1
            table.put_item(Item={
                'bet_id':      jc_key,
                'bet_date':    'HISTORY',
                'jockey':      jockey_name,
                'course':      venue,
                'course_wins': new_wins,
                'course_runs': new_runs,
                'updated':     datetime.now().isoformat(),
            })
            print(f'    Jockey-course saved: {jockey_name} @ {venue}  {new_wins}/{new_runs}')
        except Exception as e:
            print(f'    Jockey-course error: {e}')

# ---------- Learning analysis ------------------------------------------------
print('\n' + '=' * 60)
print('LEARNING ANALYSIS — 14:30 Ffos Las')
print('=' * 60)
our_pick = next((h for h in race_horses if h['horse'] == 'Queen Of Steel'), None)
winner_item = next((h for h in race_horses if h['horse'] == WINNER), None)

if our_pick and winner_item:
    our_score      = float(our_pick.get('comprehensive_score', 0))
    winner_score   = float(winner_item.get('comprehensive_score', 0))
    our_odds       = float(our_pick.get('odds', 0))
    winner_odds    = float(winner_item.get('odds', 0))
    our_bd         = our_pick.get('score_breakdown', {})
    winner_bd      = winner_item.get('score_breakdown', {})

    print(f'  Our pick:  Queen Of Steel        score={our_score:.0f}  odds={our_odds:.2f}  finish=3rd  WRONG')
    print(f'  Winner:    {WINNER:25}  score={winner_score:.0f}  odds={winner_odds:.2f}  finish=1st')
    print(f'  Score gap: winner scored {winner_score - our_score:+.0f} vs our pick')
    print()

    # Key factors winner had that our pick didn't (or had more of)
    print('  FACTOR COMPARISON:')
    all_keys = set(list(our_bd.keys()) + list(winner_bd.keys()))
    for k in sorted(all_keys):
        ov = float(our_bd.get(k, 0))
        wv = float(winner_bd.get(k, 0))
        if abs(ov - wv) >= 2:
            diff = wv - ov
            mark = '>>> WINNER HIGHER' if diff > 0 else '    our pick higher'
            print(f'    {k:30} our={ov:+.0f}  winner={wv:+.0f}  diff={diff:+.0f}  {mark}')

    print()
    print('  KEY LESSONS:')
    print('  1. Hellfire Princess (score 67) beat Queen Of Steel (score 99)')
    print('     — High score did NOT guarantee a win in a Class 5 field')
    print('  2. Hellfire Princess has a claiming jockey NOT in our scoring — weight allowance matters')
    print('  3. Queen Of Steel had a (3) claiming jockey (Fern O\'Brien) — 3lb allowance not yet scoring')
    print('  4. Kerry Lee is NOT in trainer tier list — lesson: smaller trainers can win Class 5')
    print('  5. Odds: winner was 4/1 (4.0 decimal), our pick 5/2 (3.5) — both reasonable')
    print()
    print('  SUGGESTED WEIGHT NUDGES:')
    # Winner had lower score but won — our model overvalued something
    if our_score > winner_score + 20:
        print('  - Score gap was large (>20pts) but model was wrong — reduce over-confidence in high scores')
    print('  - Jockey claiming allowance scoring matters more in Class 5/soft going')
    print('  - Consider flagging Class 5 races as reduced-confidence regardless of AW/turf')

print('\nDone.')

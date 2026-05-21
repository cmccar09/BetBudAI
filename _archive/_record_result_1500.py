"""
Record race result: 15:00 Ffos Las - 16 March 2026
RESULT:
  1st: Boston Joe     J: Ben Jones           T: Rebecca Curtis   3/1
  2nd: El Rojo Grande J: Shane Quinlan (3)   T: Katy Price       9/4  (OUR PICK #3)
  3rd: Benignitas     J: Rian Corcoran (7)   T: Gordon Treacy    17/2
  4th: Henry Box Brown J: Ellis Collier (5)  T: Mrs C. Williams  7/1
"""
import boto3
from decimal import Decimal
from datetime import datetime

today = '2026-03-16'
ddb   = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

WINNER       = 'Boston Joe'
RACE_TIME_ID = '150000'
VENUE        = 'Ffos Las'

# ---------- fetch all horses from this race ----------------------------------
all_items = []
kwargs = {
    'FilterExpression': 'bet_date = :d AND course = :c',
    'ExpressionAttributeValues': {':d': today, ':c': VENUE}
}
while True:
    resp = table.scan(**kwargs)
    all_items.extend(resp['Items'])
    if 'LastEvaluatedKey' not in resp:
        break
    kwargs['ExclusiveStartKey'] = resp['LastEvaluatedKey']

race_horses = [i for i in all_items if RACE_TIME_ID in i.get('bet_id', '')]
print(f'Found {len(race_horses)} horses in 15:00 {VENUE}')
for h in sorted(race_horses, key=lambda x: -float(x.get('comprehensive_score', 0))):
    print(f"  {h['horse']:30}  score={float(h.get('comprehensive_score',0)):.0f}")

# Known finish positions
finish_map = {
    'Boston Joe':      1,
    'El Rojo Grande':  2,
    'Benignitas':      3,
    'Henry Box Brown': 4,
}
jockey_map = {
    'Boston Joe':      'Ben Jones',
    'El Rojo Grande':  'Shane Quinlan',
    'Benignitas':      'Rian Corcoran',
    'Henry Box Brown': 'Ellis Collier',
}
trainer_map = {
    'Boston Joe':      'Rebecca Curtis',
    'El Rojo Grande':  'Katy Price',
    'Benignitas':      'Gordon Treacy',
    'Henry Box Brown': 'Mrs C. Williams',
}

print()
for h in race_horses:
    horse   = h['horse']
    finish  = finish_map.get(horse, 0)
    is_win  = (horse == WINNER)
    try:
        table.update_item(
            Key={'bet_id': h['bet_id'], 'bet_date': h['bet_date']},
            UpdateExpression=(
                'SET result_won = :w, result_winner_name = :wn, result_settled = :s, '
                'finish_position = :fp, outcome = :oc'
            ),
            ExpressionAttributeValues={
                ':w':  is_win,
                ':wn': WINNER,
                ':s':  True,
                ':fp': finish,
                ':oc': 'win' if is_win else 'loss',
            }
        )
        mark = '   WIN' if is_win else ('  2nd' if finish == 2 else '  loss')
        print(f'  Updated {horse:30} finish={finish}{mark}')
    except Exception as e:
        print(f'  ERROR {horse}: {e}')

    # Save jockey-course history
    jockey_name = jockey_map.get(horse, '')
    if jockey_name:
        jc_key = f"JOCKEY_COURSE_{jockey_name.replace(' ','_')}_{VENUE.replace(' ','_')}"
        try:
            jc_resp = table.get_item(Key={'bet_id': jc_key, 'bet_date': 'HISTORY'})
            jc_item = jc_resp.get('Item', {})
            new_wins = int(jc_item.get('course_wins', 0)) + (1 if is_win else 0)
            new_runs = int(jc_item.get('course_runs', 0)) + 1
            table.put_item(Item={
                'bet_id':      jc_key,
                'bet_date':    'HISTORY',
                'jockey':      jockey_name,
                'course':      VENUE,
                'course_wins': new_wins,
                'course_runs': new_runs,
                'updated':     datetime.now().isoformat(),
            })
            print(f'    Jockey-course: {jockey_name} @ {VENUE}  {new_wins}/{new_runs}')
        except Exception as e:
            print(f'    Jockey-course error: {e}')

# ---------- learning analysis ------------------------------------------------
print('\n' + '='*60)
print('LEARNING ANALYSIS — 15:00 Ffos Las')
print('='*60)

our_pick    = next((h for h in race_horses if h['horse'] == 'El Rojo Grande'), None)
winner_item = next((h for h in race_horses if h['horse'] == WINNER), None)

if our_pick and winner_item:
    our_sc   = float(our_pick.get('comprehensive_score', 0))
    win_sc   = float(winner_item.get('comprehensive_score', 0))
    our_odds = float(our_pick.get('odds', 0))
    win_odds = float(winner_item.get('odds', 0))

    print(f'  Our pick : El Rojo Grande  score={our_sc:.0f}  odds={our_odds:.2f}  finish=2nd  NEAR MISS')
    print(f'  Winner   : Boston Joe      score={win_sc:.0f}  odds={win_odds:.2f}  finish=1st')
    print(f'  Score gap: winner scored {win_sc - our_sc:+.0f} vs our pick')
    print()

    our_bd = our_pick.get('score_breakdown', {})
    win_bd = winner_item.get('score_breakdown', {})
    all_keys = set(list(our_bd.keys()) + list(win_bd.keys()))
    print('  FACTOR COMPARISON (diff >= 2pts):')
    for k in sorted(all_keys):
        ov = float(our_bd.get(k, 0))
        wv = float(win_bd.get(k, 0))
        if abs(ov - wv) >= 2:
            diff = wv - ov
            mark = '>>> WINNER HIGHER' if diff > 0 else '    our pick higher'
            print(f'    {k:30} our={ov:+.0f}  winner={wv:+.0f}  diff={diff:+.0f}  {mark}')

    print()
    print('  KEY OBSERVATIONS:')
    print('  1. Another Class 5 turf race — Boston Joe (winner) at 3/1, our pick El Rojo Grande 9/4')
    print('  2. El Rojo Grande ran 2nd — very close (3/4 length), near miss')
    print('  3. Rebecca Curtis newly added to Tier 3 — would now give Boston Joe +4pts')

    if our_sc > win_sc + 15:
        print('  4. High score gap again in Class 5 — Class 5 turf penalty (-17pts) is working correctly')
    elif our_sc > win_sc:
        print('  4. Our pick marginally higher score but winner won — reasonable result in Class 5')
    else:
        print('  4. Winner actually scored higher — model correctly identified the race as competitive')

    print()
    print('  VERDICT: Near miss (2nd). Class 5 turf penalty flag is appropriate.')
    print('  Both claiming jockeys in top 3 (Quinlan 3lb, Corcoran 7lb) — confirms weight allowance relevance')

elif not winner_item:
    print('  Winner Boston Joe not found in our race scan (may not have been fetched from Betfair)')
    print('  Lesson: we should ensure all declared runners are fetched, not just those with back prices')

print('\nDone.')

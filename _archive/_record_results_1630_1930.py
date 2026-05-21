"""
Record results for two remaining races from 16 March 2026:
  1. 16:30 Ffos Las (Class 4, Heavy)
  2. 19:30 Wolverhampton (Class 5, Standard AW)
"""
import boto3
from datetime import datetime

TODAY = '2026-03-16'
ddb   = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# ── helpers ──────────────────────────────────────────────────────────────────

def scan_race(time_id, venue):
    items, kwargs = [], {
        'FilterExpression': 'bet_date = :d AND course = :c',
        'ExpressionAttributeValues': {':d': TODAY, ':c': venue}
    }
    while True:
        r = table.scan(**kwargs)
        items.extend(r['Items'])
        if 'LastEvaluatedKey' not in r: break
        kwargs['ExclusiveStartKey'] = r['LastEvaluatedKey']
    return [i for i in items if time_id in i.get('bet_id', '')]


def record_race(race_horses, winner, finish_map, jockey_map, venue, label):
    print(f'\n{"="*60}')
    print(f'RECORDING: {label}')
    print(f'{"="*60}')
    print(f'Found {len(race_horses)} horses in DB')
    for h in sorted(race_horses, key=lambda x: -float(x.get('comprehensive_score', 0))):
        print(f"  {h['horse']:30}  score={float(h.get('comprehensive_score',0)):.0f}")

    for h in race_horses:
        horse   = h['horse']
        finish  = finish_map.get(horse, 0)
        is_win  = (horse == winner)
        try:
            table.update_item(
                Key={'bet_id': h['bet_id'], 'bet_date': h['bet_date']},
                UpdateExpression=(
                    'SET result_won = :w, result_winner_name = :wn, '
                    'result_settled = :s, finish_position = :fp, outcome = :oc'
                ),
                ExpressionAttributeValues={
                    ':w': is_win, ':wn': winner, ':s': True,
                    ':fp': finish, ':oc': 'win' if is_win else 'loss',
                }
            )
            tag = '  WIN' if is_win else f'  pos={finish}'
            print(f'  Updated {horse:30}{tag}')
        except Exception as e:
            print(f'  ERROR {horse}: {e}')

        jockey_name = jockey_map.get(horse, '')
        if jockey_name:
            jc_key = f"JOCKEY_COURSE_{jockey_name.replace(' ','_')}_{venue.replace(' ','_')}"
            try:
                jc_resp = table.get_item(Key={'bet_id': jc_key, 'bet_date': 'HISTORY'})
                jc_item = jc_resp.get('Item', {})
                new_wins = int(jc_item.get('course_wins', 0)) + (1 if is_win else 0)
                new_runs = int(jc_item.get('course_runs', 0)) + 1
                table.put_item(Item={
                    'bet_id': jc_key, 'bet_date': 'HISTORY',
                    'jockey': jockey_name, 'course': venue,
                    'course_wins': new_wins, 'course_runs': new_runs,
                    'updated': datetime.now().isoformat(),
                })
                print(f'    Jockey-course: {jockey_name} @ {venue}  {new_wins}/{new_runs}')
            except Exception as e:
                print(f'    Jockey-course error: {e}')

    # Learning analysis
    print(f'\nLEARNING ANALYSIS — {label}')
    winner_item = next((i for i in race_horses if i['horse'] == winner), None)
    win_sc  = float(winner_item.get('comprehensive_score', 0)) if winner_item else 0
    win_odds = float(winner_item.get('odds', 0)) if winner_item else 0

    our_top = max(race_horses, key=lambda x: float(x.get('comprehensive_score', 0))) if race_horses else None
    if our_top:
        our_sc  = float(our_top.get('comprehensive_score', 0))
        our_pos = our_top.get('finish_position', '?')
        print(f'  Our top  : {our_top["horse"]:30} score={our_sc:.0f}  pos={our_pos}')
        print(f'  Winner   : {winner:30} score={win_sc:.0f}  odds={win_odds:.2f}')
        if not winner_item:
            print('  (Winner was NOT in our DB scan — not fetched from Betfair)')
        else:
            print(f'  Score gap: winner scored {win_sc - our_sc:+.0f} vs our top pick')


# ════════════════════════════════════════════════════════════════════════════
# RACE 1: 16:30 Ffos Las — Class 4, HEAVY  (our pick: El Gavilan, score=100)
# Winner: Jack's Jury 9/1 (Barry John Murphy)
# ════════════════════════════════════════════════════════════════════════════
r1_horses = scan_race('163000', 'Ffos Las')

r1_finish = {
    "Jack's Jury":   1,
    'Up To Trix':    2,
    'Double Click':  3,
    'Jukebox Fury':  4,
    'El Gavilan':    5,
}
r1_jockeys = {
    "Jack's Jury":  'Callum Pritchard',
    'Up To Trix':   'Sean Bowen',
    'Double Click': 'Gavin Sheehan',
    'Jukebox Fury': 'James Bowen',
    'El Gavilan':   'Richard Patrick',
}

record_race(r1_horses, "Jack's Jury", r1_finish, r1_jockeys, 'Ffos Las', '16:30 Ffos Las (Class 4, Heavy)')


# ════════════════════════════════════════════════════════════════════════════
# RACE 2: 19:30 Wolverhampton — Class 5, Standard AW  (our pick: Beauzon 91)
# Winner: Water Of Leith 6/4 (Jim Goldie)
# ════════════════════════════════════════════════════════════════════════════
r2_horses = scan_race('193000', 'Wolverhampton')

r2_finish = {
    'Water Of Leith':    1,
    'Mumayaz':           2,
    'Twilight Madness':  3,
    'Mart':              4,
    'Silky Robin':       5,
    'Beauzon':           6,
}
r2_jockeys = {
    'Water Of Leith':   'Billy Loughnane',
    'Mumayaz':          'Jack Doughty',
    'Twilight Madness': 'Alistair Rawlinson',
    'Mart':             'Luke Morris',
    'Silky Robin':      'Sean Dylan Bowen',
    'Beauzon':          'Charles Bishop',
}

record_race(r2_horses, 'Water Of Leith', r2_finish, r2_jockeys, 'Wolverhampton', '19:30 Wolverhampton (Class 5, AW Standard)')


# ════════════════════════════════════════════════════════════════════════════
# Combined day summary
# ════════════════════════════════════════════════════════════════════════════
print('\n' + '='*60)
print('16-MAR-2026 FULL DAY SUMMARY (after recording all results)')
print('='*60)

picks = [
    ('Ffos Las 14:30', 'Queen Of Steel',  99,  3.60, 3,    'Hellfire Princess (4/1)'),
    ('Ffos Las 15:00', 'El Rojo Grande',  98,  3.35, 2,    'Boston Joe (3/1)'),
    ('Ffos Las 16:00', 'Fortunate Man',  122,  3.30, 'NR', 'NON-RUNNER'),
    ('Ffos Las 16:30', 'El Gavilan',     100,  4.20, 5,    "Jack's Jury (9/1)"),
    ('Wolv 19:30',     'Beauzon',         91,  3.90, 6,    'Water Of Leith (6/4)'),
]

print(f'\n{"Race":<20} {"Pick":<22} {"Sc":>4} {"Odds":>5} {"Pos":>4}  {"Winner / Notes"}')
print('-'*80)
for race, horse, sc, odds, pos, notes in picks:
    tag = '✓ WIN' if pos == 1 else ('NR' if pos == 'NR' else f'{pos}th')
    print(f'{race:<20} {horse:<22} {sc:>4}  {odds:>5.2f}  {tag:>5}  {notes}')

print()
print('KEY LESSONS FROM TODAY:')
print('  1. HEAVY going (16:30): El Gavilan (score 100) finished 5th at 3/1 fav')
print('     - Going changed from Soft forecast → Heavy actual. Model must penalise Heavy more.')
print('     - Jack\'s Jury (9/1) won: outsider, Barry John Murphy (had Karuma Grey too in 16:00)')
print('     - Stable in-form signal: same trainer winning same card')
print('  2. AW Class 5 Standard (19:30): Beauzon finished 6th despite score 91')
print('     - Form 31111111 inflated score hugely via recent_win/consistency bonuses')
print('     - AW Class 5 penalty (-35) was not enough to counteract 8-race win streak')
print('     - Water Of Leith (6/4 fav) won — the market favourite got it right')
print('     - LESSON: AW Class 5 = avoid all, regardless of form — raise penalty to -50pts')
print('  3. Only 2/4 scorable races (NR excluded): 0 wins, 1x 2nd, 1x 3rd, 1x 5th, 1x 6th')
print('  4. HEAVY going needs its own going_suitability penalty category')

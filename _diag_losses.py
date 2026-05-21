"""Diagnose the two losses: why we picked them and why we didn't pick the winners"""
import boto3, json
from decimal import Decimal
from boto3.dynamodb.conditions import Key

class DE(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal): return float(o)
        return super().default(o)

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = ddb.Table('SureBetBets')
resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-14'))
items = resp['Items']
while resp.get('LastEvaluatedKey'):
    resp = tbl.query(KeyConditionExpression=Key('bet_date').eq('2026-04-14'), ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp['Items'])

def f(v):
    try: return float(v)
    except: return 0.0

# Analyse both losing picks
for race_label, search_horse, winner_search in [
    ('RACE 1: Tiger Power (Newmarket 15:10/16:10)', 'tiger power', 'darn hot'),
    ('RACE 2: Profit Street (Lingfield 18:30/19:30)', 'profit street', 'bella bisbee'),
]:
    pick = [i for i in items if search_horse in str(i.get('horse', '')).lower()]
    if not pick:
        print(f'{race_label}: NO RECORD FOUND')
        continue
    p = pick[0]
    rt = str(p.get('race_time', ''))[:16]
    course = p.get('course', '')

    print('=' * 90)
    print(f'{race_label}')
    print('=' * 90)
    print()
    print(f'OUR PICK: {p.get("horse")}')
    print(f'  Score: {f(p.get("comprehensive_score"))}  |  Odds: {p.get("odds")}  |  Grade: {p.get("confidence_level")}')
    print(f'  Created: {str(p.get("created_at",""))[:19]}')
    print()
    print('WHY WE PICKED IT:')
    reasons = p.get('selection_reasons', p.get('reasons', []))
    for r in reasons:
        print(f'  + {r}')
    print()
    
    sb = p.get('score_breakdown', {})
    print('SCORE BREAKDOWN:')
    for k, v in sorted(sb.items(), key=lambda x: f(x[1]), reverse=True):
        val = f(v)
        if val != 0:
            print(f'  {k:30s} = {val:+6.0f}')
    print()

    # Full field from all_horses
    all_h = p.get('all_horses', [])
    if all_h:
        print(f'FULL FIELD ({len(all_h)} runners, sorted by score):')
        for h in sorted(all_h, key=lambda x: f(x.get('score', 0)), reverse=True):
            name = h.get('horse', '?')
            marker = ' <<< OUR PICK' if name.lower() == search_horse else ''
            if winner_search in name.lower():
                marker = ' <<< ACTUAL WINNER'
            print(f'  {name:30s} score={f(h.get("score")):5.0f}  odds={str(h.get("odds","?")):8s}  trainer={h.get("trainer","?")}{marker}')
    print()

    # Find the winner's full record
    winner_records = [i for i in items if winner_search in str(i.get('horse', '')).lower()]
    if winner_records:
        w = winner_records[0]
        print(f'THE WINNER: {w.get("horse")}')
        print(f'  Score: {f(w.get("comprehensive_score"))}  |  Odds: {w.get("odds")}  |  Grade: {w.get("confidence_level")}')
        print()
        print('WINNER REASONS:')
        w_reasons = w.get('selection_reasons', w.get('reasons', []))
        for r in w_reasons:
            print(f'  + {r}')
        print()
        w_sb = w.get('score_breakdown', {})
        print('WINNER SCORE BREAKDOWN:')
        for k, v in sorted(w_sb.items(), key=lambda x: f(x[1]), reverse=True):
            val = f(v)
            if val != 0:
                print(f'  {k:30s} = {val:+6.0f}')
        print()
        
        # Compare key differences
        our_score = f(p.get('comprehensive_score'))
        win_score = f(w.get('comprehensive_score'))
        print(f'SCORE GAP: Our pick {our_score:.0f} vs Winner {win_score:.0f} (gap: {our_score - win_score:+.0f})')
        print()
        
        # Key areas where winner was weaker
        print('KEY FACTOR DIFFERENCES (Our Pick vs Winner):')
        all_keys = set(list(sb.keys()) + list(w_sb.keys()))
        diffs = []
        for k in all_keys:
            ours = f(sb.get(k, 0))
            theirs = f(w_sb.get(k, 0))
            if ours != theirs:
                diffs.append((k, ours, theirs, theirs - ours))
        diffs.sort(key=lambda x: abs(x[3]), reverse=True)
        for k, ours, theirs, diff in diffs[:15]:
            print(f'  {k:30s}  Ours={ours:+5.0f}  Winner={theirs:+5.0f}  Diff={diff:+5.0f}')
    else:
        print(f'NO RECORD FOUND for winner matching "{winner_search}"')
    
    print()
    print()

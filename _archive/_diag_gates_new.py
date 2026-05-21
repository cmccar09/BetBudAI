"""
Simulates complete_daily_analysis.py quality gates with the UPDATED settings
against the Mar 26 and Mar 27 DynamoDB data to verify picks would now be generated.
"""
import boto3
from decimal import Decimal
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

def float_it(o):
    if isinstance(o, Decimal): return float(o)
    if isinstance(o, dict): return {k: float_it(v) for k,v in o.items()}
    if isinstance(o, list): return [float_it(v) for v in o]
    return o

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

MIN_CONFIDENCE = 78

def _passes_quality_gates(horse, score, bd, score_gap):
    ml       = float(bd.get('market_leader', 0))
    tr       = float(bd.get('trainer_reputation', 0))
    cd       = float(bd.get('cd_bonus', 0))
    age      = float(bd.get('age_bonus', 0))
    unexposed = float(bd.get('unexposed_bonus', 0))

    # S2 override check
    if ml == 0 and tr == 0 and cd == 0 and unexposed == 0:
        if score >= 88 and score_gap >= 20:
            pass  # Override — passes
        else:
            return False, 'S2:no_anchor'

    # S1
    if ml == 0:
        if unexposed >= 10:
            min_s1 = 50
        elif tr > 0 or cd > 0:
            min_s1 = 80
        else:
            min_s1 = 85
        if score < min_s1:
            return False, f'S1:<{min_s1}'

    # S3
    if age >= 10 and ml == 0 and tr == 0:
        min_s3 = 50 if unexposed >= 10 else 92
        if score < min_s3:
            return False, f'S3:age<{min_s3}'

    # S4
    if score < 88 and score_gap < 8:
        return False, f'S4:gap={score_gap:.0f}<8'

    return True, 'PASS'


for date in ['2026-03-27', '2026-03-26']:
    resp = table.query(KeyConditionExpression=Key('bet_date').eq(date))
    items = [float_it(x) for x in resp['Items']]
    non_config = [x for x in items if x.get('bet_id') not in ('SYSTEM_WEIGHTS',)]
    
    # Group by race
    races = {}
    for x in non_config:
        course = x.get('course', '?')
        rt = str(x.get('race_time', ''))[:16]
        key = f"{course} {rt}"
        races.setdefault(key, []).append(x)
    
    qualifying = []
    print(f"\n{'='*80}")
    print(f"SIMULATION for {date} (new gates, MIN_CONFIDENCE={MIN_CONFIDENCE})")
    print(f"{'='*80}")
    
    for race_key in sorted(races.keys()):
        runners = races[race_key]
        if not runners:
            continue
        # Find best scorer
        best = max(runners, key=lambda x: float(x.get('comprehensive_score', 0) or 0))
        score = float(best.get('comprehensive_score', 0) or 0)
        score_gap = float(best.get('score_gap', 0) or 0)
        bd = best.get('score_breakdown', {})
        
        if score < MIN_CONFIDENCE:
            continue
        
        passes, reason = _passes_quality_gates(best.get('horse','?'), score, bd, score_gap)
        ml = float(bd.get('market_leader', 0))
        tr = float(bd.get('trainer_reputation', 0))
        cd_b = float(bd.get('cd_bonus', 0))
        
        if passes:
            qualifying.append({
                'race': race_key,
                'horse': best.get('horse','?'),
                'score': score,
                'gap': score_gap,
                'ml': ml,
                'tr': tr,
                'cd': cd_b,
                'odds': float(best.get('odds', 0) or 0),
            })
        
        print(f"  {race_key:38} {best.get('horse','?')[:22]:22} sc={score:5.0f} gap={score_gap:4.0f} ml={ml:.0f} tr={tr:.0f} -> {'✓ QUALIFIES' if passes else 'FAIL:'+reason}")
    
    print(f"\n  >>> {len(qualifying)} qualifying picks for {date}:")
    qualifying.sort(key=lambda x: x['score'], reverse=True)
    for q in qualifying[:5]:
        print(f"    #{qualifying.index(q)+1} {q['horse']:28} @ {q['odds']:.2f}  score={q['score']:.0f} gap={q['gap']:.0f}")

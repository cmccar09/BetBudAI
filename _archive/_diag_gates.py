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

# Check what scores exist in Mar 26 partition - understand why no picks
for date in ['2026-03-27', '2026-03-26']:
    resp = table.query(KeyConditionExpression=Key('bet_date').eq(date))
    items = [float_it(x) for x in resp['Items']]
    non_config = [x for x in items if x.get('bet_id') not in ('SYSTEM_WEIGHTS',) and x.get('bet_id') != 'CONFIG']
    
    if not non_config:
        print(f"\n{date}: no scoreable records")
        continue
    
    scores = sorted([float(x.get('comprehensive_score', 0) or 0) for x in non_config], reverse=True)
    top10 = scores[:10]
    
    # Group by race
    races = {}
    for x in non_config:
        course = x.get('course','?')
        rt = str(x.get('race_time',''))[:16]
        key = f"{course} {rt}"
        races.setdefault(key, []).append({
            'horse': x.get('horse','?'),
            'score': float(x.get('comprehensive_score',0) or 0),
            'score_gap': float(x.get('score_gap',0) or 0),
            'show_in_ui': x.get('show_in_ui'),
            'bd': x.get('score_breakdown', {}),
        })
    
    print(f"\n{'='*80}")
    print(f"{date}: {len(non_config)} records, top 10 scores: {[round(s,0) for s in top10]}")
    print(f"{'='*80}")
    
    for race_key in sorted(races.keys()):
        runners = sorted(races[race_key], key=lambda x: x['score'], reverse=True)
        best = runners[0]
        gap = best['score_gap']
        bd = best.get('bd', {})
        ml = float(bd.get('market_leader', 0))
        tr = float(bd.get('trainer_reputation', 0))
        cd = float(bd.get('cd_bonus', 0))
        unexp = float(bd.get('unexposed_bonus', 0))
        age = float(bd.get('age_bonus', 0))
        
        # Determine gate failures
        gates = []
        if best['score'] < 85:
            gates.append(f"S0:score={best['score']:.0f}<85")
        if ml == 0 and tr == 0 and cd == 0 and unexp == 0:
            gates.append("S2:no_anchor")
        elif ml == 0:
            mn = 50 if unexp >= 10 else 90
            if best['score'] < mn: gates.append(f"S1:non_mkt<{mn}")
        if age >= 10 and ml == 0 and tr == 0:
            mn = 50 if unexp >= 10 else 92
            if best['score'] < mn: gates.append(f"S3:age_dominated<{mn}")
        if best['score'] < 92 and gap < 8:
            gates.append(f"S4:gap={gap:.1f}<8")
        
        status = "UI" if best['show_in_ui'] else ("PASS" if not gates else "FAIL:" + "|".join(gates))
        print(f"  {race_key:35} best={best['horse'][:22]:22} score={best['score']:5.0f} gap={gap:4.1f} ml={ml:.0f} tr={tr:.0f} cd={cd:.0f} -> {status}")

import boto3, json, re
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from datetime import date

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

dates = ['2026-03-07','2026-03-08','2026-03-14','2026-03-15','2026-03-21','2026-03-22','2026-03-28','2026-03-29']
stats = {}

for d in dates:
    resp = tbl.query(KeyConditionExpression=Key('bet_date').eq(d))
    items = [p for p in resp['Items']
             if p.get('show_in_ui', True) is not False
             and (p.get('bet_type') == 'PICK' or p.get('pick_rank') is not None)]
    # deduplicate by horse+race_time, take highest score version
    seen = {}
    for p in items:
        k = (p.get('horse',''), str(p.get('race_time','')))
        if k not in seen or float(p.get('comprehensive_score', p.get('score', 0))) > float(seen[k].get('comprehensive_score', seen[k].get('score', 0))):
            seen[k] = p
    unique = list(seen.values())

    wins    = [p for p in unique if (p.get('outcome','') or '').lower() in ('win','won') or p.get('result_emoji') == 'WIN']
    losses  = [p for p in unique if (p.get('outcome','') or '').lower() in ('loss','lost') or p.get('result_emoji') == 'LOSS']
    placed  = [p for p in unique if (p.get('outcome','') or '').lower() == 'placed' or p.get('result_emoji') == 'PLACED']
    settled = len(wins) + len(losses) + len(placed)

    field_sizes = []
    for p in unique:
        ra = p.get('result_analysis','') or ''
        m = re.search(r'of (\d+)', ra)
        if m:
            field_sizes.append(int(m.group(1)))

    dow = date.fromisoformat(d).strftime('%A')
    stats[d] = {
        'dow': dow,
        'picks': len(unique),
        'wins': len(wins),
        'losses': len(losses),
        'placed': len(placed),
        'settled': settled,
        'strike': round(len(wins)/settled*100) if settled > 0 else None,
        'avg_field': round(sum(field_sizes)/len(field_sizes),1) if field_sizes else None,
        'max_field': max(field_sizes) if field_sizes else None,
    }

print("\nDAY-OF-WEEK PERFORMANCE BREAKDOWN")
print("="*70)
for d in sorted(stats):
    s = stats[d]
    sr = f"{s['strike']}%" if s['strike'] is not None else "n/a"
    af = str(s['avg_field']) if s['avg_field'] else "n/a"
    mf = str(s['max_field']) if s['max_field'] else "n/a"
    print(f"{d} ({s['dow'][:3]}): picks={s['picks']:2d}  W={s['wins']} P={s['placed']} L={s['losses']}  strike={sr:>4}  avg_field={af}  max_field={mf}")

print()
sat_wins   = sum(v['wins']    for v in stats.values() if v['dow'] == 'Saturday')
sat_settled= sum(v['settled'] for v in stats.values() if v['dow'] == 'Saturday')
sun_wins   = sum(v['wins']    for v in stats.values() if v['dow'] == 'Sunday')
sun_settled= sum(v['settled'] for v in stats.values() if v['dow'] == 'Sunday')
sat_field  = [v['avg_field'] for v in stats.values() if v['dow'] == 'Saturday' and v['avg_field']]
sun_field  = [v['avg_field'] for v in stats.values() if v['dow'] == 'Sunday'   and v['avg_field']]
print(f"SAT total: {sat_wins}W from {sat_settled} settled = {round(sat_wins/sat_settled*100) if sat_settled else 'n/a'}% strike  avg_field={round(sum(sat_field)/len(sat_field),1) if sat_field else 'n/a'}")
print(f"SUN total: {sun_wins}W from {sun_settled} settled = {round(sun_wins/sun_settled*100) if sun_settled else 'n/a'}% strike  avg_field={round(sum(sun_field)/len(sun_field),1) if sun_field else 'n/a'}")

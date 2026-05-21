import boto3, re
from decimal import Decimal
from boto3.dynamodb.conditions import Key

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

for d, label in [('2026-03-21','Sat Mar21'), ('2026-03-22','Sun Mar22'), ('2026-03-28','Sat Mar28'), ('2026-03-29','Sun Mar29')]:
    resp = tbl.query(KeyConditionExpression=Key('bet_date').eq(d))
    items = resp['Items']
    seen = {}
    for p in items:
        k = (p.get('horse',''), str(p.get('race_time','')))
        sc = float(p.get('comprehensive_score', p.get('score', 0)))
        if k not in seen or sc > float(seen[k].get('comprehensive_score', seen[k].get('score', 0))):
            seen[k] = p
    print(f'\n{label}:')
    for p in sorted(seen.values(), key=lambda x: str(x.get('race_time',''))):
        oc = (p.get('outcome') or p.get('result_emoji') or 'PENDING').upper()[:7]
        ra = p.get('result_analysis') or ''
        m = re.search(r'of (\d+)', ra)
        fsize = m.group(1) if m else '?'
        odds = float(p.get('odds', 0))
        wn = p.get('result_winner_name') or ''
        rtime = str(p.get('race_time',''))[11:16]
        course = (p.get('course') or '')[:12]
        horse = (p.get('horse') or '')[:18]
        print(f'  {rtime} {course:<13} {horse:<19} field={fsize:>3} odds={odds:.1f} {oc:<7} winner={wn}')

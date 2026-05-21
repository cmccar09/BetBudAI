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

for i in range(5):
    d = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
    resp = table.query(KeyConditionExpression=Key('bet_date').eq(d))
    items = [float_it(x) for x in resp['Items']]
    ui_picks = [x for x in items if x.get('show_in_ui') == True]
    print(f"\n{d}: {len(items)} total records, {len(ui_picks)} show_in_ui=True")
    if not ui_picks:
        # Check for any non-CONFIG items
        non_config = [x for x in items if x.get('bet_id') != 'SYSTEM_WEIGHTS']
        print(f"  (no UI picks; {len(non_config)} non-config records)")
        for p in non_config[:3]:
            print(f"    bet_id={p.get('bet_id')} show_in_ui={p.get('show_in_ui')} outcome={p.get('outcome')}")
    for p in ui_picks:
        horse = str(p.get('horse','?'))
        course = str(p.get('course','?'))
        outcome = str(p.get('outcome','None'))
        sport = str(p.get('sport','?'))
        mid = str(p.get('market_id','NONE'))
        sel = str(p.get('selection_id','NONE'))
        fin = str(p.get('finish_position','?'))
        winner = str(p.get('winner_horse',''))
        print(f"  {horse} @ {course} [{sport}] outcome={outcome} finish={fin} winner={winner} mkt={mid[:15]} sel={sel}")

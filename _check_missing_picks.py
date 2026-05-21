"""Quick diagnostic: check Le Blue and Vega's Muse picks."""
import boto3
from boto3.dynamodb.conditions import Key

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')

resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-15'))
items = resp.get('Items', [])

ui_picks = [p for p in items if p.get('show_in_ui')]
print(f"Total UI picks today: {len(ui_picks)}\n")
for p in sorted(ui_picks, key=lambda x: str(x.get('race_time', ''))):
    h = p.get('horse', '')
    c = str(p.get('course', p.get('race_course', '')))
    rt = str(p.get('race_time', ''))[:22]
    oc = p.get('outcome', p.get('result_emoji', ''))
    sc = p.get('comprehensive_score', p.get('analysis_score', ''))
    od = p.get('odds', '')
    pr = p.get('profit', '')
    bid = p.get('bet_id', '')
    print(f"  {rt:22} | {h:30} | {c:15} | oc={str(oc):8} | sc={sc} | odds={od} | profit={pr}")

print("\n--- Searching for 'Le Blue' ---")
for p in items:
    nm = str(p.get('horse', '')).lower()
    if 'le blue' in nm or 'leblue' in nm or 'le_blue' in nm:
        bid = p.get('bet_id', '')
        print(f"  horse={p.get('horse')} | show_ui={p.get('show_in_ui')} | course={p.get('course')} | rt={str(p.get('race_time', ''))[:22]} | bid={bid}")

print("\n--- Searching for 'Vega' ---")
for p in items:
    nm = str(p.get('horse', '')).lower()
    if 'vega' in nm:
        bid = p.get('bet_id', '')
        print(f"  horse={p.get('horse')} | show_ui={p.get('show_in_ui')} | course={p.get('course')} | rt={str(p.get('race_time', ''))[:22]} | bid={bid}")

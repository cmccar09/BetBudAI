import boto3
from boto3.dynamodb.conditions import Key

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-04-10'))
items = [it for it in resp.get('Items', []) if it.get('bet_id') != 'WORKFLOW_RUN_LOCK']

# Show keys of first real item
if items:
    print("Keys in first item:", sorted(items[0].keys()))
    print()

# Show show_in_ui=True picks only
ui_picks = [it for it in items if it.get('show_in_ui') == True]
print(f"UI picks today: {len(ui_picks)}")
for it in sorted(ui_picks, key=lambda x: x.get('race_time', '')):
    horse = it.get('horse') or it.get('horse_name') or it.get('selection') or '?'
    print(f"  {it.get('race_time','')}  {it.get('course','')}  {horse}  score={it.get('comprehensive_score')}  odds={it.get('odds')}  outcome={it.get('outcome','pending')}")

# Search for Gold Dancer in any field
print("\nSearching all items for 'Gold':")
for it in items:
    for k, v in it.items():
        if isinstance(v, str) and 'gold' in v.lower():
            horse = it.get('horse') or it.get('horse_name') or it.get('selection') or '?'
            print(f"  Found in field '{k}': {v[:80]}  | horse={horse}")
            break

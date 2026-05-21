import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-02-26'))
items = resp['Items']

# UI picks today
ui_picks = [i for i in items if i.get('show_in_ui') == True]
ui_picks.sort(key=lambda x: (x.get('course',''), str(x.get('race_time',''))))

print(f"Total today: {len(items)}, UI picks: {len(ui_picks)}")
print()
print("UI PICKS:")
for h in ui_picks:
    print(f"  {h.get('course','')} {str(h.get('race_time',''))[11:16]} | {h.get('horse','')} | score={h.get('comprehensive_score','')} | outcome={h.get('outcome','')} | P/L={h.get('profit_loss','')}")

print()
print("CLONMEL 12:49 (all, sorted by score):")
c1249 = [i for i in items if 'clonmel' in i.get('course','').lower() and '12:49' in str(i.get('race_time',''))]
c1249.sort(key=lambda x: float(x.get('comprehensive_score', 0) or 0), reverse=True)
for h in c1249[:5]:
    print(f"  {h.get('horse','')} | score={h.get('comprehensive_score','')} | ui={h.get('show_in_ui','')} | outcome={h.get('outcome','')} | odds={h.get('odds','')}")

print()
# Check going fields
sample = items[0]
going_fields = [k for k in sample.keys() if 'going' in k.lower() or 'ground' in k.lower()]
print("Going-related fields in schema:", going_fields)

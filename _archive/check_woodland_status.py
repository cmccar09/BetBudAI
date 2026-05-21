import boto3
from boto3.dynamodb.conditions import Key
from collections import defaultdict

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-02-26'))
items = resp['Items']

# Check Woodland Park status
wp = [i for i in items if i.get('horse') == 'Woodland Park' and i.get('comprehensive_score')]
print("Woodland Park status:")
for h in wp:
    print(f"  outcome={h.get('outcome','')} | show_in_ui={h.get('show_in_ui','')} | score={h.get('comprehensive_score','')} | race={str(h.get('race_time',''))[11:16]}")

# Current pending UI picks
print("\nCurrent PENDING UI picks (no outcome yet):")
pending_ui = [i for i in items if i.get('show_in_ui') == True and not i.get('outcome')]
pending_ui.sort(key=lambda x: int(x.get('comprehensive_score',0) or 0), reverse=True)
for h in pending_ui:
    rt = str(h.get('race_time',''))[11:16]
    print(f"  {h.get('course','')} {rt} | {h.get('horse','')} | score={h.get('comprehensive_score','')} | odds={h.get('odds','')}")

# Also what does the API /picks/today return (filters future races only)
print(f"\nAll UI picks (including settled):")
all_ui = [i for i in items if i.get('show_in_ui') == True]
all_ui.sort(key=lambda x: (str(x.get('race_time',''))))
for h in all_ui:
    rt = str(h.get('race_time',''))[11:16]
    print(f"  {h.get('course','')} {rt} | {h.get('horse','')} | score={h.get('comprehensive_score','')} | outcome={h.get('outcome','(pending)')}")

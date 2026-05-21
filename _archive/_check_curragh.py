import boto3
from datetime import date
from boto3.dynamodb.conditions import Attr

db = boto3.resource('dynamodb', region_name='eu-west-1')
table = db.Table('SureBetBets')
today = str(date.today())

resp = table.scan(FilterExpression=Attr('bet_date').eq(today))
items = resp['Items']

curragh = [i for i in items if 'curragh' in str(i.get('course', '')).lower()
           and '1355' in str(i.get('race_time', '')).replace(':', '').replace('-', '')]

print(f"Today={today}, total DynamoDB items={len(items)}, Curragh 1355 items={len(curragh)}")
for h in sorted(curragh, key=lambda x: float(x.get('comprehensive_score', 0) or 0), reverse=True):
    print(f"  {str(h.get('horse','?')):25}  score={h.get('comprehensive_score','?')}  show_ui={h.get('show_in_ui')}")

# Also check how many total runners per race
from collections import defaultdict
race_counts = defaultdict(list)
for i in items:
    key = f"{i.get('course','')} {str(i.get('race_time',''))[:16]}"
    race_counts[key].append(i.get('horse', '?'))
print("\nAll races in DynamoDB today:")
for k, horses in sorted(race_counts.items()):
    print(f"  {k}: {len(horses)} horses")

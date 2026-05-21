import boto3
from boto3.dynamodb.conditions import Attr
from collections import Counter

db = boto3.resource('dynamodb', region_name='eu-west-1')
tbl = db.Table('SureBetBets')

resp = tbl.scan(FilterExpression=Attr('show_in_ui').eq(True))
items = resp['Items']
while resp.get('LastEvaluatedKey'):
    resp = tbl.scan(FilterExpression=Attr('show_in_ui').eq(True), ExclusiveStartKey=resp['LastEvaluatedKey'])
    items += resp['Items']

dates = sorted(set(i.get('bet_date','') for i in items if i.get('bet_date','')))
grades = Counter(i.get('confidence_grade','?') for i in items)
total = len(items)
results = [i for i in items if i.get('result') and i.get('result') not in ['PENDING','',None]]
wins = [i for i in results if str(i.get('result','')).upper() in ['WIN','WON','1ST','WINNER']]
print("Total UI picks ever:", total)
print("Date range:", dates[0] if dates else "?", "to", dates[-1] if dates else "?")
print("Days with picks:", len(dates))
print("With results:", len(results))
print("Confirmed wins:", len(wins))
print("Grades:", dict(grades))

# Average score
scores = [float(i.get('comprehensive_score',0) or 0) for i in items]
if scores:
    print("Avg score:", round(sum(scores)/len(scores),1), "Max:", max(scores))

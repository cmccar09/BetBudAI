import boto3
from boto3.dynamodb.conditions import Key

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-03-21'))
items = resp['Items']
while 'LastEvaluatedKey' in resp:
    resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-03-21'), ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp['Items'])

ui = [i for i in items if i.get('show_in_ui') == True]
print(f"Total items for 2026-03-21: {len(items)}, UI picks: {len(ui)}")
print()
for p in sorted(ui, key=lambda x: str(x.get('race_time',''))):
    rt = str(p.get('race_time','?'))[:16]
    course = str(p.get('course','?'))[:15].ljust(15)
    horse  = str(p.get('horse','?'))[:25].ljust(25)
    outcome= str(p.get('outcome','None'))
    score  = p.get('comprehensive_score','?')
    bet_id = str(p.get('bet_id','?'))
    print(f"  {rt} | {course} | {horse} | outcome={outcome:<10} | score={score}")
    print(f"    bet_id: {bet_id}")

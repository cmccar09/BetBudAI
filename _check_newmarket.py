import boto3
from boto3.dynamodb.conditions import Key
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
today = datetime.now().strftime('%Y-%m-%d')

resp = table.query(KeyConditionExpression=Key('bet_date').eq(today))
items = resp.get('Items', [])
while 'LastEvaluatedKey' in resp:
    resp = table.query(KeyConditionExpression=Key('bet_date').eq(today), ExclusiveStartKey=resp['LastEvaluatedKey'])
    items.extend(resp.get('Items', []))

# Find Newmarket races around 16:20 UTC (17:20 BST)
for item in items:
    rt = item.get('race_time', '')
    course = (item.get('course', '') or '').lower()
    if 'newmarket' in course and '16:20' in rt:
        h = item.get('horse', '')
        o = float(item.get('odds', 0))
        ui = item.get('show_in_ui')
        oc = item.get('outcome', 'pending')
        sc = float(item.get('comprehensive_score', 0))
        print(f"  {h:30} odds={o:6.2f}  show_ui={ui}  outcome={oc}  score={sc}")

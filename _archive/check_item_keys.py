import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
resp = table.query(KeyConditionExpression=Key('bet_date').eq('2026-02-26'))
items = resp['Items']

# Find a Clonmel 12:49 item with a score to inspect its keys
clonmel = [i for i in items if 'clonmel' in i.get('course', '').lower()
           and '12:49' in str(i.get('race_time', ''))]

if clonmel:
    sample = max(clonmel, key=lambda x: float(x.get('comprehensive_score', 0) or 0))
    print("Sample item keys:", sorted(sample.keys()))
    for k, v in sorted(sample.items()):
        if k not in ('raw_data',):
            print(f"  {k}: {v}")
else:
    # Print keys from any item
    sample = items[0]
    print("Keys from first item:", sorted(sample.keys()))

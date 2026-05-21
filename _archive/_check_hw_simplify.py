import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')
resp = table.query(KeyConditionExpression='bet_date = :d', ExpressionAttributeValues={':d': '2026-03-31'})

print("=== Halftheworldaway records ===")
for item in resp['Items']:
    if 'Halftheworldaway' in str(item.get('horse', '')):
        print(f"  bet_id     : {item.get('bet_id')}")
        print(f"  race_time  : {item.get('race_time')}")
        print(f"  created_at : {item.get('created_at')}")
        print(f"  show_in_ui : {item.get('show_in_ui')}")
        print(f"  score      : {item.get('comprehensive_score')}")
        print(f"  outcome    : {item.get('outcome')}")
        print(f"  odds       : {item.get('odds')}")
        print(f"  sp_odds    : {item.get('sp_odds')}")
        print(f"  profit     : {item.get('profit')}")
        print()

print("=== Simplify records ===")
for item in resp['Items']:
    if item.get('horse') == 'Simplify' and 'Wolverhampton' in str(item.get('course', '')):
        print(f"  bet_id     : {item.get('bet_id')}")
        print(f"  race_time  : {item.get('race_time')}")
        print(f"  show_in_ui : {item.get('show_in_ui')}")
        print(f"  odds       : {item.get('odds')}")
        print(f"  sp_odds    : {item.get('sp_odds')}")
        print(f"  outcome    : {item.get('outcome')}")
        print()

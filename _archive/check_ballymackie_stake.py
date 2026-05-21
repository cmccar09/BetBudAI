import boto3

table = boto3.resource('dynamodb', region_name='eu-west-1').Table('SureBetBets')
resp = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key('bet_date').eq('2026-02-10')
)

ballymackie = [i for i in resp['Items'] if 'Ballymackie' in i.get('horse', '')][0]

print(f"stake: {ballymackie.get('stake')}")
print(f"odds: {ballymackie.get('odds')}")
print(f"starting_price: {ballymackie.get('starting_price')}")
print(f"outcome: {ballymackie.get('outcome')}")
print(f"show_in_ui: {ballymackie.get('show_in_ui')}")

"""Check if River Voyage outcome appears anywhere in DynamoDB across all dates."""
import boto3
from decimal import Decimal
from boto3.dynamodb.conditions import Attr

def float_it(o):
    if isinstance(o, Decimal): return float(o)
    if isinstance(o, dict): return {k: float_it(v) for k,v in o.items()}
    if isinstance(o, list): return [float_it(v) for v in o]
    return o

ddb = boto3.resource('dynamodb', region_name='eu-west-1')
table = ddb.Table('SureBetBets')

# Scan for River Voyage
resp = table.scan(FilterExpression=Attr('horse').eq('River Voyage'))
items = [float_it(x) for x in resp.get('Items', [])]
print(f"River Voyage records: {len(items)}")
for x in items:
    print(f"  bet_date={x.get('bet_date')} outcome={x.get('outcome')} finish={x.get('finish_position')} winner={x.get('winner_horse')} mkt={x.get('market_id')} sel={x.get('selection_id')}")

# Also check L'aventara
resp2 = table.scan(FilterExpression=Attr('horse').eq("L'aventara"))
items2 = [float_it(x) for x in resp2.get('Items', [])]
print(f"\nL'aventara records: {len(items2)}")
for x in items2:
    print(f"  bet_date={x.get('bet_date')} outcome={x.get('outcome')} finish={x.get('finish_position')} winner={x.get('winner_horse')}")

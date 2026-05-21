"""Search with contains for apostrophe names."""
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

resp = table.scan(FilterExpression=Attr('horse').contains('aventara'))
items = [float_it(x) for x in resp.get('Items', [])]
print(f"aventara records: {len(items)}")
for x in items:
    print(f"  bet_date={x.get('bet_date')} horse={x.get('horse')} outcome={x.get('outcome')} finish={x.get('finish_position')} show_in_ui={x.get('show_in_ui')}")

resp2 = table.scan(FilterExpression=Attr('horse').contains('River'))
items2 = [float_it(x) for x in resp2.get('Items', [])]
print(f"\nRiver records: {len(items2)}")
for x in items2:
    print(f"  bet_date={x.get('bet_date')} horse={x.get('horse')} course={x.get('course')} outcome={x.get('outcome')} finish={x.get('finish_position')}")

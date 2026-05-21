import boto3
from decimal import Decimal
import json

dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
table = dynamodb.Table('SureBetBets')

def d2f(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: d2f(v) for k, v in obj.items()}
    if isinstance(obj, list): return [d2f(i) for i in obj]
    return obj

# Check SYSTEM_WEIGHTS (key: bet_date=CONFIG, bet_id=SYSTEM_WEIGHTS)
try:
    resp = table.get_item(Key={'bet_date': 'CONFIG', 'bet_id': 'SYSTEM_WEIGHTS'})
    item = d2f(resp.get('Item', {}))
    if item:
        print("SYSTEM_WEIGHTS found:")
        print(f"  version: {item.get('version', 'unknown')}")
        print(f"  last_updated: {item.get('last_updated', item.get('updated_at', 'unknown'))}")
        print(f"  notes: {item.get('notes', '')}")
        weights = item.get('weights', {})
        for k, v in sorted(weights.items()):
            print(f"  {k}: {v}")
    else:
        print("No SYSTEM_WEIGHTS record found at CONFIG/SYSTEM_WEIGHTS")
except Exception as e:
    print(f"Error: {e}")

# Also check for any SYSTEM records (scan for bet_date=SYSTEM)
print("\n--- All SYSTEM records ---")
try:
    resp = table.query(
        KeyConditionExpression='bet_date = :s',
        ExpressionAttributeValues={':s': 'CONFIG'}
    )
    items = [d2f(i) for i in resp.get('Items', [])]
    print(f"Found {len(items)} CONFIG records")
    for item in items:
        print(f"  bet_id={item.get('bet_id')} updated_at={item.get('updated_at', '?')}")
        w = item.get('weights', {})
        if w:
            print(f"  weights: {json.dumps(w)[:200]}")
except Exception as e:
    print(f"Error scanning SYSTEM: {e}")

# Check weight_nudges history
print("\n--- Learning history ---")
try:
    resp = table.query(
        KeyConditionExpression='bet_date = :s',
        ExpressionAttributeValues={':s': 'LEARNING'}
    )
    items = [d2f(i) for i in resp.get('Items', [])]
    print(f"Found {len(items)} LEARNING records")
    for item in items[:5]:
        print(f"  {item.get('bet_id')} | {item.get('applied_at', '?')} | nudges={item.get('nudges', {})}")
except Exception as e:
    print(f"Error: {e}")
